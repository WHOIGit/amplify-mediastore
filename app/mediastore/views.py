from ninja import Router

from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate, \
    MediaSearchSchema, BulkUpdateResponseSchema, MediaErrorSchema
from mediastore.schemas import StoreConfigSchema, StoreConfigSchemaCreate, S3ConfigSchemaSansKeys, S3ConfigSchemaCreate
from mediastore.schemas import LoginInputDTO, TokenOutputDTO, ErrorDTO
from mediastore.services import MediaService, StoreService, S3ConfigService


router = Router()


@router.post("/login", response={200: TokenOutputDTO, 401: ErrorDTO}, auth=None)
def login(request, login: LoginInputDTO):
    from config.api import AuthService
    token = AuthService.login(login.username, login.password)
    if token:
        return 200, TokenOutputDTO(token=token)
    return 401, ErrorDTO(error="Invalid credentials")

@router.get("/hello", auth=None)
def hello(request):
    return {"msg": "Hello, world!"}


## MEDIA ##

@router.get('/medias', response=list[MediaSchema])
def list_media(request):
    return MediaService.list_media()

@router.post('/media', response=MediaSchema)
def create_media(request, media: MediaSchemaCreate):
    return MediaService.create(media)

@router.get('/media/{pid}', response=MediaSchema)
def read_media(request, pid: str):
    return MediaService.read(pid)

@router.patch('/media/{pid}', response={204: int})
def patch_media(request, pid: str, media: MediaSchemaUpdate):
    MediaService.patch(pid, media)
    return 204

@router.put('/media/{pid}', response={204: int})
def put_media(request, pid: str, media: MediaSchemaUpdate):
    MediaService.put(pid, media)
    return 204

@router.delete('/media/{pid}', response={204: int})
def delete_media(request, pid: str):
    MediaService.delete(pid)
    return 204


## MEDIA BULK ##

@router.post('/medias/search', response=list[MediaSchema])
def search_medias(request, search_params:MediaSearchSchema):
    return MediaService.search(search_params)

@router.post('/medias/create', response=list[MediaSchema])
def create_medias(request, medias: list[MediaSchemaCreate]):
    created_media = []
    for media in medias:
        created_media.append( MediaService.create(media) )
    return created_media

@router.post('/medias/read', response=list[MediaSchema])
def read_medias(request, pids: list[str]):
    # TODO list failed efforts?
    return MediaService.bulk_read(pids)

@router.patch('/medias/update', response=BulkUpdateResponseSchema)
def patch_medias(request, pids: list[str], medias: list[MediaSchemaUpdate]):
    successes = []
    failures = []
    for pid,media in zip(pids,medias):
        try:
            MediaService.patch(pid, media)
            successes.append(pid)
        except Exception as e:
            failures.append( MediaErrorSchema(pid=pid, error=str(type(e)), msg=str(e)) )
    return BulkUpdateResponseSchema(successes=successes, failures=failures)

@router.put('/medias/update', response=BulkUpdateResponseSchema)
def put_medias(request, pids: list[str], medias: list[MediaSchemaUpdate]):
    successes = []
    failures = []
    for pid,media in zip(pids,medias):
        try:
            MediaService.put(pid, media)
            successes.append(pid)
        except Exception as e:
            failures.append( MediaErrorSchema(pid=pid, error=str(type(e)), msg=str(e)) )
    return BulkUpdateResponseSchema(successes=successes, failures=failures)

@router.post('/medias/delete', response=BulkUpdateResponseSchema)
def delete_medias(request, pids: list[str]):
    successes = []
    failures = []
    for pid in pids:
        try:
            MediaService.delete(pid)
            successes.append(pid)
        except Exception as e:
            failures.append( MediaErrorSchema(pid=pid, error=str(type(e)), msg=str(e)) )
    return BulkUpdateResponseSchema(successes=successes, failures=failures)


## STORE CONFIG ##

@router.get('/stores', response=list[StoreConfigSchema])
def list_stores(request):
    return StoreService.list_stores()

@router.post('/store', response=StoreConfigSchema)
def create_store(request, store: StoreConfigSchemaCreate):
    return StoreService.create(store)

@router.get('/store/{pk}', response=StoreConfigSchema)
def read_store(request, pk: int):
    return StoreService.read(pk)

#@router.put('/store/{pk}', response={204: int})
#def put_store(request, pk: int, store: StoreConfigSchemaCreate):
#    StoreService.update(pk, store)
#    return 204

@router.delete('/store/{pk}', response={204: int})
def delete_store(request, pk: int):
    StoreService.delete(pk)
    return 204


## S3 CONFIGS ##

@router.get('/s3cfgs', response=list[S3ConfigSchemaSansKeys])
def list_s3cfg(request):
    return S3ConfigService.list_s3cfgs()

@router.post('/s3cfg', response=S3ConfigSchemaSansKeys)
def create_s3cfg(request, s3cfg: S3ConfigSchemaCreate):
    return S3ConfigService.create(s3cfg)

@router.get('/s3cfg/{pk}', response=S3ConfigSchemaSansKeys)
def read_s3cfg(request, pk: int):
    return S3ConfigService.read(pk)

@router.put('/s3cfg/{pk}', response={204: int})
def put_s3cfg(request, pk: int, s3cfg: S3ConfigSchemaCreate):
    S3ConfigService.update(pk, s3cfg)
    return 204

@router.delete('/s3cfg/{pk}', response={204: int})
def delete_s3cfg(request, pk: int):
    S3ConfigService.delete(pk)
    return 204
