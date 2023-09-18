import logging

import coloredlogs
import yaml


def setup_logger():
    logger = logging.getLogger()
    with open("config/logging.yml", "r") as log_config:
        config = yaml.safe_load(log_config)
    coloredlogs.install(
        level="INFO",
        logger=logger,
        fmt=config["formats"]["console"],
        datefmt=config["formats"]["datetime"],
        level_styles=config["levels"],
        field_styles=config["fields"],
    )
    return logger