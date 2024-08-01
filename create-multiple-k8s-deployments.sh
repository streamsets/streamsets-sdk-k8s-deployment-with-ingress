#!/usr/bin/env bash
# IBM Confidential
# PID 5900-BAF
# Copyright StreamSets Inc., an IBM Company 2024

# Check the number of arguments
if [ "$#" -ne 3 ]; then
    echo "Wrong number of arguments"
    echo "Usage: ./create-k8s-deployment.sh <deployment_properties_file>  <environment-name> <deployment-suffix-1>[,<deployment-suffix-2>[,<deployment-suffix-2>[...]],"
    echo "Example ./create-k8s-deployment.sh env-1 sdc1,sdc2,sdc3"
    exit 1
fi

# Set Control Hub credentials
source private/sdk-env.sh

DEPLOYMENT_PROPERTIES_FILE=${1}
ENVIRONMENT_NAME=${2}
DEPLOYMENT_SUFFIXES=${3}

echo "---------"
echo "Creating StreamSets Deployments"
echo "Deployment Properties File: " ${DEPLOYMENT_PROPERTIES_FILE}
echo "Environment Name: " ${ENVIRONMENT_NAME}
echo "Deployment Suffixes: " ${DEPLOYMENT_SUFFIXES}
echo "---------"
echo ""

INDEX=0
for SUFFIX in ${DEPLOYMENT_SUFFIXES//,/ }
do
  echo "---------"
  echo "Creating StreamSets Deployment"
  echo "Environment Name" ${ENVIRONMENT_NAME}
  echo "SDC Suffix:" "${SUFFIX}"
  echo "---------"
  DEPLOYMENT_SUFFIX=${SUFFIX}
  DEPLOYMENT_INDEX=${INDEX}

  # Launch the SDK script
  python3 python/create-k8s-deployment.py ${DEPLOYMENT_PROPERTIES_FILE} ${ENVIRONMENT_NAME} ${SUFFIX} ${DEPLOYMENT_INDEX}

  # Bump the deployment index
  INDEX=$((INDEX+1))
done






