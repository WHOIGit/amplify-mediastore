from ninja import NinjaAPI
from ninja.errors import HttpError

from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate
from mediastore.services import MediaService

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    return {"msg": "Hello, world!"}

@api.get('/media', response=list[MediaSchema])
def list_media(request):
    return MediaService.list()

@api.post('/media', response=MediaSchema)
def create_media(request, media: MediaSchemaCreate):
    return MediaService.create(media)

@api.get('/media/{pid}', response=MediaSchema)
def read_media(request, pid: str):
    return MediaService.read(pid)

@api.patch('/media/{pid}', response={204: int})
def patch_media(request, pid: str, media: MediaSchemaUpdate):
    MediaService.patch(pid, media)
    return 204

@api.put('/media/{pid}', response={204: int})
def put_media(request, pid: str, media: MediaSchemaUpdate):
    MediaService.put(pid, media)
    return 204

@api.delete('/media/{pid}', response={204: int})
def delete_media(request, pid: str):
    MediaService.delete(pid)
    return 204


