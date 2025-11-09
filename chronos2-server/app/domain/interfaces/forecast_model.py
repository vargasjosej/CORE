"""
Interface para modelos de forecasting.

Este módulo define la abstracción IForecastModel que permite
diferentes implementaciones de modelos (Chronos, Prophet, ARIMA, etc.)
cumpliendo con DIP (Dependency Inversion Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


class IForecastModel(ABC):
    """
    Interface para modelos de forecasting.
    
    Esta abstracción permite que diferentes implementaciones de modelos
    sean intercambiables sin modificar el código que las usa (DIP + LSP).
    
    Ejemplos de implementaciones:
        - ChronosModel (Chronos-2)
        - ProphetModel (Facebook Prophet)
        - ARIMAModel (ARIMA tradicional)
    """
    
    @abstractmethod
    def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        quantile_levels: List[float],
        **kwargs
    ) -> pd.DataFrame:
        """
        Genera pronósticos probabilísticos.
        
        Args:
            context_df: DataFrame con datos históricos.
                       Debe contener columnas: id, timestamp, target
            prediction_length: Número de pasos a predecir
            quantile_levels: Lista de cuantiles a calcular (ej: [0.1, 0.5, 0.9])
            **kwargs: Parámetros adicionales específicos del modelo
        
        Returns:
            pd.DataFrame: Pronósticos con columnas:
                         - id: Identificador de serie
                         - timestamp: Timestamp de predicción
                         - predictions: Valor mediano
                         - {q}: Valor para cada cuantil q
        
        Raises:
            ValueError: Si los datos de entrada son inválidos
            RuntimeError: Si el modelo falla al predecir
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna información del modelo.
        
        Returns:
            Dict con información del modelo:
                - type: Tipo de modelo (ej: "Chronos2", "Prophet")
                - model_id: ID del modelo
                - version: Versión del modelo
                - device: Dispositivo usado (cpu/cuda)
                - otros campos específicos del modelo
        """
        pass
    
    def validate_context(self, context_df: pd.DataFrame) -> bool:
        """
        Valida que el DataFrame de contexto tenga el formato correcto.
        
        Args:
            context_df: DataFrame a validar
        
        Returns:
            bool: True si es válido
        
        Raises:
            ValueError: Si el DataFrame es inválido
        """
        required_columns = {"id", "timestamp", "target"}
        
        if not isinstance(context_df, pd.DataFrame):
            raise ValueError("context_df debe ser un pandas DataFrame")
        
        missing_columns = required_columns - set(context_df.columns)
        if missing_columns:
            raise ValueError(
                f"Faltan columnas requeridas: {missing_columns}. "
                f"Se encontraron: {set(context_df.columns)}"
            )
        
        if context_df.empty:
            raise ValueError("context_df no puede estar vacío")
        
        if context_df["target"].isnull().any():
            raise ValueError("La columna 'target' contiene valores nulos")
        
        return True
