import logging
from httpx import AsyncClient, TimeoutException, HTTPStatusError
import  traceback
from datetime import datetime, timezone
from typing import Optional, Dict, List

from src.database.repositories.repositories import TwitterAccountRepository, CategoryRepository

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


async def get_map_ids_to_categories(account_repo: TwitterAccountRepository, category_repo: CategoryRepository):
    try:
        account_details = await account_repo.get_account_details()
        category_mappings = await category_repo.get_account_category_mappings()

        account_id_to_name = {int(account_id): username
                              for account_id, username in account_details}
        account_id_to_category = {int(account_id): int(category_id)
                                  for account_id, category_id in category_mappings}

        # Build the final mapping
        mapped_account_names_to_categories = {}
        for account_id in account_id_to_name:
            if account_id in account_id_to_category:
                mapped_account_names_to_categories[account_id_to_name[account_id]] = (
                    account_id,
                    account_id_to_category[account_id]
                )
        logger.info(f"Mapped account names to categories: {mapped_account_names_to_categories}")
        return mapped_account_names_to_categories

    except Exception as e:
        logger.error(f"Error mapping ids to categories: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
