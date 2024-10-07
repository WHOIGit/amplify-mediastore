from typing import List, Optional

from ninja import Schema, File
from ninja.files import UploadedFile

from mediastore.schemas import MediaSchemaCreate, MediaSchema

## Upload Schemas ##
class UploadSchemaInput(Schema):
    mediadata: MediaSchemaCreate
    base64: Optional[str] = ''

class UploadSchemaOutput(Schema):
    status: str
    presigned_put: Optional[str] = None

class UploadError(Schema):
    error: str

## Download Schemas ##
class DownloadSchemaInput(Schema):
    pid: str
    direct: Optional[bool] = True

class DownloadSchemaOutput(Schema):
    mediadata: MediaSchema
    base64: Optional[str] = ''
    presigned_get: Optional[str] = ''

class DownloadError(Schema):
    pid: str
    error: str
    msg: str

