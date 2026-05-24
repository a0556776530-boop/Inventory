import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# משתנה גלובלי שמחזיק את החיבור — נוצר פעם אחת בלבד
_client = None


def get_mongo_client():
    """מחזירה את ה-MongoClient. יוצרת חיבור חדש רק אם עוד לא קיים."""
    global _client
    if _client is None:
        uri = os.environ.get("MONGO_URI")
        if not uri:
            raise RuntimeError("MONGO_URI לא מוגדר בקובץ .env")
        _client = MongoClient(
            uri,
            maxPoolSize=10,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=20000,
        )
    return _client


def get_db(db_name: str = "netstock"):
    """מחזירה דאטאבייס מתוך ה-cluster."""
    return get_mongo_client()[db_name]


def ping_mongo() -> bool:
    """בודקת שהחיבור למונגו פעיל. מחזירה True/False."""
    try:
        get_mongo_client().admin.command("ping")
        return True
    except ConnectionFailure:
        return False
