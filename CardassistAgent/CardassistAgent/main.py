import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import engine.apis as apis
app = FastAPI()

    
app.add_middleware(SessionMiddleware,secret_key="4385ec52fe48826a04d34846ccd6d7f2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(apis.api_router)

