from ninja import Router, File, Form
from ninja.files import UploadedFile


upload_router = Router()
download_router = Router()

from file_handler.schemas import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput, DownloadError
from file_handler.services import UploadService, DownloadService


@upload_router.post('', response={200:UploadSchemaOutput, 401:UploadError})
def upload_media(request, payload:UploadSchemaInput):
    #return 200, UploadService.upload(payload)
    try:
        return 200, UploadService.upload(payload)
    except Exception as e:
        return 401, UploadError(error=f'{type(e)}: {e}')

@download_router.get('/{pid}', response={200:DownloadSchemaOutput, 401:DownloadError})
def download_media(request, pid):
    #return 200, DownloadService.download(DownloadSchemaInput(pid=pid, direct=True))
    try:
        payload = DownloadSchemaInput(pid=pid, direct=True)
        return 200, DownloadService.download(payload)
    except Exception as e:
        return 401, DownloadError(error=f'{type(e)}: {e}')

@download_router.get('/url/{pid}', response={200:DownloadSchemaOutput, 401:DownloadError})
def download_media_url(request, pid):
    #return 200, DownloadService.download(DownloadSchemaInput(pid=pid, direct=False))
    try:
        payload = DownloadSchemaInput(pid=pid, direct=False)
        return 200, DownloadService.download(payload)
    except Exception as e:
        return 401, DownloadError(error=f'{type(e)}: {e}')
