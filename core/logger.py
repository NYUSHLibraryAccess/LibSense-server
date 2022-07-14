import os
import time
import logging
import sys
from loguru import logger


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(cls, ENV):
        new_logger = cls.customize_logging(ENV)
        return new_logger

    @classmethod
    def customize_logging(cls, ENV):
        logger.remove()
        log_path = "./logs"
        log_path = os.path.join(
            log_path, f"""{(ENV + "_") if ENV else ""}LibSense_{time.strftime("%Y-%m-%d")}.log"""
        )
        logger.add(sys.stdout, enqueue=True, backtrace=True, level="INFO")
        logger.add(log_path, rotation="12:00", retention="5 days", enqueue=True)
        logging.basicConfig(handlers=[InterceptHandler()], level=0)
        logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
            _logger = logging.getLogger(_log)
            _logger.propagate = False
            _logger.handlers = [InterceptHandler()]

        return logger
