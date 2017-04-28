# bf-api

API service for the Beachfront project. This is the central point of interaction
for the Beachfront front-end.

## Local development setup

`bf-api` requires a non-trivial environment setup for development, including
Python, GeoServer, PostgreSQL, and PostGIS. For this reason, a Vagrant setup is
available, and outlined below.

### 1. Install dependencies

If you have not already done so, install Vagrant directly (not via your package
manager): https://www.vagrantup.com/downloads.html

Vagrant requires a virtual machine provider, and works seamlessly with Virtualbox.
If you do not have it available, install Virtualbox from directly (not via your
package manager): https://www.virtualbox.org/wiki/Downloads

### 2. Let Vagrant do most of the work

In your command line, navigate to the source repository directory and run:

    vagrant up

Vagrant will download, install, and run all the necessary setup. This will take
a while. Near the end of the process, watch for and take note of lines such as
these:

    ==> bfapi: Forwarding ports...
        bfapi: 5000 (guest) => 5001 (host) (adapter 1)
        bfapi: 5432 (guest) => 5432 (host) (adapter 1)
        bfapi: 8080 (guest) => 8089 (host) (adapter 1)
        bfapi: 22 (guest) => 2222 (host) (adapter 1)

They will be important for accessing the services in the virtual machine.

### 3. Set up your environment variables

> If you are using an instance of the `bf-api` repository that already was set
  up to run without vagrant, you will need to re-build your development environment
  variables. Clear them by running:
>  
>     scripts/create-development-environment.sh --force

Configure the following environment variables in `.dev/environment-vars.sh`, as needed:

| Variable            | Description |
|---------------------|-------------|
| `PIAZZA_API_KEY`    | Credentials for accessing Piazza.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS`           | GEOAxIS hostname.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS_CLIENT_ID` | GEOAxIS OAuth client ID.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `GEOAXIS_SECRET`    | GEOAxIS OAuth secret.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `DOMAIN`            | Overrides the domain where the other services can be found (automatically injected by Pivotal CloudFoundry) |
| `PORT`              | Overrides the default listening port (automatically injected by Pivotal CloudFoundry) |
| `VCAP_SERVICES`     | Overrides the default [PCF `VCAP_SERVICES`](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES) (automatically injected by A Pivotal CloudFoundry) |
| `UI`                | Overrides the Beachfront UI hostname |
| `PIAZZA`            | Overrides the Piazza hostname |
| `CATALOG`           | Overrides the Beachfront Image Catalog hostname |
| `SECRET_KEY`        | Overrides the randomly-generated secret key used by Flask for session I/O |
| `DEBUG_MODE`        | Set to `1` to start the server in debug mode.  Note that this will have some fairly noisy logs. |
| `MUTE_LOGS`         | Set to `1` to mute the logs (happens by default in test mode) |

Restart the instance to make it take account of the environment variables:

    $ vagrant reload

### 4. Test the instance

Check if everything is OK by querying the Vagrant-forwarded port for `bf-api`.
With `curl`, you will need to use `-k` or pass in the correct certificate.

    $ curl -k https://localhost:5001
    {
      "uptime": 49.939
    }

    $ curl --cacert .dev/ssl-certificate.pem https://localhost:5001
    {
      "uptime": 78.199
    }

Refer to the earlier provisioned ports if 5001 is not the correct port.

## Local development operation

### Run unit tests

    $ vagrant ssh -c /vagrant/scripts/test.sh

### Apply code changes

The Gunicorn server is configured with auto-reloading, so any changes
should trigger a reload of the server. However, if you need to hard-reload the
server, use the following command:

    $ vagrant reload

### Manually run the server to see standard output

In order to do this, you must connect to the Vagrant machine, shut down the
background (provisioned) server, and run it manually:

    $ vagrant ssh
    $ killall gunicorn
    $ /vagrant/scripts/run-in-development-mode.sh

## Deploying

1. Either `cf push` or use the normal CI build pipeline to deploy to PCF.
2. Provide credentials to the running instance via the PCF web management
portal, or from the terminal, ala:

```bash
cf set-env bf-api PIAZZA_API_KEY <valid Piazza API key>
```
