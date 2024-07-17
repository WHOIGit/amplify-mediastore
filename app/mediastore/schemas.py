from typing import List, Optional
from ninja import Schema
from mediastore.models import IdentityType

class IdentitySchema(Schema):
    media_pk: int
    type: str
    token: str

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

class MediaSchemaPatch(Schema):
    pid: Optional[str] = None
    pid_type: Optional[str] = None
    s3url: Optional[str] = ''
    identifiers: Optional[dict] = {}
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []

def clean_identifiers(payload, media_obj=None):
    pop_me = None
    if media_obj: pid,pid_type = payload.pid, media_obj.pid_type
    else:         pid, pid_type = payload.pid, payload.pid_type
    assert IdentityType.objects.filter(name=pid_type).exists()
    for key,val in payload.identifiers.items():
        assert isinstance(key,str) and isinstance(val,str)
        assert IdentityType.objects.filter(name=key).exists()
        if key == pid_type:
            assert val == pid, f'duplicate pid_type in identifiers DO NOT MATCH: media[{pid_type}]:{pid} =! identifier[{key}]:{val}'
            pop_me=key
    if pop_me: payload.identifiers.pop(pop_me)
    return payload.identifiers