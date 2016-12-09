#!/bin/bash -e

if [ -z $PCF_DOMAIN ]; then
    echo "Cannot read PCF_DOMAIN from the environment"
    exit 1
fi
if [ -z $PCF_SPACE ]; then
    echo "Cannot read PCF_SPACE from the environment"
    exit 1
fi
if [ -z $BEACHFRONT_PIAZZA_AUTH ]; then
    echo "Cannot read BEACHFRONT_PIAZZA_AUTH from the environment"
    exit 1
fi

echo ###########################################################################

pcf_domain=$(echo $PCF_DOMAIN|sed -E 's/^int\./stage./')
piazza_url=https://piazza.$pcf_domain/key
echo "Requesting new Piazza API key via $piazza_url"
response=$(curl -s $piazza_url -u "$BEACHFRONT_PIAZZA_AUTH")
echo
echo "Response:"
echo $response|sed 's/^/    | /'

echo ###########################################################################

api_key=$(echo $response|grep -oE '\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')
if [ -z $api_key ]; then
    echo "No Piazza API key found"
    exit 1
fi
manifest_filename=manifest.$PCF_SPACE.yml
echo "Writing Cloud Foundry manifest to $manifest_filename:"
sed "s/__SYSTEM_API_KEY__/$api_key/" manifest.jenkins.yml > $manifest_filename
cat $manifest_filename|sed 's/^/    | /'

echo ###########################################################################
echo
