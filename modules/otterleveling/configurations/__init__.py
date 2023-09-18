from typing import List, Dict

from modules.otterleveling import LevelingGuild
from modules.otterleveling.configurations.config import LevelingConfigData, LevelingConfiguration


def get_config_categories():
    categories_list = []
    config_data: LevelingConfiguration = LevelingConfigData() # type:ignore
    categories: Dict[str] = config_data['LEVELING_CONFIG_DATA']['CONFIGURATION']['CATEGORIES']  # type:ignore
    for category_name, category_properties in categories.items():
        categories_list.append(category_name)
    return categories_list


def get_config_category(category_name: str) -> List[str]:
    config = LevelingConfigData()["LEVELING_CONFIG_DATA"]["CONFIGURATION"]["CATEGORIES"]
    if category_name in config:
        category_config = config[category_name]
        return [key for key in category_config.keys() if key != "TITLE"]
    else:
        return []


def get_config_category_with_description(category_name: str) -> Dict[str, str]:
    config = LevelingConfigData()["LEVELING_CONFIG_DATA"]["CONFIGURATION"]["CATEGORIES"]
    if category_name in config:
        category_config = config[category_name]
        return {key: category_config[key]["DESCRIPTION"] for key in category_config.keys() if key != "TITLE"}
    else:
        return {}

def get_config_category_setting_type(category_name: str, setting: str) -> str:
    config = LevelingConfigData()["LEVELING_CONFIG_DATA"]["CONFIGURATION"]["CATEGORIES"]
    return config[category_name][setting]["TYPE"]

async def get_guild_configurations(guild_id: str):
    return await LevelingGuild.fetch(guild_id=guild_id)
