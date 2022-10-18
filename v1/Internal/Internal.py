import os
import subprocess
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from core.gsuite.tools import LibSenseGSuite
from starlette.exceptions import HTTPException
from core.schema import BasicResponse


def internal_dependency(req: Request):
    if "127.0.0.1" not in req.headers.get("Host", "127.0.0.1"):
        raise HTTPException(status_code=422, detail="Unauthorized.")


router = APIRouter(prefix="/internal", dependencies=[Depends(internal_dependency)])


@router.get("/backup", response_model=BasicResponse)
def mysql_backup(username=None, password=None):
    ts = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
    target_path = os.path.join(os.getcwd(), "assets/db_backup/", f"libsense_{ts}.sql")
    proc = subprocess.Popen(
        [f"mysqldump -u{username} -p{password} libsense > {target_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    proc.wait()

    service = LibSenseGSuite()
    service.initialize_drive()
    result = service.upload_file(f"libsense_{ts}.sql", target_path)
    if result:
        return BasicResponse(msg=f"Last backup time: {ts}")
    else:
        raise HTTPException(status_code=500, detail="An error occurs when uploading the file.")



