# Beachfront API

The beachfront API (bf-api) project is a standalone web service which provides the Beachfront UI and other external projects with a unified interface for creating and querying automated shoreline detection data.

## Requirements
Before building and/or running bf-api, please ensure that the following components are available and/or installed, as necessary:
- [Java](http://www.oracle.com/technetwork/java/javase/downloads/index.html) (JDK for building/developing, otherwise JRE is fine)
- [Maven (v3 or later)](https://maven.apache.org/install.html)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [PostgreSQL](https://www.postgresql.org/download)
- [RabbitMQ](https://www.rabbitmq.com/)
- An available instance of [Beachfront IA Broker](https://github.com/venicegeo/bf-ia-broker)
- Access to Nexus is required to build

Ensure that the nexus url environment variable `ARTIFACT_STORAGE_URL` is set:

	$ export ARTIFACT_STORAGE_URL={Artifact Storage URL}

If running bf-api locally, the following components are also necessary:
- [fake_geoaxis](https://github.com/venicegeo/fake_geoaxis) (to run locally
- [PostGIS](https://www.postgresql.org/download/) - Recommend Vagrant Box that comes with [pz-ingest](https://github.com/venicegeo/pz-ingest) (vagrant up postgis)
- [GeoServer](http://geoserver.org/) - Recommend GeoServer Vagrant Box that comes with [pz-access](https://github.com/venicegeo/pz-access) (vagrant up geoserver)


***
## Setup, Configuring, & Running

### Setup
Create the directory the repository must live in, and clone the git repository:

    $ mkdir -p {PROJECT_DIR}/src/github.com/venicegeo
	$ cd {PROJECT_DIR}/src/github.com/venicegeo
    $ git clone git@github.com:venicegeo/bf-api.git
    $ cd bf-api

>__Note:__ In the above commands, replace {PROJECT_DIR} with the local directory path for where the project source is to be installed.

### Configuring
The `src/main/resources/application.properties` file controls URL information for postgreSQL, ia-broker, and geoserver connection configurations. By default, PostgreSQL is assumed to be running locally on port 5432. If this needs to be changed, this can be done through `application.properties`.


## Building & Running locally

To build and run the Beachfront API locally, navigate to the project directory and run:

	$ mvn clean install -U spring-boot:run

### Running Unit Tests

To run the Beachfront API unit tests from the main directory, run the following command:

	$ mvn test
