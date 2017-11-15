#!/bin/bash -e

VIRTUALENV_ROOT=.env
DEV_ROOT=.dev
[ "$1" == "--force" ] && FORCE=1

create_dev_root() {
    if [ -d $DEV_ROOT ]; then
        if [ $FORCE ]; then
            rm -rf $DEV_ROOT
        else
            echo -e "\n$FUNCNAME: '$DEV_ROOT' already exists.  To recreate, try running '$0 --force'."
            exit 1
        fi
    fi
    echo -e "\n$FUNCNAME: Creating $DEV_ROOT"
    mkdir -p $DEV_ROOT
    if ! grep -E "\\b$DEV_ROOT\\b" .gitignore >/dev/null; then
        echo "Adding $DEV_ROOT to .gitignore"
        echo -e "\n$DEV_ROOT" >> .gitignore
    fi
}

create_environment_vars() {
    local filepath=$DEV_ROOT/environment-vars.sh
    echo -e "\n$FUNCNAME: Creating $filepath"
    cat <<'EOT' | sed -E 's/^        //' > $filepath
        export GEOAXIS=
        export GEOAXIS_AUTH=
        export GEOAXIS_CLIENT_ID=
        export GEOAXIS_SECRET=
        export DOMAIN=
        export SECRET_KEY=
        export PIAZZA_API_KEY=
        export REQUESTS_CA_BUNDLE="$(dirname $BASH_SOURCE)/ssl-certificate.pem"
        export PORT=5000
        export VCAP_SERVICES='{
          "user-provided": [
            {
              "name": "pz-postgres",
              "credentials": {
                "db_host": "localhost",
                "username": "beachfront",
                "password": "secret",
                "db_name": "beachfront",
                "db_port": "5432"
              }
            },
            {
              "name": "pz-geoserver",
              "credentials": {
                "boundless_geoserver_url": "http://localhost:8080/geoserver/index.html",
                "boundless_geoserver_username": "admin",
                "boundless_geoserver_password": "geoserver"
              }
            }
          ]
        }'
EOT
}

create_ssl_certs() {
    local key_filepath=$DEV_ROOT/ssl-certificate.key
    local cert_filepath=$DEV_ROOT/ssl-certificate.pem
    local keystore=$DEV_ROOT/ssl-certificate.pkcs12

    echo -e "\n$FUNCNAME: Creating $key_filepath"
    openssl genrsa -out $key_filepath 2048 \
        2>&1 |indent_stream

    echo -e "\n$FUNCNAME: Creating $cert_filepath"
    openssl req \
        -x509 \
        -new \
        -key $key_filepath \
        -out $cert_filepath \
        -days 3652 \
        -config <(echo '
            [req]
                default_md             = sha256
                prompt                 = no
                distinguished_name     = req_distinguished_name

            [req_distinguished_name]
                countryName            = "US"
                stateOrProvinceName    = "VA"
                localityName           = "Unknown"
                organizationName       = "Beachfront"
                organizationalUnitName = "Development"
                commonName             = "Beachfront Development Server (localhost)"

            [Beachfront]
                basicConstraints       = CA:false
                subjectAltName         = DNS:localhost, DNS:localhost.localdomain, DNS:vagranthost
        ') \
        -extensions Beachfront \
        2>&1 |indent_stream

    echo -e "\n$FUNCNAME: Creating $keystore"
    openssl pkcs12 \
        -export \
        -nodes \
        -inkey $key_filepath \
        -in $cert_filepath \
        -out $keystore \
        -passout pass:secret \
        2>&1 |indent_stream
}

create_virtualenv() {
    if [ -d $VIRTUALENV_ROOT ]; then
        if [ $FORCE ]; then
            rm -rf $VIRTUALENV_ROOT
        else
            echo -e "\n$FUNCNAME: '$VIRTUALENV_ROOT' already exists.  To recreate, try running '$0 --force'."
            exit 1
        fi
    fi
    if ! (which python3.5 && python3.5 -c 'import sys; assert sys.version_info >= (3, 5, 0)') >/dev/null 2>&1; then
        echo -e "\n$FUNCNAME: Python 3.5.0 or higher must be installed first"
        exit 1
    fi
    echo -e "\n$FUNCNAME: Creating $VIRTUALENV_ROOT (virtual environment)"
    virtualenv --python=python3.5 $VIRTUALENV_ROOT --always-copy |indent_stream
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
