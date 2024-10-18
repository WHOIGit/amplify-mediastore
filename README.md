# AMPLIfy Mediastore

AMPLIfy Mediastore is a data-storage bridge and metadata store server application designed to simplify data management. It provides an API endpoint that abstracts the complexities of data storage, allowing users to query and fetch data using a primary ID associated with each data product. The system supports multiple identifiers and can store arbitrary amounts of metadata for each data product, making it a versatile solution for data handling.

This project utilizes Docker, Django, django-ninja, other django libraries, as well as other AMPLIfy repositories such as [amplify-schemas](https://github.com/WHOIGit/amplify-schemas), [amplify-storage-utils](https://github.com/WHOIGit/amplify-storage-utils), and [amplify-amqp-utils](https://github.com/WHOIGit/amplify-amqp-utils). It uses django-simple-history to track changes to media objects, and django-taggit for its media tagging system. 

The Python client library for this API application is [amplify-mediastore-client](https://github.com/WHOIGit/amplify-mediastore-client).


## Installation
###Local Installation
To set up AMPLIfy Mediastore locally, follow these steps:

1. Clone this repository.
2. Make a copy of the dotenv file and rename it to .env. Fill in the `DJANGO_SUPERUSER_` and `DJANGO_SERVICEUSER_` username and password variables, and the `DJANGO_CSRF_TRUSTED_ORIGINS` variable. For local users this later should be "0.0.0.0" or "localhost".
3. Build the Docker containers: `docker compose build`
4. Optionally, to actually run the django runserver, modify the `compose.yaml` file to change the 'api: command:' argument from "testonly" to "test", or comment it out entirely. 
5. Start the application: `docker compose up`

### Production Installation
For a production setup, follow the steps below. Nginx is used to route traffic from a configured site name to the django server instance. 

1. Make a copy of the dotenv file and rename it to .env. Fill in the `DJANGO_SUPERUSER_` and `DJANGO_SERVICEUSER_` username and password variables, and the `DJANGO_CSRF_TRUSTED_ORIGINS` variable to your site's url. Additionally, set the `SSL_` key and cert filepath variables, and the `HTTP_PROXY` variables if needed. Change `DJANGO_DEBUG` from "true" to "false".
2. Copy over `nginx.conf`, and modify it as necessary to fit your site's URL. 
3. Copy `compose-prod.yml` to your production directory.
4. Ensure that you have built and tagged the container image for the Mediastore and hosted it on a container registry like Harbor. Modify `compose-prod.yml` to set the "api: image:" to use the correct image and tag. You may also want to adjust parameters like the location of Nginx logs.
5. Start the production system: `docker compose -f compose-prod.yml up -d`


## Usage Overview
Data products are managed through "media" database objects, each uniquely identified by a primary ID (PID). These objects have practical properties such as metadata, tags, and auxiliary identifiers as well as functional properties like storage configurations. The API facilitates easy access to data products by allowing users to download data or metadata using the PID without needing to know the underlying storage details.

### PIDs and Identifiers
PIDs should be globally unique. If you do not provide one, one will be created for you. Some data product may inherit identifiers from other sources, say an instrument or cruise-schema or filename. Although not neccessarily a primary ID, these other identifiers are important to track- all-the-better to find the desired data product later-on. PIDs and identifiers have associated Identifier Types to help manage identifiers, and can additionally be used to validate correct id formatting.

### Store Configurations
Store configurations (store_config) can be shared by multiple media objects and is used to define where the actual data bytes of the data product is actually stored. A Store Key (store_key) string captures the actual location in the Store of the data product; it is not required for the user to know the store_key, the system handles it behind the scenes. 

A Store can be an S3 bucket, an on-disk filesystem path, or a temporary RAM storage solution for ephemeral intermediary products. S3 Stores ("BucketStores") additonally require an S3 configuration (S3Config) object be created that notes the desired S3 endpoint and credentials. Behind the scenes, [amplify-storage-utils](https://github.com/WHOIGit/amplify-storage-utils) is used to handle interactions with storage.

### Metadata
Data product metadata is stored in the media object database as json, so anything that is json serializable (dicts, lists, strings, numbers) can be stored. 

### Search
'work in progress`
It is intended for users to be able to search for data products based on PID/identifiers using wildcard characters, tags, metadata fields and values. 

Other search vectors such as file creation time and data/process relationships are not handled by the mediastore, look to the AMPLIfy Provenance service for that. 

### Upload and Download
The media store can act as a bridge allowing users to upload and download data product bytes directly to/from it using base64 string encoding. If a data product is stored on an S3 based store however, a user may opt to upload or download using pre-signed urls generated by the mediastore to upload/download directly to/from the S3 store.  

### API Endpoints
You can access the Swagger UI, which exposes all available API endpoints, in your browser at _your.site.com/api/docs_. This interface also provides POST message schemas.

Most endpoints require authentication. You may already have a service account or superuser account generated (check your `.env` file), or you can ask someone with admin privileges to create an account for you via the Django _your.site.com/admin_ panel.

Once you have your username and password, log in using those credentials at the `/api/login` endpoint. Use the token from the login response to authenticate against other endpoints by clicking the "Authenticate" button in the top right corner of the page and entering your token.

## Initial Project Setup Note
When the project is first deployed, there will be no configured S3 Stores or IdentifierTypes. Before uploading data products and creating media objects, you must create IdentifierTypes; otherwise, your PIDs and identifiers will be rejected. You can create these using the `POST /api/identifier` endpoint.

Stores can be created on the fly during the media object creation process. However, for S3 "BUCKETSTORE" type Store Configurations, an S3Config with the endpoint URL and access credentials must already exist. If it doesn't, you will need to create it first using the `POST /api/s3cfg` endpoint.

