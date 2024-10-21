import asyncio 
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import datetime
import re
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterIDScraper:
    def __init__(self, username: str, days_to_scrape: int):
        self.username = username
        self.days_to_scrape = days_to_scrape
        self.cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_scrape)

    async def get_tweet_info(self, article) -> Tuple[str, datetime.datetime]:
        try:
            link = await article.query_selector('a[href*="/status/"]')
            href = await link.get_attribute('href')
            tweet_id = re.search(r'/status/(\d+)', href).group(1)
            
            time_element = await article.query_selector('time')
            if time_element:
                datetime_str = await time_element.get_attribute('datetime')
                tweet_date = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
            else:
                tweet_date = None
            
            return tweet_id, tweet_date
        except Exception as e:
            logger.error(f"Error getting tweet info: {str(e)}")
            return None, None

    async def scrape_tweet_ids(self) -> List[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()

                await page.goto(f"https://twitter.com/{self.username}")
                await page.wait_for_selector('article[data-testid="tweet"]')  # Wait for the first tweet to load
                
                all_tweets = []
                last_height = 0
                consecutive_no_new_tweets = 0
                
                while True:
                    current_height = await page.evaluate('document.body.scrollHeight')
                    
                    tweet_articles = await page.query_selector_all('article[data-testid="tweet"]')
                    
                    new_tweets_found = False
                    for article in tweet_articles:
                        tweet_id, tweet_date = await self.get_tweet_info(article)
                        if tweet_id and tweet_id not in [t[0] for t in all_tweets]:
                            all_tweets.append((tweet_id, tweet_date))
                            new_tweets_found = True
                            logger.info(f"Found tweet: {tweet_id}, Date: {tweet_date or 'Unknown'}")

                    if new_tweets_found:
                        consecutive_no_new_tweets = 0
                    else:
                        consecutive_no_new_tweets += 1

                    logger.info(f"Collected {len(all_tweets)} tweets so far...")

                    if consecutive_no_new_tweets > 5:
                        logger.info("No new tweets found in multiple scrolls. Stopping collection.")
                        break

                    # Scroll
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)  # Wait for 2 seconds after each scroll

                    if current_height == last_height:
                        logger.info("Reached the end of the timeline. Stopping collection.")
                        break
                    last_height = current_height

                await browser.close()

            # Filter tweets based on date after collection
            filtered_tweets = [
                tweet_id for tweet_id, tweet_date in all_tweets
                if tweet_date is None or tweet_date >= self.cutoff_date
            ]

            logger.info(f"Filtered to {len(filtered_tweets)} tweets within the last {self.days_to_scrape} days.")
            return filtered_tweets

        except Exception as e:
            logger.error(f"Fatal error in scrape_tweet_ids: {str(e)}")
            return []

async def main():
    try:
        scraper = TwitterIDScraper("MSC72m", 10)  # Scrape tweets from the last 10 days
        tweet_ids = await scraper.scrape_tweet_ids()
        logger.info(f"Scraped {len(tweet_ids)} unique tweet IDs in total")
        for tweet_id in tweet_ids[:10]:  # Log first 10 IDs as an example
            logger.info(f"Tweet ID: {tweet_id}")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())