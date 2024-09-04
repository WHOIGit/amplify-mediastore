from typing import Optional

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token

from ninja import NinjaAPI
from ninja.security import HttpBearer

from mediastore.views import router as mediastore_router
from file_handler.views import upload_router, download_router


class AuthService:
    @staticmethod
    def login(username: str, password: str) -> Optional[str]:
        user = authenticate(username=username, password=password)
        if user is not None and user.has_usable_password():
            token, _ = Token.objects.get_or_create(user=user)
            return token.key
        return None

    @staticmethod
    def validate_token(token: str) -> Optional[User]:
        try:
            token_obj = Token.objects.get(key=token)
            return token_obj.user
        except ObjectDoesNotExist:
            return None

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        return AuthService.validate_token(token)

auth = AuthBearer()
api = NinjaAPI(auth=auth)

api.add_router("/", mediastore_router)
api.add_router("/upload", upload_router)
api.add_router("/download", download_router)
