"""Environment-based configuration with BATMC_ prefix."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BATMC_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    env: str = "dev"
    api_url: str = "http://localhost:8000"
    supabase_url: str
    supabase_anon_key: str
    user_email: str
    user_password: str
    user_name: str = "Chester"


_config: MCPConfig | None = None


def get_config() -> MCPConfig:
    global _config
    if _config is None:
        _config = MCPConfig()
    return _config
