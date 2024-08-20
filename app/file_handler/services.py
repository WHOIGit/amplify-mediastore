from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from ninja.errors import ValidationError, HttpError

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from mediastore.services import MediaService

class UploadService:

    @staticmethod
    def upload(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:

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
        # TODO save the file
        return UploadSchemaOutput()

    @staticmethod
    def upload_sans_file(payload: UploadSchemaInput) -> UploadSchemaOutput|UploadError:
        # TODO generate presigned url
        return UploadSchemaOutput(presigned_url='my_presigned_url')


class DownloadService:

    @staticmethod
    def download(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
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
        # TODO fetch file content
        file = 'the_fetched_file'
        return DownloadSchemaOutput(metadata=metadata, file = file)

    @staticmethod
    def download_link(payload: DownloadSchemaInput) -> DownloadSchemaOutput|DownloadError:
        metadata = MediaService.read(payload.pid)
        # TODO generate presigned url
        file = 'link_to_file'
        return DownloadSchemaOutput(metadata=metadata, file = file)
