from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.security import HttpBearer

from mediastore.views import api

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from file_handler.services import UploadService, DownloadService

@api.post('/upload', response=UploadSchemaOutput|UploadError)
def upload_media(request, payload: UploadSchemaInput):
    return UploadService.upload(payload)

@api.post('/download', response=DownloadSchemaOutput|DownloadError)
def download_media(request, payload: DownloadSchemaInput):
    return DownloadService.download(payload)

