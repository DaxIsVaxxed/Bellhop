import json


def get_config():
    with open("config/config.json") as f:
        cfg = json.load(f)
    return cfg
