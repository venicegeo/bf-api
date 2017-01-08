#!/bin/bash -e

VIRTUALENV_ROOT=.env
DEV_ROOT=.dev
[ "$1" == "--force" ] && FORCE=1

create_dev_root() {
    if [ -d $DEV_ROOT ]; then
        if [ $FORCE ]; then
            rm -rf $DEV_ROOT
        else
            echo "create_dev_root: '$DEV_ROOT' already exists.  To recreate, try running '$0 --force'."
            exit 1
        fi
    fi
    echo "Creating $DEV_ROOT"
    mkdir -p $DEV_ROOT
    if ! grep -E "\\b$DEV_ROOT\\b" .gitignore >/dev/null; then
        echo "Adding $DEV_ROOT to .gitignore"
        echo -e "\n$DEV_ROOT" >> .gitignore
    fi
}

create_environment_vars() {
    local _filepath=$DEV_ROOT/environment-vars.sh
    echo "Creating ${_filepath}"
    sed <<'EOT' | sed -E 's/^        //' > $_filepath
        export GEOAXIS=
        export GEOAXIS_CLIENT_ID=
        export GEOAXIS_SECRET=
        export DOMAIN=
        export PIAZZA_API_KEY=
        export REQUESTS_CA_BUNDLE="$(dirname $BASH_SOURCE)/ssl-certificate.pem"
        export PORT=5000
        export VCAP_SERVICES='{
          "user-provided": [
            {
              "name": "pz-postgres",
              "credentials": {
                "hostname": "localhost",
                "username": "beachfront",
                "password": "secret",
                "database": "beachfront",
                "port": "5432",
                "host": "localhost:5432"
              }
            },
            {
              "name": "pz-geoserver-efs",
              "credentials": {
                "host": "localhost:8443",
                "username": "beachfront",
                "password": "secret",
                "port": "8443"
              }
            }
          ]
        }'
EOT
}

create_ssl_certs() {
    local _filepath_pem=$DEV_ROOT/ssl-certificate.pem
    local _filepath_key=$DEV_ROOT/ssl-certificate.key
    local _filepath_keystore=$DEV_ROOT/ssl-certificate.pkcs12
    echo "Creating ${_filepath_pem}"
    echo "Creating ${_filepath_key}"
    openssl req \
      -newkey rsa:2048 -nodes -keyout $_filepath_key \
      -x509 -days 99999 -out $_filepath_pem \
      -subj "/C=US/ST=Unknown/L=Unknown/O=Beachfront/OU=Development/CN=localhost" \
      -passin pass:secret \
      -passout pass:secret \
      2>&1 |indent_stream
    echo "Creating ${_filepath_keystore}"
    openssl pkcs12 \
      -inkey $_filepath_key -in $_filepath_pem \
      -export -out $_filepath_keystore \
      -passin pass:secret \
      -passout pass:secret \
      2>&1 |indent_stream
}

create_virtualenv() {
    if [ -d $VIRTUALENV_ROOT ]; then
        if [ $FORCE ]; then
            rm -rf $VIRTUALENV_ROOT
        else
            echo "create_virtualenv: '$VIRTUALENV_ROOT' already exists.  To recreate, try running '$0 --force'."
            exit 1
        fi
    fi
    if ! which python3.5 >/dev/null; then
        echo "create_virtualenv: Cannot proceed; Python 3.5 is missing"
        exit 1
    fi
    echo "Creating $VIRTUALENV_ROOT (virtual environment)"
    virtualenv --python=python3.5 $VIRTUALENV_ROOT |indent_stream
    . $VIRTUALENV_ROOT/bin/activate
    pip install -r requirements.txt |indent_stream
    deactivate
}

indent_stream() {
    sed 's/^/     | /'
}

#
# Main
#

cd $(dirname $(dirname $0))  # Return to root

create_virtualenv
create_dev_root
create_ssl_certs
create_environment_vars
