from ninja import NinjaAPI

from mediastore.schemas import MediaSchema
from mediastore.services import MediaService

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    return {"msg": "Hello, world!"}


@api.get('/media', response=list[MediaSchema])
def list_media(request):
    return MediaService.list()


@api.post('/media', response=MediaSchema)
def create_media(request, media: MediaSchema):
    return MediaService.create(media)


@api.get('/media/{id}', response=MediaSchema)
def read_media(request, id: str):
    return MediaService.read(id)


@api.put('/media/patch/{pid}', response={204: int})
def update_media(request, pid: str, media: MediaSchema):
    MediaService.update(pid, media)
    return 204


@api.delete('/media/del/{pid}', response={204: int})
def delete_media(request, pid: str):
    MediaService.delete(pid)
    return 204


