"""Unit tests for elastic/client.py."""

from unittest.mock import AsyncMock, patch, MagicMock


from src.elastic.client import init_es, close_es, get_es_client


async def test_init_es_disabled():
    with patch("src.elastic.client.settings") as mock_settings:
        mock_settings.ES_ENABLED = False
        result = await init_es()
    assert result is None


async def test_init_es_success():
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with (
        patch("src.elastic.client.settings") as mock_settings,
        patch("src.elastic.client.AsyncElasticsearch", return_value=mock_client),
        patch("src.elastic.client._client", None),
    ):
        mock_settings.ES_ENABLED = True
        mock_settings.ELASTICSEARCH_URL = "http://localhost:9200"
        result = await init_es()

    assert result is mock_client


async def test_init_es_ping_fails():
    mock_client = AsyncMock()
    mock_client.ping.return_value = False

    with (
        patch("src.elastic.client.settings") as mock_settings,
        patch("src.elastic.client.AsyncElasticsearch", return_value=mock_client),
    ):
        mock_settings.ES_ENABLED = True
        mock_settings.ELASTICSEARCH_URL = "http://localhost:9200"
        result = await init_es()

    assert result is None
    mock_client.close.assert_called_once()


async def test_init_es_exception():
    with (
        patch("src.elastic.client.settings") as mock_settings,
        patch("src.elastic.client.AsyncElasticsearch", side_effect=Exception("conn refused")),
    ):
        mock_settings.ES_ENABLED = True
        mock_settings.ELASTICSEARCH_URL = "http://localhost:9200"
        result = await init_es()

    assert result is None


async def test_close_es_with_client():
    mock_client = AsyncMock()
    with patch("src.elastic.client._client", mock_client):
        await close_es()
    mock_client.close.assert_called_once()


async def test_close_es_no_client():
    with patch("src.elastic.client._client", None):
        await close_es()  # should not raise


def test_get_es_client():
    mock_client = MagicMock()
    with patch("src.elastic.client._client", mock_client):
        assert get_es_client() is mock_client


def test_get_es_client_none():
    with patch("src.elastic.client._client", None):
        assert get_es_client() is None
