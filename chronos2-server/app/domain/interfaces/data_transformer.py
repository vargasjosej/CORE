"""
Interface para transformación de datos.

Define la abstracción para convertir datos entre diferentes formatos,
cumpliendo con ISP (Interface Segregation Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd


class IDataTransformer(ABC):
    """
    Interface para transformación de datos de series temporales.
    
    Esta interface está segregada para contener solo métodos relacionados
    con transformación de datos (ISP).
    """
    
    @abstractmethod
    def build_context_df(
        self,
        values: List[float],
        timestamps: Optional[List[str]] = None,
        series_id: str = "series_0",
        freq: str = "D"
    ) -> pd.DataFrame:
        """
        Construye un DataFrame de contexto para forecasting.
        
        Args:
            values: Lista de valores históricos
            timestamps: Lista de timestamps (opcional, se generan si es None)
            series_id: Identificador de la serie
            freq: Frecuencia temporal (D=daily, H=hourly, etc.)
        
        Returns:
            pd.DataFrame: DataFrame con columnas id, timestamp, target
        
        Raises:
            ValueError: Si valores y timestamps tienen longitudes diferentes
        """
        pass
    
    @abstractmethod
    def parse_prediction_result(
        self,
        pred_df: pd.DataFrame,
        quantile_levels: List[float]
    ) -> Dict[str, Any]:
        """
        Parsea el resultado de predicción a un formato estándar.
        
        Args:
            pred_df: DataFrame con predicciones del modelo
            quantile_levels: Cuantiles calculados
        
        Returns:
            Dict con:
                - timestamps: Lista de timestamps
                - median: Lista de valores medianos
                - quantiles: Dict {cuantil: [valores]}
        """
        pass
