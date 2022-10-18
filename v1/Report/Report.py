import os
import glob
import pandas as pd
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from core.schema import *
from core.gsuite.tools import LibSenseGSuite
from core.database import crud
from core.utils.dependencies import get_db, validate_auth

router = APIRouter(prefix="/report", tags=["Report"], dependencies=[Depends(validate_auth)])


@router.post("/send-report", response_model=BasicResponse)
def send_report(payload: SendReportRequest, db: Session = Depends(get_db)):
    service = LibSenseGSuite()
    service.initialize_mail()
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

    if os.getenv("LIBSENSE_ENV", "Prod") == "Prod":
        service.send_message(payload.email, payload.username, count, attachments)

        files = glob.glob("temp/*")
        for f in files:
            os.remove(f)
    
    return {"msg": "Successfully sent report."}
    