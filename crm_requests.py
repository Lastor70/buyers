import requests
import pandas as pd
import aiohttp
import asyncio
import time

def fetch_orders(api_key, start_date, end_date, buyer_id):
    """Отримує замовлення з CRM за заданими параметрами."""
    url = 'https://uzshopping.retailcrm.ru/api/v5/orders'
    
    params = {
        'apiKey': api_key,
        'filter[createdAtFrom]': start_date,
        'filter[createdAtTo]': end_date,
        'filter[customFields][buyer_id]': buyer_id,
    }

    r = requests.get(url, params=params)
    
    if r.status_code != 200:
        raise Exception(f"Error fetching orders: {r.json().get('error', 'Unknown error')}")
    
    total_pages = r.json()['pagination']['totalPageCount']
    return total_pages, url, params

async def req(session, *a, **kw):
    """Асинхронний запит до CRM."""
    async with session.request(*a, **kw) as r:
        return await r.json()

async def fetch_page(session, url, params, page):
    """Отримує дані з певної сторінки."""
    params['page'] = page
    return await req(session, 'GET', url, params=params)

async def gather_orders(api_key, start_date, end_date, buyer_id):
    """Групує асинхронні запити до CRM."""
    total_pages, url, params = fetch_orders(api_key, start_date, end_date, buyer_id)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, url, params, page) for page in range(1, total_pages + 1)]
        results = await asyncio.gather(*tasks)

    # Обробка результатів
    all_orders = []
    for result in results:
        if result['success']:
            all_orders.extend(result['orders'])  # або інша обробка, залежно від структури даних

    return pd.DataFrame(all_orders)  # Повертає DataFrame з усіма замовленнями

def get_orders(api_key, start_date, end_date, buyer_id):
    """Основна функція для отримання замовлень."""
    return asyncio.run(gather_orders(api_key, start_date, end_date, buyer_id))
