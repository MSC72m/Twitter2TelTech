import logging
from httpx import AsyncClient
from httpx import AsyncClient, TimeoutException, HTTPStatusError
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)


async def download_content(self, url: str) -> List[Dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        # Note the parentheses after AsyncClient and await for async operations
        async with AsyncClient(verify=False, timeout=15.0) as client:
            response = await client.get(
                url,
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


def parse_date(self, date_str: str) -> datetime:
    try:
        # Parse Twitter's date format
        dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        # Convert to UTC
        return dt.astimezone(timezone.utc)
    except ValueError as e:
        logger.error(f"Failed to parse date: {date_str}, error: {e}")
        return None