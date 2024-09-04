from ninja import Router

from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate
from mediastore.schemas import LoginInputDTO, TokenOutputDTO, ErrorDTO
from mediastore.services import MediaService


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

@router.get('/medias', response=list[MediaSchema])
def list_media(request):
    return MediaService.list()

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


