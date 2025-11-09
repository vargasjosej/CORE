"""
Tests unitarios para los modelos de dominio.
"""

import pytest
from app.domain.models.time_series import TimeSeries
from app.domain.models.forecast_config import ForecastConfig
from app.domain.models.forecast_result import ForecastResult
from app.domain.models.anomaly import AnomalyPoint


class TestTimeSeries:
    """Tests para TimeSeries"""
    
    def test_create_valid_series(self):
        """Test crear serie válida"""
        series = TimeSeries(
            values=[100.0, 102.0, 105.0],
            series_id="test_series"
        )
        
        assert series.length == 3
        assert series.series_id == "test_series"
        assert series.validate()
    
    def test_empty_series_raises_error(self):
        """Test que serie vacía lanza error"""
        with pytest.raises(ValueError, match="no puede estar vacía"):
            TimeSeries(values=[])
    
    def test_non_numeric_values_raise_error(self):
        """Test que valores no numéricos lanzan error"""
        with pytest.raises(ValueError, match="numéricos"):
            TimeSeries(values=[100, "invalid", 105])
    
    def test_null_values_raise_error(self):
        """Test que valores nulos lanzan error"""
        with pytest.raises(ValueError, match="numéricos"):
            TimeSeries(values=[100.0, None, 105.0])
    
    def test_timestamps_length_mismatch(self):
        """Test que timestamps de longitud incorrecta lanzan error"""
        with pytest.raises(ValueError, match="misma longitud"):
            TimeSeries(
                values=[100, 102, 105],
                timestamps=["2025-01-01", "2025-01-02"]  # Solo 2
            )
    
    def test_get_subset(self):
        """Test obtener subset de serie"""
        series = TimeSeries(values=[100, 102, 105, 103, 108])
        subset = series.get_subset(1, 4)
        
        assert subset.length == 3
        assert subset.values == [102, 105, 103]
    
    def test_to_dict(self):
        """Test serialización a dict"""
        series = TimeSeries(values=[100, 102, 105])
        d = series.to_dict()
        
        assert d["values"] == [100, 102, 105]
        assert d["series_id"] == "series_0"
        assert d["length"] == 3


class TestForecastConfig:
    """Tests para ForecastConfig"""
    
    def test_create_valid_config(self):
        """Test crear configuración válida"""
        config = ForecastConfig(
            prediction_length=7,
            quantile_levels=[0.1, 0.5, 0.9]
        )
        
        assert config.prediction_length == 7
        assert 0.5 in config.quantile_levels
        assert config.validate()
    
    def test_invalid_prediction_length(self):
        """Test que prediction_length inválido lanza error"""
        with pytest.raises(ValueError, match="debe ser >= 1"):
            ForecastConfig(prediction_length=0)
    
    def test_quantile_out_of_range(self):
        """Test que cuantil fuera de rango lanza error"""
        with pytest.raises(ValueError, match="deben estar en"):
            ForecastConfig(
                prediction_length=7,
                quantile_levels=[0.1, 1.5]  # 1.5 > 1
            )
    
    def test_empty_quantiles(self):
        """Test que cuantiles vacíos lanzan error"""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            ForecastConfig(
                prediction_length=7,
                quantile_levels=[]
            )
    
    def test_median_auto_added(self):
        """Test que mediana se agrega automáticamente"""
        config = ForecastConfig(
            prediction_length=7,
            quantile_levels=[0.1, 0.9]  # Sin 0.5
        )
        
        assert 0.5 in config.quantile_levels
        assert config.has_median
    
    def test_quantiles_sorted(self):
        """Test que cuantiles se ordenan automáticamente"""
        config = ForecastConfig(
            prediction_length=7,
            quantile_levels=[0.9, 0.1, 0.5]
        )
        
        assert config.quantile_levels == [0.1, 0.5, 0.9]
    
    def test_default_config(self):
        """Test configuración por defecto"""
        config = ForecastConfig.default()
        
        assert config.prediction_length == 7
        assert config.quantile_levels == [0.1, 0.5, 0.9]
        assert config.freq == "D"


class TestForecastResult:
    """Tests para ForecastResult"""
    
    def test_create_valid_result(self):
        """Test crear resultado válido"""
        result = ForecastResult(
            timestamps=["2025-11-10", "2025-11-11"],
            median=[120.5, 122.3],
            quantiles={"0.1": [115.2, 116.8], "0.9": [125.8, 127.8]}
        )
        
        assert result.length == 2
        assert result.validate()
    
    def test_empty_result_raises_error(self):
        """Test que resultado vacío lanza error"""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            ForecastResult(
                timestamps=[],
                median=[],
                quantiles={}
            )
    
    def test_median_length_mismatch(self):
        """Test que longitud incorrecta de median lanza error"""
        with pytest.raises(ValueError, match="misma longitud"):
            ForecastResult(
                timestamps=["2025-11-10", "2025-11-11"],
                median=[120.5],  # Solo 1
                quantiles={}
            )
    
    def test_quantile_length_mismatch(self):
        """Test que longitud incorrecta de cuantil lanza error"""
        with pytest.raises(ValueError, match="misma longitud"):
            ForecastResult(
                timestamps=["2025-11-10", "2025-11-11"],
                median=[120.5, 122.3],
                quantiles={"0.1": [115.2]}  # Solo 1
            )
    
    def test_get_quantile(self):
        """Test obtener cuantil específico"""
        result = ForecastResult(
            timestamps=["2025-11-10"],
            median=[120.5],
            quantiles={"0.1": [115.2], "0.9": [125.8]}
        )
        
        assert result.get_quantile(0.1) == [115.2]
        assert result.get_quantile(0.9) == [125.8]
    
    def test_get_quantile_not_found(self):
        """Test que cuantil inexistente lanza error"""
        result = ForecastResult(
            timestamps=["2025-11-10"],
            median=[120.5],
            quantiles={"0.1": [115.2]}
        )
        
        with pytest.raises(KeyError, match="no encontrado"):
            result.get_quantile(0.9)
    
    def test_get_interval(self):
        """Test obtener intervalo de predicción"""
        result = ForecastResult(
            timestamps=["2025-11-10"],
            median=[120.5],
            quantiles={"0.1": [115.2], "0.9": [125.8]}
        )
        
        interval = result.get_interval(0.1, 0.9)
        
        assert interval["lower"] == [115.2]
        assert interval["median"] == [120.5]
        assert interval["upper"] == [125.8]


class TestAnomalyPoint:
    """Tests para AnomalyPoint"""
    
    def test_create_anomaly(self):
        """Test crear punto de anomalía"""
        point = AnomalyPoint(
            index=0,
            value=200.0,
            expected=120.0,
            lower_bound=115.0,
            upper_bound=125.0,
            is_anomaly=True,
            z_score=4.5
        )
        
        assert point.is_anomaly
        assert point.deviation == 80.0
        assert point.severity == "high"
    
    def test_severity_high(self):
        """Test severidad alta (z_score >= 4)"""
        point = AnomalyPoint(
            index=0, value=200, expected=120,
            lower_bound=115, upper_bound=125,
            is_anomaly=True, z_score=4.5
        )
        
        assert point.severity == "high"
    
    def test_severity_medium(self):
        """Test severidad media (3 <= z_score < 4)"""
        point = AnomalyPoint(
            index=0, value=200, expected=120,
            lower_bound=115, upper_bound=125,
            is_anomaly=True, z_score=3.5
        )
        
        assert point.severity == "medium"
    
    def test_severity_low(self):
        """Test severidad baja (z_score < 3)"""
        point = AnomalyPoint(
            index=0, value=200, expected=120,
            lower_bound=115, upper_bound=125,
            is_anomaly=True, z_score=2.5
        )
        
        assert point.severity == "low"
    
    def test_deviation_percentage(self):
        """Test cálculo de porcentaje de desviación"""
        point = AnomalyPoint(
            index=0, value=150, expected=100,
            lower_bound=95, upper_bound=105,
            is_anomaly=True, z_score=3.0
        )
        
        assert point.deviation_percentage == 50.0  # 50% de desviación
    
    def test_is_above_expected(self):
        """Test verificar si está arriba del esperado"""
        point = AnomalyPoint(
            index=0, value=150, expected=100,
            lower_bound=95, upper_bound=105,
            is_anomaly=True, z_score=3.0
        )
        
        assert point.is_above_expected()
        assert not point.is_below_expected()
    
    def test_to_dict(self):
        """Test serialización a dict"""
        point = AnomalyPoint(
            index=0, value=150, expected=100,
            lower_bound=95, upper_bound=105,
            is_anomaly=True, z_score=3.0
        )
        
        d = point.to_dict()
        
        assert d["index"] == 0
        assert d["value"] == 150
        assert d["is_anomaly"] is True
        assert "deviation" in d
        assert "severity" in d
