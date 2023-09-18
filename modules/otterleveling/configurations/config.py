# noinspection PyInterpreter
from typing import List, Dict, Any, Union

LevelingConfiguration = Dict[str,
                            Union[str, Dict[str, Union[str, Dict[str, str]]]]]
LevelingCategory = Dict[str, Dict[str, Union[str, Dict[str, str]]]]


def LevelingConfigData() -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, LevelingCategory]]]]]:
    return {
        "LEVELING_CONFIG_DATA": {
            "TITLE": "Leveling Settings",
            "CONFIGURATION": {
                "CATEGORIES": {
                    "LEVELING": {
                        "TITLE": "Leveling Settings",
                        "leveling_enabled": {
                            "TYPE": "BOOLEAN",
                            "DESCRIPTION": "Enable/Disable Leveling"
                        },
                        "leveling_xp_base": {
                            "TYPE": "FLOAT",
                            "DESCRIPTION": "XP Base"
                        },
                        "leveling_xp_per_message_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Minimum XP per Message"
                        },
                        "leveling_xp_per_message_max": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Maximum XP per Message"
                        },
                        "leveling_xp_per_message_levelup_msg": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "Level Up Message"
                        },
                        "leveling_xp_per_message_levelup_channel": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Level Up Channel"
                        },
                        "leveling_server_multiplier": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Server Multiplier"
                        },
                        "leveling_earnable_messages_per_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Earnable Messages per Minute"
                        }

                    }
                }
            }
        }
    }
