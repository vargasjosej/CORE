"""
Configuración centralizada del proyecto usando Pydantic Settings.

Este módulo implementa el patrón Singleton para la configuración,
cumpliendo con el principio SRP (Single Responsibility Principle).
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación.
    
    Todas las configuraciones se cargan desde variables de entorno
    o valores por defecto. Esto permite fácil configuración en
    diferentes ambientes (dev, staging, production).
    """
    
    # API Configuration
    api_title: str = "Chronos-2 Forecasting API"
    api_version: str = "3.0.0"
    api_description: str = (
        "API de pronósticos con Chronos-2 + Excel Add-in. "
        "Refactorizado con Clean Architecture y principios SOLID."
    )
    api_port: int = 8000
    
    # Model Configuration
    model_id: str = "amazon/chronos-2"
    device_map: str = "cpu"
    
    # CORS Configuration
    cors_origins: List[str] = [
        "https://localhost:3000",
        "https://localhost:3001",
        "https://ttzzs-chronos2-excel-forecasting-api.hf.space",
        "*"  # Permitir todos los orígenes para Office Add-ins
    ]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Static Files
    static_dir: str = "static"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton instance
_settings_instance = None


def get_settings() -> Settings:
    """
    Obtiene la instancia singleton de Settings.
    
    Returns:
        Settings: Instancia de configuración
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# Exportar instancia por defecto para uso directo
settings = get_settings()
