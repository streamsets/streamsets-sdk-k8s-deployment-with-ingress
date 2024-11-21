#!/usr/bin/env bash
# IBM Confidential
# PID 5900-BAF
# Copyright StreamSets Inc., an IBM Company 2024

# Check the number of arguments
if [ "$#" -ne 3 ]; then
    echo "Wrong number of arguments"
    echo "Usage: ./create-k8s-deployment.sh  <deployment_properties_file> <environment_name> <deployment_suffix>"
    echo "Example ./create-k8s-deployment.sh config/eks-deployment.properties env-1 sdc1"
    exit 1
fi

# Make sure there is only one deployment suffix in the list
if [[ ${3} == *,* ]]; then
  echo "Error: Deployment Suffix contains a comma."
  echo "Use the 'create-multiple-k8s-deployments.sh' script if you intend to create multiple deployments.'"
  exit 1
fi

# Set Control Hub credentials
source private/sdk-env.sh

echo "---------"
echo "Creating StreamSets Deployment"
echo "Deployment Properties File: " ${1}
echo "Environment Name: " ${2}
echo "Deployment Suffix: " ${3}
echo "---------"
echo ""

# Launch the SDK script
python3 python/create-k8s-deployment.py ${1} ${2} ${3}

