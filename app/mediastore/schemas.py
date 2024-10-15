from typing import List, Dict, Optional, Union

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
    identifiers: Optional[Dict[str,str]] = {}
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []

class MediaSchemaUpdate(Schema):
    pid: Optional[str] = None
    new_pid: Optional[str] = None
    pid_type: Optional[str] = None
    store_config: Optional[Union[int,StoreConfigSchemaCreate]] = None

class MediaSchemaUpdateTags(Schema):
    pid: str
    tags: List[str]

class MediaSchemaUpdateStorekey(Schema):
    pid: str
    store_key: str

class MediaSchemaUpdateIdentifiers(Schema):
    pid: str
    identifiers: Dict[str,str]

class MediaSchemaUpdateMetadata(Schema):
    pid: str
    keys: Optional[List[str]] = []
    data: Optional[Union[dict,list]] = {}

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