from typing import List, Optional

from ninja import Schema, File
from ninja.files import UploadedFile

from mediastore.schemas import MediaSchemaCreate, MediaSchema

## Upload Schemas ##
class UploadSchemaInput(Schema):
    mediadata: MediaSchemaCreate
    file: UploadedFile = File(...)

class UploadSchemaOutput(Schema):
    object_url: Optional[str] = None
    presigned_url: Optional[str] = None

class UploadError(Schema):
    error: str

## Download Schemas ##
class DownloadSchemaInput(Schema):
    pid: str
    direct: Optional[bool] = True

class DownloadSchemaOutput(Schema):
    mediadata: MediaSchema
    file: Optional[bytes]
    object_url: Optional[str]
    # TODO verify that at-least/only file or link is not None

class DownloadError(Schema):
    error: str

