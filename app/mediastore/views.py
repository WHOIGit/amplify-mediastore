from ninja import NinjaAPI

from mediastore.dto_models import MediaInput, MediaOutput, MediaService

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    return {"message": "Hello, world!"}


@api.post('/media', response=MediaOutput)
def create_media(request, input: MediaInput):
    return MediaService.create(input)


@api.get('/media/{id}', response=MediaOutput)
def read_media(request, id: int):
    return MediaService.read(id)


@api.put('/media/{id}')
def update_media(request, id: int, input: MediaInput):
    MediaService.update(id, input)
    return 204


@api.delete('/media/{id}')
def delete_media(request, id: int):
    MediaService.delete(id)
    return 204


@api.get('/media', response=list[MediaOutput])
def list_media(request):
    return MediaService.list()
