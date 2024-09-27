from datetime import datetime
import streamlit as st
from google_sheets import authenticate_google_sheets
from caching import *
from data_processing_main_req import *
from facebook_api import *

st.set_page_config(page_title="Рассчет баеров", page_icon="📈")
st.title("Рассчет баеров")
st.header('Фильтр по датам')

api_key = st.secrets["api_key"]
google_sheets_creds = st.secrets["gcp_service_account"]

buyers_list = ['ss', 'il', 'dm', 'mb']
b = st.selectbox("Виберите категорию заказа", buyers_list)

start_date = st.date_input('Начальная дата', value=datetime(2024, 9, 1))
end_date = st.date_input('Конечная дата', value=datetime(2024, 9, 3))

if end_date < start_date:
    st.error('Конечная дата не может быть раньше начальной даты')

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# отримання токенів з гуглшит
spreadsheet_id_tokens = '1Q8eFscYd9dsl6QTzLiRQqKXMg3HFuZgwjd9kg0fOMdQ'
sheet_name_tokens = 'Лист1'

df_tokens = fetch_tokens_data(spreadsheet_id_tokens, sheet_name_tokens, dict(google_sheets_creds), b)
if st.button("Fetch Tokens Data"):
    st.dataframe(df_tokens)

# отримання даних справочніка гуглшит
spreadsheet_id_offers = '15GvP6wElztDSQKqk5kxnB37dKxKi3nTyEsTbBF1vqW4'

combined_df = fetch_offers_data(spreadsheet_id_offers, dict(google_sheets_creds))
if st.button("Fetch Spravochnik Data"):
    st.dataframe(combined_df)

sheet_name_payment = 'Выплата (new)'

df_payment, df_appruv_range = fetch_payment_data(spreadsheet_id_offers, sheet_name_payment, dict(google_sheets_creds))
if st.button("Fetch Payment Data"):
    st.dataframe(df_payment)
    st.dataframe(df_appruv_range)


df_grouped = cached_fetch_facebook_data(df_tokens, start_date_str, end_date_str)
if st.button("Fetch Facebook Data"):
    if df_grouped is not None:
        st.dataframe(df_grouped)
    else:
        st.warning("Нету доступных токенов фб")


# отримання даних з CRM
if st.button("Fetch Orders"):
    df_orders = fetch_orders_data(api_key, start_date_str, end_date_str, b)
    # print(df_orders)

    processed_orders = process_orders_data(df_orders, combined_df, df_payment, df_appruv_range, df_grouped, b)
    st.write(processed_orders)