import os
import glob
import pandas as pd
from datetime import date
from fastapi import APIRouter, Depends, Body
from pydantic import Field
from sqlalchemy.orm import Session
from core import schema
from core.gmail.tools import LibSenseEmail
from core.database import crud
from core.database.database import SessionLocal

router = APIRouter(prefix="/report", tags=["Report"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/send-report", tags=["Report"])
async def send_report(payload: dict = Body(...), db: Session = Depends(get_db)):
    service = LibSenseEmail()
    today = date.today().strftime("%Y-%m-%d")
    attachments = {}
    count = {}
    for rt in payload["report_types"]:
        if rt == "Rush-Local":
            filters = [schema.FieldFilter(op="in", col="tags", val=["Rush", "Local"])]
            query = crud.get_overdue_rush_local(db, 0, -1, filters=filters, sorter=None, for_pandas=True)
            df = pd.read_sql(query, db.get_bind())
            del df["id"]
            file_path = "temp/Report-%s-%s.csv" % (rt, today)
            count[rt] = df.shape[0]
            df.to_csv(file_path, index=False)
            attachments[rt] = file_path

    for k, v in attachments.items():
        service.send_message(payload["email"], payload["username"], k, count[k], [v])
    
    files = glob.glob("temp/*")
    for f in files:
        os.remove(f)
    
    return {"msg": "Successfully sent report."}
    