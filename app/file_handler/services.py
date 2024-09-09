import base64
from typing import Optional

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from ninja.errors import ValidationError, HttpError

import amqp  # amplify_amqp_utils
import storage  # amplify_storage_utils
import storage.fs, storage.s3, storage.db

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from mediastore.services import MediaService
from mediastore.models import StoreConfig, S3Config


def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)


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
        mediadata = MediaService.create(payload.mediadata)  # returns MediaSchema after creating database entry
        store_config = mediadata.store_config
        match store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                store = storage.fs.FilesystemStore(store_config.bucket)
                store.put(mediadata.store_key, bytearray(decode64(payload.base64)))
            case StoreConfig.BUCKETSTORE:
                s3_params = S3Config.objects.get(url=store_config.s3_params.url, access_key=store_config.s3_params.access_key)
                S3_CLIENT_ARGS = dict(
                    s3_url = s3_params.url,
                    s3_access_key = s3_params.access_key,
                    s3_secret_key = s3_params.secret_key,
                    bucket_name = store_config.bucket,
                )
                with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                    store.put(mediadata.store_key, bytearray(decode64(payload.base64)))
            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(store_config.bucket) as store:
                    store.put(mediadata.store_key, bytearray(decode64(payload.base64)))

        # set media object successful storage
        MediaService.update_status(mediadata.pid, status=StoreConfig.READY)

        return UploadSchemaOutput(status=StoreConfig.READY)

    @staticmethod
    def upload_sans_file(payload: UploadSchemaInput) -> UploadSchemaOutput:
        assert payload.mediadata.store_config.type == StoreConfig.BUCKETSTORE
        # TODO generate presigned url with storage_util
        return UploadSchemaOutput(status=StoreConfig.PENDING, presigned_url='my_presigned_url')


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
        mediadata = MediaService.read(payload.pid)
        store_config = mediadata.store_config
        match mediadata.store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                store = storage.fs.FilesystemStore(store_config.bucket)
                obj_content = store.get(mediadata.store_key)
            case StoreConfig.BUCKETSTORE:
                s3_params = S3Config.objects.get(url=store_config.s3_params.url, access_key=store_config.s3_params.access_key)
                S3_CLIENT_ARGS = dict(
                    s3_url = s3_params.url,
                    s3_access_key = s3_params.access_key,
                    s3_secret_key = s3_params.secret_key,
                    bucket_name = store_config.bucket,
                )
                with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                    obj_content = store.get(mediadata.store_key)
            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(store_config.bucket) as store:
                    obj_content = store.put(mediadata.store_key)

        # converting obj_content bytes to base64
        b64_content = encode64(obj_content)

        return DownloadSchemaOutput(mediadata=mediadata, base64=b64_content)

    @staticmethod
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        mediadata = MediaService.read(payload.pid)
        # TODO generate presigned url with storage_util
        object_url = 'link_to_file'
        return DownloadSchemaOutput(mediadata=mediadata, object_url=object_url)
