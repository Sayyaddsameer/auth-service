from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PORT: int = 8000
    DATABASE_URL: str
    REDIS_URL: str
    
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    JWT_REFRESH_EXPIRATION_DAYS: int = 7
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    class Config:
        env_file = ".env.example"
        extra = "ignore"

settings = Settings()