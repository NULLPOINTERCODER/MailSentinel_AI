import logging
import re
from typing import Any

# Sensitive patterns to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(api[-_]?key[\"']?\s*[:=]\s*[\"'])[A-Za-z0-9\-._~+/]+([\"'])", re.IGNORECASE), r"\1[REDACTED]\2"),
    (re.compile(r"(password[\"']?\s*[:=]\s*[\"'])[^\"']+([\"'])", re.IGNORECASE), r"\1[REDACTED]\2"),
    (re.compile(r"(secret[\"']?\s*[:=]\s*[\"'])[^\"']+([\"'])", re.IGNORECASE), r"\1[REDACTED]\2"),
    (re.compile(r"(access_token[\"']?\s*[:=]\s*[\"'])[^\"']+([\"'])", re.IGNORECASE), r"\1[REDACTED]\2"),
]


class SensitiveFilter(logging.Filter):
    """Filters log records to ensure no passwords, tokens or API keys are printed in plain text."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        if record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, repl in SENSITIVE_PATTERNS:
                        arg = pattern.sub(repl, arg)
                cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configures application-wide logging with security masking."""
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    # Replace existing handlers
    root_logger.handlers = [handler]
