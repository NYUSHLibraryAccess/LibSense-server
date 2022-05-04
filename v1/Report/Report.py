import os
import glob
import pandas as pd
from datetime import date
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from core.schema import *
from core.gmail.tools import LibSenseEmail
from core.database import crud
from core.utils.dependencies import get_db, validate_auth
from v1.Order.Order import get_tags

router = APIRouter(prefix="/report", tags=["Report"], dependencies=[Depends(validate_auth)])


@router.post("/send-report", response_model=BasicResponse)
def send_report(payload: SendReportRequest, db: Session = Depends(get_db)):
    service = LibSenseEmail()
    today = date.today().strftime("%Y-%m-%d")
    attachments = {}
    count = {}
    for rt in payload.report_type:
        if rt == "RushLocal":
            query = crud.get_overdue_rush_local(db, 0, -1, for_pandas=True)
            df = pd.read_sql(query, db.get_bind())
            file_path = "temp/Report-%s-%s.csv" % (rt, today)
            count[rt] = df.shape[0]
            df.to_csv(file_path, index=False)
            attachments[rt] = file_path
        elif rt == "CDLOrder":
            query = crud.get_overdue_cdl(db, 0, -1, for_pandas=True)
            df = pd.read_sql(query, db.get_bind())
            file_path = "temp/Report-%s-%s.csv" % (rt, today)
            count[rt] = df.shape[0]
            df.to_csv(file_path, index=False)
            attachments[rt] = file_path
        elif rt == "ShanghaiOrder":
            query = crud.get_sh_order_report(db, 0, -1, for_pandas=True)
            df = pd.read_sql(query, db.get_bind())
            file_path = "temp/Report-%s-%s.csv" % (rt, today)
            count[rt] = df.shape[0]
            df.to_csv(file_path, index=False)
            attachments[rt] = file_path

    service.send_message(payload.email, payload.username, count, attachments)
    
    files = glob.glob("temp/*")
    for f in files:
        os.remove(f)
    
    return {"msg": "Successfully sent report."}


@router.post("/rush-local", response_model=PageableOrdersSet)
def get_overdue(body: PageableOrderRequest, db: Session = Depends(get_db)):
    page_index = body.page_index
    page_size = body.page_size
    filters = body.filters
    sorter = body.sorter

    result_set, total_records = crud.get_overdue_rush_local(db, page_index, page_size, filters=filters, sorter=sorter)
    result_lst = get_tags(result_set)

    pageable_set = {
        'page_index': page_index,
        'page_limit': page_size,
        'total_records': total_records,
        'result': result_lst
    }
    return PageableOrdersSet(**pageable_set)
    