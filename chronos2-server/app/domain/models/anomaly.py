"""
Modelo de dominio para anomalías detectadas.

Este módulo define la entidad AnomalyPoint, cumpliendo con SRP.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnomalyPoint:
    """
    Representa un punto con posible anomalía detectada.
    
    Attributes:
        index: Índice del punto en la serie
        value: Valor observado
        expected: Valor esperado (mediana del pronóstico)
        lower_bound: Límite inferior del intervalo de confianza
        upper_bound: Límite superior del intervalo de confianza
        is_anomaly: Indica si el punto es una anomalía
        z_score: Puntuación Z del punto (opcional)
        severity: Severidad de la anomalía (low, medium, high)
    
    Example:
        >>> point = AnomalyPoint(
        ...     index=5,
        ...     value=200.0,
        ...     expected=120.0,
        ...     lower_bound=115.0,
        ...     upper_bound=125.0,
        ...     is_anomaly=True,
        ...     z_score=4.5
        ... )
        >>> point.deviation
        80.0
        >>> point.severity
        'high'
    """
    
    index: int
    value: float
    expected: float
    lower_bound: float
    upper_bound: float
    is_anomaly: bool
    z_score: float = 0.0
    severity: Optional[str] = None
    
    def __post_init__(self):
        """Cálculo automático de severidad"""
        if self.severity is None and self.is_anomaly:
            self.severity = self._calculate_severity()
    
    @property
    def deviation(self) -> float:
        """
        Calcula la desviación del valor respecto al esperado.
        
        Returns:
            float: Diferencia absoluta entre valor y esperado
        """
        return abs(self.value - self.expected)
    
    @property
    def deviation_percentage(self) -> float:
        """
        Calcula el porcentaje de desviación.
        
        Returns:
            float: Desviación como porcentaje del valor esperado
        """
        if self.expected == 0:
            return float('inf') if self.value != 0 else 0.0
        return (self.deviation / abs(self.expected)) * 100
    
    def _calculate_severity(self) -> str:
        """
        Calcula la severidad de la anomalía basada en z_score.
        
        Returns:
            str: "low", "medium" o "high"
        """
        abs_z = abs(self.z_score)
        
        if abs_z >= 4.0:
            return "high"
        elif abs_z >= 3.0:
            return "medium"
        else:
            return "low"
    
    def is_above_expected(self) -> bool:
        """Retorna True si el valor está por encima del esperado"""
        return self.value > self.expected
    
    def is_below_expected(self) -> bool:
        """Retorna True si el valor está por debajo del esperado"""
        return self.value < self.expected
    
    def to_dict(self) -> dict:
        """Serializa el punto a diccionario"""
        return {
            "index": self.index,
            "value": self.value,
            "expected": self.expected,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "is_anomaly": self.is_anomaly,
            "z_score": self.z_score,
            "severity": self.severity,
            "deviation": self.deviation,
            "deviation_percentage": self.deviation_percentage
        }
