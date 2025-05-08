from pydantic_settings import BaseSettings

class Config(BaseSettings):
    BOT_TOKEN: str

    class Config:
        env_file = ".env"

config = Config()
