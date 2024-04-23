#!/usr/bin/env python

"""
This script creates and optionally starts a Kubernetes Deployment on StreamSets Platform

Prerequisites:
 - Python 3.6+

 - StreamSets DataOps Platform SDK for Python v6.1+
   See: https://docs.streamsets.com/platform-sdk/latest/learn/installation.html

 - StreamSets Platform API Credentials for a user with Organization Administrator role

 - An active StreamSets Kubernetes Environment with an online Kubernetes Agent
"""

import datetime
import os
import sys

from streamsets.sdk import ControlHub

from config_manager import ConfigManager

# Check the number of command line args
if len(sys.argv) not in (4, 5):
    print('Error:Wrong number of arguments')
    print('Usage: $ python3 create-k8s-deployment.py <deployment_properties_file> <environment_name> <deployment_suffix> [<deployment_index>]')
    print('Usage Example: $ python3 create-k8s-deployment.py config/eks-deployment.properties env-1 sdc1')
    sys.exit(1)

# Get the command line args
deployment_properties_file = sys.argv[1]
environment_name = sys.argv[2]
deployment_suffix = sys.argv[3]

# If this script is called multiple times in a single run, we'll keep track using the deployment index
if len(sys.argv) == 5:
    deployment_index = int(sys.argv[4])
else:
    deployment_index = 0


def print_message(message):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + message)

def replace_in_yaml(yaml, key, value):
    print_message('- Setting \'%s\' to \'%s\'' % (key, value))
    return yaml.replace(key, value)

# Load properties from the deployment.properties file
config = ConfigManager(deployment_properties_file, deployment_index)

# Get Control Hub API credentials from the environment
cred_id = os.getenv('CRED_ID')
cred_token = os.getenv('CRED_TOKEN')

# Connect to Control Hub
print_message('Connecting to Control Hub')
sch = ControlHub(credential_id=cred_id, token=cred_token)

# Get the environment
print_message('Getting the environment')
environment = sch.environments.get(environment_name=environment_name)

# Get the environment's namespace
namespace = environment.kubernetes_namespace
print_message('Using namespace \'%s\'' % namespace)

# Create a deployment builder
deployment_builder = sch.get_deployment_builder(deployment_type='KUBERNETES')

# Create the name for the deployment
deployment_name = environment_name + '-' + deployment_suffix

# Create the deployment
print_message('Creating deployment \'%s\'' % deployment_name)
print_message('SDC Version: ' + config.get('SDC_VERSION'))
print_message('Deployment Tags: ' + str(config.get_deployment_tags()))
deployment = deployment_builder.build(deployment_name=deployment_name,
                                      environment=environment,
                                      engine_type='DC',
                                      engine_version=config.get('SDC_VERSION'),
                                      deployment_tags=config.get_deployment_tags())

# Add the deployment to Control Hub
sch.add_deployment(deployment)

# These stage libs always need to be included
deployment.engine_configuration.stage_libs = ['dataformats', 'dev', 'basic']

# Add user stage libs to the Deployment
user_stage_libs = config.get_user_stage_libs()
print_message('Adding Stage Libs: ' + str(user_stage_libs))
deployment.engine_configuration.stage_libs.extend(user_stage_libs)

# Engine config
engine_config = deployment.engine_configuration
engine_config.engine_labels.extend(config.get_engine_labels())
engine_config.max_cpu_load = config.get('SDC_MAX_CPU_LOAD')
engine_config.max_memory_used = config.get('SDC_MAX_MEMORY_USED')
engine_config.max_pipelines_running = config.get('SDC_MAX_PIPELINES_RUNNING')

# Engine Java config
java_config = engine_config.java_configuration
java_config.java_memory_strategy = 'ABSOLUTE'
java_config.minimum_java_heap_size_in_mb = config.get('SDC_JAVA_MIN_HEAP_MB')
java_config.maximum_java_heap_size_in_mb = config.get('SDC_JAVA_MAX_HEAP_MB')
java_config.java_options = config.get('SDC_JAVA_OPTS')

# Advanced Engine config
advanced_engine_config = engine_config.advanced_configuration

# sdc.properties
print_message('---')
print_message('Setting values in sdc.properties:')
with open('etc/sdc.properties') as f:
    sdc_properties = f.read()

# Create and set the SDC URL
sdc_url = 'https://' + config.get('LOAD_BALANCER_HOSTNAME') + '/' + deployment_suffix + '/'
print_message('- Setting URL to ' + sdc_url)
sdc_properties = sdc_properties.replace('${SDC_BASE_HTTP_URL}', sdc_url)

# Set SDC's http port
print_message('- Setting http.port to ' + config.get('HTTP_PORT'))
sdc_properties = sdc_properties.replace('${HTTP_PORT}', config.get('HTTP_PORT'))

# Set SDC's https port
print_message('- Setting https.port to ' + config.get('HTTPS_PORT'))
sdc_properties = sdc_properties.replace('${HTTPS_PORT}', config.get('HTTPS_PORT'))

# If using https, set the keystore
if config.get('BACKEND_PROTOCOL') == 'https':
    print_message('- Setting keystore to \'%s\'' % (config.get('SDC_KEYSTORE')))
    sdc_properties = sdc_properties.replace('${KEYSTORE}', config.get('SDC_KEYSTORE'))
print_message('---')
advanced_engine_config.data_collector_configuration = sdc_properties

# credential-stores.properties
print_message('Loading credential-stores.properties') 
with open('etc/credential-stores.properties') as f:
    credential_stores = f.read()
advanced_engine_config.credential_stores = credential_stores

# security_policy
print_message('Loading security.policy') 
with open('etc/security.policy') as f:
    security_policy = f.read()
advanced_engine_config.security_policy = security_policy

# log4j2
print_message('Loading sdc-log4j2.properties') 
with open('etc/sdc-log4j2.properties') as f:
    log4j2 = f.read()
advanced_engine_config.log4j2 = log4j2

# proxy.properties
print_message('Loading proxy.properties') 
with open('etc/proxy.properties') as f:
    proxy_properties = f.read()
advanced_engine_config.proxy_properties = proxy_properties

# Update the deployment
sch.update_deployment(deployment)

# Set advanced mode to True to support custom YAML
deployment._data["advancedMode"] = True

# Load the SDC Deployment manifest from the file
print_message('---')
print_message('Setting values in yaml template \'%s\':' % config.get('SDC_DEPLOYMENT_MANIFEST'))
with open(config.get('SDC_DEPLOYMENT_MANIFEST')) as f:
    yaml = f.read()
# Get the first part of the deployment ID
short_deployment_id = deployment.deployment_id[0:deployment.deployment_id.index(':')]

# Replace the tokens in the YAML template
yaml = replace_in_yaml(yaml, '${DEP_ID}', short_deployment_id)
yaml = replace_in_yaml(yaml, '${NAMESPACE}', namespace)
yaml = replace_in_yaml(yaml, '${SDC_VERSION}', config.get('SDC_VERSION'))
yaml = replace_in_yaml(yaml, '${ORG_ID}', config.get('ORG_ID'))
yaml = replace_in_yaml(yaml, '${SCH_URL}', config.get('SCH_URL'))
yaml = replace_in_yaml(yaml, '${REQUESTS_MEMORY}', config.get('REQUESTS_MEMORY'))
yaml = replace_in_yaml(yaml, '${LIMITS_MEMORY}', config.get('LIMITS_MEMORY'))
yaml = replace_in_yaml(yaml, '${REQUESTS_CPU}', config.get('REQUESTS_CPU'))
yaml = replace_in_yaml(yaml, '${LIMITS_CPU}', config.get('LIMITS_CPU'))
yaml = replace_in_yaml(yaml, '${DEPLOYMENT_SUFFIX}', deployment_suffix)
yaml = replace_in_yaml(yaml, '${SERVICE_TYPE}', config.get('SERVICE_TYPE'))
yaml = replace_in_yaml(yaml, '${SERVICE_PORT}', config.get('SERVICE_PORT'))
yaml = replace_in_yaml(yaml, '${LOAD_BALANCER_HOSTNAME}', config.get('LOAD_BALANCER_HOSTNAME'))
yaml = replace_in_yaml(yaml, '${BACKEND_PROTOCOL}', config.get('BACKEND_PROTOCOL').upper())
yaml = replace_in_yaml(yaml, '${KEYSTORE}', config.get('SDC_KEYSTORE'))
print_message('---')

# Assign the yaml to the deployment
deployment.yaml = yaml

# Update the deployment
sch.update_deployment(deployment)

# (Optional) Autostart the deployment
#print_message('Starting the deployment...')
#sch.start_deployment(deployment)

print_message('Done')
