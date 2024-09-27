import pandas as pd
from google_sheets import authenticate_google_sheets

def fetch_and_process_payment_sheet(gc, spreadsheet_id, sheet_name):
    """Отримання та обробка даних з листка 'Выплата (new)'."""
    worksheet_payment = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data_payment = worksheet_payment.get_all_values()
    headers_1 = data_payment.pop(0)
    df_payment = pd.DataFrame(data_payment, columns=headers_1)

    # Обробка df_appruv_range
    
    df_appruv_range = df_payment.iloc[:, 5:7]
    df_appruv_range.columns = df_appruv_range.iloc[1]
    df_appruv_range = df_appruv_range[2:].dropna(how='all')
    df_appruv_range['Диапазон апрува'] = df_appruv_range['Диапазон апрува'].str.replace('[^0-9<>-]', '', regex=True)
    df_appruv_range = df_appruv_range[:5]
    
    # Обробка df_payment
    df_pay = df_payment.iloc[0:, 1:4].dropna(how='all')
    df_pay.columns = df_pay.iloc[1]
    df_pay = df_pay[2:]
    
    # Функції для обробки числових даних
    def extract_numbers(string):
        return float(''.join(filter(str.isdigit, string)))
    
    def extract_lead_range(string):
        range_values = string.split('-')
        if len(range_values) == 2:
            return range_values[0], range_values[1].replace('$', '')
        else:
            return None, None

    df_pay[['Лид от $', 'Лид до $']] = df_pay['Диапазон лида:'].apply(lambda x: pd.Series(extract_lead_range(x)))
    df_pay['Сумма по товарам(вкл.)'] = df_pay['Сумма по товарам(вкл.)'].apply(extract_numbers)
    df_pay['Выплата за выкуп(ставка)'] = df_pay['Выплата за выкуп(ставка)'].str.replace('$', '').str.replace(',', '.').astype(float)

    return df_pay, df_appruv_range
