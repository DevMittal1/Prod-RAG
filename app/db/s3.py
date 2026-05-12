import aioboto3

from app.core.config import get_settings


class S3Client:
    _session = None

    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = aioboto3.Session()
        return cls._session

    @classmethod
    def get_client(cls):
        settings = get_settings()
        return cls.get_session().client(
            "s3",
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )


async def get_s3_client():
    async with S3Client.get_client() as client:
        yield client
