from ninja import Router, File, Form
from ninja.files import UploadedFile


upload_router = Router()
download_router = Router()

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from file_handler.services import UploadService, DownloadService

from mediastore.schemas import MediaSchemaCreate,StoreConfigSchema

@upload_router.post('', response={200:UploadSchemaOutput, 401:UploadError})
def upload_media(request, media_schema_create:dict=Form(...), file: UploadedFile=File(...)):
    mediadata = MediaSchemaCreate(**media_schema_create)
    return UploadService.upload(UploadSchemaInput(mediadata=mediadata, file=file))

@download_router.post('', response={200:DownloadSchemaOutput, 401:DownloadError})
def download_media(request, payload: DownloadSchemaInput):
    return DownloadService.download(payload)

