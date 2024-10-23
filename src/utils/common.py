import logging
import os
from urllib.parse import urlparse
from typing import Optional
import requests

logger = logging.getLogger(__name__)


def download_file(url: str, save_path: str, is_twitter: bool = False) -> bool:
    """
    Downloads a file from the given URL and saves it to the specified path.

    Args:
    url (str): The URL of the file to download.
    save_path (str): The full path where the file should be saved.
    is_twitter (bool): Flag to indicate if it's a Twitter media download.

    Returns:
    bool: True if download was successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True, verify=not is_twitter, timeout=10)
        response.raise_for_status()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        logger.info(f"File downloaded successfully: {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        error_message = f"Failed to download file: {str(e)}"
        logger.error(error_message)
        return False
    except IOError as e:
        error_message = f"Failed to save file: {str(e)}"
        logger.error(error_message)
        return False
    except Exception as e:
        error_message = f"Unexpected error while downloading file: {str(e)}"
        logger.error(error_message)
        return False
