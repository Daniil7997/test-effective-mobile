from pydantic_settings import BaseSettings, SettingsConfigDict


class MySettings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    IS_TEST_DB: bool = False
    PUBLIC_KEY_HEX: str
    REDIS_PASSWORD: str
    model_config = SettingsConfigDict(env_file="envs/.env.local",
                                      env_file_required=False,
                                      extra='ignore')

    @property
    def url_db_asyncpg(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

    @property
    def api_root_url(self):
        return '/resource/'

    @property
    def url_redis(self):
        return f'redis://:{self.REDIS_PASSWORD}@resource_redis:6379'


settings = MySettings()
