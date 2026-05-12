from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

class MongoDBClient:
    client: AsyncIOMotorClient = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            settings = get_settings()
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
        return cls.client

    @classmethod
    def get_db(cls):
        settings = get_settings()
        return cls.get_client()[settings.mongodb_db_name]

def get_db():
    return MongoDBClient.get_db()
