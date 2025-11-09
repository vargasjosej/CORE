"""
Modelo de dominio para configuración de forecasting.

Este módulo define la entidad ForecastConfig, cumpliendo con SRP.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ForecastConfig:
    """
    Configuración para operaciones de forecasting.
    
    Define los parámetros necesarios para realizar un pronóstico,
    incluyendo horizonte de predicción, cuantiles y frecuencia.
    
    Attributes:
        prediction_length: Número de períodos a pronosticar
        quantile_levels: Cuantiles a calcular (ej: [0.1, 0.5, 0.9])
        freq: Frecuencia temporal (D, H, M, etc.)
    
    Example:
        >>> config = ForecastConfig(
        ...     prediction_length=7,
        ...     quantile_levels=[0.1, 0.5, 0.9],
        ...     freq="D"
        ... )
        >>> config.has_median
        True
    """
    
    prediction_length: int
    quantile_levels: List[float] = field(default_factory=lambda: [0.1, 0.5, 0.9])
    freq: str = "D"
    
    def __post_init__(self):
        """Validación y normalización automática"""
        self.validate()
        self._ensure_median()
        self._sort_quantiles()
    
    @property
    def has_median(self) -> bool:
        """Verifica si el cuantil 0.5 (mediana) está incluido"""
        return 0.5 in self.quantile_levels
    
    def validate(self) -> bool:
        """
        Valida la configuración.
        
        Returns:
            bool: True si es válida
        
        Raises:
            ValueError: Si la configuración es inválida
        """
        # Validar prediction_length
        if self.prediction_length < 1:
            raise ValueError(
                f"prediction_length debe ser >= 1, recibido: {self.prediction_length}"
            )
        
        # Validar quantile_levels
        if not self.quantile_levels:
            raise ValueError("quantile_levels no puede estar vacío")
        
        # Verificar que los cuantiles estén en [0, 1]
        for q in self.quantile_levels:
            if not 0 <= q <= 1:
                raise ValueError(
                    f"Todos los cuantiles deben estar en [0, 1], encontrado: {q}"
                )
        
        # Validar freq
        valid_freqs = {"D", "H", "M", "W", "Y", "Q", "S", "T", "min"}
        if self.freq not in valid_freqs:
            raise ValueError(
                f"Frecuencia '{self.freq}' no reconocida. "
                f"Válidas: {valid_freqs}"
            )
        
        return True
    
    def _ensure_median(self):
        """Asegura que la mediana (0.5) esté incluida"""
        if not self.has_median:
            self.quantile_levels.append(0.5)
    
    def _sort_quantiles(self):
        """Ordena los cuantiles de menor a mayor"""
        self.quantile_levels = sorted(set(self.quantile_levels))
    
    @classmethod
    def default(cls) -> "ForecastConfig":
        """
        Crea una configuración con valores por defecto.
        
        Returns:
            ForecastConfig: Configuración por defecto
                - prediction_length: 7
                - quantile_levels: [0.1, 0.5, 0.9]
                - freq: "D"
        """
        return cls(
            prediction_length=7,
            quantile_levels=[0.1, 0.5, 0.9],
            freq="D"
        )
    
    def to_dict(self) -> dict:
        """Serializa la configuración a diccionario"""
        return {
            "prediction_length": self.prediction_length,
            "quantile_levels": self.quantile_levels,
            "freq": self.freq
        }
