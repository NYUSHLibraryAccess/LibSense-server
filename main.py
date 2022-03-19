# Author: Barry Wang
# Date: Feb. 16, 2022

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import uvicorn
from fastapi import FastAPI
from api import api

app = FastAPI(title="NYU Shanghai Library WMS")

app.include_router(api.router)

if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=8080, reload=True)
