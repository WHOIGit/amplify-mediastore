from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from ninja.errors import ValidationError, HttpError

import amplify_amqp_utils as amqp_utils
import amplify_storage_utils as storage_utils

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from mediastore.services import MediaService


class UploadService:

    @staticmethod
    def upload(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        # TODO provenance log file upload attempt with amqp_util
        if payload.file:
            resp = UploadService.upload_with_file(payload)
        else:
            resp = UploadService.upload_sans_file(payload)

        if isinstance(resp, UploadSchemaOutput):
            media = payload.metadata
            media = MediaService.create(media)
        return resp  # may include presigned url


    @staticmethod
    def upload_with_file(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        # TODO save the file with storage_util
        return UploadSchemaOutput()

    @staticmethod
    def upload_sans_file(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
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
        metadata = MediaService.read(payload.pid)
        # TODO fetch file content with storage_util
        file = 'the_fetched_file'
        return DownloadSchemaOutput(metadata=metadata, file = file)

    @staticmethod
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
        metadata = MediaService.read(payload.pid)
        # TODO generate presigned url with storage_util
        file = 'link_to_file'
        return DownloadSchemaOutput(metadata=metadata, file = file)
