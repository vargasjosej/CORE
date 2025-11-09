"""
Tests unitarios para el módulo de configuración.
"""

import pytest
from app.infrastructure.config.settings import Settings, get_settings, settings


class TestSettings:
    """Tests para la clase Settings"""
    
    def test_default_values(self):
        """Verifica que los valores por defecto sean correctos"""
        s = Settings()
        
        assert s.api_title == "Chronos-2 Forecasting API"
        assert s.api_version == "3.0.0"
        assert s.api_port == 8000
        assert s.model_id == "amazon/chronos-2"
        assert s.device_map == "cpu"
        assert s.log_level == "INFO"
    
    def test_cors_origins_is_list(self):
        """Verifica que cors_origins sea una lista"""
        s = Settings()
        
        assert isinstance(s.cors_origins, list)
        assert len(s.cors_origins) > 0
        assert "*" in s.cors_origins
    
    def test_settings_from_env(self, monkeypatch):
        """Verifica que settings se cargue desde variables de entorno"""
        monkeypatch.setenv("MODEL_ID", "amazon/chronos-t5-small")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        s = Settings()
        
        assert s.model_id == "amazon/chronos-t5-small"
        assert s.api_port == 9000
        assert s.log_level == "DEBUG"
    
    def test_get_settings_singleton(self):
        """Verifica que get_settings retorne la misma instancia"""
        s1 = get_settings()
        s2 = get_settings()
        
        assert s1 is s2
    
    def test_settings_module_instance(self):
        """Verifica que settings sea una instancia de Settings"""
        assert isinstance(settings, Settings)


class TestSettingsValidation:
    """Tests de validación de configuración"""
    
    def test_api_version_format(self):
        """Verifica que la versión tenga formato correcto"""
        s = Settings()
        
        # Formato X.Y.Z
        parts = s.api_version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
    
    def test_log_level_valid(self):
        """Verifica que el nivel de log sea válido"""
        s = Settings()
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert s.log_level.upper() in valid_levels
    
    def test_device_map_valid(self):
        """Verifica que device_map sea válido"""
        s = Settings()
        
        valid_devices = ["cpu", "cuda", "auto"]
        assert s.device_map in valid_devices
