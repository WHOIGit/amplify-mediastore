from typing import List, Optional

from ninja import Schema
from pydantic import BaseModel, ValidationError, model_validator, field_validator, ValidationInfo


class S3ConfigSchema(Schema):
    url: str
    access_key: str
    secret_key: Optional[str] = None

class StoreConfigSchema(Schema):
    type: str
    bucket: str
    s3_params: Optional[S3ConfigSchema] = None

class MediaSchema(Schema):
    pk: int
    pid: str
    pid_type: str
    store_config: StoreConfigSchema
    store_key: str
    store_status: str
    identifiers: dict
    metadata: dict
    tags: List[str] = []

class MediaSchemaCreate(Schema):
    pid: str
    pid_type: str
    store_config: StoreConfigSchema
    store_key: Optional[str] = ''
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
    store_config: Optional[StoreConfigSchema] = ''
    store_key: Optional[str] = ''
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