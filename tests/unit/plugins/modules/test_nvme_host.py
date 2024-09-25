# Copyright: (c) 2024, Dell Technologies

# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

"""Unit Tests for NVMe host module on PowerFlex"""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
# pylint: disable=unused-import
from ansible_collections.dellemc.powerflex.tests.unit.plugins.module_utils.libraries import initial_mock
from mock.mock import MagicMock
from ansible_collections.dellemc.powerflex.tests.unit.plugins.module_utils.mock_nvme_host_api import MockNvmeHostApi
from ansible_collections.dellemc.powerflex.tests.unit.plugins.module_utils.mock_api_exception \
    import MockApiException
from ansible_collections.dellemc.powerflex.plugins.module_utils.storage.dell \
    import utils
from ansible_collections.dellemc.powerflex.tests.unit.plugins.module_utils.mock_fail_json \
    import FailJsonException, fail_json

utils.get_logger = MagicMock()
utils.get_powerflex_gateway_host_connection = MagicMock()
utils.PowerFlexClient = MagicMock()

from ansible.module_utils import basic
basic.AnsibleModule = MagicMock()
from ansible_collections.dellemc.powerflex.plugins.modules.nvme_host import PowerFlexNvmeHost

class TestPowerflexSdc():

    get_module_args = MockNvmeHostApi.COMMON_ARGS
    
    @pytest.fixture
    def nvme_host_module_mock(self, mocker):
        mocker.patch(
            MockNvmeHostApi.MODULE_UTILS_PATH + '.PowerFlexClient',
            new=MockApiException)
        nvme_host_module_mock = PowerFlexNvmeHost()
        nvme_host_module_mock.module.check_mode = False
        nvme_host_module_mock.module.fail_json = fail_json
        return nvme_host_module_mock

    def capture_fail_json_call(self, error_msg, nvme_host_module_mock):
        try:
            nvme_host_module_mock.perform_module_operation()
        except FailJsonException as fj_object:
            assert error_msg in fj_object.message

    def test_get_nvme_host_details(self, nvme_host_module_mock):
        self.get_module_args.update({
            "nvme_host_id": "test_nvem_host",
            "state": "present"
        })
        nvme_host_module_mock.module.params = self.get_module_args
        nvme_host_module_mock.powerflex_conn.nvme_host.get = MagicMock(
            return_value=MockNvmeHostApi.get_sdc_details()
        )
        nvme_host_module_mock.perform_module_operation()
        nvme_host_module_mock.powerflex_conn.nvme_host.get.assert_called()
