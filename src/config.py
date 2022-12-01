from logging import _nameToLevel as valid_log_levels
from typing import Any

import yaml
from loguru import logger
from pydantic import BaseModel, validator


class AppConfig(BaseModel):
    crontab_path: str


class LoggerConfig(BaseModel):
    level: str
    file_path: str

    @validator('level')
    @classmethod
    def is_valid_log_level(cls, level: str) -> str:
        if level not in valid_log_levels:
            raise ValueError(f'Invalid log level. Expected: {valid_log_levels}')
        return level


class Config(BaseModel):
    app: AppConfig
    logger: LoggerConfig

    @classmethod
    def load(cls, path: str) -> Any:
        logger.debug(f'Trying to load config from {path}')

        try:
            with open(path, 'r') as f:
                yml = yaml.safe_load(f)
        except FileNotFoundError as ex:
            logger.error(ex)
            raise ex

        logger.debug('Application config load successfully')

        return cls(**yml)

    def configure_logger(self) -> None:
        logger.add(self.logger.file_path, level=self.logger.level)
