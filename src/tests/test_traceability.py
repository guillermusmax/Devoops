"""
🥤 NovaLat - Pruebas Unitarias
Pruebas para el sistema de trazabilidad alimentaria
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.app.models.traceability import (
    TraceabilityEventCreate,
    EventType,
    TraceabilityEventResponse
)
from src.app.services.traceability_service import TraceabilityService
from src.app.models.database import DatabaseManager


class TestTraceabilityService:
    """Pruebas para el servicio de trazabilidad"""
    
    @pytest.fixture
    def db_manager(self):
        """Fixture para el gestor de base de datos"""
        return Mock(spec=DatabaseManager)
    
    @pytest.fixture
    def traceability_service(self, db_manager):
        """Fixture para el servicio de trazabilidad"""
        return TraceabilityService(db_manager)
    
    @pytest.fixture
    def sample_event_data(self):
        """Datos de ejemplo para un evento de trazabilidad"""
        return {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": EventType.PRODUCTION_START,
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Juan Pérez"
            },
            "operator_id": "OP-001",
            "equipment_id": "EQ-001"
        }
    
    @pytest.fixture
    def sample_user(self):
        """Usuario de ejemplo"""
        return {
            "id": "user-123",
            "username": "test_user",
            "role": "OPERATOR"
        }
    
    @pytest.mark.asyncio
    async def test_validate_event_data_success(self, traceability_service, sample_event_data):
        """Probar validación exitosa de datos de evento"""
        event = TraceabilityEventCreate(**sample_event_data)
        
        # No debe lanzar excepción
        await traceability_service.validate_event_data(event)
    
    @pytest.mark.asyncio
    async def test_validate_event_data_invalid_product_id(self, traceability_service, sample_event_data):
        """Probar validación con ID de producto inválido"""
        sample_event_data["product_id"] = "INVALID-001"
        event = TraceabilityEventCreate(**sample_event_data)
        
        with pytest.raises(ValueError, match="Product ID debe comenzar con NVL- o NOVALAT-"):
            await traceability_service.validate_event_data(event)
    
    @pytest.mark.asyncio
    async def test_validate_event_data_invalid_batch_id(self, traceability_service, sample_event_data):
        """Probar validación con ID de lote inválido"""
        sample_event_data["batch_id"] = "INVALID-BATCH"
        event = TraceabilityEventCreate(**sample_event_data)
        
        with pytest.raises(ValueError, match="Batch ID debe comenzar con BATCH-"):
            await traceability_service.validate_event_data(event)
    
    @pytest.mark.asyncio
    async def test_validate_event_data_missing_metadata_fields(self, traceability_service, sample_event_data):
        """Probar validación con campos faltantes en metadata"""
        sample_event_data["metadata"] = {"temperature": 25.5}  # Falta humidity
        event = TraceabilityEventCreate(**sample_event_data)
        
        with pytest.raises(ValueError, match="Campo obligatorio faltante según DIGEMAPS: humidity"):
            await traceability_service.validate_event_data(event)
    
    @pytest.mark.asyncio
    async def test_validate_event_data_invalid_temperature(self, traceability_service, sample_event_data):
        """Probar validación con temperatura fuera de rango"""
        sample_event_data["metadata"]["temperature"] = 100  # Temperatura muy alta
        event = TraceabilityEventCreate(**sample_event_data)
        
        with pytest.raises(ValueError, match="Temperatura debe estar entre -20°C y 50°C según DIGEMAPS"):
            await traceability_service.validate_event_data(event)
    
    @pytest.mark.asyncio
    async def test_create_event_success(self, traceability_service, sample_event_data, sample_user):
        """Probar creación exitosa de evento"""
        event = TraceabilityEventCreate(**sample_event_data)
        
        # Mock de la respuesta de la base de datos
        mock_db_event = Mock()
        mock_db_event.id = "evt-123e4567-e89b-12d3-a456-426614174000"
        mock_db_event.product_id = event.product_id
        mock_db_event.batch_id = event.batch_id
        mock_db_event.event_type = event.event_type.value
        mock_db_event.location = event.location
        mock_db_event.timestamp = event.timestamp
        mock_db_event.quantity = event.quantity
        mock_db_event.unit = event.unit
        mock_db_event.metadata = event.metadata
        mock_db_event.operator_id = event.operator_id
        mock_db_event.equipment_id = event.equipment_id
        mock_db_event.created_at = datetime.now(timezone.utc)
        mock_db_event.created_by = sample_user["id"]
        
        traceability_service.db.create_traceability_event = AsyncMock(return_value=mock_db_event)
        
        # Crear evento
        result = await traceability_service.create_event(event, sample_user)
        
        # Verificar resultado
        assert isinstance(result, TraceabilityEventResponse)
        assert result.id == mock_db_event.id
        assert result.product_id == event.product_id
        assert result.batch_id == event.batch_id
        assert result.event_type == event.event_type
        
        # Verificar que se llamó al método de la base de datos
        traceability_service.db.create_traceability_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_product_traceability_success(self, traceability_service, sample_user):
        """Probar obtención exitosa de trazabilidad de producto"""
        product_id = "NVL-001"
        
        # Mock de eventos de la base de datos
        mock_db_events = []
        for i in range(3):
            mock_event = Mock()
            mock_event.id = f"evt-{i}"
            mock_event.product_id = product_id
            mock_event.batch_id = "BATCH-2024-001"
            mock_event.event_type = EventType.PRODUCTION_START.value
            mock_event.location = "PLANTA-SANTO-DOMINGO"
            mock_event.timestamp = datetime.now(timezone.utc)
            mock_event.quantity = 1000.0
            mock_event.unit = "kg"
            mock_event.metadata = {"temperature": 25.5, "humidity": 60}
            mock_event.operator_id = "OP-001"
            mock_event.equipment_id = "EQ-001"
            mock_event.created_at = datetime.now(timezone.utc)
            mock_event.created_by = sample_user["id"]
            mock_db_events.append(mock_event)
        
        traceability_service.db.get_traceability_events = AsyncMock(return_value=mock_db_events)
        
        # Obtener trazabilidad
        result = await traceability_service.get_product_traceability(product_id)
        
        # Verificar resultado
        assert result is not None
        assert result.product_id == product_id
        assert len(result.events) == 3
        assert result.total_events == 3
        assert result.compliance_status == "COMPLIANT"
        assert result.quality_score is not None
        
        # Verificar que se llamó al método de la base de datos
        traceability_service.db.get_traceability_events.assert_called_once_with(
            product_id=product_id, limit=1000
        )
    
    @pytest.mark.asyncio
    async def test_get_product_traceability_no_events(self, traceability_service):
        """Probar obtención de trazabilidad sin eventos"""
        product_id = "NVL-999"
        
        traceability_service.db.get_traceability_events = AsyncMock(return_value=[])
        
        # Obtener trazabilidad
        result = await traceability_service.get_product_traceability(product_id)
        
        # Verificar resultado
        assert result is None
        
        # Verificar que se llamó al método de la base de datos
        traceability_service.db.get_traceability_events.assert_called_once_with(
            product_id=product_id, limit=1000
        )
    
    @pytest.mark.asyncio
    async def test_calculate_compliance_status_compliant(self, traceability_service):
        """Probar cálculo de estado de cumplimiento - COMPLIANT"""
        # Crear eventos que cumplan con todos los requisitos
        events = []
        for event_type in [EventType.PRODUCTION_START, EventType.QUALITY_CHECK, EventType.PACKAGING]:
            event = Mock()
            event.event_type = event_type
            event.metadata = {"temperature": 25.5, "humidity": 60, "operator": "Juan"}
            events.append(event)
        
        result = await traceability_service._calculate_compliance_status(events)
        assert result == "COMPLIANT"
    
    @pytest.mark.asyncio
    async def test_calculate_compliance_status_non_compliant(self, traceability_service):
        """Probar cálculo de estado de cumplimiento - NON_COMPLIANT"""
        # Crear eventos que no cumplan con todos los requisitos
        events = []
        event = Mock()
        event.event_type = EventType.PRODUCTION_START
        event.metadata = {"temperature": 25.5}  # Falta humidity y operator
        events.append(event)
        
        result = await traceability_service._calculate_compliance_status(events)
        assert result == "NON_COMPLIANT"
    
    @pytest.mark.asyncio
    async def test_calculate_quality_score_perfect(self, traceability_service):
        """Probar cálculo de puntuación de calidad - perfecta"""
        # Crear eventos con calidad perfecta
        events = []
        for event_type in [EventType.QUALITY_CHECK, EventType.SAFETY_INSPECTION]:
            event = Mock()
            event.event_type = event_type
            event.metadata = {"temperature": 25.5, "humidity": 60, "operator": "Juan"}
            events.append(event)
        
        result = await traceability_service._calculate_quality_score(events)
        assert result == 100.0
    
    @pytest.mark.asyncio
    async def test_calculate_quality_score_with_deductions(self, traceability_service):
        """Probar cálculo de puntuación de calidad - con deducciones"""
        # Crear eventos con problemas de calidad
        events = []
        event = Mock()
        event.event_type = EventType.PRODUCTION_START
        event.metadata = {"temperature": 25.5}  # Falta humidity y operator
        events.append(event)
        
        result = await traceability_service._calculate_quality_score(events)
        assert result < 100.0
        assert result >= 0.0
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report_compliant(self, traceability_service):
        """Probar generación de reporte de cumplimiento - compliant"""
        # Crear eventos que cumplan con todas las regulaciones
        events = []
        for event_type in [EventType.PRODUCTION_START, EventType.QUALITY_CHECK]:
            event = Mock()
            event.event_type = event_type
            event.metadata = {"temperature": 25.5, "humidity": 60, "operator": "Juan"}
            events.append(event)
        
        result = await traceability_service._generate_compliance_report(events)
        
        assert result["digemaps_compliant"] is True
        assert result["codex_compliant"] is True
        assert result["iso22000_compliant"] is True
        assert len(result["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report_with_issues(self, traceability_service):
        """Probar generación de reporte de cumplimiento - con problemas"""
        # Crear eventos con problemas de cumplimiento
        events = []
        event = Mock()
        event.event_type = EventType.PRODUCTION_START
        event.metadata = {"temperature": 100}  # Temperatura fuera de rango
        events.append(event)
        
        result = await traceability_service._generate_compliance_report(events)
        
        assert result["digemaps_compliant"] is False
        assert result["codex_compliant"] is False
        assert len(result["issues"]) > 0


class TestTraceabilityModels:
    """Pruebas para los modelos de trazabilidad"""
    
    def test_traceability_event_create_valid(self):
        """Probar creación de evento con datos válidos"""
        event_data = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": EventType.PRODUCTION_START,
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Juan Pérez"
            },
            "operator_id": "OP-001",
            "equipment_id": "EQ-001"
        }
        
        event = TraceabilityEventCreate(**event_data)
        
        assert event.product_id == "NVL-001"
        assert event.batch_id == "BATCH-2024-001"
        assert event.event_type == EventType.PRODUCTION_START
        assert event.location == "PLANTA-SANTO-DOMINGO"
        assert event.quantity == 1000.0
        assert event.unit == "kg"
        assert event.metadata["temperature"] == 25.5
        assert event.metadata["humidity"] == 60
        assert event.operator_id == "OP-001"
        assert event.equipment_id == "EQ-001"
    
    def test_traceability_event_create_invalid_product_id(self):
        """Probar creación de evento con ID de producto inválido"""
        event_data = {
            "product_id": "INVALID-001",  # ID inválido
            "batch_id": "BATCH-2024-001",
            "event_type": EventType.PRODUCTION_START,
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc),
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Juan Pérez"
            }
        }
        
        with pytest.raises(ValueError, match="Product ID debe comenzar con NVL- o NOVALAT-"):
            TraceabilityEventCreate(**event_data)
    
    def test_traceability_event_create_invalid_batch_id(self):
        """Probar creación de evento con ID de lote inválido"""
        event_data = {
            "product_id": "NVL-001",
            "batch_id": "INVALID-BATCH",  # ID inválido
            "event_type": EventType.PRODUCTION_START,
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc),
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Juan Pérez"
            }
        }
        
        with pytest.raises(ValueError, match="Batch ID debe comenzar con BATCH-"):
            TraceabilityEventCreate(**event_data)
    
    def test_traceability_event_create_invalid_temperature(self):
        """Probar creación de evento con temperatura inválida"""
        event_data = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": EventType.PRODUCTION_START,
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc),
            "metadata": {
                "temperature": 100,  # Temperatura fuera de rango
                "humidity": 60,
                "operator": "Juan Pérez"
            }
        }
        
        with pytest.raises(ValueError, match="Temperatura debe estar entre -20°C y 50°C"):
            TraceabilityEventCreate(**event_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 