# Beachfront API

## Running locally

The services you'll need to run this locally include:

- [fake_geoaxis](https://github.com/venicegeo/fake_geoaxis)
- [postgis](https://www.postgresql.org/download/) - Recommend Vagrant Box that comes with [pz-ingest](https://github.com/venicegeo/pz-ingest) (vagrant up postgis)
- [geoserver](http://geoserver.org/) - Recommend GeoServer Vagrant Box that comes with [pz-access](https://github.com/venicegeo/pz-access) (vagrant up geoserver)

Run the application by invoking `clean install -U spring-boot:run`
