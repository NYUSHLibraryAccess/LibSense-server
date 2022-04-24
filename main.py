# Author: Barry Wang
# Date: Feb. 16, 2022

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.logger import CustomizeLogger
from v1 import api

ENV = os.getenv("LIBSENSE_ENV", "World")
logger = CustomizeLogger.make_logger(ENV)


def create_app() -> FastAPI:
    app = FastAPI(title="NYU Shanghai Library WMS", debug=False)
    app.logger = logger
    return app


app = create_app()
if ENV == "TEST":
    logger.warning("fastapi is running in TESTING mode.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api.router)

if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=8081, reload=True)
