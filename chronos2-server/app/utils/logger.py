"""
Sistema de logging centralizado.

Este módulo proporciona una función para crear loggers consistentes
en toda la aplicación, cumpliendo con SRP.
"""

import logging
import sys
from typing import Optional
from app.infrastructure.config.settings import settings


def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configura y retorna un logger con formato consistente.
    
    Args:
        name: Nombre del logger (típicamente __name__ del módulo)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Si es None, usa el nivel de settings
        format_string: Formato personalizado del log
                      Si es None, usa el formato de settings
    
    Returns:
        logging.Logger: Logger configurado
    
    Example:
        >>> from app.utils.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Aplicación iniciada")
    """
    logger = logging.getLogger(name)
    
    # Configurar nivel
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicar handlers
    if not logger.handlers:
        # Handler para stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # Formato
        log_format = format_string or settings.log_format
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    # No propagar a logger raíz para evitar duplicados
    logger.propagate = False
    
    return logger


# Logger por defecto para el módulo
logger = setup_logger(__name__)
