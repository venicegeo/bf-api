# bf-api

API service for the Beachfront project.


## Running locally for development

Follow the instructions below to install and configure the following items:

- Python 3.5 (with `virtualenv`)
- GeoServer
- PostgreSQL
- PostGIS


### 1. Install Python 3.5 on your machine

Install [Python 3.5](https://www.python.org/downloads/) as normal.  Then from
the terminal, execute:

```
pip3 install virtualenv
python3 -m virtualenv --version
```


### 2. Install PostgreSQL + PostGIS on your machine

Even if you intend to point at a remote database, [`psycopg2` has a runtime
dependency on `libpq`](http://initd.org/psycopg/docs/install.html), which is
bundled with most PostgreSQL distributions.

> **Tip:** If you're running MacOS, the simplest setup/configuration route is to
>          just use [Postgres.app](http://postgresql.org/download/macosx/) which
>          includes both PostgreSQL and the PostGIS extensions.

After you finish installing, start Postgres.  Then, from the terminal execute:

```bash
psql -c "CREATE ROLE beachfront WITH LOGIN PASSWORD 'secret'"
psql -c "CREATE DATABASE beachfront WITH OWNER beachfront"
psql beachfront -c "CREATE EXTENSION postgis"
```

Lastly, you need to add Postgres' `bin/` directory to your system `PATH` (this
will depend on which Postgres distribution you use and where you installed it).
From the terminal, execute:

```
echo 'export PATH="/Applications/Postgres.app/Contents/Versions/9.6/bin:${PATH}"' >> ~/.profile
```


### 3. Install GeoServer on your machine

> **Warning:** This part is a hot mess, but the alternative is installing and
>              configuring Apache Tomcat or some other JEE servlet container.
>              **Do not** use these instructions to configure a production
>              instance of GeoServer.

First, [follow the official instructions to install
GeoServer](http://docs.geoserver.org/latest/en/user/installation/osx_binary.html),
then make sure the server is not running.

Next, we're going to restore the platform-independent binary's built-in servlet
container's ability to listen on HTTPS.  From a new terminal window/tab, execute:

```bash
cd $GEOSERVER_HOME

curl "https://raw.githubusercontent.com/eclipse/jetty.project/jetty-$(ls lib/jetty-server-*.jar | sed -E 's_^lib/jetty-server-(.*)\.jar$_\1_')/jetty-server/src/main/config/modules/ssl.mod" -o modules/ssl.mod

keytool -importkeystore \
    -srcstoretype PKCS12 \
    -srckeystore /path/to/bf-api/.dev/ssl-certificate.pkcs12 \
    -destkeystore beachfront.jks \
    -srcstorepass secret \
    -deststorepass secret \
    -noprompt

cat <<'EOT' >> start.ini
##########################################
# Enable HTTPS
--module=https
jetty.truststore=beachfront.jks
jetty.keystore=beachfront.jks
jetty.keymanager.password=secret
jetty.truststore.password=secret
jetty.keystore.password=secret
##########################################
EOT

./bin/startup.sh
```

Lastly, visit [https://localhost:8443/geoserver/web/](https://localhost:8443/geoserver/web/)
in your browser.  Log in using the default geoserver admin credentials and
create a `beachfront` user with password `secret` as described in the above
instructions.

> TODO: Add instructions about creating workspace and PostGIS datastore.


### 4. Create development environment

From the terminal, execute:

```bash
./scripts/create-development-environment.sh
```

This will create a virtualenv and the dev environment artifacts.  After the
script finishes, edit `.dev/environment-vars.sh` to fill in the empty values.

Lastly, add the Beachfront certificate (i.e., `.dev/ssl-certificate.pem`) to
your machine and/or browser's SSL store and authorize its use for identifying
websites via SSL/HTTPS.


### 5. Start bf-api

From the terminal, execute:

```bash
./scripts/run-in-development-mode.sh
```


## Running unit tests

From the terminal, execute:

```bash
./scripts/test.sh
```


## Deploying

1. Either `cf push` or use the normal CI build pipeline to deploy to PCF.
2. Provide credentials to the running instance via the PCF web management
portal, or from the terminal, ala:

```bash
cf set-env bf-api SYSTEM_API_KEY <valid Piazza API key>
```


## Environment Variables

| Variable            | Description |
|---------------------|-------------|
| `SYSTEM_API_KEY`    | Credentials for accessing Piazza.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS`           | GEOAxIS hostname.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS_CLIENT_ID` | GEOAxIS OAuth client ID.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS_SECRET`    | GEOAxIS OAuth secret.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `DOMAIN`            | Overrides the domain where the other services can be found (automatically injected by Pivotal CloudFoundry) |
| `PORT`              | Overrides the default listening port (automatically injected by Pivotal CloudFoundry) |
| `PZ_GATEWAY`        | Overrides the Piazza gateway autodetection/configuration |
| `VCAP_SERVICES`     | Overrides the default [PCF `VCAP_SERVICES`](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES) (automatically injected by A Pivotal CloudFoundry) |
| `CATALOG`           | Overrides the Image Catalog hostname |
| `TIDE_SERVICE`      | Overrides the Tide Prediction service hostname |
| `DEBUG_MODE`        | Set to `1` to start the server in debug mode.  Note that this will have some fairly noisy logs. |
| `SKIP_PRODUCTLINE_INSTALL` | Set to `1` to skip installing triggers and services for catalog harvest events (recommended for local development). |
