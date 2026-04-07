import logging
from elasticsearch import AsyncElasticsearch
from src.config import settings

logger = logging.getLogger(__name__)

_client: AsyncElasticsearch | None = None


def get_es_client() -> AsyncElasticsearch | None:
    return _client


async def init_es() -> AsyncElasticsearch | None:
    global _client
    if not settings.ES_ENABLED:
        logger.info("Elasticsearch отключён (ES_ENABLED=False)")
        return None
    try:
        client = AsyncElasticsearch(settings.ELASTICSEARCH_URL)
        if await client.ping():
            _client = client
            logger.info("Elasticsearch подключён: %s", settings.ELASTICSEARCH_URL)
            return client
        await client.close()
        logger.warning("Elasticsearch не отвечает на ping: %s", settings.ELASTICSEARCH_URL)
    except Exception as exc:
        logger.warning("Elasticsearch недоступен, используется PostgreSQL: %s", exc)
    return None


async def close_es() -> None:
    global _client
    if _client:
        await _client.close()
        _client = None
