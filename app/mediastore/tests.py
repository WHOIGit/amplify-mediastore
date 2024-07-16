import os
os.environ["NINJA_SKIP_REGISTRY"] = "yes"
import json

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from ninja.testing import TestClient

from .views import api

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


class MediaApiTest(TestCase):

    def setUp(self):
        self.client = TestClient(api)

    def test_hello(self):
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello, world!"})

    def test_MediaService_list(self):
        resp = self.client.get("/media")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id1(self):
        PID = 'm1'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
            metadata = {'egg':'nog'},
            identifiers = {'BIN':'bin_xyz'} )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id2(self):
        # minimal create
        PID = 'm2'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id3_dupeIDs(self):
        PID = 'm3'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'DEMO':PID, 'BIN':'bin_xyz'},
        )
        expected = dict(
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'BIN':'bin_xyz'},
            s3url = '',
            metadata = {},
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        resp2 = self.client.get(f"/media/{PID}")
        received = resp2.content.decode()
        received = json.loads(received)
        received.pop('pk')
        received = ordered(received)
        expected = ordered(expected)
        self.assertEqual(received, expected, msg=f'{received} != {expected}')

    def test_MediaService_create_id4_once(self):
        PID = 'm4'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        demo2 = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
        )
        with self.assertRaises(IntegrityError):
            resp2 = self.client.post("/media", json=demo2)

    def test_MediaService_create_read_delete(self):
        PID = 'm5'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        resp2 = self.client.get(f"/media/{PID}")
        self.assertEqual(resp2.status_code, 200, msg=resp2.content.decode())

        resp3 = self.client.delete(f"/media/{PID}")
        self.assertEqual(resp3.status_code, 204, msg=resp3.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp4 = self.client.get(f"/media/{PID}")


    def test_create_patch(self):
        PID = 'm6'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
            metadata = {'egg':'nog', 'zip':'zap', 'quick':'quack'}
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  json.loads( resp.content.decode() )
        PK = received1['pk']
        payload2 = dict(s3url='bucketB:abc',
                        identifiers={'DEMO2':'newvalue'},
                        metadata={'EGG':'NOG','zip':'ZAP'})

        resp2 = self.client.patch(f'/media/{PID}', json=payload2)
        self.assertEqual(resp.status_code, 200, msg=resp2.content.decode())  # TODO why status_code != 204 ?
        #self.assertEqual(resp.status_code, 204, msg=resp2.content.decode())  # TODO why status_code != 204 ?
        resp3 = self.client.get(f'/media/{PID}')
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())
        received3 = json.loads( resp3.content.decode() )
        received3 = ordered(received3)

        expected = dict(
            pk = PK,
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketB:abc',
            identifiers = {'DEMO2':'newvalue'},
            metadata = {'egg':'nog', 'EGG':'NOG', 'zip':'ZAP', 'quick':'quack'}
        )

        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')


    def test_create_put(self):
        PID = 'm7'
        PID2 = 'm77'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
            metadata = {'egg':'nog', 'zip':'zap', 'quick':'quack'}
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  json.loads( resp.content.decode() )
        PK = received1['pk']
        payload2 = dict(pid=PID2,
                        pid_type='DEMO',
                        s3url='bucketB:abc',
                        identifiers={'DEMO2':'newvalue'},
                        metadata={'EGG':'NOG','zip':'ZAP'})

        resp2 = self.client.put(f'/media/{PID}', json=payload2)
        self.assertEqual(resp.status_code, 200, msg=resp2.content.decode())  # TODO why status_code != 204 ?
        #self.assertEqual(resp.status_code, 204, msg=resp2.content.decode())  # TODO why status_code != 204 ?
        resp3 = self.client.get(f'/media/{PID2}')
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())
        received3 = json.loads( resp3.content.decode() )
        received3 = ordered(received3)

        expected = dict(
            pk = PK,
            pid = PID2,
            pid_type = 'DEMO',
            s3url = 'bucketB:abc',
            identifiers = {'DEMO2':'newvalue'},
            metadata = {'EGG':'NOG', 'zip':'ZAP'}
        )

        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')
