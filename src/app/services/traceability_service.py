"""
🥤 NovaLat - Servicio de Trazabilidad Alimentaria
Servicio para gestión de trazabilidad con cumplimiento regulatorio
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from ..models.traceability import (
    TraceabilityEventCreate,
    TraceabilityEventResponse,
    ProductTraceability,
    BatchTraceability,
    EventType
)
from ..models.database import DatabaseManager, TraceabilityEventDB

logger = logging.getLogger(__name__)

class TraceabilityService:
    """Servicio de trazabilidad alimentaria para NovaLat"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
        
        # Configuración de cumplimiento regulatorio
        self.regulatory_config = {
            "digemaps": {
                "required_fields": ["temperature", "humidity", "operator"],
                "temperature_range": (-20, 50),
                "humidity_range": (0, 100),
                "retention_period_days": 2555  # 7 años según DIGEMAPS
            },
            "codex": {
                "required_fields": ["temperature", "humidity"],
                "temperature_range": (-18, 50),
                "quality_checks_required": True
            },
            "iso22000": {
                "haccp_required": True,
                "documentation_required": True,
                "audit_trail_required": True
            }
        }
    
    async def validate_event_data(self, event: TraceabilityEventCreate) -> None:
        """
        Validar datos del evento según regulaciones alimentarias
        
        Cumple con:
        - DIGEMAPS (República Dominicana)
        - Codex Alimentarius
        - ISO 22000
        """
        self.logger.info(f"Validando evento de trazabilidad: {event.event_type}")
        
        # Validaciones básicas
        if not event.product_id or not event.batch_id:
            raise ValueError("Product ID y Batch ID son obligatorios")
        
        # Validar formato de IDs según estándares NovaLat
        if not event.product_id.startswith(('NVL-', 'NOVALAT-')):
            raise ValueError("Product ID debe comenzar con NVL- o NOVALAT-")
        
        if not event.batch_id.startswith('BATCH-'):
            raise ValueError("Batch ID debe comenzar con BATCH-")
        
        # Validar metadatos según DIGEMAPS
        if event.metadata:
            await self._validate_digemaps_requirements(event.metadata)
            await self._validate_codex_requirements(event.metadata)
        
        # Validar ubicación
        if not event.location or len(event.location.strip()) == 0:
            raise ValueError("Ubicación es obligatoria")
        
        # Validar timestamp
        if event.timestamp > datetime.now(timezone.utc) + timedelta(hours=1):
            raise ValueError("Timestamp no puede ser en el futuro")
        
        # Validar cantidad si está presente
        if event.quantity is not None and event.quantity <= 0:
            raise ValueError("Cantidad debe ser mayor a 0")
        
        self.logger.info("✅ Validación de evento completada exitosamente")
    
    async def _validate_digemaps_requirements(self, metadata: Dict[str, Any]) -> None:
        """Validar requisitos específicos de DIGEMAPS"""
        required_fields = self.regulatory_config["digemaps"]["required_fields"]
        
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Campo obligatorio faltante según DIGEMAPS: {field}")
        
        # Validar rangos de temperatura
        if "temperature" in metadata:
            temp = metadata["temperature"]
            min_temp, max_temp = self.regulatory_config["digemaps"]["temperature_range"]
            
            if not isinstance(temp, (int, float)) or temp < min_temp or temp > max_temp:
                raise ValueError(f"Temperatura debe estar entre {min_temp}°C y {max_temp}°C según DIGEMAPS")
        
        # Validar rangos de humedad
        if "humidity" in metadata:
            humidity = metadata["humidity"]
            min_humidity, max_humidity = self.regulatory_config["digemaps"]["humidity_range"]
            
            if not isinstance(humidity, (int, float)) or humidity < min_humidity or humidity > max_humidity:
                raise ValueError(f"Humedad debe estar entre {min_humidity}% y {max_humidity}% según DIGEMAPS")
    
    async def _validate_codex_requirements(self, metadata: Dict[str, Any]) -> None:
        """Validar requisitos específicos de Codex Alimentarius"""
        required_fields = self.regulatory_config["codex"]["required_fields"]
        
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Campo obligatorio faltante según Codex: {field}")
        
        # Validar rangos de temperatura según Codex
        if "temperature" in metadata:
            temp = metadata["temperature"]
            min_temp, max_temp = self.regulatory_config["codex"]["temperature_range"]
            
            if not isinstance(temp, (int, float)) or temp < min_temp or temp > max_temp:
                raise ValueError(f"Temperatura debe estar entre {min_temp}°C y {max_temp}°C según Codex")
    
    async def create_event(self, event: TraceabilityEventCreate, user: Dict[str, Any]) -> TraceabilityEventResponse:
        """Crear un nuevo evento de trazabilidad"""
        try:
            # Validar datos del evento
            await self.validate_event_data(event)
            
            # Preparar datos para la base de datos
            event_data = {
                "product_id": event.product_id,
                "batch_id": event.batch_id,
                "event_type": event.event_type.value,
                "location": event.location,
                "timestamp": event.timestamp,
                "quantity": event.quantity,
                "unit": event.unit,
                "metadata": event.metadata,
                "operator_id": event.operator_id,
                "equipment_id": event.equipment_id
            }
            
            # Crear evento en base de datos
            db_event = await self.db.create_traceability_event(event_data, user["id"])
            
            # Convertir a respuesta
            response = TraceabilityEventResponse(
                id=str(db_event.id),
                product_id=db_event.product_id,
                batch_id=db_event.batch_id,
                event_type=EventType(db_event.event_type),
                location=db_event.location,
                timestamp=db_event.timestamp,
                quantity=db_event.quantity,
                unit=db_event.unit,
                metadata=db_event.event_metadata or {},
                operator_id=db_event.operator_id,
                equipment_id=db_event.equipment_id,
                created_at=db_event.created_at,
                created_by=db_event.created_by
            )
            
            self.logger.info(f"Evento de trazabilidad creado exitosamente: {response.id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error al crear evento de trazabilidad: {e}")
            raise
    
    async def get_product_traceability(self, product_id: str) -> Optional[ProductTraceability]:
        """Obtener trazabilidad completa de un producto"""
        try:
            # Obtener eventos del producto
            events_db = await self.db.get_traceability_events(product_id=product_id, limit=1000)
            
            if not events_db:
                return None
            
            # Convertir eventos a respuesta
            events = []
            for event_db in events_db:
                event = TraceabilityEventResponse(
                    id=str(event_db.id),
                    product_id=event_db.product_id,
                    batch_id=event_db.batch_id,
                    event_type=EventType(event_db.event_type),
                    location=event_db.location,
                    timestamp=event_db.timestamp,
                    quantity=event_db.quantity,
                    unit=event_db.unit,
                    metadata=event_db.event_metadata or {},
                    operator_id=event_db.operator_id,
                    equipment_id=event_db.equipment_id,
                    created_at=event_db.created_at,
                    created_by=event_db.created_by
                )
                events.append(event)
            
            # Calcular métricas de cumplimiento
            compliance_status = await self._calculate_compliance_status(events)
            quality_score = await self._calculate_quality_score(events)
            
            # Obtener información del producto (simulado)
            product_name = await self._get_product_name(product_id)
            
            # Obtener batch ID del primer evento
            batch_id = events[0].batch_id if events else None
            
            # Calcular fechas
            first_event = min(events, key=lambda x: x.timestamp).timestamp if events else None
            last_event = max(events, key=lambda x: x.timestamp).timestamp if events else None
            
            traceability = ProductTraceability(
                product_id=product_id,
                product_name=product_name,
                batch_id=batch_id,
                events=events,
                total_events=len(events),
                first_event=first_event,
                last_event=last_event,
                compliance_status=compliance_status,
                quality_score=quality_score
            )
            
            self.logger.info(f"Trazabilidad obtenida para producto {product_id}: {len(events)} eventos")
            return traceability
            
        except Exception as e:
            self.logger.error(f"Error al obtener trazabilidad del producto {product_id}: {e}")
            raise
    
    async def get_batch_traceability(self, batch_id: str) -> Optional[BatchTraceability]:
        """Obtener trazabilidad de un lote específico"""
        try:
            # Obtener eventos del lote
            events_db = await self.db.get_traceability_events(batch_id=batch_id, limit=1000)
            
            if not events_db:
                return None
            
            # Convertir eventos a respuesta
            events = []
            for event_db in events_db:
                event = TraceabilityEventResponse(
                    id=str(event_db.id),
                    product_id=event_db.product_id,
                    batch_id=event_db.batch_id,
                    event_type=EventType(event_db.event_type),
                    location=event_db.location,
                    timestamp=event_db.timestamp,
                    quantity=event_db.quantity,
                    unit=event_db.unit,
                    metadata=event_db.event_metadata or {},
                    operator_id=event_db.operator_id,
                    equipment_id=event_db.equipment_id,
                    created_at=event_db.created_at,
                    created_by=event_db.created_by
                )
                events.append(event)
            
            # Obtener información del lote
            product_id = events[0].product_id if events else None
            
            # Calcular ubicaciones visitadas
            locations_visited = list(set([event.location for event in events]))
            
            # Filtrar eventos de calidad y seguridad
            quality_checks = [event for event in events if event.event_type == EventType.QUALITY_CHECK]
            safety_inspections = [event for event in events if event.event_type == EventType.SAFETY_INSPECTION]
            
            # Generar reporte de cumplimiento
            compliance_report = await self._generate_compliance_report(events)
            
            # Obtener fechas de producción y expiración (simulado)
            production_date = await self._get_batch_production_date(batch_id)
            expiration_date = await self._get_batch_expiration_date(batch_id)
            
            traceability = BatchTraceability(
                batch_id=batch_id,
                product_id=product_id,
                production_date=production_date,
                expiration_date=expiration_date,
                events=events,
                total_events=len(events),
                locations_visited=locations_visited,
                quality_checks=quality_checks,
                safety_inspections=safety_inspections,
                compliance_report=compliance_report
            )
            
            self.logger.info(f"Trazabilidad obtenida para lote {batch_id}: {len(events)} eventos")
            return traceability
            
        except Exception as e:
            self.logger.error(f"Error al obtener trazabilidad del lote {batch_id}: {e}")
            raise
    
    async def list_events(
        self,
        product_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TraceabilityEventResponse]:
        """Listar eventos de trazabilidad con filtros"""
        try:
            events_db = await self.db.get_traceability_events(
                product_id=product_id,
                batch_id=batch_id,
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            
            events = []
            for event_db in events_db:
                event = TraceabilityEventResponse(
                    id=str(event_db.id),
                    product_id=event_db.product_id,
                    batch_id=event_db.batch_id,
                    event_type=EventType(event_db.event_type),
                    location=event_db.location,
                    timestamp=event_db.timestamp,
                    quantity=event_db.quantity,
                    unit=event_db.unit,
                    metadata=event_db.event_metadata or {},
                    operator_id=event_db.operator_id,
                    equipment_id=event_db.equipment_id,
                    created_at=event_db.created_at,
                    created_by=event_db.created_by
                )
                events.append(event)
            
            self.logger.info(f"Listados {len(events)} eventos de trazabilidad")
            return events
            
        except Exception as e:
            self.logger.error(f"Error al listar eventos de trazabilidad: {e}")
            raise
    
    async def _calculate_compliance_status(self, events: List[TraceabilityEventResponse]) -> str:
        """Calcular estado de cumplimiento regulatorio"""
        if not events:
            return "NO_DATA"
        
        # Verificar eventos requeridos según ISO 22000
        required_event_types = [
            EventType.PRODUCTION_START,
            EventType.QUALITY_CHECK,
            EventType.PACKAGING
        ]
        
        event_types = [event.event_type for event in events]
        missing_events = [et for et in required_event_types if et not in event_types]
        
        if missing_events:
            return "NON_COMPLIANT"
        
        # Verificar metadatos requeridos según DIGEMAPS
        for event in events:
            if event.metadata:
                required_fields = self.regulatory_config["digemaps"]["required_fields"]
                missing_fields = [field for field in required_fields if field not in event.metadata]
                if missing_fields:
                    return "NON_COMPLIANT"
        
        return "COMPLIANT"
    
    async def _calculate_quality_score(self, events: List[TraceabilityEventResponse]) -> Optional[float]:
        """Calcular puntuación de calidad (0-100)"""
        if not events:
            return None
        
        score = 100.0
        deductions = 0
        
        # Verificar eventos de calidad
        quality_events = [event for event in events if event.event_type == EventType.QUALITY_CHECK]
        if not quality_events:
            deductions += 20
        
        # Verificar eventos de seguridad
        safety_events = [event for event in events if event.event_type == EventType.SAFETY_INSPECTION]
        if not safety_events:
            deductions += 15
        
        # Verificar metadatos completos
        for event in events:
            if event.metadata:
                required_fields = self.regulatory_config["digemaps"]["required_fields"]
                missing_fields = [field for field in required_fields if field not in event.metadata]
                deductions += len(missing_fields) * 2
        
        # Verificar temperaturas dentro de rango
        for event in events:
            if event.metadata and "temperature" in event.metadata:
                temp = event.metadata["temperature"]
                min_temp, max_temp = self.regulatory_config["digemaps"]["temperature_range"]
                if temp < min_temp or temp > max_temp:
                    deductions += 5
        
        final_score = max(0, score - deductions)
        return round(final_score, 1)
    
    async def _generate_compliance_report(self, events: List[TraceabilityEventResponse]) -> Dict[str, Any]:
        """Generar reporte de cumplimiento regulatorio"""
        digemaps_compliant = True
        codex_compliant = True
        iso22000_compliant = True
        issues = []
        
        # Verificar cumplimiento DIGEMAPS
        for event in events:
            if event.metadata:
                required_fields = self.regulatory_config["digemaps"]["required_fields"]
                missing_fields = [field for field in required_fields if field not in event.metadata]
                if missing_fields:
                    digemaps_compliant = False
                    issues.append(f"Campos faltantes según DIGEMAPS: {missing_fields}")
        
        # Verificar cumplimiento Codex
        for event in events:
            if event.metadata and "temperature" in event.metadata:
                temp = event.metadata["temperature"]
                min_temp, max_temp = self.regulatory_config["codex"]["temperature_range"]
                if temp < min_temp or temp > max_temp:
                    codex_compliant = False
                    issues.append(f"Temperatura fuera de rango Codex: {temp}°C")
        
        # Verificar cumplimiento ISO 22000
        event_types = [event.event_type for event in events]
        required_events = [EventType.PRODUCTION_START, EventType.QUALITY_CHECK]
        missing_events = [et for et in required_events if et not in event_types]
        if missing_events:
            iso22000_compliant = False
            issues.append(f"Eventos faltantes según ISO 22000: {missing_events}")
        
        return {
            "digemaps_compliant": digemaps_compliant,
            "codex_compliant": codex_compliant,
            "iso22000_compliant": iso22000_compliant,
            "issues": issues
        }
    
    async def _get_product_name(self, product_id: str) -> Optional[str]:
        """Obtener nombre del producto (simulado)"""
        # En un sistema real, esto consultaría la base de datos
        product_names = {
            "NVL-001": "Refresco Cola 500ml",
            "NVL-002": "Refresco Limón 500ml",
            "NVL-003": "Agua Mineral 1L",
            "NOVALAT-001": "Jugo de Naranja 1L"
        }
        return product_names.get(product_id)
    
    async def _get_batch_production_date(self, batch_id: str) -> Optional[datetime]:
        """Obtener fecha de producción del lote (simulado)"""
        # En un sistema real, esto consultaría la base de datos
        return datetime.now(timezone.utc) - timedelta(days=30)
    
    async def _get_batch_expiration_date(self, batch_id: str) -> Optional[datetime]:
        """Obtener fecha de expiración del lote (simulado)"""
        # En un sistema real, esto consultaría la base de datos
        return datetime.now(timezone.utc) + timedelta(days=335)  # 11 meses 