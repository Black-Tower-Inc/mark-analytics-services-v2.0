import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi

class MongoDB:
    _client: MongoClient = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            cls._client = MongoClient(
                st.secrets["DB"]["URIMONGODB"],
                server_api=ServerApi("1")
            )
        return cls._client

    @classmethod
    def get_database(cls):
        return cls.get_client()[st.secrets["DB"]["DATABASE"]]

    @classmethod
    def get_collection(cls, name: str):
        return cls.get_database()[name]

    @classmethod
    def get_usereminds_by_month(cls, month: str):
        """
        Ej: month = '202506' para userlists202506
        """
        return cls.get_collection(f"userlists{month}")

    @classmethod
    def get_collection_usereminds_real(cls):
        return cls.get_collection("usereminds")

    @classmethod
    def get_collection_suscriptions(cls):
        return cls.get_collection("suscriptions")

    @classmethod
    def get_all_usereminds_collections(cls):
        months = ["202502", "202503", "202504", "202505", "202506"]
        return [cls.get_usereminds_by_month(m) for m in months]
    
    # @classmethod
    # def get_all_notifications_collections(cls):
    #     months = ["202502", "202503", "202504", "202505", "202506"]
    #     zonas = ["America_Mexico_City"]
    #     return [cls.get_usereminds_by_month(m) for m in months]

    @classmethod
    def close_client(cls):
        if cls._client:
            cls._client.close()
