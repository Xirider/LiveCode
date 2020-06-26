from typing import List

class Settings(object):

    # HALT! do NOT change this without changing corresponding type in the frontend! <----
    # Also note that this uses camelCase because that is standard in JS frontend
    def __init__(self, showGlobalVars=True, default_filter_vars: List[str] = [], default_filter_types: List[str] = [], *args, **kwargs):
        self.showGlobalVars = showGlobalVars
        self.default_filter_vars = default_filter_vars
        self.default_filter_types = default_filter_types
        # HALT! do NOT change this without changing corresponding type in the frontend! <----


settings = Settings()


def get_settings() -> Settings:
    return settings


def update_settings(new_settings) -> None:
    """
    Updates all settings
    """
    global settings
    settings = Settings(**new_settings)
