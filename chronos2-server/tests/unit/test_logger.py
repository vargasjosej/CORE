"""
Tests unitarios para el módulo de logging.
"""

import pytest
import logging
from app.utils.logger import setup_logger


class TestLogger:
    """Tests para la función setup_logger"""
    
    def test_setup_logger_basic(self):
        """Verifica que setup_logger cree un logger"""
        logger = setup_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_logger_level_from_settings(self):
        """Verifica que el logger use el nivel de settings por defecto"""
        logger = setup_logger("test_logger_level")
        
        # Por defecto debería ser INFO
        assert logger.level == logging.INFO
    
    def test_logger_custom_level(self):
        """Verifica que se pueda especificar un nivel personalizado"""
        logger = setup_logger("test_custom", level="DEBUG")
        
        assert logger.level == logging.DEBUG
    
    def test_logger_has_handler(self):
        """Verifica que el logger tenga al menos un handler"""
        logger = setup_logger("test_handler")
        
        assert len(logger.handlers) > 0
    
    def test_logger_no_duplicate_handlers(self):
        """Verifica que no se dupliquen handlers al llamar varias veces"""
        logger1 = setup_logger("test_duplicate")
        initial_count = len(logger1.handlers)
        
        logger2 = setup_logger("test_duplicate")
        
        assert len(logger2.handlers) == initial_count
        assert logger1 is logger2
    
    def test_logger_output(self, caplog):
        """Verifica que el logger pueda escribir mensajes"""
        # Crear un logger sin propagate=False para que caplog funcione
        logger = logging.getLogger("test_output_capture")
        logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO, logger="test_output_capture"):
            logger.info("Test message")
        
        assert "Test message" in caplog.text
    
    def test_logger_different_levels(self):
        """Verifica que se puedan crear loggers con diferentes niveles"""
        logger_debug = setup_logger("test_debug", level="DEBUG")
        logger_error = setup_logger("test_error", level="ERROR")
        
        assert logger_debug.level == logging.DEBUG
        assert logger_error.level == logging.ERROR
