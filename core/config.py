"""Zentrale Konfiguration via pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_default_model: str = "qwen2.5:14b-instruct-q5_K_M"

    # Streamlit
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "localhost"

    # App
    app_ocr_enabled: bool = True
    app_ocr_lang: str = "deu"
    app_default_output_format: str = "docx"
    app_max_upload_size_mb: int = 50
    app_gnotkg_check_enabled: bool = True
    app_data_dir: str = "data"
    app_history_dir: str = "history"
    app_fee_tables_dir: str = "data/fee_tables"

    # LLM
    llm_temperature: float = 0.1
    llm_max_retries: int = 3
    llm_format: str = "json"

    @property
    def ollama_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"

    @property
    def data_dir_path(self) -> Path:
        return Path(self.app_data_dir).resolve()

    @property
    def history_dir_path(self) -> Path:
        return Path(self.app_history_dir).resolve()

    @property
    def fee_tables_dir_path(self) -> Path:
        return Path(self.app_fee_tables_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
