import logging
import os


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;5;240m"
    white = "\x1b[38;5;15m"
    yellow = "\x1b[33;20m"
    green = "\x1b[32;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    error_format = "%(asctime)s - %(name)s - %(levelname)s - (%(filename)s:%(lineno)d) - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + error_format + reset,
        logging.ERROR: red + error_format + reset,
        logging.CRITICAL: bold_red + error_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name):
    """
    Set up a logger for the module
    :param name: The name of the module
    :return: The logger
    """
    # Set up logging
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get("LOG_LEVEL", "DEBUG"))

    # If the logger already has handlers, we don't need to add them again.
    if logger.handlers:
        return logger

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Check if running in AWS Lambda
    if os.environ.get("AWS_EXECUTION_ENV") is None:
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

    return logger
