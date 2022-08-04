import re
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import date
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from loguru import logger
from core.database import crud
from core.schema import Tags
from core.database.model import Order
from core.database.database import engine

pd.options.mode.chained_assignment = None

col_mapping = {
    "BSN": "bsn",
    "Z13_TITLE": "title",
    "Z71_TEXT": "arrival_text",
    "Z71_OPEN_DATE": "arrival_date",
    "Z71_USER_NAME": "arrival_operator",
    "Z71_DATA": "items_created",
    "Z30_BARCODE": "barcode",
    "Z30_ITEM_PROCESS_STATUS": "ips_code",
    "ITEM_PROCESS_STATUS": "ips",
    "Z30_ITEM_STATUS": "item_status",
    "Z30_MATERIAL": "material",
    "Z30_COLLECTION": "collection",
    "Z30_PROCESS_STATUS_DATE": "ips_date",
    "Z30_UPDATE_DATE": "ips_update_date",
    "Z30_CATALOGER": "ips_code_operator",
    "UPDATE_DATE": "update_date",
    "Z68_OPEN_DATE": "created_date",
    "Z68_SUB_LIBRARY": "sublibrary",
    "Z68_ORDER_STATUS": "order_status",
    "Z68_INVOICE_STATUS": "invoice_status",
    "Z68_MATERIAL_TYPE": "material_type",
    "Z68_ORDER_NUMBER": "order_number",
    "Z68_ORDER_TYPE": "order_type",
    "Z68_TOTAL_PRICE": "total_price",
    "Z68_ORDERING_UNIT": "order_unit",
    "Z68_ARRIVAL_STATUS": "arrival_status",
    "Z68_ORDER_STATUS_DATE_X": "order_status_update_date",
    "Z68_VENDOR_CODE": "vendor_code",
    "Z68_LIBRARY_NOTE": "library_note",
}

date_rows = [
    "Z71_OPEN_DATE",
    "Z30_PROCESS_STATUS_DATE",
    "Z30_UPDATE_DATE",
    "UPDATE_DATE",
    "Z68_OPEN_DATE",
    "Z68_ORDER_STATUS_DATE_X",
]


def tag_finder(order_row, local_vendors):
    tags = []
    keywords = {
        "Rush": ['Request', 'Need', 'Hold', 'Notify', 'CDL', 'ILL', 'Course', 'Reserve', 'Ares', 'Semester', 'Term',
                 'Spring', 'Summer', 'Fall', 'Winter', 'Faculty', 'By', 'For', '@', 'nyu', 'Reads',
                 'Rush', 'Possible', 'ASAP'],
        "CDL": ["CDL"],
        "ILL": ["ILL"],
        "Reserve": ["Course", "Reserve", "Course-Reserve"],
        "Sensitive": ["SENSITIVE"],
    }

    re_rules = {k: "\\b(%s)\\b" % "|".join(v) for k, v in keywords.items()}

    if order_row["vendor_code"] and order_row["vendor_code"].upper() in local_vendors:
        tags.append("Local")
    else:
        tags.append("NY")

    if order_row["material"] and "VIDEO" in order_row["material"]:
        tags.append("DVD")

    note = order_row["library_note"]
    if note is not None:
        for k, rule in re_rules.items():
            if re.search(rule, note, re.I):
                tags.append(k)
    if "Rush" not in tags:
        tags.append("Non-Rush")

    tracking_note = order_row["tracking_note"]
    if tracking_note is not None \
            and re.search("\\bsensitive\\b", tracking_note, re.I):
        tags.append("Sensitive")

    if order_row["cdl_flag"] == 1 and "CDL" not in tags:
        tags.append("CDL")

    return Tags.encode_tags(tags)


def dict_mapping(data: dict, mapping: dict):
    result = {}
    for key, value in data.items():
        if key in mapping.keys():
            result[mapping[key]] = value
    return result


def strf_date(x):
    if pd.isnull(x) or (isinstance(x, str) and len(x) == 0):
        return None
    str_x = str(int(float(x)))
    return str_x[0:4] + "-" + str_x[4:6] + "-" + str_x[6:]


def prepare_for_db(df):
    df = df.fillna(np.nan).replace([np.nan], [None])
    df = df.replace([""], [None])
    return df


def clean_data(df):
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    for d in date_rows:
        df[d] = df[d].apply(strf_date)

    df = df.reset_index(drop=True)
    df = df.drop_duplicates()
    barcode_duplicates = df["Z30_BARCODE"].duplicated(keep="last")
    barcode_duplicates.name = "barcode_duplicates"
    df = df.join(barcode_duplicates)
    barcode_nan = df["Z30_BARCODE"].isnull()
    barcode_nan.name = "barcode_nan"
    df = df.join(barcode_nan)
    df = df[(df["barcode_duplicates"] == False) | (df["barcode_nan"] == True)]
    df = df.drop(["barcode_duplicates", "barcode_nan"], axis=1)
    df["Z68_TOTAL_PRICE"] = df["Z68_TOTAL_PRICE"].fillna("")
    df["Z68_TOTAL_PRICE"] = df["Z68_TOTAL_PRICE"].apply(lambda x: "".join(x.split(",")))
    df = df.reset_index(drop=True)
    return df


def data_ingestion(db: Session, path: str = "utils/IDX_OUTPUT_NEW_REPORT.xlsx"):
    logger.info("DATA INGESTION STARTED")
    cnx = engine.connect()
    prev = pd.read_sql_table("nyc_orders", cnx)
    prev = prev.astype(str)
    path_lst = path.split(".")
    if path_lst[-1] == "xls" or path_lst[-1] == "xlsx":
        curr = pd.read_excel(path, dtype=str)
    elif path_lst[-1] == "csv":
        curr = pd.read_csv(path, dtype=str)

    curr = clean_data(curr)

    prev = prev[prev["order_number"].str.contains("NYUSH")]
    curr = curr[curr["Z68_ORDER_NUMBER"].str.contains("NYUSH")]
    prev["order_number"] = prev["order_number"].apply(lambda x: x[5:])
    curr["Z68_ORDER_NUMBER"] = curr["Z68_ORDER_NUMBER"].apply(lambda x: x[5:])

    current_year = int(date.today().isoformat()[0:4])
    year_dict = {i: None for i in range(current_year - 3, current_year + 1)}
    for year in year_dict.keys():
        this_year = prev["order_number"].apply(lambda x: x[0:4] == str(year))
        this_year.name = "this_year"
        current_df = prev.join(this_year)
        current_df = current_df[current_df["this_year"] == True]
        current_df["order_number"] = current_df["order_number"].apply(lambda x: x[4:])
        current_df["order_number"] = current_df["order_number"].astype(int)
        current_df = current_df.sort_values(by=["order_number"])
        current_df["order_number"] = current_df["order_number"].astype(str)
        current_df["order_number"] = current_df["order_number"].apply(
            lambda x: "NYUSH" + str(year) + x
        )
        del current_df["this_year"]
        year_dict[year] = current_df

    sorted_prev = pd.concat(list(year_dict.values()))
    sorted_prev.reset_index(inplace=True, drop=True)

    year_dict = {i: None for i in range(current_year - 3, current_year + 1)}
    for year in year_dict.keys():
        this_year = curr["Z68_ORDER_NUMBER"].apply(lambda x: x[0:4] == str(year))
        this_year.name = "this_year"
        current_df = curr.join(this_year)
        current_df = current_df[current_df["this_year"] == True]
        current_df["Z68_ORDER_NUMBER"] = current_df["Z68_ORDER_NUMBER"].apply(lambda x: x[4:])
        current_df["Z68_ORDER_NUMBER"] = current_df["Z68_ORDER_NUMBER"].astype(int)
        current_df = current_df.sort_values(by=["Z68_ORDER_NUMBER"])
        current_df["Z68_ORDER_NUMBER"] = current_df["Z68_ORDER_NUMBER"].astype(str)
        current_df["Z68_ORDER_NUMBER"] = current_df["Z68_ORDER_NUMBER"].apply(
            lambda x: "NYUSH" + str(year) + x
        )
        del current_df["this_year"]
        year_dict[year] = current_df

    sorted_curr = pd.concat(list(year_dict.values()))
    sorted_curr.reset_index(inplace=True, drop=True)

    prev_start = sorted_prev[sorted_prev["order_number"] == sorted_curr.iloc[0]["Z68_ORDER_NUMBER"]]
    start_idx = prev_start.iloc[0].name

    curr_end = sorted_curr[sorted_curr["Z68_ORDER_NUMBER"] == sorted_prev.iloc[-1]["order_number"]]
    end_idx = curr_end.iloc[-1].name

    check_prev = sorted_prev.iloc[int(start_idx) :]
    check_curr = sorted_curr.iloc[: int(end_idx) + 1]

    check_prev.reset_index(inplace=True, drop=True)
    check_curr.reset_index(inplace=True, drop=True)

    check_prev.reset_index(inplace=True)
    check_curr.insert(check_curr.shape[1], "id", "")
    check_curr.insert(check_curr.shape[1], "checked", False)

    to_del = check_prev.iloc[:0, :].copy()

    deleted_rows = 0
    for idx, row in check_prev.iterrows():
        if (
            check_curr.iloc[idx - deleted_rows]["BSN"] == row["bsn"]
            and check_curr.iloc[idx - deleted_rows]["Z68_ORDER_NUMBER"] == row["order_number"]
        ):
            check_curr.at[idx - deleted_rows, "id"] = row["id"]
            check_curr.at[idx - deleted_rows, "checked"] = True
        else:
            filtered_curr = check_curr[
                (check_curr["BSN"] == row["bsn"])
                & (check_curr["Z68_ORDER_NUMBER"] == row["order_number"])
                & (check_curr["checked"] == False)
            ]
            if filtered_curr.shape[0] == 0:
                to_del = to_del.append(row)
                deleted_rows += 1
            elif filtered_curr.shape[0] == 1:
                idx_in_curr = filtered_curr.iloc[0].name
                check_curr.at[idx_in_curr, "id"] = row["id"]
                check_curr.at[idx_in_curr, "checked"] = True
            elif filtered_curr.shape[0] > 1:
                filtered_curr["distance"] = filtered_curr.index.map(
                    lambda x: abs(x - int(row.name))
                )
                filtered_curr = filtered_curr.sort_values(by=["distance"])
                min_distance_idx = filtered_curr.iloc[0].name
                check_curr.at[min_distance_idx, "id"] = row["id"]
                check_curr.at[min_distance_idx, "checked"] = True

    check_curr["id"] = check_curr["id"].astype(str)

    to_insert = check_curr[check_curr["checked"] == False]
    check_curr = check_curr[check_curr["checked"] == True]
    del check_curr["checked"]
    del to_insert["id"]
    del to_insert["checked"]
    to_insert = pd.concat([to_insert, sorted_curr.iloc[end_idx + 1:]])
    to_insert = to_insert[(to_insert["Z68_ORDER_STATUS"] != "XXX")]

    check_curr = prepare_for_db(check_curr)
    to_insert = prepare_for_db(to_insert)

    logger.info("TO_DEL: %s, TO_INSERT: %s" % (str(to_del.shape), str(to_insert.shape)))

    for idx, row in tqdm(check_curr.iterrows()):
        row_dict = row.to_dict()
        this_id = row_dict["id"]
        del row_dict["id"]
        mapped_dict = dict_mapping(row_dict, col_mapping)
        db.query(Order).filter(Order.id == this_id).update(mapped_dict)

    logger.info("UPDATING PHASE COMPLETED")

    to_del.to_csv(f"./assets/to_del/{date.strftime(date.today(), '%Y%m%d')}_to_del.csv")
    for idx, row in tqdm(to_del.iterrows()):
        db.query(Order).filter(Order.id == row["id"]).delete()

    logger.info("DELETING PHASE COMPLETED")

    for idx, row in tqdm(to_insert.iterrows()):
        row_dict = dict_mapping(row.to_dict(), col_mapping)
        try:
            db.add(Order(**row_dict))
        except:
            pass

    logger.info("INSERTING PHASE COMPLETED")

    db.commit()
    logger.info("COMMIT COMPLETED")

    return True


def flush_tags(db):
    logger.info("TAG FLUSH STARTED")
    conn = db.get_bind()
    nyc_orders = pd.read_sql_query("""
    select n.*, notes.tracking_note, ei.cdl_flag
    from nyc_orders n join extra_info ei on n.id = ei.id
    left outer join notes on n.id = notes.book_id""", con=conn)
    result = crud.get_local_vendors(db)
    local_vendors = [i.vendor_code for i in result]
    logger.info("DATA READY, MAIN ITERATION STARTED")
    for _, row in tqdm(nyc_orders.iterrows()):
        tags = tag_finder(row, local_vendors)
        stmt = text(
            "INSERT INTO extra_info (id, order_number, tags) "
            "VALUES (:id, :order_number, :tags) "
            "ON DUPLICATE KEY UPDATE "
            "tags = :tags;"
        )
        conn.execute(stmt, {"id": row["id"], "order_number": row["order_number"], "tags": tags})
    logger.info("TAG FLUSH COMPLETED")

    return True
