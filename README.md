# AMPLIfy Mediastore

AMPLIfy Mediastore is a data-storage bridge and metadata store server application designed to simplify data management. It provides an API endpoint that abstracts the complexities of data storage, allowing users to query and fetch data using a primary ID associated with each data product. The system supports multiple identifiers and can store arbitrary amounts of metadata for each data product, making it a versatile solution for data handling.

This project uses Docker, Django, django-ninja, django-simple-history for change tracking, and django-taggit for media tagging. It also depends on other AMPLIfy repositories: [amplify-schemas](https://github.com/WHOIGit/amplify-schemas), [amplify-storage-utils](https://github.com/WHOIGit/amplify-storage-utils), and [amplify-amqp-utils](https://github.com/WHOIGit/amplify-amqp-utils).

The Python client library for this API is [amplify-mediastore-client](https://github.com/WHOIGit/amplify-mediastore-client).


## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+


## Getting Started

This section walks you through standing up a local instance and making your first API call.

**1. Clone and configure**

```bash
git clone https://github.com/WHOIGit/amplify-mediastore.git
cd amplify-mediastore
cp dotenv .env
```

Edit `.env` and fill in at minimum:
- `DJANGO_SECRET_KEY` — a long random string (e.g., from `python -c "import secrets; print(secrets.token_hex(50))"`)
- `DJANGO_SUPERUSER_PASSWORD` — your admin password
- `DJANGO_SERVICEUSER_PASSWORD` — your service account password
- `DJANGO_CSRF_TRUSTED_ORIGINS` — set to `http://localhost` for local use

**2. Build and start**

```bash
docker compose build
docker compose up
```

By default the container runs in `testonly` mode (runs tests, no persistent server). To start the live server, edit `compose.yaml` and change the `api: command:` from `./start-django testonly` to `./start-django` (or comment it out).

**3. Access the API**

Once running, the Swagger UI is available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

**4. Initial setup — required before first use**

Before creating media objects, you must create at least one `IdentifierType` (otherwise PIDs and identifiers will be rejected). Use the `POST /api/identifier-type` endpoint in the Swagger UI.

For S3-backed storage, create an `S3Config` first via `POST /api/s3cfg` with your endpoint URL and credentials.

**5. Authenticate**

Log in via `POST /api/login` with your superuser credentials. Use the returned token to authenticate in Swagger UI by clicking "Authorize" and entering your token.


## Installation

### Local Installation

1. Clone this repository.
2. Copy the dotenv file and rename it `.env`. Fill in `DJANGO_SECRET_KEY`, the `DJANGO_SUPERUSER_` and `DJANGO_SERVICEUSER_` username/password variables, and set `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost`.
3. Build the Docker containers: `docker compose build`
4. To run the live server, edit `compose.yaml` and change the `api: command:` value from `./start-django testonly` to `./start-django`, or comment it out entirely.
5. Start the application: `docker compose up`

### Production Installation

For production, Apache (or another reverse proxy) routes traffic to the Django server.

1. Copy `dotenv` to `.env`. Fill in `DJANGO_SECRET_KEY`, `DJANGO_SUPERUSER_*`, `DJANGO_SERVICEUSER_*`, and `DJANGO_CSRF_TRUSTED_ORIGINS` with your site's URL. Set `DJANGO_DEBUG=false`. Configure `HTTP_PROXY`/`HTTPS_PROXY` if needed.
2. Build and tag the container image and push it to your container registry.
3. Copy `compose-prod.yaml` to your production directory and update the `api: image:` field with the correct image and tag.
4. Start the production system: `docker compose -f compose-prod.yaml up -d`


## Usage Overview

Data products are managed through "media" database objects, each uniquely identified by a primary ID (PID). These objects have practical properties such as metadata, tags, and auxiliary identifiers as well as functional properties like storage configurations. The API facilitates easy access to data products by allowing users to download data or metadata using the PID without needing to know the underlying storage details.

### PIDs and Identifiers

PIDs should be globally unique. If you do not provide one, one will be created for you. Some data products may inherit identifiers from other sources, such as an instrument, cruise schema, or filename. Although not necessarily a primary ID, these other identifiers are important to track — the better to find the desired data product later. PIDs and identifiers have associated Identifier Types to help manage them, and can additionally be used to validate correct ID formatting.

### Store Configurations

Store configurations (`store_config`) can be shared by multiple media objects and define where the actual data bytes of a data product are stored. A Store Key (`store_key`) string captures the actual location within the store; users do not need to know the store key — the system handles it behind the scenes.

A Store can be an S3 bucket, an on-disk filesystem path, or a temporary RAM storage solution for ephemeral intermediary products. S3 stores ("BucketStores") additionally require an `S3Config` object specifying the desired S3 endpoint and credentials. Behind the scenes, [amplify-storage-utils](https://github.com/WHOIGit/amplify-storage-utils) handles interactions with storage.

### Metadata

Data product metadata is stored in the media object database as JSON, so anything that is JSON-serializable (dicts, lists, strings, numbers) can be stored.

### Search

*Work in progress.*

Users will be able to search for data products based on PID/identifiers using wildcard characters, tags, and metadata fields and values.

Other search vectors such as file creation time and data/process relationships are not handled by the mediastore — see the AMPLIfy Provenance service for that.

### Upload and Download

The mediastore can act as a bridge allowing users to upload and download data product bytes directly to/from it using base64 string encoding. If a data product is stored on an S3-based store, a user may opt to upload or download using pre-signed URLs generated by the mediastore to interact directly with the S3 store.

### API Endpoints

The Swagger UI, which exposes all available API endpoints and POST message schemas, is available at _your.site.com/api/docs_ (or [http://localhost:8000/api/docs](http://localhost:8000/api/docs) locally).

Most endpoints require authentication. You may already have a service account or superuser account generated (check your `.env` file), or you can ask someone with admin privileges to create an account via the Django admin panel at _your.site.com/admin_.

Once you have your credentials, log in via `POST /api/login`. Use the returned token to authenticate against other endpoints by clicking "Authorize" in the top right corner of the Swagger UI and entering your token.