from unittest.mock import Mock

import pytest
from aiohttp.web_app import Application
from ipv8.test.mocking.ipv8 import MockIPv8

from tribler.core.components.bandwidth_accounting.community.bandwidth_accounting_community \
    import BandwidthAccountingCommunity
from tribler.core.components.bandwidth_accounting.settings import BandwidthAccountingSettings
from tribler.core.components.restapi.rest.base_api_test import do_request
from tribler.core.components.restapi.rest.rest_manager import error_middleware
from tribler.core.components.restapi.rest.statistics_endpoint import StatisticsEndpoint


@pytest.fixture
async def mock_ipv8():
    ipv8 = MockIPv8("low", BandwidthAccountingCommunity, database=Mock(),
                    settings=BandwidthAccountingSettings())
    ipv8.overlays = [ipv8.overlay]
    ipv8.endpoint.bytes_up = 100
    ipv8.endpoint.bytes_down = 20
    yield ipv8
    await ipv8.stop()


@pytest.fixture
def endpoint():
    endpoint = StatisticsEndpoint()
    return endpoint


@pytest.fixture
def rest_api(web_app, event_loop, aiohttp_client, endpoint):
    web_app.add_subapp('/statistics', endpoint.app)
    yield event_loop.run_until_complete(aiohttp_client(web_app))


async def test_get_tribler_statistics(rest_api, endpoint, metadata_store):
    """
    Testing whether the API returns a correct Tribler statistics dictionary when requested
    """
    endpoint.mds = metadata_store
    stats = (await do_request(rest_api, 'statistics/tribler', expected_code=200))['tribler_statistics']
    assert 'db_size' in stats
    assert 'num_channels' in stats
    assert 'num_channels' in stats


async def test_get_ipv8_statistics(mock_ipv8, rest_api, endpoint):
    """
    Testing whether the API returns a correct IPv8 statistics dictionary when requested
    """
    endpoint.ipv8 = mock_ipv8
    json_data = await do_request(rest_api, 'statistics/ipv8', expected_code=200)
    assert json_data["ipv8_statistics"]


async def test_get_ipv8_statistics_unavailable(rest_api):
    """
    Testing whether the API returns error 500 if IPv8 is not available
    """
    json_data = await do_request(rest_api, 'statistics/ipv8', expected_code=200)
    assert not json_data["ipv8_statistics"]
