# noinspection PyInterpreter
from typing import List, Dict, Any, Union

ModmailConfiguration = Dict[str,
                                 Union[str, Dict[str, Union[str, Dict[str, str]]]]]
ModmailCategory = Dict[str, Dict[str, Union[str, Dict[str, str]]]]


def ModmailConfigData() -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, ModmailCategory]]]]]:
    return {
        "MODMAIL_CONFIG_DATA": {
            "TITLE": "Modmail Settings",
            "CONFIGURATION": {
                "CATEGORIES": {
                    "MODMAIL": {
                        "TITLE": "Modmail",
                        "modmail_category_id": {
                            "TYPE": "CHANNEL_CATEGORY",
                            "DESCRIPTION": "Category for all modmail threads to go"
                        },
                        "modmail_log_channel_id": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Channel to Log any modmails"
                        },
                        "modmail_instruction": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "Open Modmail message"
                        },
                        "modmail_staff_role_id": {
                            "TYPE": "ROLE",
                            "DESCRIPTION": "Role to ping for a new modmail"
                        },
                    }
                }
            }
        }
    }
