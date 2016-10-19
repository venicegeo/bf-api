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

```
$ virtualenv --python python3.5 .env
$ . .env/bin/activate
$ ./scripts/run-in-development-mode.sh
```

### Environment Variables

| Variable       | Description |
|----------------|-------------|
| `DOMAIN`       | Overrides the domain where the other services can be found (automatically injected by Pivotal CloudFoundry) |
| `PORT`         | Overrides the default listening port (automatically injected by Pivotal CloudFoundry) |
| `PZ_GATEWAY`   | Overrides the Piazza gateway autodetection/configuration |
| `CATALOG`      | Overrides the Image Catalog base URL |
| `TIDE_SERVICE` | Overrides the Tide Prediction service base URL |
| `DEBUG_MODE`   | Set to `1` to start the server in debug mode.  Note that this will have some fairly noisy logs. |
