# config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "secret123"

    DB_HOST = "localhost"
    DB_NAME = "Elerning"
    DB_USER = "mangesh"
    DB_PASSWORD = "Admin"
    DB_PORT = "5432"

    QUIZ_TIME_SECONDS = 300
