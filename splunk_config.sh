#!/bin/bash

# This script would be run inside the Splunk container or against its API
# to configure SmartStore / Federated Search with AWS S3.

SPLUNK_HOME="/opt/splunk"
S3_BUCKET_NAME="splunk-machine-data-lake-digital-twin"
S3_REGION="us-east-1"

echo "Configuring Splunk Machine Data Lake (AWS S3)..."

# Example of configuring indexes.conf for SmartStore
# In a real scenario, you would use 'splunk edit' or REST API
# cat <<EOF >> $SPLUNK_HOME/etc/system/local/indexes.conf
# [default]
# remotePath = volume:remote_store/$_index_name
# repFactor = auto
#
# [volume:remote_store]
# storageType = remote
# path = s3://$S3_BUCKET_NAME/splunk_data
# remote.s3.endpoint = s3.$S3_REGION.amazonaws.com
# EOF

echo "S3 volume placeholder configured for bucket: $S3_BUCKET_NAME"
echo "Note: AWS Access Keys should be provided via environment variables or IAM roles."

# Enable HEC
echo "Enabling HTTP Event Collector (HEC)..."
# /opt/splunk/bin/splunk http-event-collector enable -uri https://localhost:8089
