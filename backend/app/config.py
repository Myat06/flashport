from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://flashport:flashport@localhost:5432/flashport"
    tesseract_cmd: str = "/usr/bin/tesseract"
    secret_key: str = "changeme"
    api_key: str = "changeme"
    manager_username: str = "manager"
    manager_password: str = "flashport2026"
    jwt_expire_hours: int = 8
    fcm_server_key: str = ""
    fcm_project_id: str = "flashport-9870d"
    fcm_service_account_json: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
