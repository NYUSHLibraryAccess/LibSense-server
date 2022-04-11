import numpy as np
import pandas as pd
from ..database import crud
from ..database import model
from datetime import date
from sqlalchemy.orm import Session


def strf_date(x):
    if pd.isnull(x): return ""
    return x[0:4] + '-' + x[4:6] + '-' + x[6:]


def dict_mapping(data: dict, mapping: dict):
    result = {}
    for key, value in data.items():
        result[mapping[key]] = value
    return result


def data_ingestion(db: Session, path: str = 'utils/IDX_OUTPUT_NEW_REPORT.xlsx'):
    path_lst = path.split(".")
    if path_lst[-1] == "xls" or path_lst[-1] == "xlsx":
        src = pd.read_excel(path, dtype=str)
    elif path_lst[-1] == "csv":
        src = pd.read_csv(path, dtype=str)

    if int(src.iloc[0]['Z68_OPEN_DATE']) > int(src.iloc[-1]['Z68_OPEN_DATE']):
        src = src.iloc[::-1]
        src = src.reset_index(drop=True)

    date_rows = ['Z30_PROCESS_STATUS_DATE',
                 'Z30_UPDATE_DATE',
                 'UPDATE_DATE',
                 'Z68_OPEN_DATE',
                 'Z68_ORDER_STATUS_DATE_X']

    src = src.applymap(lambda x: x.strip() if type(x) == str else x)
    for d in date_rows:
        src[d] = src[d].apply(strf_date)

    src = src.reset_index(drop=True)
    src = src.drop_duplicates()
    barcode_duplicates = src['Z30_BARCODE'].duplicated(keep='last')
    barcode_duplicates.name = 'barcode_duplicates'
    src = src.join(barcode_duplicates)
    src = src[src['barcode_duplicates'] == False]
    src = src.drop(src.columns[-1:], axis=1)
    src = src.reset_index(drop=True)

    start_idx = -1
    for idx, row in src.iterrows():
        barcode = int(row['Z30_BARCODE'])
        order_number = row['Z68_ORDER_NUMBER']
        print("&%s&, &%s&" % (barcode, order_number))
        start_idx = crud.get_starting_position(db, barcode, order_number)
        if start_idx != -1:
            break

    src.index += start_idx
    total_orders = crud.get_order_count(db)
    inserts = src.shape[0] - (total_orders - start_idx)
    print(start_idx)
    return
    col_mapping = {
        'BSN': 'bsn',
        'Z13_TITLE': 'title',
        'Z71_TEXT': 'arrival_text',
        'Z71_OPEN_DATE': 'arrival_date',
        'Z71_USER_NAME': 'arrival_operator',
        'Z71_DATA': 'items_created',
        'Z30_BARCODE': 'barcode',
        'Z30_ITEM_PROCESS_STATUS': 'ips_code',
        'ITEM_PROCESS_STATUS': 'ips',
        'Z30_ITEM_STATUS': 'item_status',
        'Z30_MATERIAL': 'material',
        'Z30_COLLECTION': 'collection',
        'Z30_PROCESS_STATUS_DATE': 'ips_date',
        'Z30_UPDATE_DATE': 'ips_update_date',
        'Z30_CATALOGER': 'ips_code_operator',
        'UPDATE_DATE': 'update_date',
        'Z68_OPEN_DATE': 'created_date',
        'Z68_SUB_LIBRARY': 'sublibrary',
        'Z68_ORDER_STATUS': 'order_status',
        'Z68_INVOICE_STATUS': 'invoice_status',
        'Z68_MATERIAL_TYPE': 'material_type',
        'Z68_ORDER_NUMBER': 'order_number',
        'Z68_ORDER_TYPE': 'order_type',
        'Z68_TOTAL_PRICE': 'total_price',
        'Z68_ORDERING_UNIT': 'order_unit',
        'Z68_ARRIVAL_STATUS': 'arrival_status',
        'Z68_ORDER_STATUS_DATE_X': 'order_status_update_date',
        'Z68_VENDOR_CODE': 'vendor_code',
        'Z68_LIBRARY_NOTE': 'library_note'
    }
    counter = 0
    for idx, row in src.iloc[0:inserts].iterrows():
        counter += 1
        clean_row = row.to_dict()
        del clean_row["Unnamed: 0"]
        print(idx, dict_mapping(clean_row, col_mapping))
        if counter == 10:
            break
