import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formata logs sem incluir corpos de requisição, tokens ou credenciais."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
