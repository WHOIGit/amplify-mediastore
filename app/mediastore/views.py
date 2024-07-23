from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.security import HttpBearer

from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate
from mediastore.schemas import LoginInputDTO, TokenOutputDTO, ErrorDTO
from mediastore.services import MediaService, AuthService

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        return AuthService.validate_token(token)

auth = AuthBearer()
api = NinjaAPI(auth=auth)


@api.post("/login", response={200: TokenOutputDTO, 401: ErrorDTO}, auth=None)
def login(request, login: LoginInputDTO):
    token = AuthService.login(login.username, login.password)
    if token:
        return 200, TokenOutputDTO(token=token)
    return 401, ErrorDTO(error="Invalid credentials")

@api.get("/hello", auth=None)
def hello(request):
    return {"msg": "Hello, world!"}

@api.get('/medias', response=list[MediaSchema])
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


