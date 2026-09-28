from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'StockPulse'
    environment: str = 'development'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/stockpulse'
    llm_provider: str = 'mock'
    llm_api_key: str = 'local-dev-key'
    llm_base_url: str = 'https://litellm-qc.zycus.net/v1'
    llm_model: str = 'qwen-cursor'
    cors_origins: str = 'http://localhost:5173'
    demand_spike_multiplier: float = 1.5
    auto_init_db: bool = False


settings = Settings()
