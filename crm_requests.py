import requests
import pandas as pd
import aiohttp
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

def fetch_orders_params(api_key, start_date, end_date, buyer_id, request_type):
    """Отримує параметри для запитів та кількість сторінок."""
    url = 'https://uzshopping.retailcrm.ru/api/v5/orders'
    
    if request_type == 'main':
        params = {
            'apiKey': api_key,
            'filter[createdAtFrom]': start_date,
            'filter[createdAtTo]': end_date,
            'filter[customFields][buyer_id]': buyer_id,
        }
    else:
        params = {
            'apiKey': api_key,
            'filter[statusUpdatedAtFrom]': start_date,
            'filter[statusUpdatedAtTo]': end_date,
            'filter[customFields][buyer_id]': buyer_id,
        }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        raise Exception(f"Error fetching orders: {r.json().get('error', 'Unknown error')}")

    total_pages = r.json()['pagination']['totalPageCount']
    logging.info(f"Total pages: {total_pages}")  
    return total_pages, url, params

async def fetch_page(session, url, params, page, retries=6, initial_delay=2):
    """Асинхронний запит для отримання даних зі сторінки з експоненціальною затримкою."""
    delay = initial_delay  # Початкова затримка
    for attempt in range(retries):
        try:
            params['page'] = page
            async with session.get(url, params=params) as r:
                if r.status == 503:
                    raise Exception("Service Unavailable (503)")
                response = await r.json()
                return response
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying page {page} in {delay} seconds (attempt {attempt + 1})")
                await asyncio.sleep(delay)
                delay *= 2  # Експоненційна затримка
            else:
                logging.warning(f"Skipping page {page} after {retries} attempts")
                return None

async def gather_orders(api_key, start_date, end_date, buyer_id, request_type):
    """Групує асинхронні запити до CRM."""
    total_pages, url, params = fetch_orders_params(api_key, start_date, end_date, buyer_id, request_type)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, total_pages + 1):
            tasks.append(fetch_page(session, url, params, page))
            
            if page % 5 == 0:
                await asyncio.sleep(1)  # Затримка в 1 секунду після кожних 10 запитів

        results = await asyncio.gather(*tasks)

    all_orders = []
    for result in results:
        if result and 'success' in result and result['success']:
            all_orders.extend(result['orders'])

    return pd.DataFrame(all_orders)

def get_orders(api_key, start_date, end_date, buyer_id, request_type):
    """Основна функція для запуску асинхронного отримання замовлень."""
    return asyncio.run(gather_orders(api_key, start_date, end_date, buyer_id, request_type))
