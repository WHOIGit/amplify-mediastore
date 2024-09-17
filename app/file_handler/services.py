import base64
from typing import Optional

import amqp  # amplify_amqp_utils
import storage  # amplify_storage_utils
import storage.fs, storage.s3, storage.db, storage.object

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from mediastore.services import MediaService
from mediastore.models import StoreConfig, S3Config, Media


def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)

class DictStoreSingleton(storage.object.DictStore):
    """
    Singleton version of storage.object.DictStore
    for use in repeat queries to RAMSTORE
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        # Initialize objects only if not already initialized
        if not hasattr(self, 'objects'):
            self.objects = {}


class UploadService:

    @staticmethod
    def upload(payload: UploadSchemaInput) -> UploadSchemaOutput:
        # TODO provenance log file upload attempt with amqp_util
        if payload.base64:
            resp = UploadService.upload_with_file(payload)
        else:
            resp = UploadService.upload_sans_file(payload)
        return resp

    @staticmethod
    def upload_with_file(payload: UploadSchemaInput) -> UploadSchemaOutput:
        media = MediaService.create(payload.mediadata, as_schema=False)
        match media.store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                store = storage.fs.FilesystemStore(media.store_config.bucket)
                store.put(media.store_key, bytearray(decode64(payload.base64)))

            case StoreConfig.BUCKETSTORE:
                S3_CLIENT_ARGS = dict(
                    s3_url = media.store_config.s3cfg.url,
                    s3_access_key = media.store_config.s3cfg.access_key,
                    s3_secret_key = media.store_config.s3cfg.secret_key,
                    bucket_name = media.store_config.bucket,
                )
                with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                    store.put(media.store_key, bytearray(decode64(payload.base64)))

            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(media.store_config.bucket) as store:
                    store.put(media.store_key, bytearray(decode64(payload.base64)))

            case StoreConfig.DICTSTORE:
                store = DictStoreSingleton()
                store.put(media.store_key, bytearray(decode64(payload.base64)))

        # set media object successful storage
        #MediaService.update_status(media.pid, status=StoreConfig.READY)
        media.status = StoreConfig.READY
        media.save()

        return UploadSchemaOutput(status=media.status)

    @staticmethod
    def upload_sans_file(payload: UploadSchemaInput) -> UploadSchemaOutput:
        assert payload.mediadata.store_config.type == StoreConfig.BUCKETSTORE
        media = MediaService.create(payload.mediadata, as_schema=False)  # returns MediaSchema after creating database entry
        S3_CLIENT_ARGS = dict(
            s3_url = media.store_config.s3cfg.url,
            s3_access_key = media.store_config.s3cfg.access_key,
            s3_secret_key = media.store_config.s3cfg.secret_key,
            bucket_name = media.store_config.bucket,
        )
        with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
            put_url = store.presigned_put(media.store_key)
        return UploadSchemaOutput(status=StoreConfig.PENDING, presigned_put=put_url)


class DownloadService:

    @staticmethod
    def download(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        # TODO provenance log file download attempt with amqp_util
        if payload.direct:
            return DownloadService.download_direct(payload)
        else:
            return DownloadService.download_link(payload)

    @staticmethod
    def download_direct(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        media = Media.objects.get(pk=payload.pk)
        match media.store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                store = storage.fs.FilesystemStore(media.store_config.bucket)
                obj_content = store.get(media.store_key)

            case StoreConfig.BUCKETSTORE:
                S3_CLIENT_ARGS = dict(
                    s3_url = media.store_config.s3cfg.url,
                    s3_access_key = media.store_config.s3cfg.access_key,
                    s3_secret_key = media.store_config.s3cfg.secret_key,
                    bucket_name = media.store_config.bucket,
                )
                with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                    obj_content = store.get(media.store_key)

            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(media.store_config.bucket) as store:
                    obj_content = store.get(media.store_key)

            case StoreConfig.DICTSTORE:
                store = DictStoreSingleton()
                obj_content = store.get(media.store_key)

        # converting obj_content bytes to base64
        b64_content = encode64(obj_content)
        return DownloadSchemaOutput(mediadata=MediaService.serialize(media), base64=b64_content)

    @staticmethod
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        media = Media.objects.get(pid=payload.pid)
        assert media.store_config.type == StoreConfig.BUCKETSTORE
        S3_CLIENT_ARGS = dict(
            s3_url=media.store_config.s3cfg.url,
            s3_access_key=media.store_config.s3cfg.access_key,
            s3_secret_key=media.store_config.s3cfg.secret_key,
            bucket_name=media.store_config.bucket,
        )
        with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
            get_url = store.presigned_get(media.store_key)
        return DownloadSchemaOutput(mediadata=MediaService.serialize(media), presigned_get=get_url)
