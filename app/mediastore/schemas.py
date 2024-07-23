from typing import List, Optional
from typing_extensions import Self

from ninja import Schema
from pydantic import BaseModel, ValidationError, model_validator, field_validator, ValidationInfo

from mediastore.models import IdentityType


class MediaSchema(Schema):
    pk: int
    pid: str
    pid_type: str
    s3url: str
    identifiers: dict
    metadata: dict
    tags: List[str] = []

class MediaSchemaCreate(Schema):
    pid: str
    pid_type: str
    s3url: Optional[str] = ''
    identifiers: Optional[dict] = {}
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []

    @field_validator('identifiers')
    @classmethod
    def check_identifiers(cls, identifiers: dict) -> dict:
        for key,val in identifiers.items():
            assert isinstance(key,str), 'IdentifierType (dict key) must be string'
            assert isinstance(val,str), 'Identifier (dict val) must be string'
        return identifiers

class MediaSchemaUpdate(MediaSchemaCreate):
    pid: Optional[str] = None
    pid_type: Optional[str] = None
    s3url: Optional[str] = ''
    identifiers: Optional[dict] = {}
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []


class LoginInputDTO(Schema):
    username: str
    password: str

class TokenOutputDTO(Schema):
    token: str

class ErrorDTO(Schema):
    error: str