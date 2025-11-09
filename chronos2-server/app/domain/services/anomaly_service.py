"""
Servicio de dominio para detección de anomalías.

Este servicio encapsula la lógica de detección de anomalías,
cumpliendo con SRP y DIP.
"""

from typing import List
from app.domain.interfaces.forecast_model import IForecastModel
from app.domain.interfaces.data_transformer import IDataTransformer
from app.domain.models.time_series import TimeSeries
from app.domain.models.forecast_config import ForecastConfig
from app.domain.models.anomaly import AnomalyPoint
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AnomalyService:
    """
    Servicio de dominio para detección de anomalías.
    
    Detecta puntos anómalos comparando valores observados con
    pronósticos del modelo, usando intervalos de predicción.
    
    Attributes:
        model: Modelo de forecasting
        transformer: Transformador de datos
    
    Example:
        >>> service = AnomalyService(model, transformer)
        >>> context = TimeSeries(values=[100, 102, 105, 103, 108])
        >>> recent = [107, 200, 106]  # 200 es anomalía
        >>> anomalies = service.detect_anomalies(context, recent, config)
        >>> sum(1 for a in anomalies if a.is_anomaly)
        1
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
        logger.info("AnomalyService initialized")
    
    def detect_anomalies(
        self,
        context: TimeSeries,
        recent_observed: List[float],
        config: ForecastConfig,
        quantile_low: float = 0.05,
        quantile_high: float = 0.95
    ) -> List[AnomalyPoint]:
        """
        Detecta anomalías comparando observaciones con pronóstico.
        
        Un punto se considera anómalo si cae fuera del intervalo
        [quantile_low, quantile_high] del pronóstico.
        
        Args:
            context: Serie temporal histórica (contexto)
            recent_observed: Valores recientes a evaluar
            config: Configuración del forecast
            quantile_low: Cuantil inferior del intervalo (default: 0.05)
            quantile_high: Cuantil superior del intervalo (default: 0.95)
        
        Returns:
            List[AnomalyPoint]: Lista de puntos con indicador de anomalía
        
        Raises:
            ValueError: Si las longitudes no coinciden
        
        Example:
            >>> context = TimeSeries(values=[100, 102, 105])
            >>> recent = [106, 250, 104]  # 250 es anomalía
            >>> config = ForecastConfig(prediction_length=3)
            >>> anomalies = service.detect_anomalies(context, recent, config)
            >>> anomalies[1].is_anomaly
            True
        """
        logger.info(
            f"Detecting anomalies in {len(recent_observed)} points "
            f"(interval: [{quantile_low}, {quantile_high}])"
        )
        
        # Validar longitudes
        if len(recent_observed) != config.prediction_length:
            raise ValueError(
                f"recent_observed length ({len(recent_observed)}) must equal "
                f"prediction_length ({config.prediction_length})"
            )
        
        # Preparar config con cuantiles necesarios
        quantiles = sorted(set([quantile_low, 0.5, quantile_high]))
        config_anomaly = ForecastConfig(
            prediction_length=config.prediction_length,
            quantile_levels=quantiles,
            freq=config.freq
        )
        
        # Construir DataFrame de contexto
        context_df = self.transformer.build_context_df(
            values=context.values,
            timestamps=context.timestamps,
            series_id=context.series_id,
            freq=config.freq
        )
        
        # Predecir
        pred_df = self.model.predict(
            context_df=context_df,
            prediction_length=config_anomaly.prediction_length,
            quantile_levels=config_anomaly.quantile_levels
        )
        
        # Parsear resultado
        result = self.transformer.parse_prediction_result(
            pred_df=pred_df,
            quantile_levels=quantiles
        )
        
        # Detectar anomalías
        anomalies = []
        q_low_key = f"{quantile_low:.3g}"
        q_high_key = f"{quantile_high:.3g}"
        
        for i, obs in enumerate(recent_observed):
            expected = result["median"][i]
            lower = result["quantiles"][q_low_key][i]
            upper = result["quantiles"][q_high_key][i]
            
            # Verificar si está fuera del intervalo
            is_anom = (obs < lower) or (obs > upper)
            
            # Calcular z-score aproximado
            spread = (upper - lower) / 2
            z_score = abs(obs - expected) / (spread + 1e-8) if spread > 0 else 0
            
            anomalies.append(AnomalyPoint(
                index=i,
                value=obs,
                expected=expected,
                lower_bound=lower,
                upper_bound=upper,
                is_anomaly=is_anom,
                z_score=z_score
            ))
        
        num_anomalies = sum(1 for a in anomalies if a.is_anomaly)
        logger.info(
            f"Anomaly detection completed: {num_anomalies}/{len(anomalies)} "
            "anomalies detected"
        )
        
        return anomalies
    
    def get_anomaly_summary(self, anomalies: List[AnomalyPoint]) -> dict:
        """
        Genera un resumen de las anomalías detectadas.
        
        Args:
            anomalies: Lista de anomalías
        
        Returns:
            Dict con estadísticas de las anomalías
        """
        total = len(anomalies)
        detected = sum(1 for a in anomalies if a.is_anomaly)
        
        severities = {"low": 0, "medium": 0, "high": 0}
        for a in anomalies:
            if a.is_anomaly and a.severity:
                severities[a.severity] += 1
        
        return {
            "total_points": total,
            "anomalies_detected": detected,
            "anomaly_rate": (detected / total * 100) if total > 0 else 0,
            "severities": severities,
            "max_deviation": max((a.deviation for a in anomalies), default=0),
            "max_z_score": max((abs(a.z_score) for a in anomalies), default=0)
        }
