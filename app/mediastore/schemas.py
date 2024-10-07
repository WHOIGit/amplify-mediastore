from typing import List, Optional

from ninja import Schema
from pydantic import field_validator


class S3ConfigSchemaCreate(Schema):
    url: str
    access_key: str
    secret_key: str

class S3ConfigSchemaSansKeys(Schema):
    pk: int
    url: str

class StoreConfigSchemaCreate(Schema):
    type: str
    bucket: str
    s3_url: Optional[str] = ''

class StoreConfigSchema(StoreConfigSchemaCreate):
    pk: int

class MediaSchema(Schema):
    pk: int
    pid: str
    pid_type: str
    store_config: StoreConfigSchema
    store_status: str
    identifiers: dict
    metadata: dict
    tags: List[str] = []

class MediaSchemaCreate(Schema):
    pid: str
    pid_type: str
    store_config: StoreConfigSchemaCreate
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
    store_config: Optional[StoreConfigSchemaCreate] = None
    identifiers: Optional[dict] = {}
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []

class MediaErrorSchema(Schema):
    pid: str
    error: str
    msg: str

class BulkUpdateResponseSchema(Schema):
    successes: list[str]
    failures: list[MediaErrorSchema]

class MediaSearchSchema(Schema):
    tags: list[str]
    # TODO other search vectors

class LoginInputDTO(Schema):
    username: str
    password: str

class TokenOutputDTO(Schema):
    token: str

class ErrorDTO(Schema):
    error: str