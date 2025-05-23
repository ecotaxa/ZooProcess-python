import pytest
from pytest_mock import MockFixture

from providers.server import Server
from config_rdr import config


@pytest.mark.skip(reason="Skipped test")
def test_Niko_server():
    server = Server("http://niko.obs-vlfr.fr:5000")
    online = server.test_server()

    assert online is True


@pytest.mark.skip(reason="Skipped test")
def test_Seb_server():
    server = Server("http://seb:5000")
    online = server.test_server()

    assert online is True


@pytest.mark.skip(reason="Skipped test")
def test_Localhost_server():
    server = Server("http://localhost:5001")
    with pytest.raises(Exception):
        server.test_server()


@pytest.mark.skip(reason="Skipped test")
def test_dbserver():
    server = Server("http://zooprocess.imev-mer.fr:8081/v1/ping")

    assert server.test_server() is True


def test_dbserver_withconfig(mocker: MockFixture):
    # Create a mock response with status_code 200
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200

    # Patch requests.get to return our mock response
    mocker.patch("requests.get", return_value=mock_response)

    # print(config.dbserver)
    server = Server(config.dbserver)
    assert server.test_server() is True
