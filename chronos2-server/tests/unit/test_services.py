"""
Tests unitarios para los servicios de dominio.

Estos tests usan mocks para las dependencias (model, transformer)
siguiendo el principio DIP.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from app.domain.services.forecast_service import ForecastService
from app.domain.services.anomaly_service import AnomalyService
from app.domain.services.backtest_service import BacktestService, BacktestMetrics
from app.domain.models.time_series import TimeSeries
from app.domain.models.forecast_config import ForecastConfig


# Fixtures compartidos

@pytest.fixture
def mock_model():
    """Mock del modelo de forecasting"""
    model = Mock()
    model.get_model_info.return_value = {
        "type": "TestModel",
        "model_id": "test-model-v1"
    }
    
    # Mock del DataFrame de predicción
    pred_df = pd.DataFrame({
        "id": ["series_0"] * 3,
        "timestamp": ["2025-11-10", "2025-11-11", "2025-11-12"],
        "predictions": [120.0, 122.0, 124.0],
        "0.1": [115.0, 117.0, 119.0],
        "0.9": [125.0, 127.0, 129.0]
    })
    model.predict.return_value = pred_df
    model.validate_context.return_value = True
    
    return model


@pytest.fixture
def mock_transformer():
    """Mock del transformador de datos"""
    transformer = Mock()
    
    # Mock build_context_df
    transformer.build_context_df.return_value = pd.DataFrame({
        "id": ["series_0"] * 5,
        "timestamp": [0, 1, 2, 3, 4],
        "target": [100.0, 102.0, 105.0, 103.0, 108.0]
    })
    
    # Mock parse_prediction_result con todos los cuantiles posibles
    transformer.parse_prediction_result.return_value = {
        "timestamps": ["2025-11-10", "2025-11-11", "2025-11-12"],
        "median": [120.0, 122.0, 124.0],
        "quantiles": {
            "0.05": [110.0, 112.0, 114.0],
            "0.1": [115.0, 117.0, 119.0],
            "0.5": [120.0, 122.0, 124.0],
            "0.9": [125.0, 127.0, 129.0],
            "0.95": [130.0, 132.0, 134.0]
        }
    }
    
    return transformer


# Tests de ForecastService

class TestForecastService:
    """Tests para ForecastService"""
    
    def test_init_service(self, mock_model, mock_transformer):
        """Test inicialización del servicio"""
        service = ForecastService(mock_model, mock_transformer)
        
        assert service.model is mock_model
        assert service.transformer is mock_transformer
    
    def test_forecast_univariate_success(self, mock_model, mock_transformer):
        """Test forecast univariado exitoso"""
        service = ForecastService(mock_model, mock_transformer)
        
        series = TimeSeries(
            values=[100.0, 102.0, 105.0, 103.0, 108.0],
            series_id="test_series"
        )
        config = ForecastConfig(
            prediction_length=3,
            quantile_levels=[0.1, 0.5, 0.9]
        )
        
        result = service.forecast_univariate(series, config)
        
        # Verificar que se llamaron los métodos
        mock_transformer.build_context_df.assert_called_once()
        mock_model.validate_context.assert_called_once()
        mock_model.predict.assert_called_once()
        mock_transformer.parse_prediction_result.assert_called_once()
        
        # Verificar resultado
        assert result.length == 3
        assert result.series_id == "test_series"
        assert result.median == [120.0, 122.0, 124.0]
        assert "0.1" in result.quantiles
        assert "0.9" in result.quantiles
    
    def test_forecast_univariate_invalid_series(self, mock_model, mock_transformer):
        """Test que serie inválida lanza error"""
        service = ForecastService(mock_model, mock_transformer)
        
        with pytest.raises(ValueError):
            series = TimeSeries(values=[])  # Vacía
    
    def test_forecast_multi_series(self, mock_model, mock_transformer):
        """Test forecast para múltiples series"""
        service = ForecastService(mock_model, mock_transformer)
        
        series1 = TimeSeries(values=[100, 102, 105], series_id="A")
        series2 = TimeSeries(values=[200, 205, 210], series_id="B")
        config = ForecastConfig(prediction_length=3)
        
        results = service.forecast_multi_series([series1, series2], config)
        
        assert len(results) == 2
        assert results[0].series_id == "A"
        assert results[1].series_id == "B"
    
    def test_forecast_multi_series_empty_list(self, mock_model, mock_transformer):
        """Test que lista vacía lanza error"""
        service = ForecastService(mock_model, mock_transformer)
        
        with pytest.raises(ValueError, match="no puede estar vacía"):
            service.forecast_multi_series([], ForecastConfig.default())


# Tests de AnomalyService

class TestAnomalyService:
    """Tests para AnomalyService"""
    
    def test_init_service(self, mock_model, mock_transformer):
        """Test inicialización del servicio"""
        service = AnomalyService(mock_model, mock_transformer)
        
        assert service.model is mock_model
        assert service.transformer is mock_transformer
    
    def test_detect_anomalies_success(self, mock_model, mock_transformer):
        """Test detección de anomalías exitosa"""
        service = AnomalyService(mock_model, mock_transformer)
        
        context = TimeSeries(values=[100, 102, 105, 103, 108])
        recent = [107.0, 200.0, 106.0]  # 200 debería ser anomalía
        config = ForecastConfig(prediction_length=3)
        
        anomalies = service.detect_anomalies(
            context, recent, config,
            quantile_low=0.05, quantile_high=0.95
        )
        
        assert len(anomalies) == 3
        assert all(hasattr(a, 'is_anomaly') for a in anomalies)
        assert all(hasattr(a, 'z_score') for a in anomalies)
    
    def test_detect_anomalies_length_mismatch(self, mock_model, mock_transformer):
        """Test que longitudes diferentes lanzan error"""
        service = AnomalyService(mock_model, mock_transformer)
        
        context = TimeSeries(values=[100, 102, 105])
        recent = [107, 108]  # 2 valores
        config = ForecastConfig(prediction_length=3)  # Espera 3
        
        with pytest.raises(ValueError, match="must equal"):
            service.detect_anomalies(context, recent, config)
    
    def test_get_anomaly_summary(self, mock_model, mock_transformer):
        """Test resumen de anomalías"""
        service = AnomalyService(mock_model, mock_transformer)
        
        # Crear anomalías de prueba
        from app.domain.models.anomaly import AnomalyPoint
        anomalies = [
            AnomalyPoint(0, 100, 100, 95, 105, False, 1.0),
            AnomalyPoint(1, 200, 100, 95, 105, True, 4.5),
            AnomalyPoint(2, 102, 100, 95, 105, False, 0.5),
        ]
        
        summary = service.get_anomaly_summary(anomalies)
        
        assert summary["total_points"] == 3
        assert summary["anomalies_detected"] == 1
        assert summary["anomaly_rate"] > 0
        assert "severities" in summary


# Tests de BacktestService

class TestBacktestService:
    """Tests para BacktestService"""
    
    def test_init_service(self, mock_model, mock_transformer):
        """Test inicialización del servicio"""
        service = BacktestService(mock_model, mock_transformer)
        
        assert service.model is mock_model
        assert service.transformer is mock_transformer
    
    def test_simple_backtest_success(self, mock_model, mock_transformer):
        """Test backtest simple exitoso"""
        service = BacktestService(mock_model, mock_transformer)
        
        # Serie con valores conocidos
        series = TimeSeries(
            values=[100, 102, 105, 103, 108, 112, 115],
            series_id="test"
        )
        
        result = service.simple_backtest(series, test_length=3)
        
        # Verificar que se llamaron los métodos
        mock_transformer.build_context_df.assert_called_once()
        mock_model.predict.assert_called_once()
        
        # Verificar resultado
        assert isinstance(result.metrics, BacktestMetrics)
        assert len(result.forecast) == 3
        assert len(result.actuals) == 3
        assert result.metrics.mae >= 0
        assert result.metrics.mape >= 0
        assert result.metrics.rmse >= 0
    
    def test_simple_backtest_invalid_test_length(self, mock_model, mock_transformer):
        """Test que test_length inválido lanza error"""
        service = BacktestService(mock_model, mock_transformer)
        
        series = TimeSeries(values=[100, 102, 105])
        
        # test_length >= series.length
        with pytest.raises(ValueError, match="debe ser menor"):
            service.simple_backtest(series, test_length=5)
        
        # test_length < 1
        with pytest.raises(ValueError, match="debe ser >= 1"):
            service.simple_backtest(series, test_length=0)
    
    def test_calculate_metrics(self, mock_model, mock_transformer):
        """Test cálculo de métricas"""
        import numpy as np
        service = BacktestService(mock_model, mock_transformer)
        
        forecast = np.array([100.0, 102.0, 105.0])
        actuals = np.array([100.0, 100.0, 110.0])
        
        metrics = service._calculate_metrics(forecast, actuals)
        
        assert isinstance(metrics, BacktestMetrics)
        assert metrics.mae > 0  # Hay error
        assert metrics.rmse > 0
        assert 0 <= metrics.mape <= 100  # Porcentaje


# Tests de BacktestMetrics

class TestBacktestMetrics:
    """Tests para BacktestMetrics"""
    
    def test_create_metrics(self):
        """Test crear métricas"""
        metrics = BacktestMetrics(
            mae=2.5,
            mape=5.0,
            rmse=3.0,
            wql=1.25
        )
        
        assert metrics.mae == 2.5
        assert metrics.mape == 5.0
        assert metrics.rmse == 3.0
        assert metrics.wql == 1.25
    
    def test_to_dict(self):
        """Test serialización"""
        metrics = BacktestMetrics(mae=2.5, mape=5.0, rmse=3.0, wql=1.25)
        d = metrics.to_dict()
        
        assert d["mae"] == 2.5
        assert d["mape"] == 5.0
        assert d["rmse"] == 3.0
        assert d["wql"] == 1.25
