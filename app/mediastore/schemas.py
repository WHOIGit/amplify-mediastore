from typing import List
from pydantic import BaseModel
from ninja import ModelSchema, Schema
from ninja.orm import create_schema


from mediastore.models import Media, Identity

class IdentitySchema(ModelSchema):
    class Meta:
        model = Identity
        fields = ['type','token', 'is_pid']
        fields_optional = ['is_pid']

class MediaSchema(Schema):
    ids: List[IdentitySchema]
    metadata: dict
