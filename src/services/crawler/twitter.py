from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
from typing import List, Set, Optional, Dict, Any
from contextlib import asynccontextmanager
import random
from datetime import datetime, timedelta, timezone
import re
import logging
import  traceback
from pydantic import ValidationError

from src.utils.common import parse_date, download_content
from src.database.models.pydantic_models import Category, TweetDetails,TwitterCredentials, TweetDB, InitialTweetState
from src.database.models.models import Tweet
from src.core.exceptions import TwitterAuthError, TwitterScraperError
from src.database.repositories.repositories import TweetRepository, TwitterAccountRepository, CategoryRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TwitterAuth:
    """Handles Twitter authentication"""

    def __init__(self, credentials: TwitterCredentials):
        self.credentials: TwitterCredentials = credentials

    async def _check_login_selector_present(self, page: Page) -> bool:
        """Check if login is required based on current page state"""
        try:
            await page.wait_for_load_state(timeout=150000)
            login_indicator = await page.query_selector('input[autocomplete="username"], form[action="/i/flow/login"]')
            if login_indicator:
                logger.info("Login required")
                return True 
            logger.info("No login required")
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
            await asyncio.sleep(9)
            if not await self._check_login_selector_present(page):
                logger.info("No login required")
                return True

            logger.info("Starting authentication process...")

            logger.info("Waiting for username input...")
            await page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await page.fill('input[autocomplete="username"]', self.credentials.username)#self.credentials.username)

            await page.click('button[role="button"]:has-text("Next")')

            # Wait for next screen to load
            await page.wait_for_load_state('networkidle', timeout=50000)


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

            try:
                # Verify login success
                await page.wait_for_selector('[data-testid="AppTabBar_Home_Link"], article[data-testid="tweet"]', timeout=10000)
                logger.info("Login successful")
                return True
            except PlaywrightTimeoutError:
                logger.error("Login verification failed")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise TwitterAuthError(f"Authentication failed: {str(traceback.format_exc())}")


class TwitterScraper:
    """Handles Twitter scraping operations"""

    def __init__(self, auth: TwitterAuth, tweet_db_repo: TweetRepository, username_to_scrape: List[str], days_to_scrape: int, headless: bool = False):
        self.auth = auth
        self.username_to_scrape = [username.strip('@').lower() for username in username_to_scrape] 
        self.days_to_scrape = days_to_scrape
        self.processed_ids = set()
        self.db_ids = set()
        self.cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_scrape)
        self.headless = headless
        self.tweet_db_repo = tweet_db_repo
        self.current_account = None

        
    def _build_search_urls(self) -> List[str]:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.days_to_scrape)

        end_date_str = end_date.strftime('%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d')

        queries = []
        for username in self.username_to_scrape:
            query_parts = [
                f"from:{username}",
                "-filter:replies",
                "-filter:retweets",
                f"since:{start_date_str}",
                f"until:{end_date_str}"
            ]
            query = "%20".join(query_parts)
            url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            queries.append(url)

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


    async def _wait_for_network_idle(self, page: Page, timeout: int = 40000):
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
            tweet_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            tweet_date = tweet_date.replace(tzinfo=timezone.utc)

            return TweetDetails(id=tweet_id, date=tweet_date) 

        except Exception as e:
            logger.error(f"Error extracting tweet info: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    async def _scroll_page(self, page: Page, consecutive_empty: int = 2):
        """Perform adaptive scrolling with increasing scroll length"""
        try:
            # Base scroll amount increases with consecutive empty results
            base_scroll = 800 + (consecutive_empty * 200)  # Increase scroll amount when no new tweets found
            random_addition = random.randint(100, 200)
            total_scroll = base_scroll + random_addition
            await page.evaluate(f"window.scrollBy(0, {total_scroll})")

            # Adaptive wait time based on scroll distance
            wait_time = 2000 + (total_scroll / 850) * 500
            await page.wait_for_timeout(wait_time)
            await self._wait_for_network_idle(page)
        except Exception as e:
            logger.warning(f"Scroll error: {str(e)}")
            await page.wait_for_timeout(3000)

    async def initial_scrape(self) -> Dict[str, List[Any]]:
        """Main method to scrape tweets"""
        try:
            async with self._setup_browser() as browser:
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(100000)

                self.db_ids = set(await self.tweet_db_repo.get_all_ids())
                all_tweets: Dict[str, List[Any]] = {}

                search_urls = self._build_search_urls()
                for search_url in search_urls:
                    await page.goto(search_url, wait_until="domcontentloaded")
                    logger.info(f"Navigated to search page: {search_url}")

                    self.current_account = re.findall(r'from:(\w+)', search_url)[0]
                    all_tweets[self.current_account] = []

                    if not await self.auth.authenticate(page):
                        logger.error("Authentication failed")
                        raise TwitterAuthError("Authentication failed")

                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_scrape)
                    last_tweet_date = datetime.now(timezone.utc)
                    processed_ids: Set[str] = set()
                    consecutive_empty = 0

                    while last_tweet_date > cutoff_date:
                        try:
                            new_tweets = await self._scrape_tweets_from_page(page, processed_ids)

                            if not new_tweets:
                                consecutive_empty += 1
                                if consecutive_empty >= 3:
                                    logger.info(
                                        f"No new tweets found for account {self.current_account} after {consecutive_empty} attempts")
                                    break
                            else:
                                consecutive_empty = 0
                                all_tweets[self.current_account].extend(new_tweets)
                                last_tweet_date = new_tweets[-1].date

                            logger.info(
                                f"Collected {len(all_tweets[self.current_account])} tweets for account: {self.current_account}. Last tweet date: {last_tweet_date}")

                            if last_tweet_date <= cutoff_date:
                                logger.info(f"Reached cutoff date: {cutoff_date}")
                                break

                            await self._scroll_page(page, consecutive_empty)

                        except Exception as e:
                            logger.error(f"Error during scraping: {str(e)}")
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            await page.wait_for_timeout(2000)

                return all_tweets

        except Exception as e:
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise TwitterScraperError(f"Scraping failed: {str(e)}")

    async def _scrape_tweets_from_page(self, page, processed_ids: Set[str]) -> List[Any]:
        articles = await page.query_selector_all('article[data-testid="tweet"]')
        new_tweets = []

        for article in articles:
            tweet = await self._extract_tweet_info(article)
            if tweet and tweet.id not in processed_ids and tweet.id not in self.db_ids:
                new_tweets.append(tweet)
                processed_ids.add(tweet.id)

        return new_tweets

class TweetProcessor:
    def __init__(self, scraper: TwitterScraper, tweet_repo: TweetRepository, account_repo: TwitterAccountRepository, category_repo: CategoryRepository, twitter_api:str = 'https://api.vxtwitter.com/Twitter/status/'):
        self.scraper = scraper
        self.tweet_repo = tweet_repo
        self.account_repo = account_repo
        self.category_repo = category_repo
        self.mapped_account_names_to_categories = dict()
        self.twitter_api = twitter_api

    async def _get_tweets(self) -> Dict[str, List[Any]]:
        try:
            failed: Dict[str, List[Any]] = {}
            success: Dict[str, List[Any]] = {}
            tweets: Dict[str, List[TweetDetails]] = await self.scraper.initial_scrape()

            for account, tweet_list in tweets.items():
                for tweet in tweet_list:
                    tweet_url = f"{self.twitter_api}{tweet.id}"
                    tweet_json = await download_content(url=str(tweet_url))
                    if not tweet_json:
                        logger.error(f"Error fetching tweet {tweet.id}")
                        failed[account].append(tweet.id)
                        continue
                    success[account].append(tweet_json)
            return success
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {}

    async def _map_ids_to_categories(self):
        try:
            account_details = await self.account_repo.get_account_details()
            category_mappings = await self.category_repo.get_account_category_mappings()

            # Create mappings using explicit integer keys
            account_id_to_name = {int(account_id): username
                                  for account_id, username in account_details}
            account_id_to_category = {int(account_id): int(category_id)
                                      for account_id, category_id in category_mappings}

            # Build the final mapping
            self.mapped_account_names_to_categories = {}
            for account_id in account_id_to_name:
                if account_id in account_id_to_category:
                    self.mapped_account_names_to_categories[account_id_to_name[account_id]] = (
                        account_id,
                        account_id_to_category[account_id]
                    )
            logger.info(f"Mapped account names to categories: {self.mapped_account_names_to_categories}")

        except Exception as e:
            logger.error(f"Error mapping ids to categories: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _transform_tweet_objects(self, tweets: List[List[Dict]]) -> List[Tweet]:
        try:
            tweet_objects = []
            for tweet in tweets:
                account_id, category_id = self.mapped_account_names_to_categories[tweet['user_screen_name']]
                logger.info(f"Mapping account {account_id} to category {category_id}")
                dt = parse_date(tweet['date'])
                tweet_objects.append(Tweet(
                    twitter_id=str(tweet['tweetID']),
                    account_id=int(account_id),
                    category_id=int(category_id),
                    text=tweet['text'],
                    media_urls=tweet['mediaURLs'],
                    created_at=dt
                ))
            return tweet_objects
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

    async def _insert_tweets(self, tweets: List[List[Dict]]) -> bool:
        try:
            tweet_objects: List[Tweet] = self._transform_tweet_objects(tweets)
            if not tweet_objects:
                logger.info("No tweet objects to insert")
                return False
            await self.tweet_repo.create_all(tweet_objects)
            return True
        except Exception as e:
            logger.error(f"Error inserting tweets: {str(e)}")
            await self.tweet_repo.session.rollback()
            return False

    async def process_tweets(self) -> bool:
        try:
            await self._map_ids_to_categories()
            tweets_dict = await self._get_tweets()
            if not tweets_dict:
                logger.info("No tweets to process")
                return False
            for account, tweets in tweets_dict.items():
                await self._insert_tweets(tweets)
                await self.account_repo.update_last_fetched(account)
        except Exception as e:
            logger.error(f"Error processing tweets: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
async def main():
    from src.database.db import get_session
    from src.database.repositories.repositories import CategoryRepository, TweetRepository, TwitterAccountRepository
    from src.database.models.pydantic_models import TwitterCredentials
    from src.core.config import TWITTER_CREDENTIALS 

    try:
        # Initialize repositories
        logger.info("Initializing session")
        async with get_session() as session:
            logger.info("Initialized session")
            tweet_repo = TweetRepository(Tweet, session)
            account_repo = TwitterAccountRepository(TwitterAccountRepository, session)
            category_repo = CategoryRepository(CategoryRepository, session)

            # Initialize Twitter scraper
            auth = TwitterAuth(TwitterCredentials(**TWITTER_CREDENTIALS.model_dump()))
            scraper = TwitterScraper(auth, tweet_repo, ["vim_tricks", "Neovim", "LinusTech", "itpourya", "msc72m"], 10, headless=False)
            processor = TweetProcessor(scraper, tweet_repo, account_repo, category_repo)
            # Process tweets
            await processor.process_tweets()
            return None

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
