#!/usr/bin/env python

"""
This script manages the config properties used by the main script
"""
from configparser import ConfigParser
import os


class ConfigManager:

    def __init__(self, deployment_properties_file, deployment_index):
        self.deployment_properties_file = deployment_properties_file
        self.deployment_index = deployment_index
        self.deployment_properties = self.load_deployment_properties()
        self.validate_deployment_properties()
        self.set_sdc_ports()
        self.set_keystore()

    def load_deployment_properties(self):
        # load the properties from the deployment_properties_file
        if os.path.isfile(self.deployment_properties_file):
            config = ConfigParser()
            config.read(self.deployment_properties_file)
            return config['deployment']
        else:
            raise Exception('Deployment Properties file \'{}\' not found'.format(self.deployment_properties_file))

    # Raise an exception if a deployment property value does not exist for a given key
    def assert_property_is_not_null(self, key):
        value = self.deployment_properties[key].strip()
        if value is None or len(value) == 0:
            raise Exception('No value for deployment property key \'' + key + '\'')

    def validate_deployment_properties(self):
        self.check_required_properties()
        self.check_service_type_and_port()

    def check_required_properties(self):
        self.assert_property_is_not_null('SCH_URL')
        self.assert_property_is_not_null('ORG_ID')
        self.assert_property_is_not_null('LOAD_BALANCER_HOSTNAME')
        self.assert_property_is_not_null('BACKEND_PROTOCOL')
        self.assert_property_is_not_null('SERVICE_TYPE')
        self.assert_property_is_not_null('SDC_DEPLOYMENT_MANIFEST')
        self.assert_property_is_not_null('SDC_VERSION')
        self.assert_property_is_not_null('ENGINE_LABELS')
        self.assert_property_is_not_null('SDC_MAX_CPU_LOAD')
        self.assert_property_is_not_null('SDC_MAX_MEMORY_USED')
        self.assert_property_is_not_null('SDC_MAX_PIPELINES_RUNNING')
        self.assert_property_is_not_null('SDC_JAVA_MIN_HEAP_MB')
        self.assert_property_is_not_null('SDC_JAVA_MAX_HEAP_MB')
        self.assert_property_is_not_null('REQUESTS_MEMORY')
        self.assert_property_is_not_null('LIMITS_MEMORY')
        self.assert_property_is_not_null('REQUESTS_CPU')
        self.assert_property_is_not_null('LIMITS_CPU')

    def check_service_type_and_port(self):
        service_type = self.deployment_properties['SERVICE_TYPE']
        if service_type == 'ClusterIP':
            self.deployment_properties['SERVICE_PORT'] = "18630"
        elif service_type == 'NodePort':
            self.assert_property_is_not_null('STARTING_NODE_PORT_SERVICE_PORT')
            starting_port = self.deployment_properties['STARTING_NODE_PORT_SERVICE_PORT']
            self.check_service_port(starting_port)
        else:
            raise Exception(
                'SERVICE_TYPE should be either \'NodePort\' or \'ClusterIP\' but is \'' + service_type + '\'')

    def check_service_port(self, starting_port):
        if starting_port.isdigit():
            if int(starting_port) < 30000 or int(starting_port) > 32767:
                error_message = ('The \'STARTING_NODE_PORT_SERVICE_PORT\' property of {}' +
                                 ' is not within the range 30000 to 32767. ' +
                                 ' Please adjust your STARTING_NODE_PORT_SERVICE_PORT property').format(starting_port)
                raise Exception(error_message)
            else:
                service_port = int(starting_port) + self.deployment_index
                if 30000 <= service_port <= 32767:
                    self.deployment_properties['SERVICE_PORT'] = str(service_port)
                else:
                    error_message = ('The computed NodePort Service port \'{}\' (based on the value of the ' +
                                     '\'STARTING_NODE_PORT_SERVICE_PORT\' property of {} plus the deployment index of {})' +
                                     ' is not within the range 30000 to 32767. ' +
                                     ' Please adjust your STARTING_NODE_PORT_SERVICE_PORT property').format(
                        service_port, starting_port, self.deployment_index)
                    raise Exception(error_message)
        else:
            raise Exception(
                'STARTING_NODE_PORT_SERVICE_PORT \'{}\' should be a number between 30000 and 32767'.format(
                    starting_port))

    def set_sdc_ports(self):
        backend_protocol = self.deployment_properties['BACKEND_PROTOCOL'].lower()
        if backend_protocol == 'http':
            self.deployment_properties['HTTP_PORT'] = "18630"
            self.deployment_properties['HTTPS_PORT'] = "-1"
        elif backend_protocol == 'https':
            self.deployment_properties['HTTP_PORT'] = "-1"
            self.deployment_properties['HTTPS_PORT'] = "18630"
        else:
            raise Exception(
                'BACKEND_PROTOCOL should be either \'http\' or \'https\' but was \'' + backend_protocol + '\'')

    def set_keystore(self):
        # Set the keystore if the backend protocol is https
        if self.deployment_properties['BACKEND_PROTOCOL'].lower() == 'https':
            try:
                self.assert_property_is_not_null('SDC_KEYSTORE')
            except Exception:
                error_message = ('BACKEND_PROTOCOL is \'https\' but no value provided for the ' +
                                 '\'SDC_KEYSTORE\' property. Either set the name of your own keystore, ' +
                                 ' or set the value of \'streamsets.jks\' to use StreamSets\' self-signed-cert.')
                raise Exception(error_message)
        else:
            self.deployment_properties['SDC_KEYSTORE'] = 'keystore.jks'  # We'll set this to the default SDC keystore even though we won't use it

    def get_property_array_value(self, key):
        if key in self.deployment_properties.keys():
            value = self.deployment_properties[key].strip()
            if len(value) > 0:
                return value.split(',')
            else:
                return []
        else:
            return []

    def get_deployment_tags(self):
        return self.get_property_array_value('DEPLOYMENT_TAGS')

    def get_user_stage_libs(self):
        return self.get_property_array_value('USER_STAGE_LIBS')

    def get_engine_labels(self):
        return self.get_property_array_value('ENGINE_LABELS')

    def get(self, key):
        return self.deployment_properties[key]
