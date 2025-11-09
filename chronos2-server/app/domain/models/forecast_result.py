"""
Modelo de dominio para resultados de forecasting.

Este módulo define la entidad ForecastResult, cumpliendo con SRP.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ForecastResult:
    """
    Resultado de una operación de forecasting.
    
    Encapsula los pronósticos generados, incluyendo timestamps,
    valores medianos y cuantiles.
    
    Attributes:
        timestamps: Lista de timestamps pronosticados
        median: Lista de valores medianos (cuantil 0.5)
        quantiles: Dict de cuantil -> valores (ej: {"0.1": [...], "0.9": [...]})
        series_id: Identificador de la serie
        metadata: Información adicional del forecast
    
    Example:
        >>> result = ForecastResult(
        ...     timestamps=["2025-11-10", "2025-11-11"],
        ...     median=[120.5, 122.3],
        ...     quantiles={"0.1": [115.2, 116.8], "0.9": [125.8, 127.8]},
        ...     series_id="sales_A"
        ... )
        >>> result.length
        2
    """
    
    timestamps: List[str]
    median: List[float]
    quantiles: Dict[str, List[float]]
    series_id: str = "series_0"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validación automática al crear la instancia"""
        if self.metadata is None:
            self.metadata = {}
        self.validate()
    
    @property
    def length(self) -> int:
        """Retorna el número de períodos pronosticados"""
        return len(self.timestamps)
    
    def validate(self) -> bool:
        """
        Valida la consistencia del resultado.
        
        Returns:
            bool: True si es válido
        
        Raises:
            ValueError: Si el resultado es inválido
        """
        n = len(self.timestamps)
        
        # Validar que no esté vacío
        if n == 0:
            raise ValueError("El resultado no puede estar vacío")
        
        # Validar longitud de median
        if len(self.median) != n:
            raise ValueError(
                f"Median ({len(self.median)}) debe tener la misma longitud "
                f"que timestamps ({n})"
            )
        
        # Validar longitud de cada cuantil
        for q, values in self.quantiles.items():
            if len(values) != n:
                raise ValueError(
                    f"Cuantil {q} ({len(values)}) debe tener la misma longitud "
                    f"que timestamps ({n})"
                )
        
        # Validar que todos los valores sean numéricos
        if not all(isinstance(v, (int, float)) for v in self.median):
            raise ValueError("Median debe contener solo valores numéricos")
        
        for q, values in self.quantiles.items():
            if not all(isinstance(v, (int, float)) for v in values):
                raise ValueError(f"Cuantil {q} debe contener solo valores numéricos")
        
        return True
    
    def get_quantile(self, level: float) -> List[float]:
        """
        Obtiene los valores de un cuantil específico.
        
        Args:
            level: Nivel del cuantil (ej: 0.1, 0.5, 0.9)
        
        Returns:
            List[float]: Valores del cuantil
        
        Raises:
            KeyError: Si el cuantil no existe
        """
        key = f"{level:.3g}"
        if key not in self.quantiles:
            available = list(self.quantiles.keys())
            raise KeyError(
                f"Cuantil {level} no encontrado. Disponibles: {available}"
            )
        return self.quantiles[key]
    
    def get_interval(self, lower: float = 0.1, upper: float = 0.9) -> Dict[str, List[float]]:
        """
        Obtiene un intervalo de predicción.
        
        Args:
            lower: Cuantil inferior (default: 0.1)
            upper: Cuantil superior (default: 0.9)
        
        Returns:
            Dict con "lower", "median", "upper"
        """
        return {
            "lower": self.get_quantile(lower),
            "median": self.median,
            "upper": self.get_quantile(upper)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el resultado a diccionario.
        
        Returns:
            Dict con la representación del resultado
        """
        return {
            "timestamps": self.timestamps,
            "median": self.median,
            "quantiles": self.quantiles,
            "series_id": self.series_id,
            "length": self.length,
            "metadata": self.metadata
        }
