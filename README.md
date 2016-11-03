# bf-api-python

API service for the Beachfront project.


## Installing

From project root:

```
$ virtualenv --python python3.5 .env
$ . .env/bin/activate
$ pip install -r requirements.txt
```


## Running in development mode

#### 1. Create `.environment-vars.dev.sh` with the contents:

```
export DOMAIN=<some target domain>
export SYSTEM_AUTH_TOKEN=<valid Piazza auth token>
export PORT=5000
export VCAP_SERVICES='{valid json blob}'
```

> **Tip:** You can get `VCAP_SERVICES` by running `cf env bf-api` or checking
> the environment variables from the PCF web management portal.
>
> [More about `VCAP_SERVICES`](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES)

#### 2. From the terminal, execute:

```
$ ./scripts/run-in-development-mode.sh
```


## Deploying

1. Either `cf push` or use the normal CI build pipeline to deploy to PCF.
2. Provide credentials to the running instance by `cf set-env bf-api SYSTEM_AUTH_TOKEN <valid Piazza auth token>` or
via the PCF web management portal.

```
$ cf set-env bf-api SYSTEM_AUTH_TOKEN <valid Piazza auth token>
```


## Environment Variables

| Variable            | Description |
|---------------------|-------------|
| `DOMAIN`            | Overrides the domain where the other services can be found (automatically injected by Pivotal CloudFoundry) |
| `PORT`              | Overrides the default listening port (automatically injected by Pivotal CloudFoundry) |
| `VCAP_SERVICES`     | A JSON object that adheres to the [PCF `VCAP_SERVICES` interface](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES) (automatically injected by A Pivotal CloudFoundry) |
| `PZ_GATEWAY`        | Overrides the Piazza gateway autodetection/configuration |
| `CATALOG`           | Overrides the Image Catalog base URL |
| `TIDE_SERVICE`      | Overrides the Tide Prediction service base URL |
| `SYSTEM_AUTH_TOKEN` | Credentials for accessing Piazza.  **This has to be provided to the deployed instance via PCF web management portal or CF CLI.** |
| `DEBUG_MODE`        | Set to `1` to start the server in debug mode.  Note that this will have some fairly noisy logs. |
| `SKIP_PRODUCTLINE_INSTALL` | Set to `1` to skip installing triggers and services for catalog harvest events (recommended for local development). |
