import os
import base64

from django.utils.datastructures import MultiValueDict

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

import json
import io

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from ninja.testing import TestClient
from ninja import File
from ninja import UploadedFile
from rest_framework.authtoken.models import Token

from config.api import api

from mediastore.models import Media, IdentityType, StoreConfig, S3Config
from mediastore.schemas import MediaSchemaCreate,StoreConfigSchema, S3ConfigSchema

from .schemas import UploadSchemaInput, UploadSchemaOutput, DownloadSchemaInput, DownloadSchemaOutput

def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)

class FileHandlerUploadTest(TestCase):

    def setUp(self):
        IdentityType.objects.create(name='DEMO')
        self.filestore_dict = dict(StoreConfigSchema(type=StoreConfig.FILESYSTEMSTORE, bucket='/demobucket', s3_params=None))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

    def test_MediaService_create_minimal(self):
        PID = 'uploadPID'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.filestore_dict))
        filecontent = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(filecontent)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

