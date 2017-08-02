#!/bin/bash -e

if [ -z "$PIAZZA_URL" ]; then
    echo "Cannot read PIAZZA_URL from the environment"
    exit 1
fi
if [ -z "$MANIFEST_FILENAME" ]; then
    echo "Cannot read MANIFEST_FILENAME from the environment"
    exit 1
fi
if [ -z "$BEACHFRONT_PIAZZA_AUTH" ]; then
    echo "Cannot read BEACHFRONT_PIAZZA_AUTH from the environment"
    exit 1
fi
if [ -z "$BEACHFRONT_GEOAXIS_CLIENT_ID" ]; then
    echo "Cannot read BEACHFRONT_GEOAXIS_CLIENT_ID from the environment"
    exit 1
fi
if [ -z "$GEOAXIS_DOMAIN" ]; then
    echo "Cannot read GEOAXIS_DOMAIN from the environment"
    exit 1
fi
if [ -z "$BEACHFRONT_GEOAXIS_SECRET" ]; then
    echo "Cannot read BEACHFRONT_GEOAXIS_SECRET from the environment"
    exit 1
fi

echo ###########################################################################

echo "Requesting new Piazza API key via $PIAZZA_URL"
response=$(curl -s $PIAZZA_URL -u "$BEACHFRONT_PIAZZA_AUTH")
echo
echo "Response:"
echo $response|sed 's/^/    | /'

piazza_api_key=$(echo $response|grep -oE '\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')
if [ -z $piazza_api_key ]; then
    echo "No Piazza API key found"
    exit 1
fi

manifest_filename=$MANIFEST_FILENAME
echo "Writing Cloud Foundry manifest to $manifest_filename:"
cat manifest.jenkins.yml |\
    sed "s/__PIAZZA_API_KEY__/$piazza_api_key/" |\
    sed "s/__GEOAXIS__/$GEOAXIS_DOMAIN/" |\
    sed "s/__GEOAXIS_CLIENT_ID__/$BEACHFRONT_GEOAXIS_CLIENT_ID/" |\
    sed "s/__GEOAXIS_SECRET__/$BEACHFRONT_GEOAXIS_SECRET/" |\
    tee $manifest_filename |\
    sed 's/^/    | /'
echo

echo ###########################################################################
