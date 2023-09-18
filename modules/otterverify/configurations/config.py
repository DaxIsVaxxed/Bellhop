# noinspection PyInterpreter
from typing import List, Dict, Any, Union

VerificationConfiguration = Dict[str,
                                 Union[str, Dict[str, Union[str, Dict[str, str]]]]]
VerificationCategory = Dict[str, Dict[str, Union[str, Dict[str, str]]]]


# CONFIGURATION DATA CCONFIGURED FOR OTTER MODULE
def VerificationConfigData() -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, VerificationCategory]]]]]:
    return {
        "VERIFICATION_CONFIG_DATA": {
            "TITLE": "Verification Settings",
            "CONFIGURATION": {
                "CATEGORIES": {
                    "VERIFICATION": {
                        "TITLE": "Verification",
                        "verification_logging_channel": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Channel to Log Handle Applications"
                        },
                        "pending_verifications_channel_id": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Channel to Receive/Handle Verifications"
                        },
                        "unverified_role_ids": {
                            "TYPE": "ROLE_LIST",
                            "DESCRIPTION": "Collection of Unverified Roles to remove upon acceptance"
                        },
                        "verified_role_ids": {
                            "TYPE": "ROLE_LIST",
                            "DESCRIPTION": "Collection of Verified Roles to add upon acceptance"
                        },
                        "staff_role_id": {
                            "TYPE": "ROLE",
                            "DESCRIPTION": "Role for Staff to manage verification applications"
                        },
                        "verification_questions": {
                            "TYPE": "MESSAGE_LIST",
                            "DESCRIPTION": "Collection of Messages UNDER 40 CHARS to question the user"
                        },
                        "verification_instructions": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "Instructions for verification"
                        },
                    },
                    "WELCOME": {
                        "TITLE": "Welcome Settings",
                        "welcome_role_id": {
                            "TYPE": "ROLE",
                            "DESCRIPTION": "Role to ping per welcome message"
                        },
                        "welcome_channel_id": {
                            "TYPE": "CHANNEL",
                            "DESCRIPTION": "Channel to send the welcome message upon acceptance"
                        },
                        "welcome_message": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "Message to send upon acceptance"
                        },
                        "welcome_message_banner_url": {
                            "TYPE": "MESSAGE",
                            "DESCRIPTION": "URL of the banner URL"
                        }
                    }
                }
            }
        }
    }
