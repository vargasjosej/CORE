"""
Tests unitarios para las interfaces del dominio.
"""

import pytest
import pandas as pd
from abc import ABC
from app.domain.interfaces.forecast_model import IForecastModel
from app.domain.interfaces.data_transformer import IDataTransformer


class TestIForecastModel:
    """Tests para la interface IForecastModel"""
    
    def test_is_abstract(self):
        """Verifica que IForecastModel sea una clase abstracta"""
        assert issubclass(IForecastModel, ABC)
    
    def test_cannot_instantiate(self):
        """Verifica que no se pueda instanciar directamente"""
        with pytest.raises(TypeError):
            IForecastModel()
    
    def test_validate_context_success(self):
        """Verifica que validate_context funcione con datos válidos"""
        # Crear una implementación dummy para testing
        class DummyModel(IForecastModel):
            def predict(self, context_df, prediction_length, quantile_levels, **kwargs):
                return pd.DataFrame()
            
            def get_model_info(self):
                return {}
        
        model = DummyModel()
        
        # DataFrame válido
        df = pd.DataFrame({
            "id": ["series_0"] * 5,
            "timestamp": pd.date_range("2025-01-01", periods=5),
            "target": [100.0, 102.0, 105.0, 103.0, 108.0]
        })
        
        assert model.validate_context(df) is True
    
    def test_validate_context_missing_columns(self):
        """Verifica que validate_context falle con columnas faltantes"""
        class DummyModel(IForecastModel):
            def predict(self, context_df, prediction_length, quantile_levels, **kwargs):
                return pd.DataFrame()
            
            def get_model_info(self):
                return {}
        
        model = DummyModel()
        
        # DataFrame sin columna 'target'
        df = pd.DataFrame({
            "id": ["series_0"] * 5,
            "timestamp": pd.date_range("2025-01-01", periods=5)
        })
        
        with pytest.raises(ValueError, match="Faltan columnas requeridas"):
            model.validate_context(df)
    
    def test_validate_context_empty_dataframe(self):
        """Verifica que validate_context falle con DataFrame vacío"""
        class DummyModel(IForecastModel):
            def predict(self, context_df, prediction_length, quantile_levels, **kwargs):
                return pd.DataFrame()
            
            def get_model_info(self):
                return {}
        
        model = DummyModel()
        
        df = pd.DataFrame(columns=["id", "timestamp", "target"])
        
        with pytest.raises(ValueError, match="no puede estar vacío"):
            model.validate_context(df)
    
    def test_validate_context_null_values(self):
        """Verifica que validate_context falle con valores nulos en target"""
        class DummyModel(IForecastModel):
            def predict(self, context_df, prediction_length, quantile_levels, **kwargs):
                return pd.DataFrame()
            
            def get_model_info(self):
                return {}
        
        model = DummyModel()
        
        df = pd.DataFrame({
            "id": ["series_0"] * 5,
            "timestamp": pd.date_range("2025-01-01", periods=5),
            "target": [100.0, None, 105.0, 103.0, 108.0]
        })
        
        with pytest.raises(ValueError, match="valores nulos"):
            model.validate_context(df)


class TestIDataTransformer:
    """Tests para la interface IDataTransformer"""
    
    def test_is_abstract(self):
        """Verifica que IDataTransformer sea una clase abstracta"""
        assert issubclass(IDataTransformer, ABC)
    
    def test_cannot_instantiate(self):
        """Verifica que no se pueda instanciar directamente"""
        with pytest.raises(TypeError):
            IDataTransformer()
