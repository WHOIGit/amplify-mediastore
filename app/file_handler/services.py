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


def b64_to_bytearray(b64_content:str):
    return bytearray(base64.b64decode(b64_content))


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
                store.put(mediadata.store_key, b64_to_bytearray(payload.base64))
            case StoreConfig.BUCKETSTORE:
                s3_params = S3Config.objects.get(url=store_config.s3_params.url, access_key=store_config.s3_params.access_key)
                S3_CLIENT_ARGS = dict(
                    s3_url = s3_params.url,
                    s3_access_key = s3_params.access_key,
                    s3_secret_key = s3_params.secret_key,
                    bucket_name = store_config.bucket,
                )
                with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                    store.put(mediadata.store_key, b64_to_bytearray(payload.base64))
            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(store_config.bucket) as store:
                    store.put(mediadata.store_key, b64_to_bytearray(payload.base64))

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
    def download(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
        # TODO provenance log file download attempt with amqp_util
        try:
            if payload.direct:
                return DownloadService.download_direct(payload)
            else:
                return DownloadService.download_link(payload)
        except Exception as e:
            return DownloadError(error=str(e))


    @staticmethod
    def download_direct(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        mediadata = MediaService.read(payload.pid)
        store_config = mediadata.store_config
        match mediadata.store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                with storage.fs.FilesystemStore(store_config.bucket) as store:
                    file = store.get(mediadata.store_key)
            case StoreConfig.BUCKETSTORE:
                s3_params = store_config.s3_params
                s3_session = storage.s3.aiobotocore.session.get_session()
                S3_CLIENT_ARGS = dict(
                    endpoint_url=s3_params.url,
                    aws_access_key_id=s3_params.access_key,
                    aws_secret_access_key=s3_params.secret_key,  # todo, is this always available?
                )
                with s3_session.create_client('s3', **S3_CLIENT_ARGS) as s3client:
                    with storage.s3.BucketStore(s3client, store_config.bucket) as store:
                        file = store.get(mediadata.store_key)
            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(store_config.bucket) as store:
                    file = store.put(mediadata.store_key)
        # TODO serialise mediadata, filecontent -> file
        return DownloadSchemaOutput(metadata=mediadata, file=file)

    @staticmethod
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput:
        metadata = MediaService.read(payload.pid)
        # TODO generate presigned url with storage_util
        object_url = 'link_to_file'
        return DownloadSchemaOutput(metadata=metadata, object_url=object_url)
