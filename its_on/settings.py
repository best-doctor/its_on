from __future__ import annotations

from pydantic import PostgresDsn, RedisDsn, PositiveInt, HttpUrl, Field, BaseModel
from pydantic_settings import SettingsConfigDict, BaseSettings

from its_on.enums import Environment


class AppSettings(BaseSettings):
    environment: Environment = Environment.dev


class FlagSvgBadgePrefixSettings(BaseModel):
    is_active: str = '✅'
    is_inactive: str = '❌'
    is_hidden: str = '⚠️'
    not_found: str = '⛔'


class FlagSvgBadgeSettings(BaseModel):
    background_color: str = '#ff6c6c'
    prefix: FlagSvgBadgePrefixSettings = Field(default_factory=FlagSvgBadgePrefixSettings)


class EnvironmentNoticeSettings(BaseModel):
    show: bool = False
    environment_name: str = 'Development'
    background_color: str = '#74b91d'  # green


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        env_parse_none_str='null',
    )

    debug: bool = False
    host: str = 'localhost'
    port: PositiveInt = 8081
    database_dsn: PostgresDsn = 'postgresql://bestdoctor:bestdoctor@localhost:5432/its_on'  # type: ignore
    database_superuser_dsn: PostgresDsn | None = None
    enable_db_logging: bool = False
    cache_url: RedisDsn = 'redis://127.0.0.1:6379/1'  # type: ignore
    cache_ttl: int = 300
    redis_url: RedisDsn = 'redis://127.0.0.1:6379/1'  # type: ignore
    cors_allow_origin: list[str] = ['http://localhost:8081']
    cors_allow_headers: list[str] = []
    enable_switches_full_info_endpoint: bool = False
    sync_from_its_on_url: HttpUrl | None = None
    flag_ttl_days: int = 14

    flag_svg_badge: FlagSvgBadgeSettings = Field(default_factory=FlagSvgBadgeSettings)
    environment_notice: EnvironmentNoticeSettings = Field(default_factory=EnvironmentNoticeSettings)


app_settings = AppSettings()
settings = Settings(_env_file=('.env', f'settings/{app_settings.environment.name}.env'))
