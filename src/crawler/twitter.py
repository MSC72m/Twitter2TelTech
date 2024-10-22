import asyncio 
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
import datetime
import re
from typing import List, Optional
import logging
from pathlib import Path
from dataclasses import dataclass
from contextlib import asynccontextmanager
import random
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TwitterCredentials:
    """Data class to store Twitter credentials"""
    username: str
    password: str
    email: str

@dataclass
class Tweet:
    """Data class to store tweet information"""
    id: str
    date: datetime.datetime

class TwitterAuthError(Exception):
    """Custom exception for authentication errors"""
    pass

class TwitterScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class TwitterAuth:
    """Handles Twitter authentication"""
    
    def __init__(self, credentials: TwitterCredentials):
        self.credentials = credentials

    async def _check_login_required(self, page: Page) -> bool:
        """Check if login is required based on current page state"""
        try:
            login_indicator = await page.query_selector('input[autocomplete="username"], form[action="/i/flow/login"]')
            return login_indicator is not None
        except Exception:
            return False

    async def authenticate(self, page: Page) -> bool:
        """Perform Twitter authentication in current window"""
        try:
            logger.info("Starting authentication process...")
            
            logger.info("Waiting for username input...")
            await page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await page.fill('input[autocomplete="username"]', self.credentials.username)
            
            await page.click('button[role="button"]:has-text("Next")')

            await page.wait_for_timeout(3000)

            logger.info("Looking for password input...")
            pass_entry = await page.wait_for_selector('input[type="password"]', timeout=1000)
            if not pass_entry:
                logger.info(f"waiting for email input...")
                await page.wait_for_selector('input[type="text"]', timeout=10000)
                await page.fill('input[type="text"]', self.credentials.email)
                await page.click('button[type="button"]:has-text("Next")')
                
                logger.info("Looking for password input...")
                await page.wait_for_selector('input[type="password"]', timeout=10000)
                await page.fill('input[type="password"]', self.credentials.password)
                await page.click('button[type="button"]:has-text("Log in")')
                await page.wait_for_timeout(5000)

            await page.fill('input[type="password"]', self.credentials.password)
            await page.click('button[type="button"]:has-text("Log in")')
            
            await page.wait_for_timeout(5000)
            
            # Wait for login to complete
            await page.wait_for_timeout(5000)
            
            # Verify login success
            try:
                await page.wait_for_selector('[data-testid="AppTabBar_Home_Link"], article[data-testid="tweet"]', timeout=10000)
                logger.info("Login successful")
                return True
            except PlaywrightTimeoutError:
                logger.error("Login verification failed")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise TwitterAuthError(f"Authentication failed: {str(e)}")

class TwitterScraper:
    """Handles Twitter scraping operations"""
    
    def __init__(self, credentials: TwitterCredentials, username_to_scrape: str, days_to_scrape: int):
        self.credentials = credentials
        self.username_to_scrape = username_to_scrape.strip('@')
        self.days_to_scrape = days_to_scrape
        self.cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_scrape)
        self.processed_tweets = set()

    def _build_search_url(self) -> str:
        """Build Twitter search URL with appropriate filters"""
        end_date = datetime.datetime.now(datetime.timezone.utc)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # -filter:replies -> excludes replies
        # -filter:retweets -> excludes retweets
        # min_faves:1 -> minimum 1 like to filter out potential spam
        query_parts = [
            f"from:{self.username_to_scrape}",
            "-filter:replies",
            "-filter:retweets",
            "min_faves:1",
            f"until:{end_date_str}"
        ]
        query = "%20".join(query_parts)
        return f"https://x.com/search?q={query}&src=typed_query&f=live"

    @asynccontextmanager
    async def _setup_browser(self) -> Browser:
        """Set up browser with appropriate configurations"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36",
                ignore_https_errors=True
            )
            
            try:
                yield browser
            finally:
                await browser.close()


    async def _wait_for_network_idle(self, page: Page, timeout: int = 30000):
        """Wait for network to become idle"""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout reached")

    async def _extract_tweet_info(self, article) -> Optional[Tweet]:
        """Extract essential information from a tweet article element"""
        try:
            article_html = await article.evaluate('element => element.innerHTML')
            if article_html in self.processed_tweets:
                return None
            
            # Get tweet ID
            link = await article.query_selector('a[href*="/status/"]')
            if not link:
                return None
                
            href = await link.get_attribute('href')
            tweet_id_match = re.search(r'/status/(\d+)', href)
            if not tweet_id_match:
                return None
            
            tweet_id = tweet_id_match.group(1)
            
            # Get timestamp
            time_element = await article.query_selector('time')
            if not time_element:
                return None
                
            datetime_str = await time_element.get_attribute('datetime')
            tweet_date = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            tweet_date = tweet_date.replace(tzinfo=datetime.timezone.utc)

            self.processed_tweets.add(article_html)
            return Tweet(id=tweet_id, date=tweet_date)
            
        except Exception as e:
            logger.error(f"Error extracting tweet info: {str(e)}")
            return None

    async def _scroll_page(self, page: Page, consecutive_empty: int):
        """Perform adaptive scrolling with increasing scroll length"""
        try:
            # Base scroll amount increases with consecutive empty results
            base_scroll = 750 + (consecutive_empty * 250)  # Increase scroll amount when no new tweets found
            random_addition = random.randint(200, 600)
            total_scroll = base_scroll + random_addition
            
            await page.evaluate(f"window.scrollBy(0, {total_scroll})")
            
            # Adaptive wait time based on scroll distance
            wait_time = 2500 + (total_scroll / 750) * 500
            await page.wait_for_timeout(wait_time)
            await self._wait_for_network_idle(page)
            
        except Exception as e:
            logger.warning(f"Scroll error: {str(e)}")
            await page.wait_for_timeout(3000)

    async def scrape_tweets(self) -> List[Tweet]:
        """Main method to scrape tweets"""
        try:
            async with self._setup_browser() as browser:
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(60000)
                auth = TwitterAuth(self.credentials)

                # Navigate to search page
                search_url = self._build_search_url()
                await page.goto(search_url, wait_until="domcontentloaded")
                await auth._check_login_required(page)
                await auth.authenticate(page)
                logger.info(f"Navigated to search page: {search_url}")

                tweets: List[Tweet] = []
                consecutive_empty = 0
                empty_limit = 10  # Increased limit for more thorough scanning
                last_tweet_date = datetime.datetime.now(datetime.timezone.utc)
                
                while True:
                    try:
                        articles = await page.query_selector_all('article[data-testid="tweet"]')
                        
                        if not articles:
                            consecutive_empty += 1
                            if consecutive_empty >= empty_limit:
                                logger.info("Reached end of available tweets")
                                break
                            await page.wait_for_timeout(2000)
                            await self._scroll_page(page, consecutive_empty)
                            continue

                        new_tweets_found = False
                        
                        for article in articles:
                            tweet = await self._extract_tweet_info(article)
                            
                            if tweet:
                                # Check if this tweet is older than our target date
                                if tweet.date < self.cutoff_date:
                                    logger.info(f"Reached cutoff date. Last tweet from: {tweet.date}")
                                    return sorted(tweets, key=lambda x: x.date, reverse=True)
                                
                                # Check if we've already seen this tweet
                                if tweet.id not in {t.id for t in tweets}:
                                    tweets.append(tweet)
                                    new_tweets_found = True
                                    last_tweet_date = tweet.date
                                    logger.info(f"Found tweet {tweet.id} from {tweet.date}")
                        
                        if new_tweets_found:
                            consecutive_empty = 0
                        else:
                            consecutive_empty += 1
                            
                        logger.info(f"Collected {len(tweets)} tweets so far... Last tweet date: {last_tweet_date}")
                        await self._scroll_page(page, consecutive_empty)

                    except Exception as e:
                        logger.error(f"Error during scraping: {str(e)}")
                        consecutive_empty += 1
                        await page.wait_for_timeout(2000)

                # Sort tweets by date (newest first)
                return sorted(tweets, key=lambda x: x.date, reverse=True)

        except Exception as e:
            logger.error(f"Fatal error in scrape_tweets: {str(e)}")
            raise TwitterScraperError(f"Scraping failed: {str(e)}")
    
async def main():
    # Twitter credentials
    load_dotenv()
    credentials = TwitterCredentials(
        username=os.getenv("TWITTER_USERNAME"),
        password=os.getenv("TWITTER_PASSWORD"),
        email=os.getenv("TWITTER_EMAIL"),
    )
    
    try:
        # Initialize scraper with credentials and target account
        scraper = TwitterScraper(
            credentials=credentials,
            username_to_scrape="MSC72m",
            days_to_scrape=4
        )
        
        # Perform scraping
        tweets = await scraper.scrape_tweets()
        logger.info(f"Successfully scraped {len(tweets)} tweets")
        
        # Print results
        for tweet in tweets[:10]:
            logger.info("-" * 50)
            logger.info(f"Tweet ID: {tweet.id}")
            logger.info(f"Date: {tweet.date}")
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())