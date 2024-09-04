import os

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

from mediastore.models import Media, IdentityType, StoreConfig
from mediastore.schemas import MediaSchemaCreate,StoreConfigSchema

from .schemas import UploadSchemaInput, UploadSchemaOutput, DownloadSchemaInput, DownloadSchemaOutput


def generate_file(filename, content: bytes = b'test text'):
    file = io.BytesIO()
    file.write(content)
    file.name = filename
    file.seek(0)
    return file


class FileHandlerUploadTest(TestCase):

    def setUp(self):
        IdentityType.objects.create(name='DEMO')
        self.filestore_dict = dict(StoreConfigSchema(type='FilesystemStore', bucket='/demobucket', s3_params=None))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)


    def test_MediaService_create_minimal(self):
        PID = 'demo_pid'
        file = SimpleUploadedFile("test_file.txt", b"This is the content of the file.", content_type="text/plain")
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.filestore_dict))

        resp = self.client.post("/upload", data=dict(media_schema_create=mediadata), FILES={'file':file})
        # {"object_url": "the_ready_object_url pid=demo_pid fname=test_file.txt", "presigned_url": null}
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

