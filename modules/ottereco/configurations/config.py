# noinspection PyInterpreter
from typing import List, Dict, Any, Union

EconomyConfiguration = Dict[str,
                                 Union[str, Dict[str, Union[str, Dict[str, str]]]]]
EconomyCategory = Dict[str, Dict[str, Union[str, Dict[str, str]]]]


def EconomyConfigData() -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, EconomyCategory]]]]]:
    return {
        "ECONOMY_CONFIG_DATA": {
            "TITLE": "Economy Settings",
            "CONFIGURATION": {
                "CATEGORIES": {
                    "ECONOMY": {
                        "TITLE": "Economy",
                        "economy_enabled": {
                            "TYPE": "BOOLEAN",
                            "DESCRIPTION": "Enable/Disable Economy"
                        },
                        "economy_currency": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "Economy Currency/Symbol"
                        },
                        "economy_currency_on_left": {
                            "TYPE": "BOOLEAN",
                            "DESCRIPTION": "Have the currency on the left side"
                        },
                        "economy_starting_balance": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Starting Balance for new users"
                        },
                        "economy_maximum_balance": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Maximum Balance for users"
                        },
                        "economy_message_earnings_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Message Earnings Minimum"
                        },
                        "economy_message_earnings_max": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Message Earnings Maximum"
                        },
                        "economy_daily_amount_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Daily Earnings Minimum"
                        },
                        "economy_daily_amount_max": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Daily Earnings Maximum"
                        },
                        "economy_work_amount_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Work Earnings Minimum"
                        },
                        "economy_work_amount_max": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Work Earnings Maximum"
                        },
                        "economy_server_multiplier": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Server Multiplier"
                        },
                        "economy_earnable_messages_per_min": {
                            "TYPE": "NUMBER",
                            "DESCRIPTION": "Economy Earnable Messages Per Minute"
                        },
                        "economy_log_channel": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Channel to log economy events"
                        }
                    },
                }
            }
        }
    }
