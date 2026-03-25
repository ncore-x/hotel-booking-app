import json
import logging
from datetime import datetime, timezone


class _JSONFormatter(logging.Formatter):
    """Выводит каждую запись лога как JSON-строку."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack"] = self.formatStack(record.stack_info)
        return json.dumps(entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")
        )
    logging.root.handlers = []
    logging.root.addHandler(handler)
    logging.root.setLevel(level.upper())
