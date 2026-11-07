import logging
import re
import sys
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import g, has_request_context, request
from flask.logging import default_handler


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, "request_id", "-") if has_request_context() else "-"
        return True


def configure_logging(app):
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for handler in list(app.logger.handlers):
        if handler is default_handler or getattr(handler, "_jobcover_handler", False):
            app.logger.removeHandler(handler)
            if handler is not default_handler:
                handler.close()

    stream_handler = logging.StreamHandler(sys.stdout)
    _prepare_handler(stream_handler, formatter, level)
    app.logger.addHandler(stream_handler)

    log_file = str(app.config.get("LOG_FILE", "")).strip()
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=int(app.config.get("LOG_MAX_BYTES", 5 * 1024 * 1024)),
            backupCount=int(app.config.get("LOG_BACKUP_COUNT", 3)),
            encoding="utf-8",
        )
        _prepare_handler(file_handler, formatter, level)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(level)
    app.logger.propagate = False

    @app.before_request
    def log_request_start():
        supplied_id = request.headers.get("X-Request-ID", "")
        g.request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_id) else uuid.uuid4().hex[:12]
        g.request_started_at = time.perf_counter()
        app.logger.info("request.start method=%s path=%s", request.method, request.path)

    @app.after_request
    def log_request_end(response):
        duration_ms = (time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())) * 1000
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        app.logger.info(
            "request.end method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    app.logger.info("logging.ready level=%s file=%s", level_name, log_file or "disabled")


def _prepare_handler(handler, formatter, level):
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())
    handler._jobcover_handler = True
