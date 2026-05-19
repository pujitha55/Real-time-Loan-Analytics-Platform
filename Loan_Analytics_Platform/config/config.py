import os
from configparser import ConfigParser

# Paths for config and schema files
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.ini")
SOURCE_AVRO_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "loan-events-avro-schema.avsc")


def read_config() -> dict:
    """Reads Kafka + stream config from config.ini and returns as dictionary."""
    config_parser = ConfigParser()
    config_parser.read(CONFIG_FILE_PATH)

    config_dict = {}
    for section in config_parser.sections():
        config_dict[section] = dict(config_parser.items(section))
    return config_dict


def read_source_avro_schema() -> str:
    """Reads Avro schema for loan events from .avsc file."""
    with open(SOURCE_AVRO_SCHEMA_PATH, "r") as f:
        return f.read()
