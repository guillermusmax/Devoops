"""
🥤 NovaLat - Modelos de Trazabilidad Alimentaria
Modelos Pydantic para el sistema de trazabilidad
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

class EventType(str, Enum):
    """Tipos de eventos de trazabilidad según estándares alimentarios"""
    # Eventos de producción
    PRODUCTION_START = "PRODUCTION_START"
    PRODUCTION_END = "PRODUCTION_END"
    QUALITY_CHECK = "QUALITY_CHECK"
    PACKAGING = "PACKAGING"
    
    # Eventos de almacenamiento
    STORAGE_IN = "STORAGE_IN"
    STORAGE_OUT = "STORAGE_OUT"
    TEMPERATURE_CHECK = "TEMPERATURE_CHECK"
    
    # Eventos de transporte
    SHIPPING_START = "SHIPPING_START"
    SHIPPING_END = "SHIPPING_END"
    DELIVERY = "DELIVERY"
    
    # Eventos de distribución
    DISTRIBUTION_CENTER_IN = "DISTRIBUTION_CENTER_IN"
    DISTRIBUTION_CENTER_OUT = "DISTRIBUTION_CENTER_OUT"
    RETAIL_DELIVERY = "RETAIL_DELIVERY"
    
    # Eventos de cadena de suministro
    SUPPLY_CHAIN_ORDER_CREATED = "SUPPLY_CHAIN_ORDER_CREATED"
    SUPPLY_CHAIN_ORDER_APPROVED = "SUPPLY_CHAIN_ORDER_APPROVED"
    SUPPLY_CHAIN_ORDER_DELIVERED = "SUPPLY_CHAIN_ORDER_DELIVERED"
    
    # Eventos de calidad y seguridad
    SAFETY_INSPECTION = "SAFETY_INSPECTION"
    RECALL = "RECALL"
    EXPIRATION = "EXPIRATION"

class OrderType(str, Enum):
    """Tipos de órdenes de cadena de suministro"""
    RAW_MATERIAL = "RAW_MATERIAL"
    PACKAGING = "PACKAGING"
    FINISHED_GOODS = "FINISHED_GOODS"
    MAINTENANCE = "MAINTENANCE"
    EQUIPMENT = "EQUIPMENT"

class OrderStatus(str, Enum):
    """Estados de las órdenes de abastecimiento"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class LocationType(str, Enum):
    """Tipos de ubicaciones en la cadena de suministro"""
    PRODUCTION_PLANT = "PRODUCTION_PLANT"
    WAREHOUSE = "WAREHOUSE"
    DISTRIBUTION_CENTER = "DISTRIBUTION_CENTER"
    RETAIL_STORE = "RETAIL_STORE"
    SUPPLIER = "SUPPLIER"
    TRANSPORT = "TRANSPORT"

class TraceabilityEventCreate(BaseModel):
    """Modelo para crear un evento de trazabilidad"""
    product_id: str = Field(..., description="ID único del producto", min_length=1, max_length=50)
    batch_id: str = Field(..., description="ID del lote de producción", min_length=1, max_length=50)
    event_type: EventType = Field(..., description="Tipo de evento de trazabilidad")
    location: str = Field(..., description="Ubicación donde ocurrió el evento", min_length=1, max_length=100)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp del evento")
    quantity: Optional[float] = Field(None, description="Cantidad involucrada en el evento")
    unit: Optional[str] = Field(None, description="Unidad de medida", max_length=20)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales del evento")
    operator_id: Optional[str] = Field(None, description="ID del operador responsable", max_length=50)
    equipment_id: Optional[str] = Field(None, description="ID del equipo utilizado", max_length=50)
    
    @validator('product_id')
    def validate_product_id(cls, v):
        """Validar formato del ID del producto según estándares NovaLat"""
        if not v.startswith(('NVL-', 'NOVALAT-')):
            raise ValueError('Product ID debe comenzar con NVL- o NOVALAT-')
        return v
    
    @validator('batch_id')
    def validate_batch_id(cls, v):
        """Validar formato del ID del lote"""
        if not v.startswith('BATCH-'):
            raise ValueError('Batch ID debe comenzar con BATCH-')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validar metadatos según regulaciones alimentarias"""
        if v:
            # Verificar campos obligatorios según DIGEMAPS
            required_fields = ['temperature', 'humidity']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'Campo obligatorio faltante en metadata: {field}')
            
            # Validar rangos de temperatura según Codex
            if 'temperature' in v:
                temp = v['temperature']
                if not isinstance(temp, (int, float)) or temp < -20 or temp > 50:
                    raise ValueError('Temperatura debe estar entre -20°C y 50°C')
        
        return v

class TraceabilityEvent(TraceabilityEventCreate):
    """Modelo completo de evento de trazabilidad"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único del evento")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de creación")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de actualización")
    created_by: str = Field(..., description="ID del usuario que creó el evento")
    version: int = Field(default=1, description="Versión del evento para auditoría")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "evt-123e4567-e89b-12d3-a456-426614174000",
                "product_id": "NVL-001",
                "batch_id": "BATCH-2024-001",
                "event_type": "PRODUCTION_START",
                "location": "PLANTA-SANTO-DOMINGO",
                "timestamp": "2024-01-15T10:30:00Z",
                "quantity": 1000.0,
                "unit": "kg",
                "metadata": {
                    "temperature": 25.5,
                    "humidity": 60,
                    "operator": "Juan Pérez",
                    "equipment": "LINEA-01"
                },
                "operator_id": "OP-001",
                "equipment_id": "EQ-001",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "created_by": "user-123",
                "version": 1
            }
        }

class TraceabilityEventResponse(BaseModel):
    """Modelo de respuesta para eventos de trazabilidad"""
    id: str
    product_id: str
    batch_id: str
    event_type: EventType
    location: str
    timestamp: datetime
    quantity: Optional[float]
    unit: Optional[str]
    metadata: Dict[str, Any]
    operator_id: Optional[str]
    equipment_id: Optional[str]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True

class ProductTraceability(BaseModel):
    """Modelo para trazabilidad completa de un producto"""
    product_id: str
    product_name: Optional[str]
    batch_id: str
    events: List[TraceabilityEventResponse]
    total_events: int
    first_event: Optional[datetime]
    last_event: Optional[datetime]
    compliance_status: str = Field(..., description="Estado de cumplimiento regulatorio")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Puntuación de calidad (0-100)")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": "NVL-001",
                "product_name": "Refresco Cola 500ml",
                "batch_id": "BATCH-2024-001",
                "events": [],
                "total_events": 5,
                "first_event": "2024-01-15T10:30:00Z",
                "last_event": "2024-01-20T15:45:00Z",
                "compliance_status": "COMPLIANT",
                "quality_score": 95.5
            }
        }

class BatchTraceability(BaseModel):
    """Modelo para trazabilidad de un lote específico"""
    batch_id: str
    product_id: str
    production_date: Optional[datetime]
    expiration_date: Optional[datetime]
    events: List[TraceabilityEventResponse]
    total_events: int
    locations_visited: List[str]
    quality_checks: List[TraceabilityEventResponse]
    safety_inspections: List[TraceabilityEventResponse]
    compliance_report: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "BATCH-2024-001",
                "product_id": "NVL-001",
                "production_date": "2024-01-15T10:30:00Z",
                "expiration_date": "2024-12-15T10:30:00Z",
                "events": [],
                "total_events": 8,
                "locations_visited": ["PLANTA-SANTO-DOMINGO", "ALMACEN-CENTRAL"],
                "quality_checks": [],
                "safety_inspections": [],
                "compliance_report": {
                    "digemaps_compliant": True,
                    "codex_compliant": True,
                    "iso22000_compliant": True,
                    "issues": []
                }
            }
        }

class SupplyChainOrderCreate(BaseModel):
    """Modelo para crear una orden de cadena de suministro"""
    order_type: OrderType = Field(..., description="Tipo de orden")
    supplier_id: str = Field(..., description="ID del proveedor", min_length=1, max_length=50)
    product_id: Optional[str] = Field(None, description="ID del producto (para órdenes de materiales)")
    quantity: float = Field(..., gt=0, description="Cantidad solicitada")
    unit: str = Field(..., description="Unidad de medida", max_length=20)
    expected_delivery_date: datetime = Field(..., description="Fecha esperada de entrega")
    priority: str = Field(default="NORMAL", description="Prioridad de la orden")
    notes: Optional[str] = Field(None, description="Notas adicionales", max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales")
    
    @validator('supplier_id')
    def validate_supplier_id(cls, v):
        """Validar formato del ID del proveedor"""
        if not v.startswith('SUP-'):
            raise ValueError('Supplier ID debe comenzar con SUP-')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validar prioridad de la orden"""
        valid_priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        if v not in valid_priorities:
            raise ValueError(f'Prioridad debe ser una de: {valid_priorities}')
        return v

class SupplyChainOrder(SupplyChainOrderCreate):
    """Modelo completo de orden de cadena de suministro"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de la orden")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Estado actual de la orden")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de creación")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de actualización")
    created_by: str = Field(..., description="ID del usuario que creó la orden")
    approved_by: Optional[str] = Field(None, description="ID del usuario que aprobó la orden")
    approved_at: Optional[datetime] = Field(None, description="Timestamp de aprobación")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp de entrega")
    actual_quantity: Optional[float] = Field(None, description="Cantidad realmente entregada")
    delivery_notes: Optional[str] = Field(None, description="Notas de entrega")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "ord-123e4567-e89b-12d3-a456-426614174000",
                "order_type": "RAW_MATERIAL",
                "supplier_id": "SUP-001",
                "product_id": "NVL-001",
                "quantity": 5000.0,
                "unit": "kg",
                "expected_delivery_date": "2024-01-25T10:00:00Z",
                "priority": "HIGH",
                "notes": "Material para producción de la semana próxima",
                "metadata": {
                    "quality_requirements": "ISO 22000",
                    "packaging_type": "BULK"
                },
                "status": "PENDING",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "created_by": "user-123"
            }
        }

class ComplianceReport(BaseModel):
    """Modelo para reportes de cumplimiento regulatorio"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único del reporte")
    product_id: Optional[str] = Field(None, description="ID del producto evaluado")
    batch_id: Optional[str] = Field(None, description="ID del lote evaluado")
    report_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Fecha del reporte")
    digemaps_compliant: bool = Field(..., description="Cumplimiento DIGEMAPS")
    codex_compliant: bool = Field(..., description="Cumplimiento Codex Alimentarius")
    iso22000_compliant: bool = Field(..., description="Cumplimiento ISO 22000")
    issues: List[str] = Field(default_factory=list, description="Problemas identificados")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones")
    generated_by: str = Field(..., description="ID del usuario que generó el reporte")
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "rep-123e4567-e89b-12d3-a456-426614174000",
                "product_id": "NVL-001",
                "batch_id": "BATCH-2024-001",
                "report_date": "2024-01-15T10:30:00Z",
                "digemaps_compliant": True,
                "codex_compliant": True,
                "iso22000_compliant": True,
                "issues": [],
                "recommendations": ["Mantener protocolos actuales"],
                "generated_by": "user-123"
            }
        } 