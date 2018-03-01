# bf-api-v2

BF-API spring boot java app repository

## Running locally

The services you'll need to run this locally include:

- [Elasticsearch 5.x](https://www.elastic.co/downloads/past-releases)
- [fake_geoaxis](https://github.com/venicegeo/fake_geoaxis)
- [postgis](https://www.postgresql.org/download/) - I typically use the vagrant vm that comes with [pz-ingest](https://github.com/venicegeo/pz-ingest) (vagrant up postgis)
- [RabbitMQ](https://www.rabbitmq.com/download.html) - This also seems to work pretty well https://github.com/gusnips/vagrant-rabbitmq
- [pz-idam](https://github.com/venicegeo/pz-idam)

## Configuration

You'll want to make sure your configuration is setup to look at all of the instances that you just spun up.
