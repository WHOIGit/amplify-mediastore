import os
import base64
import uuid
import json
from unittest import skipIf, skipUnless

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

from django.test import TestCase
from ninja.testing import TestClient
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token

try: import requests  # only used for one test in whole project
except ImportError: requests=None

from config.api import api

from mediastore.models import Media, IdentifierType, StoreConfig, S3Config
from schemas.mediastore import MediaSchemaCreate, StoreConfigSchemaCreate, S3ConfigSchemaCreate
from schemas.mediastore import UploadSchemaInput, DownloadSchemaInput

def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)


class FileHandlerFilestoreTests(TestCase):
    def setUp(self):
        IdentifierType.objects.create(name='DEMO')
        self.storeconfig_dict = dict(StoreConfigSchemaCreate(type=StoreConfig.FILESYSTEMSTORE, bucket='/demobucket', s3_url=''))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

    def test_updown_ram(self):
        PID = 'test_updown_ram'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict))
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        #print(data)
        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)


@skipUnless(os.environ.get('TESTS_S3_URL'), '"TESTS_S3_URL" env variable set')
class FileHandlerS3storeTests(TestCase):
    def setUp(self):
        IdentifierType.objects.create(name='DEMO')
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

        self.s3cfg,created_s3cfg = S3Config.objects.get_or_create(
            url=os.environ['TESTS_S3_URL'],
            access_key=os.environ['TESTS_S3_ACCESS'],
            secret_key=os.environ['TESTS_S3_SECRET'])
        self.s3store_dict = dict(StoreConfigSchemaCreate(type=StoreConfig.BUCKETSTORE,
                bucket=os.environ['TESTS_S3_BUCKET'], s3_url=os.environ['TESTS_S3_URL']))

    def tearDown(self) -> None:
        # removes uploaded objects from test bucket
        import storage.s3
        medias = Media.objects.all()
        for media in medias:
            proxies = dict(proxies={'http': os.environ.get('HTTP_PROXY')}) if os.environ.get('HTTP_PROXY') else None
            S3_CLIENT_ARGS = dict(
                s3_url=media.store_config.s3cfg.url,
                s3_access_key=media.store_config.s3cfg.access_key,
                s3_secret_key=media.store_config.s3cfg.secret_key,
                bucket_name=media.store_config.bucket,
                botocore_config_kwargs = proxies
            )
            with storage.s3.BucketStore(**S3_CLIENT_ARGS) as store:
                store.delete(media.store_key)

    def test_updown_s3_direct(self):
        PID = 'test_updown_s3_direct'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.s3store_dict))
        upload_content = b'egg salad sand witch'
        encoded_content = encode64(upload_content)
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encoded_content))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD DIRECT
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)

    @skipIf(requests is None, 'requests module unavailable')
    def test_updown_s3_presigned(self):
        PID = 'test_updown_s3_presigned'
        mediadata = dict(MediaSchemaCreate(
            pid=PID, pid_type='DEMO',
            store_config=self.s3store_dict))
        upload_content = b'egg salad sand witch\n'+str(uuid.uuid1()).encode('ascii')
        payload = dict(UploadSchemaInput(mediadata=mediadata))  # sans base64 data
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        presigned_put = resp.json()['presigned_put']

        # Uploading file using presigned url for put.
        # Filename of uploaded file totally ignored, store_key gets used instead.
        test_file = SimpleUploadedFile("TEST2.txt", upload_content)#, content_type="text/plain")
        download_response = requests.put(presigned_put, data=test_file)
        self.assertEqual(download_response.status_code, 200)

        # Fetching presigned S3 GET url
        resp = self.client.get(f"/download/url/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        presigned_get = json.loads(resp.content.decode())['presigned_get']

        # Fetching presigned S3 GET urls list
        resp = self.client.post(f"/download/urls", json=[PID])
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        presigned_gets = [dso['presigned_get'] for dso in json.loads(resp.content.decode())]
        self.assertEqual([presigned_get],presigned_gets)

        # Downloading file using presigned GET url.
        # Filename of uploaded file totally ignored, store_key gets used instead.
        download_response = requests.get(presigned_get)
        self.assertEqual(download_response.status_code, 200, download_response.content.decode())
        downloaded_content = download_response.content
        self.assertEqual(upload_content,downloaded_content)


class FileHandlerDictstoreTests(TestCase):
    def setUp(self):
        FileHandlerFilestoreTests.setUp(self)
        self.storeconfig_dict = dict(StoreConfigSchemaCreate(type=StoreConfig.DICTSTORE, bucket='/demobucket'))

    def test_updown_RAM(self):
        PID = 'test_updown_RAM'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict))
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)


class FileHandlerSqlitestoreTests(TestCase):
    def setUp(self):
        FileHandlerFilestoreTests.setUp(self)
        self.storeconfig_dict = dict(StoreConfigSchemaCreate(
            type=StoreConfig.SQLITESTORE, bucket='/demobucket/demodb.sqlite3'))

    def test_updown_Sqlite(self):
        PID = 'test_updown_Sqlite'
        mediadata = dict(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict)
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)
