"""
Servicio de dominio para forecasting.

Este servicio orquesta la lógica de negocio de forecasting,
cumpliendo con SRP y DIP.
"""

from typing import List
from app.domain.interfaces.forecast_model import IForecastModel
from app.domain.interfaces.data_transformer import IDataTransformer
from app.domain.models.time_series import TimeSeries
from app.domain.models.forecast_config import ForecastConfig
from app.domain.models.forecast_result import ForecastResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ForecastService:
    """
    Servicio de dominio para operaciones de forecasting.
    
    Este servicio encapsula la lógica de negocio para generar pronósticos,
    dependiendo de abstracciones (IForecastModel, IDataTransformer) en lugar
    de implementaciones concretas (DIP).
    
    Attributes:
        model: Modelo de forecasting (implementa IForecastModel)
        transformer: Transformador de datos (implementa IDataTransformer)
    
    Example:
        >>> from app.infrastructure.ml.chronos_model import ChronosModel
        >>> from app.utils.dataframe_builder import DataFrameBuilder
        >>> 
        >>> model = ChronosModel("amazon/chronos-2")
        >>> transformer = DataFrameBuilder()
        >>> service = ForecastService(model, transformer)
        >>> 
        >>> series = TimeSeries(values=[100, 102, 105])
        >>> config = ForecastConfig(prediction_length=3)
        >>> result = service.forecast_univariate(series, config)
    """
    
    def __init__(
        self,
        model: IForecastModel,
        transformer: IDataTransformer
    ):
        """
        Inicializa el servicio con sus dependencias.
        
        Args:
            model: Implementación de IForecastModel
            transformer: Implementación de IDataTransformer
        """
        self.model = model
        self.transformer = transformer
        
        model_info = self.model.get_model_info()
        logger.info(
            f"ForecastService initialized with model: {model_info.get('type', 'unknown')}"
        )
    
    def forecast_univariate(
        self,
        series: TimeSeries,
        config: ForecastConfig
    ) -> ForecastResult:
        """
        Genera pronóstico para una serie univariada.
        
        Args:
            series: Serie temporal a pronosticar
            config: Configuración del forecast
        
        Returns:
            ForecastResult: Resultado con pronósticos
        
        Raises:
            ValueError: Si la serie o configuración son inválidas
            RuntimeError: Si el modelo falla al predecir
        
        Example:
            >>> series = TimeSeries(values=[100, 102, 105, 103, 108])
            >>> config = ForecastConfig(prediction_length=3)
            >>> result = service.forecast_univariate(series, config)
            >>> len(result.median)
            3
        """
        logger.info(
            f"Forecasting univariate series '{series.series_id}' "
            f"(length={series.length}, horizon={config.prediction_length})"
        )
        
        # Validar entrada
        series.validate()
        config.validate()
        
        # Transformar serie a DataFrame
        context_df = self.transformer.build_context_df(
            values=series.values,
            timestamps=series.timestamps,
            series_id=series.series_id,
            freq=config.freq
        )
        
        logger.debug(f"Context DataFrame shape: {context_df.shape}")
        
        # Validar DataFrame
        self.model.validate_context(context_df)
        
        # Predecir
        try:
            pred_df = self.model.predict(
                context_df=context_df,
                prediction_length=config.prediction_length,
                quantile_levels=config.quantile_levels
            )
        except Exception as e:
            logger.error(f"Model prediction failed: {e}", exc_info=True)
            raise RuntimeError(f"Error al predecir: {e}") from e
        
        logger.debug(f"Prediction DataFrame shape: {pred_df.shape}")
        
        # Parsear resultado
        result_dict = self.transformer.parse_prediction_result(
            pred_df=pred_df,
            quantile_levels=config.quantile_levels
        )
        
        # Crear ForecastResult
        result = ForecastResult(
            timestamps=result_dict["timestamps"],
            median=result_dict["median"],
            quantiles=result_dict["quantiles"],
            series_id=series.series_id,
            metadata={
                "prediction_length": config.prediction_length,
                "quantile_levels": config.quantile_levels,
                "freq": config.freq,
                "model": self.model.get_model_info()
            }
        )
        
        logger.info(
            f"Forecast completed: {result.length} periods generated "
            f"for series '{series.series_id}'"
        )
        
        return result
    
    def forecast_multi_series(
        self,
        series_list: List[TimeSeries],
        config: ForecastConfig
    ) -> List[ForecastResult]:
        """
        Genera pronósticos para múltiples series.
        
        Args:
            series_list: Lista de series temporales
            config: Configuración del forecast (misma para todas)
        
        Returns:
            List[ForecastResult]: Lista de resultados (uno por serie)
        
        Example:
            >>> series1 = TimeSeries(values=[100, 102], series_id="A")
            >>> series2 = TimeSeries(values=[200, 205], series_id="B")
            >>> results = service.forecast_multi_series([series1, series2], config)
            >>> len(results)
            2
        """
        logger.info(f"Forecasting {len(series_list)} series")
        
        if not series_list:
            raise ValueError("series_list no puede estar vacía")
        
        results = []
        for i, series in enumerate(series_list):
            logger.debug(f"Processing series {i+1}/{len(series_list)}: {series.series_id}")
            
            try:
                result = self.forecast_univariate(series, config)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to forecast series '{series.series_id}': {e}",
                    exc_info=True
                )
                raise
        
        logger.info(f"Multi-series forecast completed: {len(results)} series processed")
        return results
