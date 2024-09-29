from datetime import datetime
import streamlit as st
from google_sheets import authenticate_google_sheets
from caching import *
from data_processing_main_req import *
from facebook_api import *
from data_processing_vykup_req import *
from carspace_catalog import *
from excel_utils import save_data_to_excel

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
# if st.button("Fetch Tokens Data"):
#     st.dataframe(df_tokens)

# отримання даних справочніка гуглшит
spreadsheet_id_offers = '15GvP6wElztDSQKqk5kxnB37dKxKi3nTyEsTbBF1vqW4'

combined_df = fetch_offers_data(spreadsheet_id_offers, dict(google_sheets_creds))
# if st.button("Fetch Spravochnik Data"):
#     st.dataframe(combined_df)

sheet_name_payment = 'Выплата (new)'

df_payment, df_appruv_range = fetch_payment_data(spreadsheet_id_offers, sheet_name_payment, dict(google_sheets_creds))
# if st.button("Fetch Payment Data"):
#     st.dataframe(df_payment)
#     st.dataframe(df_appruv_range)


# if st.button("Fetch Facebook Data"):
#     if df_grouped is not None:
#         st.dataframe(df_grouped)
#     else:
#         st.warning("Нету доступных токенов фб")


# отримання даних з CRM
if st.button("Выгрузить и обработать заказы"):
    df_grouped = cached_fetch_facebook_data(df_tokens, start_date_str, end_date_str)
    st.session_state['df_grouped'] = df_grouped
    request_type = 'main'
    df_orders = fetch_orders_data(api_key, start_date_str, end_date_str, b, request_type)
    
    processed_orders, spend_wo_leads, df = process_orders_data(df_orders, combined_df, df_payment, df_appruv_range, df_grouped, b)
    
    st.session_state['processed_orders'] = processed_orders
    st.session_state['spend_wo_leads'] = spend_wo_leads
    st.session_state['df_orders'] = df_orders
    st.session_state['df'] = df

    cash = 2  
    catalog_w_leads, catalog_cash = process_catalog(df, df_payment, df_grouped, combined_df, b, cash, df_appruv_range)

    cash = 1 
    car_space_merged = process_carspace(df, df_payment, df_grouped, combined_df, b, cash, df_appruv_range)
    st.session_state['car_space_merged'] = car_space_merged
    st.session_state['catalog_w_leads'] = catalog_w_leads
    st.session_state['catalog_cash'] = catalog_cash

    st.write(processed_orders)
    # st.write(spend_wo_leads)




# # catalog
# if st.button('Catalog'):
#     if 'df' in st.session_state:
#         df = st.session_state['df']
#         cash = 2  
#         catalog_w_leads, catalog_cash = process_catalog(df, df_payment, df_grouped, combined_df, b, cash, df_appruv_range)
#         st.write(catalog_w_leads)
#         st.session_state['catalog_w_leads'] = catalog_w_leads
#         st.session_state['catalog_cash'] = catalog_cash
#     else: pass

# if st.button('Car Space'):
#     if 'df' in st.session_state:
#         df = st.session_state['df']
#         cash = 1 
#         car_space_merged = process_carspace(df, df_payment, df_grouped, combined_df, b, cash, df_appruv_range)
#         st.write(car_space_merged)
#         st.session_state['car_space_merged'] = car_space_merged
#     else: pass


# отримання даних про викупи
if st.button("Выгрузить и обработать выкупы"):
    request_type = 'vykup'
    
    # чек чи є дані про замовлення у session_state
    if 'processed_orders' in st.session_state:
        processed_orders = st.session_state['processed_orders']
        spend_wo_leads = st.session_state['spend_wo_leads']
        df_grouped = st.session_state['df_grouped']

    else:
        st.warning("Спочатку завантажте замовлення, натиснувши кнопку 'Fetch Orders'.")
        processed_orders = None  

    if processed_orders is not None:
        df_vykups = fetch_vykups_data(api_key, start_date_str, end_date_str, b, request_type)
        processed_vykups, df_all_cs_catalog = process_orders_data_vykup(df_vykups, combined_df, df_payment, df_appruv_range, df_grouped, b, processed_orders)
        
        car_space_merged = st.session_state['car_space_merged']
        catalog_w_leads = st.session_state['catalog_w_leads']
        total_vykup = process_total_vykup(processed_vykups, df_all_cs_catalog, car_space_merged, catalog_w_leads, df_appruv_range)
        
        st.session_state['total_vykup'] = total_vykup
        st.write(total_vykup)


if st.button("Вставить данные в эксель"):
    processed_orders = st.session_state.get('processed_orders')
    car_space_merged = st.session_state.get('car_space_merged')
    catalog_w_leads = st.session_state.get('catalog_w_leads')
    catalog_cash = st.session_state.get('catalog_cash')
    spend_wo_leads = st.session_state.get('spend_wo_leads')
    total_vykup = st.session_state.get('total_vykup')
    
    filename = save_data_to_excel(
        catalog_w_leads, 
        car_space_merged, 
        catalog_cash, 
        processed_orders, 
        spend_wo_leads, 
        total_vykup, 
        b, 
        start_date_str, 
        end_date_str
    )
    
    with open(filename, "rb") as f:
        st.download_button(
            "Скачать",
            f,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"  
        )
