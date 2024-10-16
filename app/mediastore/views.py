from typing import List
from ninja import Router

from schemas.mediastore import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate, \
    MediaSearchSchema, BulkUpdateResponseSchema, MediaErrorSchema, MediaSchemaUpdateTags, MediaSchemaUpdateStorekey, \
    MediaSchemaUpdateIdentifiers, MediaSchemaUpdateMetadata
from schemas.mediastore import StoreConfigSchema, StoreConfigSchemaCreate, S3ConfigSchemaSansKeys, S3ConfigSchemaCreate, IdentifierTypeSchema
from schemas.mediastore import LoginInputDTO, TokenOutputDTO, ErrorDTO
from mediastore.services import MediaService, StoreService, S3ConfigService, IdentifierTypeService

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


## MEDIA BULK ##

@router.post('/media/search', response=List[MediaSchema])
def media_search(request, search_params:MediaSearchSchema):
    return MediaService.search(search_params)

@router.post('/media/create', response=List[MediaSchema])
def media_create(request, medias: List[MediaSchemaCreate]):
    created_media = []
    for media in medias:
        created_media.append( MediaService.create(media) )
    return created_media

@router.post('/media/read', response=List[MediaSchema])
def media_read(request, pids: List[str]):
    # TODO list failed efforts?
    return MediaService.bulk_read(pids)

def bulk_update_response(payload:list, function):
    successes = []
    failures = []
    for elem in payload:
        pid = elem if isinstance(elem,str) else elem.pid
        try:
            resp = function(elem)
            successes.append(pid)
        except Exception as e:
            failures.append( MediaErrorSchema(pid=pid, error=str(type(e)), msg=str(e)) )
    return BulkUpdateResponseSchema(successes=successes, failures=failures)

@router.post('/media/delete', response=BulkUpdateResponseSchema)
def media_delete(request, pids: List[str]):
    return bulk_update_response(pids, MediaService.delete)

@router.patch('/media/update/tags', response=BulkUpdateResponseSchema)
def media_update_tags_add(request, payload: List[MediaSchemaUpdateTags]):
    return bulk_update_response(payload, MediaService.update_tags_add)
@router.put('/media/update/tags', response=BulkUpdateResponseSchema)
def media_update_tags_put(request, payload: List[MediaSchemaUpdateTags]):
    return bulk_update_response(payload, MediaService.update_tags_put)

@router.put('/media/update/storekeys', response=BulkUpdateResponseSchema)
def media_update_storekeys(request, payload: List[MediaSchemaUpdateStorekey]):
    return bulk_update_response(payload, MediaService.update_storekey)

@router.put('/media/update/identifiers', response=BulkUpdateResponseSchema)
def media_update_identifiers(request, payload: List[MediaSchemaUpdateIdentifiers]):
    return bulk_update_response(payload, MediaService.update_identifiers)

@router.put('/media/update/metadata', response=BulkUpdateResponseSchema)
def media_update_metadata_put(request, payload: List[MediaSchemaUpdateMetadata]):
    return bulk_update_response(payload, MediaService.update_metadata_put)
@router.patch('/media/update/metadata', response=BulkUpdateResponseSchema)
def media_update_metadata_patch(request, payload: List[MediaSchemaUpdateMetadata]):
    return bulk_update_response(payload, MediaService.update_metadata_patch)
@router.delete('/media/update/metadata', response=BulkUpdateResponseSchema)
def media_update_metadata_delete(request, payload: List[MediaSchemaUpdateMetadata]):
    return bulk_update_response(payload, MediaService.update_metadata_delete)

@router.patch('/media/update', response=BulkUpdateResponseSchema)
def patch_medias(request, pids: List[str], medias: List[MediaSchemaUpdate]):
    return bulk_update_response(pids, MediaService.patch)


## MEDIA ##

@router.get('/media/dump', response=List[MediaSchema])
def list_media(request):
    return MediaService.list_media()

@router.post('/media', response=MediaSchema)
def media_create_single(request, media: MediaSchemaCreate):
    return MediaService.create(media)

@router.get('/media/{pid}', response=MediaSchema)
def media_read_single(request, pid: str):
    return MediaService.read(pid)

@router.delete('/media/{pid}', response={204: int})
def media_delete_single(request, pid: str):
    MediaService.delete(pid)
    return 204

@router.patch('/media/{pid}', response={204: int})
def media_patch_single(request, pid: str, payload: MediaSchemaUpdate):
    payload.pid = pid
    MediaService.patch(payload)
    return 204


## STORE CONFIG ##

@router.get('/stores', response=List[StoreConfigSchema])
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

@router.get('/s3cfgs', response=List[S3ConfigSchemaSansKeys])
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

## Identifiers ##
@router.get('/identifier/list', response=List[IdentifierTypeSchema])
def list_identifiers(request):
    return IdentifierTypeService.list()

@router.get('/identifier/{name}', response=IdentifierTypeSchema)
def read_identifier(request, name):
    return IdentifierTypeService.read(name)

@router.post('/identifier', response=IdentifierTypeSchema)
def create_identifier(request, payload:IdentifierTypeSchema):
    return IdentifierTypeService.create(payload)

@router.put('/identifier', response={204: int})
def update_identifier(request, payload:IdentifierTypeSchema):
    IdentifierTypeService.update(payload)
    return 204

@router.delete('/identifier', response={204: int})
def delete_identifier(request, payload:IdentifierTypeSchema):
    IdentifierTypeService.delete(payload)
    return 204
