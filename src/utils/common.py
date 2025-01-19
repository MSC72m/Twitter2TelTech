import logging
from httpx import AsyncClient, TimeoutException, HTTPStatusError
import  traceback
from datetime import datetime, timezone
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


async def download_content(url: str) -> List[Dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        # Note the parentheses after AsyncClient and await for async operations
        async with AsyncClient(verify=False, timeout=15.0) as client:
            response = await client.get(
                url,
                headers=headers,
            )
            await response.aread()  # Ensure the response body is fully read
            response.raise_for_status()

            tweet_content = response.json()

            if not tweet_content:
                logger.error(f"No tweet content found for url: {url}")
                return []

            return tweet_content

    except TimeoutException as e:
        logger.error(f"Timeout while fetching url {url}: {str(e)}")
        return []

    except HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}"
        logger.error(f"Failed to fetch url: {url}: {error_msg}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error fetching url: {url}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return []


def parse_date(date_str: str) -> Optional[datetime]:
    try:
        # Parse Twitter's date format
        dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        # Convert to UTC
        return dt.astimezone(timezone.utc)
    except ValueError as e:
        logger.error(f"Failed to parse date: {date_str}, error: {e}")
        return None