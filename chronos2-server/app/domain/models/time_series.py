"""
Modelo de dominio para series temporales.

Este módulo define la entidad TimeSeries, cumpliendo con SRP.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TimeSeries:
    """
    Modelo de dominio para una serie temporal.
    
    Representa una serie temporal con sus valores, timestamps opcionales
    y metadata asociada. Esta clase es inmutable después de la validación.
    
    Attributes:
        values: Lista de valores numéricos de la serie
        timestamps: Lista opcional de timestamps (strings ISO o índices)
        series_id: Identificador único de la serie
        freq: Frecuencia temporal (D=daily, H=hourly, M=monthly, etc.)
        metadata: Diccionario con información adicional
    
    Example:
        >>> series = TimeSeries(
        ...     values=[100, 102, 105, 103, 108],
        ...     series_id="sales_product_a",
        ...     freq="D"
        ... )
        >>> series.length
        5
        >>> series.validate()
        True
    """
    
    values: List[float]
    timestamps: Optional[List[str]] = None
    series_id: str = "series_0"
    freq: str = "D"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validación automática al crear la instancia"""
        self.validate()
    
    @property
    def length(self) -> int:
        """Retorna la longitud de la serie"""
        return len(self.values)
    
    def validate(self) -> bool:
        """
        Valida la consistencia de la serie temporal.
        
        Returns:
            bool: True si la serie es válida
        
        Raises:
            ValueError: Si la serie es inválida
        """
        # Verificar que no esté vacía
        if not self.values or len(self.values) == 0:
            raise ValueError("La serie temporal no puede estar vacía")
        
        # Verificar que todos sean números
        if not all(isinstance(v, (int, float)) for v in self.values):
            raise ValueError("Todos los valores deben ser numéricos")
        
        # Verificar que no haya None/NaN
        if any(v is None or (isinstance(v, float) and v != v) for v in self.values):
            raise ValueError("La serie contiene valores nulos o NaN")
        
        # Si hay timestamps, verificar longitud
        if self.timestamps is not None:
            if len(self.timestamps) != len(self.values):
                raise ValueError(
                    f"Timestamps ({len(self.timestamps)}) y values ({len(self.values)}) "
                    "deben tener la misma longitud"
                )
        
        return True
    
    def get_subset(self, start: int, end: int) -> "TimeSeries":
        """
        Retorna un subset de la serie temporal.
        
        Args:
            start: Índice de inicio (inclusive)
            end: Índice de fin (exclusive)
        
        Returns:
            TimeSeries: Nueva instancia con el subset
        """
        subset_values = self.values[start:end]
        subset_timestamps = None
        
        if self.timestamps:
            subset_timestamps = self.timestamps[start:end]
        
        return TimeSeries(
            values=subset_values,
            timestamps=subset_timestamps,
            series_id=self.series_id,
            freq=self.freq,
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa la serie a diccionario.
        
        Returns:
            Dict con la representación de la serie
        """
        return {
            "values": self.values,
            "timestamps": self.timestamps,
            "series_id": self.series_id,
            "freq": self.freq,
            "length": self.length,
            "metadata": self.metadata
        }
