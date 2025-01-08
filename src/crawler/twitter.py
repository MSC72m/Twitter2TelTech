import asyncio

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from httpx import AsyncClient, TimeoutException, HTTPStatusError
from sqlalchemy.ext.asyncio import AsyncSession
import random
import os
import json
from datetime import datetime, timezone
import re
import logging

from src.database.models.pydantic_models import TweetDetails,TwitterCredentials, Tweet, InitialTweetState
from src.core.exceptions import TwitterAuthError, TwitterScraperError
from src.database.repositories.repositories import TweetRepository, TwitterAccountRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()


class TwitterAuth:
    """Handles Twitter authentication"""

    def __init__(self, credentials: TwitterCredentials):
        self.credentials: TwitterCredentials = credentials

    async def _check_login_selector_present(self, page: Page) -> bool:
        """Check if login is required based on current page state"""
        try:
            login_indicator = await page.query_selector('input[autocomplete="username"], form[action="/i/flow/login"]')
            if login_indicator:
                logger.info("Login required")
                return True
            return False

        except Exception:
            return False
    
    async def _check_auth_token_present(self, page: Page) -> bool:
        try:
            # Check if there is an Auth token
            cookies = await page.context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'auth_token':
                    logger.info("Auth token found")
                    return True
            return False 


        except Exception as e:
            logger.error(f"Error checking auth token: {str(e)}")
            raise
    async def authenticate(self, page: Page) -> bool:
        """Perform Twitter authentication in current window"""
        try:
            if not await self._check_login_selector_present(page) or await self._check_auth_token_present(page):
                logger.info("No login required")
                return True

            logger.info("Starting authentication process...")

            logger.info("Waiting for username input...")
            await page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await page.fill('input[autocomplete="username"]', "msc72m_dev")#self.credentials.username)

            await page.click('button[role="button"]:has-text("Next")')

            # Wait for next screen to load
            await page.wait_for_load_state('networkidle', timeout=15000)


            pass_entry = await page.query_selector('input[type="password"]')
            if not pass_entry:
                logger.info("password input not found, trying email input...")
                logger.info(f"waiting for email input...")
                await page.wait_for_selector('input[type="text"]', timeout=15000)
                await page.fill('input[type="text"]', self.credentials.email)
                await page.click('button[type="button"]:has-text("Next")')

            await page.fill('input[type="password"]', self.credentials.password)
            await page.click('button[type="button"]:has-text("Log in")')

            await page.wait_for_timeout(7000)

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

    def __init__(self, auth: TwitterAuth, tweet_db_repo: TweetRepository, username_to_scrape: List[str], days_to_scrape: int, headless: bool = False):
        self.auth = auth
        self.username_to_scrape = [username.strip('@').lower() for username in username_to_scrape] 
        self.days_to_scrape = days_to_scrape
        self.cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_scrape)
        self.processed_ids = set()
        self.twitter_api = "https://api.vxtwitter.com/Twitter/status"
        self.headless = headless
        self.tweet_db_repo = tweet_db_repo
        self.current_account = None

        
    def _build_search_urls(self) -> str:
        """Build Twitter search URL with appropriate filters"""
        end_date = datetime.datetime.now(datetime.timezone.utc)
        end_date_str = end_date.strftime('%Y-%m-%d')

        # -filter:replies -> excludes replies
        # -filter:retweets -> excludes retweets
        # min_faves:1 -> minimum 1 like to filter out potential spam
        queries = []
        for username in self.username_to_scrape:
            query_parts = [
                f"from:{username}",
                "-filter:replies",
                "-filter:retweets",
                "min_faves:1",
                f"until:{end_date_str}"
            ]
            query = "%20".join(query_parts)
            queries.append(query)
        return queries 

    @asynccontextmanager
    async def _setup_browser(self) -> Browser:
        """Set up browser with appropriate configurations"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36",
                ignore_https_errors=True
            )

            try:
                yield browser
            finally:
                await browser.close()


    async def _wait_for_network_idle(self, page: Page, timeout: int = 6000):
        """Wait for network to become idle"""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout reached")

    async def _extract_tweet_info(self, article) -> Optional[TweetDetails]:
        """Extract essential information from a tweet article element"""
        try:
            article_html = await article.evaluate('element => element.innerHTML')

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

            return TweetDetails(_id=tweet_id, date=tweet_date) 

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

    async def initial_scrape(self) -> Dict[List[Tweet]]:
        """Main method to scrape tweets"""
        # TODO: Need to implement logic to retrive all present ids from database all at once and do local check and not query for each of them
        # TODO: need to revamp crawling logic seems buggy
        try:
            async with self._setup_browser() as browser:
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(60000)
                all_tweets = {}
                self.processed_ids = await self.tweet_db_repo.get_all_ids()

                # Authenticate if necessary
                if not await self.auth.authenticate(page):
                    logger.error("Authentication failed")
                    raise TwitterAuthError("Authentication failed")

                # Navigate to search page
                search_urls = self._build_search_urls()
                for search_url in search_urls:
                    await page.goto(search_url, wait_until="domcontentloaded")
                    logger.info(f"Navigated to search page: {search_url}")
                    self.current_account = re.findall(r'from:(\w+)', search_url)[0]

                    account_tweets: Dict[List[TweetDetails]] = {} 
                    consecutive_empty = 0
                    empty_limit = 20 # Increased limit for more thorough scanning
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
                                    if tweet._id in self.processed_ids:
                                        logger.info(f"Tweet {tweet._id} already exists in database")
                                        continue

                                    if tweet.date < self.cutoff_date:
                                        logger.info(f"Reached cutoff date. Last tweet from: {tweet.date}")
                                        all_tweets[self.current_account] = sorted(account_tweets, key=lambda x: x.date, reverse=True)

                                    # Check if we've already seen this tweet
                                    if tweet._id not in {t._id for t in account_tweets}:
                                        account_tweets.append(tweet)
                                        self.processed_ids.add(tweet._id)
                                        new_tweets_found = True
                                        last_tweet_date = tweet.date
                                        logger.info(f"Found tweet {tweet.id} from {tweet.date}")

                            if new_tweets_found:
                                consecutive_empty = 0
                            else:
                                consecutive_empty += 1

                            logger.info(f"Collected {len(account_tweets)} tweets for account: {self.current_account} so far... Last tweet date: {last_tweet_date}")
                            await self._scroll_page(page, consecutive_empty)

                        except Exception as e:
                            logger.error(f"Error during scraping: {str(e)}")
                            consecutive_empty += 1
                            await page.wait_for_timeout(2000)
                return all_tweets 
        except Exception as e:
            logger.error(f"Fatal error in scrape_tweets: {str(e)}")
            raise TwitterScraperError(f"Scraping failed: {str(e)}")

    async def get_tweet(self, tweet_id: str) -> List[Dict]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        try:
            # Note the parentheses after AsyncClient and await for async operations
            async with AsyncClient(verify=False, timeout=15.0) as client:
                response = await client.get(
                    f"{self.twitter_api}/{tweet_id}",
                    headers=headers
                )
                await response.aread()  # Ensure the response body is fully read
                response.raise_for_status()

                tweet_content = response.json()

                if not tweet_content:
                    logger.info(f"No tweet content found for tweet ID {tweet_id}")
                    return []

                logger.info(f"Successfully scraped tweet {tweet_id}")
                logger.debug(f"Tweet content: {tweet_content}")

                return tweet_content

        except TimeoutException as e:
            logger.error(f"Timeout while fetching tweet {tweet_id}: {str(e)}")
            return []

        except HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if e.response.status_code == 404:
                logger.info(f"Tweet {tweet_id} not found")
            else:
                logger.error(f"Failed to fetch tweet {tweet_id}: {error_msg}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error fetching tweet {tweet_id}: {str(e)}")
            return []

class TweetProcessor:
    def __init__(self, scraper: TwitterScraper, tweet_repo: TweetRepository, account_repo: TwitterAccountRepository):
        self.scraper = scraper
        self.tweet_repo = tweet_repo
        self.account_repo = account_repo
        self.maped_account_names_to_categories = dict()

    def _parse_date(self, date_str: str) -> datetime:
        try:
            # Parse Twitter's date format
            dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
            # Convert to UTC
            return dt.astimezone(timezone.utc)
        except ValueError as e:
            logger.error(f"Failed to parse date: {date_str}, error: {e}")
            return None

    async def _get_tweets(self) -> List[InitialTweetState]:
        try:
            failed = [] 
            success = []
            tweets: Dict[str, TweetDetails] = await self.scraper.initial_scrape()
            for tweet in tweets:
                tweet_json = await self.scraper.get_tweet(tweet._id)
                if not tweet_json:
                    logger.error(f"Error fetching tweet {tweet._id}")
                    failed.append(tweet._id)
                    continue
                success.append(tweet_json)
                self.present_ids.add(tweet._id)
            return success
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []

    async def _map_ids_to_categories(self):
        try:
            account_name_category_list = await self.account_repo.get_all_name_category()
            self.maped_account_names_to_categories = {
                account_name: (account_id, category) for account_id, account_name, category in account_name_category_list
            }
            return 
        except Exception as e: 
            logger.error(f"Error mapping ids to categories: {str(e)}")
            raise

    def _transform_tweet_objects(self, tweets: List[InitialTweetState]) -> List[Tweet]:
        tweet_objects = []
        for tweet in tweets:
            account_id, category_id = self.maped_account_names_to_categories[tweet['user_name']]
            dt = self._parse_date(tweet['date'])
            tweet_objects.append(Tweet(
                twitter_id=tweet['tweetID'],
                account_id=account_id,
                category_id=category_id,
                content=tweet['text'],
                media_urls=tweet['mediaURLs'],
                created_at=dt
            ))
        return tweet_objects

    async def _insert_tweets(self, tweets: List[InitialTweetState]) -> bool:
        try:
            tweet_objects: List[Tweet] = self.transform_tweet_objects(tweets)
            if not tweet_objects:
                logger.info("No tweet objects to insert")
                return False
            await self.tweet_repo.create_all(tweet_objects)
            return True
        except Exception as e:
            logger.error(f"Error inserting tweets: {str(e)}")
            await self.session.rollback()
            return False

    async def process_tweets(self) -> bool:
        try:
            tweets = await self._get_tweets()
            if not tweets:
                logger.info("No tweets to process")
                return False
            tweet_objects = self._transform_tweet_objects(tweets)
            if not tweet_objects:
                logger.info("No tweet objects to process")
                return False
            return await self._insert_tweets(tweet_objects)
        except Exception as e:
            logger.error(f"Error processing tweets: {str(e)}")
            return False 
    

if __name__ == "__main__":
    try:
        asyncio.run()
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main function: {str(e)}")
