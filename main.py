#!/usr/bin/env python3
import os
import asyncio
import time
import logging
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from playwright.async_api import async_playwright
import random
from fake_useragent import UserAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --------------------
# Logger Setup
# --------------------
logging.basicConfig(
    level=logging.INFO,
    filename='logging.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load configuration from environment variables
SCOPES = os.getenv('GOOGLE_SHEETS_SCOPES', "https://www.googleapis.com/auth/spreadsheets").split(',')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
KEYFILE_PATH = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '5'))
SHEET_NAME = os.getenv('SHEET_NAME', 'General')
START_ROW = int(os.getenv('START_ROW', '142'))
SLEEP_INTERVAL = int(os.getenv('SLEEP_INTERVAL', '60'))

# Validate required environment variables
required_vars = ['SPREADSHEET_ID', 'GOOGLE_SERVICE_ACCOUNT_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Load the service account credentials from the key file
credentials = service_account.Credentials.from_service_account_file(
    KEYFILE_PATH, 
    scopes=SCOPES
)

def generate_user_agents(count):
    ua = UserAgent()
    return [ua.random for _ in range(count)]

async def gmgn_web_scraping(i, Token_network, Token_address):
    link = f"https://gmgn.ai/sol/token/{Token_address}"
    returning_list = []
    logging.info(f"Processing row {i}: Token_network={Token_network}, Token_address={Token_address}")
    user_agents = generate_user_agents(10)
    
    subscript_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(user_agents))
            page = await context.new_page()

            try:
                await page.set_viewport_size({"width": 1920, "height": 1080})
                await page.goto(link)
                await asyncio.sleep(random.uniform(2, 5))

                try:
                    got_it_button = page.locator('text="Got it"')
                    await got_it_button.click(timeout=5000)
                    logging.info("Pop-up appeared and 'Got it' button was clicked.")
                except TimeoutError:
                    logging.info("Pop-up did not appear or 'Got it' button was not found.")

                parent_element = await page.wait_for_selector('.css-1lqrh8c', timeout=5000)
                if parent_element:
                    price_element = await parent_element.query_selector('div:first-child')
                    
                    if price_element:
                        price_text = await price_element.inner_text()
                        logging.info(f"Raw price text: {price_text}")
                        
                        price_text = price_text.replace('$', '')
                        for subscript, digit in subscript_map.items():
                            price_text = price_text.replace(subscript, digit)
                        
                        price = float(price_text)
                        
                        logging.info(f"The Price is: {price}")
                        logging.info(f"The GMGN.ai URL is: {link}")
                        returning_list = [price, link]
                    else:
                        logging.warning("Price element (first child) not found.")
                else:
                    logging.warning("Parent element with class css-1lqrh8c not found.")

            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")

            finally:
                screenshot_path = os.getenv('SCREENSHOT_PATH', 'last.jpg')
                try:
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logging.info(f"Screenshot saved successfully at {screenshot_path}")
                except Exception as e:
                    logging.error(f"Error saving screenshot: {e}")
                
                await browser.close()
                return returning_list

    except Exception as e:
        logging.error(f"Error GMGN Scraping row {i}: because -> {e}")
        return []

async def prepare_data(i, sheet, spreadsheetId, list_of_data):
    if not list_of_data:
        logging.info(f"Skipping preparing data for row {i} as list_of_data is empty.")
        return

    price, website = list_of_data
    price = f"${price}"
    current_time = time.strftime("%Y/%m/%d")

    data = [
        {'range': f'E{i}', 'values': [[price]]},
        {'range': f'F{i}', 'values': [[website]]},
        {'range': f'T{i}', 'values': [[current_time]]}
    ]

    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }

    await asyncio.to_thread(sheet.values().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute)

async def process_row(row, i, sheet, spreadsheetId):
    Token_network, Token_address = row[0].lower(), row[1]
    if not Token_network or not Token_address:
        logging.warning(f"Skipping row {i} due to missing data")
        return
    
    list_of_data = await gmgn_web_scraping(i, Token_network, Token_address)
    await prepare_data(i, sheet, spreadsheetId, list_of_data)

async def Send_Data_To_Sheet(credentials):
    try:
        service = build("sheets", "v4", credentials=credentials)
        sheets = service.spreadsheets()

        result = await asyncio.to_thread(
            sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=SHEET_NAME).execute
        )
        values = result.get('values', [])

        if not values:
            logging.info('No data found.')
            return

        tasks = []
        for i, row in enumerate(values[START_ROW-1:], start=START_ROW):
            if not any(row):
                logging.info(f"Reached empty row at {i}. Stopping processing.")
                break
            
            if len(row) < 2:
                logging.warning(f"Skipping row {i} due to insufficient data")
                continue
            
            task = asyncio.create_task(process_row(row, i, sheets, SPREADSHEET_ID))
            tasks.append(task)
            
            if len(tasks) >= MAX_CONCURRENT_TASKS:
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

    except HttpError as error:
        logging.error(f'An error occurred: {error}')
    except Exception as error:
        logging.error(f'Error in Send Data Because : {error}')

async def main():
    while True:
        logging.info('Starting..')
        await Send_Data_To_Sheet(credentials)
        logging.info(f'Sleeping {SLEEP_INTERVAL} seconds')
        await asyncio.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())