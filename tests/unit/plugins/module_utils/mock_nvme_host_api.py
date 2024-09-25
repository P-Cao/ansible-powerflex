# Copyright: (c) 2024, Dell Technologies

# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

"""
Mock Api response for Unit tests of NVMe host module on Dell Technologies (Dell) PowerFlex
"""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

class MockNvmeHostApi:
    MODULE_UTILS_PATH = "ansible_collections.dellemc.powerflex.plugins.module_utils.storage.dell.utils"
    COMMON_ARGS = {
        "nqn": None,
        "max_num_paths": None,
        "max_num_sys_ports": None,
        "nvme_host_id": None,
        "nvme_host_name": None,
        "nvme_host_new_name": None,
        "state": None
    }
    
    @staticmethod
    def get_nvme_host_details():
        return [{
            "hostOsFullType": "Generic",
            "systemId": "f4c3b7f5c48cb00f",
            "sdcApproved": None,
            "sdcAgentActive": None,
            "mdmIpAddressesCurrent": None,
            "sdcIp": None,
            "sdcIps": None,
            "osType": None,
            "perfProfile": None,
            "peerMdmId": None,
            "sdtId": None,
            "mdmConnectionState": None,
            "softwareVersionInfo": None,
            "socketAllocationFailure": None,
            "memoryAllocationFailure": None,
            "versionInfo": None,
            "sdcType": None,
            "nqn": "nqn.2014-08.org.nvmexpress:uuid:79e90a42-47c9-a0f6-d9d3-51c47c72c7c1",
            "maxNumPaths": 3,
            "maxNumSysPorts": 3,
            "sdcGuid": None,
            "installedSoftwareVersionInfo": None,
            "kernelVersion": None,
            "kernelBuildNumber": None,
            "sdcApprovedIps": None,
            "hostType": "NVMeHost",
            "sdrId": None,
            "name": "nvme_host_test",
            "id": "da8f60fd00010000",
            "links": []
        }]

    RESPONSE_EXEC_DICT = {
    }

    @staticmethod
    def get_sdc_exception_response(response_type):
        return MockSdcApi.RESPONSE_EXEC_DICT.get(response_type, "")
