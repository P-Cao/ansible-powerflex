# !/usr/bin/python

# Copyright: (c) 2024, Dell Technologies
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dellemc.powerflex.plugins.module_utils.storage.dell\
    import utils

LOG = utils.get_logger('nvme')

DOCUMENTATION = r'''
module: nvme_host
version_added: '1.0.0'
short_description: Manage NVMe hosts on Dell PowerFlex
description:
- Managing NVMe hosts on PowerFlex storage system includes getting details of NVMe hosts
  and renaming NVMe hosts.

author:
- Peter Cao (@P-Cao) <ansible.team@dell.com>

extends_documentation_fragment:
  - dellemc.powerflex.powerflex

options:
  nvme_host_name:
    description:
    - Name of the NVMe host.
    - Specify either I(nvme_host_name), I(nvme_host_id), I(nqn) for create/get/rename operation.
    type: str
  nvme_host_id:
    description:
    - ID of the NVMe host.
    - Specify I(nvme_host_id) for get/rename operation.
    type: str
  nvme_host_new_name:
    description:
    - New name of the NVMe host. Used to rename the NVMe host.
    type: str
  nqn:
    description:
    - NQN of the NVMe host. Used to create/get/modify the NVMe host.
  max_num_paths:
    description:
    - Maximum number of paths per volume. Used to create/modify the NVMe host.
    type: str
  max_num_sys_ports:
    description:
    - Maximum number of ports per protection domain. Used to create/modify the NVMe host.
    type: str
  state:
    description:
    - State of the NVMe host.
    choices: ['present', 'absent']
    required: true
    type: str
notes:
  - The I(check_mode) is not supported.
'''

EXAMPLES = r'''
- name: Get NVMe host details using NVMe host id
  dellemc.powerflex.nvme_host:
    hostname: "{{hostname}}"
    username: "{{username}}"
    password: "{{password}}"
    validate_certs: "{{validate_certs}}"
    nvme_host_id: "{{nvme_host_id}}"
    state: "present"

- name: Create NVMe host
  dellemc.powerflex.nvme_host:
    hostname: "{{hostname}}"
    username: "{{username}}"
    password: "{{password}}"
    validate_certs: "{{validate_certs}}"
    nqn: "{{nqn}}"
    nvme_host_name: "example_nvme_host"
    max_num_paths: "{{max_num_paths}}"
    max_num_sys_ports: "{{max_num_sys_ports}}"
    state: "present"

- name: Rename NVMe host
  dellemc.powerflex.nvme_host:
    hostname: "{{hostname}}"
    username: "{{username}}"
    password: "{{password}}"
    validate_certs: "{{validate_certs}}"
    nvme_host_name: "example_nvme_host"
    nvme_host_new_name: "new_example_nvme_host"
    state: "present"

- name: Remove SDC using SDC name
  dellemc.powerflex.sdc:
    hostname: "{{hostname}}"
    username: "{{username}}"
    password: "{{password}}"
    validate_certs: "{{validate_certs}}"
    nvme_host_id: "{{nvme_host_id}}"
    state: "absent"
'''

class PowerFlexNvmeHost(object):
    """Class with NVMe host operations"""

    def __init__(self):
        """ Define all parameters required by this module"""
        self.module_params = utils.get_powerflex_gateway_host_parameters()
        self.module_params.update(get_powerflex_nvme_host_parameters())

        required_one_of = [['nvme_host_name', 'nvme_host_id', 'nqn']]
        mutually_exclusive = [['nvme_host_name', 'nvme_host_id']]

        # initialize the Ansible module
        self.module = AnsibleModule(
            argument_spec=self.module_params,
            supports_check_mode=False,
            mutually_exclusive=mutually_exclusive,
            required_one_of=required_one_of)

        utils.ensure_required_libs(self.module)

        try:
            self.powerflex_conn = utils.get_powerflex_gateway_host_connection(
                self.module.params)
            LOG.info("Got the PowerFlex system connection object instance")
        except Exception as e:
            LOG.error(str(e))
            self.module.fail_json(msg=str(e))


    def perform_module_operation(self):
        """
        Perform different actions on NVMe host based on parameters passed in the playbook
        """
        nvme_host_id = self.module.params['nvme_host_id']
        nvme_host_name = self.module.params['nvme_host_name']
        nvme_host_new_name = self.module.params['nvme_host_new_name']
        max_num_paths = self.module.params['max_num_paths']
        max_num_sys_ports = self.module.params['max_num_sys_ports']
        nqn = self.module.params['nqn']
        state = self.module.params['state']

        changed = False
        result = dict(
            changed=False,
            nvme_host_details={}
        )

        self.validate_parameters()

        # try to get NVMe host detail
        # nvme host can be queried using name or id
        nvme_host_details = self.get_nvme_host(nvme_host_id=nvme_host_id, nvme_host_name=nvme_host_name, nqn=nqn)
        if nvme_host_details:
            msg = "Fetched the NVMe host details %s" % str(nvme_host_details)
            LOG.info(msg)
        if state == 'absent' and nvme_host_details:
            changed = self.remove(nvme_host_details['id'])

        if state == 'present' and nvme_host_details:
            changed = self.perform_modify(nvme_host_details, nvme_host_new_name, 
                                          max_num_paths, max_num_sys_ports)
            
        # do create operation if no host exists
        if state == 'present' and not nvme_host_details:
            nvme_host_details, changed = self.create_host(nvme_host_name, nqn, max_num_paths, max_num_sys_ports)

        if changed:
            nvme_host_details = self.get_nvme_host(nvme_host_name = nvme_host_new_name or nvme_host_name,
                                                   nvme_host_id=nvme_host_id, nqn=nqn)
        
        result['nvme_host_details'] = nvme_host_details
        result['changed'] = changed
        self.module.exit_json(**result)

    def create_host(self, nvme_host_name, nqn, max_num_paths, max_num_sys_ports):
        """
        Create a new NVMe host based on the given parameters.
        """
        if not nqn:
            self.module.fail_json(msg="nqn parameter is required for creating an NVMe host.")

        if self.module.params['nvme_host_new_name']:
            self.module.fail_json(
                msg="nvme_host_new_name parameter is not supported during "
                    "creation of a volume. Try renaming the NVMe host after"
                    " the creation.")

        created_nvme = self.create_nvme_host(nqn=nqn, name=nvme_host_name,
                                        max_num_paths=max_num_paths,
                                        max_num_sys_ports=max_num_sys_ports)
        
        if created_nvme:
            nvme_host_details = self.get_nvme_host(nvme_host_id=created_nvme['id'])
            msg = "NVMe host created successfully, fetched " \
                "NVMe host details %s" % str(nvme_host_details)
            LOG.info(msg)
            return nvme_host_details, True
        return None, False

    def get_nvme_host(self, nvme_host_id=None, nvme_host_name=None, nqn=None):
        """Get the NVMe host Details
            :param nvme_host_name: The name of the NVMe host
            :param nvme_host_di: The ID of the NVMe host
            :return: The dict containing NVMe host details
        """
        if nvme_host_name:
            id_name = nvme_host_name
        elif nvme_host_id:
            id_name = nvme_host_id
        elif nqn:
            id_name = nqn
        try:
            if nvme_host_name:
                nvme_host_details = self.powerflex_conn.sdc.get(
                    filter_fields={'name': nvme_host_name})
            elif nvme_host_id:
                nvme_host_details = self.powerflex_conn.sdc.get(
                    filter_fields={'id': nvme_host_id})
            elif nqn:
                nvme_host_details = self.powerflex_conn.sdc.get(
                    filter_fields={'nqn': nqn})

            if len(nvme_host_details) == 0:
                if nvme_host_id:
                    error_msg = "Unable to find NVMe host with identifier %s" \
                                % id_name
                    LOG.error(error_msg)
                    self.module.fail_json(msg=error_msg)
                return None
            return nvme_host_details[0]

        except Exception as e:
            errormsg = "Failed to get the NVMe host %s with error %s" % (
                id_name, str(e))
            LOG.error(errormsg)
            self.module.fail_json(msg=errormsg)

    def create_nvme_host(self, nqn, name, max_num_paths, max_num_sys_ports):
        """Create the NVMe host
            :param nqn: The NQN of the NVMe host
            :param name: The name of the NVMe host
            :param max_num_paths: The maximum number of paths per volume
            :param max_num_sys_ports: Maximum Number of Ports Per Protection Domain
        """
        try:
            if nqn is None or len(nqn.strip()) == 0:
                self.module.fail_json(msg="Please provide valid NQN.")
            host_id = self.powerflex_conn.host.create(nqn=nqn, name=name, 
                                            max_num_paths=max_num_paths,
                                            max_num_sys_ports=max_num_sys_ports)
            return host_id

        except Exception as e:
            errormsg = "Create NVMe host operation failed with " \
                       "error %s" % str(e)
            LOG.error(errormsg)
            self.module.fail_json(msg=errormsg)

    def validate_parameters(self):
        """Validate the input parameters"""

        sdc_identifiers = ['nvme_host_id', 'nvme_host_name']
        for param in sdc_identifiers:
            if self.module.params[param] is not None and \
                    len(self.module.params[param].strip()) == 0:
                msg = f"Please provide valid {param}"
                LOG.error(msg)
                self.module.fail_json(msg=msg)
        
        if self.module.params['nvme_host_id'] is None and self.module.params['nvme_host_name'] is None \
            and self.module.params['nqn'] is None:
                msg = "Please provide at least one of nvme_host_id, nvme_host_name or nqn"
                LOG.error(msg)
                self.module.fail_json(msg=msg)

    def remove(self, nvme_id):
        """Remove the NVMe host"""
        try:
            LOG.info(msg=f"Removing NVMe host {nvme_id}")
            self.powerflex_conn.sdc.delete(nvme_id)
            return True
        except Exception as e:
            errormsg = f"Removing NVMe host {nvme_id} failed with error {str(e)}"
            LOG.error(errormsg)
            self.module.fail_json(msg=errormsg)

    def perform_modify(self, nvme_host_details, nvme_host_new_name, 
                                          max_num_paths, max_num_sys_ports):
        modified = False
        if nvme_host_new_name is not None and nvme_host_new_name != nvme_host_details['name']:
            try:
                self.powerflex_conn.sdc.rename(sdc_id=nvme_host_details['id'], name=nvme_host_new_name)
                msg = "Succeeded to rename NVMe host from %s to %s" % (nvme_host_details['name'], nvme_host_new_name)
                LOG.info(msg)
                modified = True
            except Exception as e:
                errormsg = "Failed to rename NVMe host %s with error %s" % (nvme_host_details['id'], str(e))
                LOG.error(errormsg)
                self.module.fail_json(msg=errormsg)

        if max_num_paths and max_num_paths != str(nvme_host_details['maxNumPaths']):
            try:
                self.powerflex_conn.host.modify_max_num_paths(host_id=nvme_host_details['id'], max_num_paths=max_num_paths)
                msg = "Succeeded to modify NVMe host max_num_paths from %s to %s" % (nvme_host_details['maxNumPaths'], max_num_paths)
                LOG.info(msg)
                modified = True
            except Exception as e:
                errormsg = "Failed to modify NVMe host %s max_num_paths with error %s" % (nvme_host_details['id'], str(e))
                LOG.error(errormsg)
                self.module.fail_json(msg=errormsg)
                
        if max_num_sys_ports and max_num_sys_ports != str(nvme_host_details['maxNumSysPorts']):
            try:
                self.powerflex_conn.host.modify_max_num_sys_ports(host_id=nvme_host_details['id'], max_num_sys_ports=max_num_sys_ports)
                msg = "Succeeded to modify NVMe host max_num_sys_ports from %s to %s" % (nvme_host_details['maxNumSysPorts'], max_num_sys_ports)
                LOG.info(msg)
                modified = True
            except Exception as e:
                errormsg = "Failed to modify NVMe host %s max_num_sys_ports with error %s" % (nvme_host_details['id'], str(e))
                LOG.error(errormsg)
                self.module.fail_json(msg=errormsg)
        return modified

def get_powerflex_nvme_host_parameters():
    """This method provide parameter required for the Ansible NVMe host module on
    PowerFlex"""
    return dict(
        nvme_host_id = dict(type = 'str'),
        nqn = dict(type = 'str'),
        nvme_host_name = dict(type = 'str'),
        nvme_host_new_name = dict(type = 'str'),
        max_num_paths =  dict(type = 'str'),
        max_num_sys_ports = dict(type = 'str'),
        state = dict(required = True, type = 'str', choices=['present', 'absent'])
    )

def main():
    """ Create PowerFlex NVMe host and perform actions on it
        based on user input from playbook"""
    obj = PowerFlexHost()
    obj.perform_module_operation()


if __name__ == '__main__':
    main()