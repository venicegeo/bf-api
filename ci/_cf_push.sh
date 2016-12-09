#!/bin/bash -e

if [ -z $PIAZZA_URL ]; then
    echo "Cannot read PIAZZA_URL from the environment"
    exit 1
fi
if [ -z $MANIFEST_FILENAME ]; then
    echo "Cannot read MANIFEST_FILENAME from the environment"
    exit 1
fi
if [ -z $BEACHFRONT_PIAZZA_AUTH ]; then
    echo "Cannot read BEACHFRONT_PIAZZA_AUTH from the environment"
    exit 1
fi

echo ###########################################################################

echo "Requesting new Piazza API key via $PIAZZA_URL"
response=$(curl -s $PIAZZA_URL -u "$BEACHFRONT_PIAZZA_AUTH")
echo
echo "Response:"
echo $response|sed 's/^/    | /'

api_key=$(echo $response|grep -oE '\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')
if [ -z $api_key ]; then
    echo "No Piazza API key found"
    exit 1
fi
manifest_filename=$MANIFEST_FILENAME
echo "Writing Cloud Foundry manifest to $manifest_filename:"
sed "s/__SYSTEM_API_KEY__/$api_key/" manifest.jenkins.yml > $manifest_filename
cat $manifest_filename|sed 's/^/    | /'
echo

echo ###########################################################################
