import os
import logging
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def save_full_session(context, username: str, password: str):
    """Save both credentials and context storage"""
    # Get storage state
    storage = await context.storage_state()
    
    # Create full session data
    session_data = {
        "credentials": {
            "username": username,
            "password": password
        },
        "storage_state": storage
    }
    
    # Save to file
    with open('session.json', 'w') as f:
        json.dump(session_data, f, indent=4)
    logger.info("Full session saved successfully")
    return session_data

async def load_full_session():
    """Load full session data if exists"""
    try:
        if os.path.exists('session.json'):
            with open('session.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading session: {e}")
    return None


async def login_and_save_session(page, username: str, password: str, email:str):
    try:
        await page.goto("https://twitter.com/i/flow/login", wait_until="domcontentloaded")
        await page.wait_for_load_state("load")
        
        logger.info("Waiting for username input...")
        await page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
        await page.fill('input[autocomplete="username"]', username)
        
        await page.click('button[role="button"]:has-text("Next")')

        await page.wait_for_timeout(3000)

        logger.info("Looking for password input...")
        pass_entry = await page.wait_for_selector('input[type="password"]', timeout=1000)
        if not pass_entry:
            logger.info(f"waiting for email input...")
            await page.wait_for_selector('input[type="text"]', timeout=10000)
            await page.fill('input[type="text"]', email)
            await page.click('button[type="button"]:has-text("Next")')
            
            logger.info("Looking for password input...")
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            await page.fill('input[type="password"]', password)
            await page.click('button[type="button"]:has-text("Log in")')
            await page.wait_for_timeout(5000)

        await page.fill('input[type="password"]', password)
        await page.click('button[type="button"]:has-text("Log in")')
        
        await page.wait_for_timeout(5000)


        
        # Save full session including credentials and storage state
        session_data = await save_full_session(page.context, username, password)
        logger.info("Full session saved successfully")
        return session_data
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise

async def main():
    try:
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
            
            # First try to load existing session
            session_data = await load_full_session()
            
            if session_data:
                logger.info("Found existing session, using stored credentials")
                username = session_data["credentials"]["username"]
                password = session_data["credentials"]["password"]
                # Create context with stored state
                context = await browser.new_context(
                    storage_state=session_data["storage_state"],
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
            else:
                logger.info("No existing session found, using default credentials")
                username = "msc72m_dev"
                password = "09935083803M@m"
                email = "Mohammad278Sadeghian1@gmail.com"
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
            
            context.set_default_navigation_timeout(60000)
            page = await context.new_page()
            
            try:
                # Only perform login if we didn't have a stored session
                if not session_data:
                    session_data = await login_and_save_session(page, username, password, email)
                    if session_data:
                        logger.info("Login and session save successful")
                else:
                    logger.info("Using existing session")
                    
            except Exception as e:
                logger.error(f"Login process failed: {e}")
                await page.screenshot(path="error.png")
            finally:
                await browser.close()
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    asyncio.run(main())