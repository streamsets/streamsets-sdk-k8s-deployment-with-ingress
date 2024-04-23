#!/usr/bin/env bash

# Check the number of arguments
if [ "$#" -ne 3 ]; then
    echo "Wrong number of arguments"
    echo "Usage: ./create-k8s-deployment.sh  <deployment_properties_file> <environment_name> <deployment_suffix>"
    echo "Example ./create-k8s-deployment.sh config/eks-deployment.properties env-1 sdc1"
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

