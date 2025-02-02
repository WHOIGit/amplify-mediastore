from ninja import Router

upload_router = Router()
download_router = Router()

from typing import Union, List
from schemas.mediastore import MediaErrorSchema
from schemas.mediastore import UploadSchemaInput, UploadSchemaOutput, UploadError, \
                                 DownloadSchemaInput, DownloadSchemaOutput
from file_handler.services import UploadService, DownloadService


@upload_router.post('', response={200:UploadSchemaOutput, 401:UploadError})
def upload_media(request, payload:UploadSchemaInput):
    #return 200, UploadService.upload(payload)
    try:
        return 200, UploadService.upload(payload)
    except Exception as e:
        return 401, UploadError(error=f'{type(e)}: {e}')


@download_router.post('/urls', response=Union[DownloadSchemaOutput,MediaErrorSchema])
def download_media_urls(request, pids:List[str]):
    responses = []
    for pid in pids:
        _, response = download_media_url(request, pid=pid)
        responses.append(response)
    return responses

@download_router.get('/url/{pid}', response={200:DownloadSchemaOutput, 401:MediaErrorSchema})
def download_media_url(request, pid:str):
    #return 200, DownloadService.download(DownloadSchemaInput(pid=pid, direct=False))
    try:
        payload = DownloadSchemaInput(pid=pid, direct=False)
        return 200, DownloadService.download(payload)
    except Exception as e:
        return 401, MediaErrorSchema( pid=pid, error=str(type(e)), msg=str(e) )

@download_router.get('/{pid}', response={200:DownloadSchemaOutput, 401:MediaErrorSchema})
def download_media(request, pid:str):
    #return 200, DownloadService.download(DownloadSchemaInput(pid=pid, direct=True))
    try:
        payload = DownloadSchemaInput(pid=pid, direct=True)
        return 200, DownloadService.download(payload)
    except Exception as e:
        return 401, MediaErrorSchema(pid=pid, error=str(type(e)), msg=str(e))