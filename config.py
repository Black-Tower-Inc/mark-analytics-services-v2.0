# config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:

    # ----------------------------------------------------
    # 1) CONFIGURACIÓN DE MONGO
    # ----------------------------------------------------
    MONGODB_URI = os.getenv("URIMONGODB", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("DATABASE", "arcobits_sandbox")