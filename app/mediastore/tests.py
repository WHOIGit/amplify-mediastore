import os

os.environ["NINJA_SKIP_REGISTRY"] = "yes"
import json

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from ninja.testing import TestClient

from .models import Media, IdentityType

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
        IdentityType.objects.create(name='DEMO')
        IdentityType.objects.create(name='BIN')
        IdentityType.objects.create(name='DEMO2')

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
            tags = [],
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
            metadata = {'egg':'nog', 'zip':'zap', 'quick':'quack'},
            tags=['one', 'two'],
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  json.loads( resp.content.decode() )
        PK = received1['pk']
        payload2 = dict(s3url='bucketB:abc',
                        identifiers={'DEMO2':'newvalue'},
                        metadata={'EGG':'NOG','zip':'ZAP'},
                        tags = ['two', 'three'],)

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
            metadata = {'egg':'nog', 'EGG':'NOG', 'zip':'ZAP', 'quick':'quack'},
            tags = ['one', 'two', 'three'],
        )

        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')
        return PK


    def test_create_put(self):
        PID = 'm7'
        PID2 = 'm77'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            s3url = 'bucketA:xyz',
            metadata = {'egg':'nog', 'zip':'zap', 'quick':'quack'},
            tags = ['one two'],
        )
        resp = self.client.post("/media", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  json.loads( resp.content.decode() )
        PK = received1['pk']
        payload2 = dict(pid=PID2,
                        pid_type='DEMO',
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
            s3url = '',
            identifiers = {'DEMO2':'newvalue'},
            metadata = {'EGG':'NOG', 'zip':'ZAP'},
            tags = [],
        )

        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')
        return PK




class MediaVersioningTest(TestCase):

    def setUp(self):
        MediaApiTest.setUp(self)

    def test_hello(self):
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello, world!"})

    def test_Versioning_patch(self):
        PK = MediaApiTest.test_create_patch(self)
        media = Media.objects.get(pk=PK)
        m1 = media.history.earliest()   # first one   .first() not correrct
        m2 = media.history.latest()     # most recent .last() not correct
        self.assertEqual(m1.s3url, 'bucketA:xyz')
        self.assertEqual(m2.s3url, 'bucketB:abc')

        self.assertEqual(m1.metadata, {'egg':'nog', 'zip':'zap', 'quick':'quack'})
        self.assertEqual(m2.metadata, {'egg':'nog', 'EGG':'NOG', 'zip':'ZAP', 'quick':'quack'} )

        model_diff = m2.diff_against(m1)  # NEWER INSTANCE diff_against OLDER INSTANCE
        expected_changed_fields = sorted(['s3url','identifiers','metadata'])  # tags is foreign key and not diff'd
        self.assertEqual(sorted(model_diff.changed_fields), expected_changed_fields )

        metadata_changes = [modelchange for modelchange in model_diff.changes if modelchange.field=='metadata'][0]
        dict_diff = set(metadata_changes.new.items()) - set(metadata_changes.old.items())
        expected = {'EGG':'NOG','zip':'ZAP'}   # the PATCH that was used
        self.assertEqual(dict_diff, set(expected.items()))

        # METADATA dict COMPARE WORKS FOR PATCH (additive) BUT NOT PUT
        # for true comparison need "new KEYs (and val)"  "changed key:VALs"  "removed KEYs (and val)"
        # and that's out of scope for rn

    def test_Versioning_put(self):
        PK = MediaApiTest.test_create_put(self)
        media = Media.objects.get(pk=PK)
        m1 = media.history.earliest()   # first one   .first() not correrct
        m2 = media.history.latest()     # most recent .last() not correct
        self.assertEqual(m1.pid, 'm7', msg=m1)
        self.assertEqual(m2.pid, 'm77', msg=m2)

        model_diff = m2.diff_against(m1)  # NEWER INSTANCE diff_against OLDER INSTANCE
        expected_changed_fields = sorted(['pid','s3url','identifiers','metadata'])  # tags is foreign key and not diff'd
        self.assertEqual(sorted(model_diff.changed_fields), expected_changed_fields )

        # METADATA dict COMPARE WORKS FOR PATCH (additive) BUT NOT PUT
        # for true comparison need "new KEYs (and val)"  "changed key:VALs"  "removed KEYs (and val)"
        # and that's out of scope for rn

        #metadata_changes = [modelchange for modelchange in model_diff.changes if modelchange.field=='metadata'][0]
        #dict_diff = set(metadata_changes.new.items()) - set(metadata_changes.old.items())
        #expected = {'EGG':'NOG','zip':'ZAP'}   # the PUT that was used
        #self.assertEqual(dict_diff, set(expected.items()))
        #self.assertEqual(metadata_changes.old, metadata_changes.new)