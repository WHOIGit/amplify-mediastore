from typing import List, Optional
from ninja import Schema


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

class MediaSchemaCreate(Schema):
    pid: str
    pid_type: str
    s3url: Optional[str] = ''
    identifiers: Optional[dict] = {}
    metadata: Optional[dict] = {}

class MediaSchemaPatch(Schema):
    pid: Optional[str] = None
    pid_type: Optional[str] = None
    s3url: Optional[str] = None
    identifiers: Optional[dict] = None
    metadata: Optional[dict] = None

def clean_identifiers(payload, media_obj=None):
    pop_me = None
    if media_obj: pid,pid_type = payload.pid, media_obj.pid_type
    else:         pid, pid_type = payload.pid, payload.pid_type
    for key,val in payload.identifiers.items():
        assert isinstance(key,str) and isinstance(val,str)
        # TODO key in IdentityTypes, val formatting correct
        if key == pid_type:
            assert val == pid, f'duplicate pid_type in identifiers DO NOT MATCH: media[{pid_type}]:{pid} =! identifier[{key}]:{val}'
            pop_me=key
    #assert payload.pid_type in IdentityType.objects.all().values_list('name',flat=True)
    if pop_me: payload.identifiers.pop(pop_me)
    return payload.identifiers