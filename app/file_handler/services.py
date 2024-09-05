from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from ninja.errors import ValidationError, HttpError

import amqp  # amplify_amqp_utils
import storage  # amplify_storage_utils

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from mediastore.services import MediaService
from mediastore.models import StoreConfig


class UploadService:

    @staticmethod
    def upload(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        # TODO provenance log file upload attempt with amqp_util
        if payload.file:
            resp = UploadService.upload_with_file(payload)
        else:
            resp = UploadService.upload_sans_file(payload)

        if isinstance(resp, UploadSchemaOutput):
            media = payload.mediadata
            media = MediaService.create(media)
        return resp  # may include presigned url


    @staticmethod
    def upload_with_file(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        mediadata = MediaService.create(payload.mediadata)  # returns MediaSchema after creating database entry
        # TODO verify that store_key is properly set or generated
        store_config = mediadata.store_config
        match store_config.type:
            case StoreConfig.FILESYSTEMSTORE:
                with storage.fs.FilesystemStore(store_config.bucket) as store:
                    store.put(mediadata.store_key, payload.file.read())
            case StoreConfig.BUCKETSTORE:
                s3_params = store_config.s3_params
                s3_session = storage.s3.aiobotocore.session.get_session()
                S3_CLIENT_ARGS = dict(
                    endpoint_url = s3_params.url,
                    aws_access_key_id = s3_params.access_key,
                    aws_secret_access_key = s3_params.secret_key, # todo, is this always available?
                )
                with s3_session.create_client('s3', **S3_CLIENT_ARGS) as s3client:
                    with storage.s3.BucketStore(s3client, store_config.bucket) as store:
                        store.put(mediadata.store_key, payload.file.read())
            case StoreConfig.SQLITESTORE:
                with storage.db.SqliteStore(store_config.bucket) as store:
                    store.put(mediadata.store_key, payload.file.read())

        return UploadSchemaOutput(object_url=f'the_ready_object_url pid={payload.mediadata.pid} fname={payload.file.name}')

    @staticmethod
    def upload_sans_file(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        assert payload.mediadata.store_config.type == StoreConfig.BUCKETSTORE
        # TODO generate presigned url with storage_util
        return UploadSchemaOutput(presigned_url='my_presigned_url')


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
    def download_direct(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
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
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
        metadata = MediaService.read(payload.pid)
        # TODO generate presigned url with storage_util
        object_url = 'link_to_file'
        return DownloadSchemaOutput(metadata=metadata, object_url=object_url)
