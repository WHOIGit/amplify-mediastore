# AMPLIfy Mediastore

AMPLIfy Mediastore is a data-storage bridge and metadata store server application designed to simplify data management. It provides an API endpoint that abstracts the complexities of data storage, allowing users to query and fetch data using a primary ID associated with each data product. The system supports multiple identifiers and can store arbitrary amounts of metadata for each data product, making it a versatile solution for data handling.

This project utilizes Django, Docker, and Pydantic, as well as other AMPLIfy repositories such as [amplify-schemas](https://github.com/WHOIGit/amplify-schemas), [amplify-storage-utils](https://github.com/WHOIGit/amplify-storage-utils), and [amplify-amqp-utils](https://github.com/WHOIGit/amplify-amqp-utils). It uses django-simple-history to track changes to media objects, and django-taggit for its media tagging system. 

The Python client library for this API application is [amplify-mediastore-client](https://github.com/WHOIGit/amplify-mediastore-client).


## Installation
###Local Installation
To set up AMPLIfy Mediastore locally, follow these steps:

1. Clone the repository: git clone <repository-url>
2. Make a copy of the dotenv file and rename it to .env. Fill in the `DJANGO_SUPERUSER_` and `DJANGO_SERVICEUSER_` username and password variables, and the `DJANGO_CSRF_TRUSTED_ORIGINS` variable. For local users this later should be "0.0.0.0" or "localhost".
3. Build the Docker containers: `docker compose build`
4. Optionally, to actually run the django runserver, modify the `compose.yaml` file to change the 'api: command:' argument from "testonly" to "test", or comment it out entirely. 
5. Start the application: `docker compose up`

### Production Installation
For a production setup, follow these steps:

1. Make a copy of the dotenv file and rename it to .env. Fill in the `DJANGO_SUPERUSER_` and `DJANGO_SERVICEUSER_` username and password variables, and the `DJANGO_CSRF_TRUSTED_ORIGINS` variable to your site's url. Additionally, set the `SSL_` key and cert filepath variables, and the `HTTP_PROXY` variables if needed.
2. Copy over `nginx.conf`, and modify it as necessary to fit your site's URL. Change `DJANGO_DEBUG=true` to `false`
3. Copy `compose-prod.yml` to your production directory.
4. Ensure that you have built and tagged the container image for the Mediastore and hosted it on a container registry like Harbor. Modify `compose-prod.yml` to set the "api: image:" to use the correct image and tag. You may also want to adjust parameters like the location of Nginx logs.
5. Start the production system: `docker compose -f compose-prod.yml up -d`


## Usage

### Overview 
Data products are tracked using "media" database objects. media objects have properties such as "PID" (primary ID), "metadata", "identifiers" for storing auxiliary IDs, "store_config", "store_key", and "tags". Store configurations (StoreConfig) can be shared by multiple media objects is used to define where the actual data bytes of the data product is actually stored. A Store Key (store_key) string captures the actual location in the Store of the data product; it is not required for the user to know the store_key, that's something for the system to handle. A Store can be an S3 bucket, an on-disk filesystem path, or a temporary RAM storage solution. (S3 BucketStore type stores additonally require an S3 configuration (S3Config) object be created that notes the desired S3 endpoint and credentials). Media objects all have a globally unique PID or primary ID that the user uses to refer to the media object. The api allows a user to download data/metadata by refering to a data product's PID, without having to know the details of where or how the data is actually stored. Some data product may inherit identifiers from other sources, say an instrument or cruise or filename. Although not neccessarily a primary ID, these other identifiers are important to track all-the-better to find the desired data product. PIDs and identifiers have associated Identifier Types to help manage identifiers, and can additionally be used to validate id formatting. Metadata can be anything, so long as it is serializable as json (dicts, lists, strings, numbers). PIDs, identifiers, tags, and metadata are all intended to be searchable. The api exposes upload, download, and database object endpoints. 

### Initial Project Setup Steps
The project when first deployed with have no configured S3 Stores or identifiers. Before uploading data products and creating media objects, these will need to be defined and created. 
