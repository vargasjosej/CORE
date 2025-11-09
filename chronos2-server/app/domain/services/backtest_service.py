"""
Servicio de dominio para backtesting.

Este servicio encapsula la lógica de validación de modelos,
cumpliendo con SRP y DIP.
"""

import numpy as np
from dataclasses import dataclass
from typing import List
from app.domain.interfaces.forecast_model import IForecastModel
from app.domain.interfaces.data_transformer import IDataTransformer
from app.domain.models.time_series import TimeSeries
from app.domain.models.forecast_config import ForecastConfig
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BacktestMetrics:
    """
    Métricas de evaluación de un backtest.
    
    Attributes:
        mae: Mean Absolute Error
        mape: Mean Absolute Percentage Error (%)
        rmse: Root Mean Squared Error
        wql: Weighted Quantile Loss (para cuantil 0.5)
    """
    mae: float
    mape: float
    rmse: float
    wql: float
    
    def to_dict(self) -> dict:
        """Serializa las métricas"""
        return {
            "mae": self.mae,
            "mape": self.mape,
            "rmse": self.rmse,
            "wql": self.wql
        }


@dataclass
class BacktestResult:
    """
    Resultado completo de un backtest.
    
    Attributes:
        metrics: Métricas de evaluación
        forecast: Valores pronosticados
        actuals: Valores reales
        timestamps: Timestamps del período de prueba
    """
    metrics: BacktestMetrics
    forecast: List[float]
    actuals: List[float]
    timestamps: List[str]
    
    def to_dict(self) -> dict:
        """Serializa el resultado"""
        return {
            "metrics": self.metrics.to_dict(),
            "forecast": self.forecast,
            "actuals": self.actuals,
            "timestamps": self.timestamps
        }


class BacktestService:
    """
    Servicio de dominio para backtesting de modelos.
    
    Realiza validación de modelos separando la serie en train/test
    y comparando pronósticos con valores reales.
    
    Attributes:
        model: Modelo de forecasting
        transformer: Transformador de datos
    
    Example:
        >>> service = BacktestService(model, transformer)
        >>> series = TimeSeries(values=[100, 102, 105, 103, 108, 112, 115])
        >>> result = service.simple_backtest(series, test_length=3)
        >>> result.metrics.mae < 5  # Buen modelo
        True
    """
    
    def __init__(
        self,
        model: IForecastModel,
        transformer: IDataTransformer
    ):
        """
        Inicializa el servicio.
        
        Args:
            model: Implementación de IForecastModel
            transformer: Implementación de IDataTransformer
        """
        self.model = model
        self.transformer = transformer
        logger.info("BacktestService initialized")
    
    def simple_backtest(
        self,
        series: TimeSeries,
        test_length: int,
        config: ForecastConfig = None
    ) -> BacktestResult:
        """
        Realiza un backtest simple: train/test split.
        
        Separa la serie en train (histórico) y test (validación),
        genera pronóstico para el período test y calcula métricas.
        
        Args:
            series: Serie temporal completa
            test_length: Número de puntos para test (final de la serie)
            config: Configuración del forecast (opcional)
        
        Returns:
            BacktestResult: Resultado con métricas y pronósticos
        
        Raises:
            ValueError: Si test_length >= longitud de la serie
        
        Example:
            >>> series = TimeSeries(values=[100, 102, 105, 103, 108])
            >>> result = service.simple_backtest(series, test_length=2)
            >>> len(result.forecast)
            2
        """
        logger.info(
            f"Running simple backtest for series '{series.series_id}' "
            f"(total_length={series.length}, test_length={test_length})"
        )
        
        # Validar
        if test_length >= series.length:
            raise ValueError(
                f"test_length ({test_length}) debe ser menor que "
                f"la longitud de la serie ({series.length})"
            )
        
        if test_length < 1:
            raise ValueError(f"test_length debe ser >= 1, recibido: {test_length}")
        
        # Configuración por defecto si no se proporciona
        if config is None:
            config = ForecastConfig(
                prediction_length=test_length,
                quantile_levels=[0.5],  # Solo mediana para backtest
                freq=series.freq
            )
        else:
            # Ajustar prediction_length
            config.prediction_length = test_length
        
        # Separar train/test
        train_length = series.length - test_length
        train_series = series.get_subset(0, train_length)
        test_values = series.values[train_length:]
        
        logger.debug(f"Train length: {train_length}, Test length: {test_length}")
        
        # Construir DataFrame de train
        context_df = self.transformer.build_context_df(
            values=train_series.values,
            timestamps=train_series.timestamps,
            series_id=series.series_id,
            freq=config.freq
        )
        
        # Predecir
        pred_df = self.model.predict(
            context_df=context_df,
            prediction_length=test_length,
            quantile_levels=[0.5]
        )
        
        # Parsear resultado
        result = self.transformer.parse_prediction_result(
            pred_df=pred_df,
            quantile_levels=[0.5]
        )
        
        forecast = np.array(result["median"], dtype=float)
        actuals = np.array(test_values, dtype=float)
        
        # Calcular métricas
        metrics = self._calculate_metrics(forecast, actuals)
        
        logger.info(
            f"Backtest completed: MAE={metrics.mae:.2f}, "
            f"MAPE={metrics.mape:.2f}%, RMSE={metrics.rmse:.2f}"
        )
        
        return BacktestResult(
            metrics=metrics,
            forecast=forecast.tolist(),
            actuals=actuals.tolist(),
            timestamps=result["timestamps"]
        )
    
    def _calculate_metrics(
        self,
        forecast: np.ndarray,
        actuals: np.ndarray
    ) -> BacktestMetrics:
        """
        Calcula métricas de evaluación.
        
        Args:
            forecast: Valores pronosticados
            actuals: Valores reales
        
        Returns:
            BacktestMetrics: Métricas calculadas
        """
        # MAE: Mean Absolute Error
        mae = float(np.mean(np.abs(actuals - forecast)))
        
        # MAPE: Mean Absolute Percentage Error
        eps = 1e-8
        mape = float(np.mean(np.abs((actuals - forecast) / (actuals + eps)))) * 100.0
        
        # RMSE: Root Mean Squared Error
        rmse = float(np.sqrt(np.mean((actuals - forecast) ** 2)))
        
        # WQL: Weighted Quantile Loss (para cuantil 0.5 = MAE/2)
        tau = 0.5
        diff = actuals - forecast
        wql = float(np.mean(np.maximum(tau * diff, (tau - 1) * diff)))
        
        return BacktestMetrics(
            mae=mae,
            mape=mape,
            rmse=rmse,
            wql=wql
        )
