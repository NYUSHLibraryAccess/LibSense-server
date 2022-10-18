# Author: Barry Wang
# Date: Feb. 16, 2022

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import uvicorn
from pydantic import BaseSettings
from redis import Redis
from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.logger import CustomizeLogger
from core.schema import Overview
from v1 import api

with open("configs/config.json") as cfg:
    json_cfg = json.load(cfg)
    SESSION_SECRET = json_cfg['session_key']
    redis_cfg = json_cfg['redis_config']

ENV = os.getenv("LIBSENSE_ENV", "PROD")
logger = CustomizeLogger.make_logger(ENV)


class SystemSettings(BaseSettings):
    overview: Overview


def create_app() -> FastAPI:
    app = FastAPI(title="NYU Shanghai Library WMS", debug=False)
    app.logger = logger
    return app


app = create_app()
if ENV == "TEST":
    logger.warning("fastapi is running in TESTING mode.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        cookie_name="JSESSIONID",
        max_age=86400
    )
else:
    redis_client = Redis(host=redis_cfg["host"], port=redis_cfg["port"], password=redis_cfg["password"])
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        cookie_name="JSESSIONID",
        max_age=86400,
        backend_type=BackendType.redis,
        backend_client=redis_client
    )

app.include_router(api.router)

if __name__ == '__main__':
    os.environ["LIBSENSE_ENV"] = "TEST"
    uvicorn.run(app="main:app", host="0.0.0.0", port=8081, reload=True)
