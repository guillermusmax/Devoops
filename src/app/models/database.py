"""
🥤 NovaLat - Modelo de Base de Datos
Configuración de PostgreSQL con SQLAlchemy para trazabilidad alimentaria
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Text, Boolean, JSON, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
import uuid
import json

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://novalat_user:novalat_pass@localhost:5432/novalat_traceability"
)

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # Set to True for debugging
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

class TraceabilityEventDB(Base):
    """Tabla de eventos de trazabilidad"""
    __tablename__ = "traceability_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String(50), nullable=False, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    location = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    event_metadata = Column(JSON, nullable=True)
    operator_id = Column(String(50), nullable=True)
    equipment_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(50), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": str(self.id),
            "product_id": self.product_id,
            "batch_id": self.batch_id,
            "event_type": self.event_type,
            "location": self.location,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "quantity": self.quantity,
            "unit": self.unit,
            "metadata": self.event_metadata or {},
            "operator_id": self.operator_id,
            "equipment_id": self.equipment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "version": self.version
        }

class SupplyChainOrderDB(Base):
    """Tabla de órdenes de cadena de suministro"""
    __tablename__ = "supply_chain_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_type = Column(String(50), nullable=False, index=True)
    supplier_id = Column(String(50), nullable=False, index=True)
    product_id = Column(String(50), nullable=True, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=False)
    priority = Column(String(20), default="NORMAL", nullable=False)
    notes = Column(Text, nullable=True)
    order_metadata = Column(JSON, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(50), nullable=False)
    approved_by = Column(String(50), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    actual_quantity = Column(Float, nullable=True)
    delivery_notes = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": str(self.id),
            "order_type": self.order_type,
            "supplier_id": self.supplier_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "expected_delivery_date": self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            "priority": self.priority,
            "notes": self.notes,
            "metadata": self.order_metadata or {},
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "actual_quantity": self.actual_quantity,
            "delivery_notes": self.delivery_notes
        }

class ProductDB(Base):
    """Tabla de productos"""
    __tablename__ = "products"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    sku = Column(String(50), nullable=True, unique=True)
    barcode = Column(String(50), nullable=True, unique=True)
    product_metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "sku": self.sku,
            "barcode": self.barcode,
            "metadata": self.product_metadata or {},
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class BatchDB(Base):
    """Tabla de lotes de producción"""
    __tablename__ = "batches"
    
    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False, index=True)
    production_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    initial_quantity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    batch_metadata = Column(JSON, nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "production_date": self.production_date.isoformat() if self.production_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "initial_quantity": self.initial_quantity,
            "unit": self.unit,
            "metadata": self.batch_metadata or {},
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLogDB(Base):
    """Tabla de logs de auditoría"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class DatabaseManager:
    """Gestor de base de datos para NovaLat"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.logger = logger
    
    async def connect(self):
        """Conectar a la base de datos"""
        try:
            # Verificar conexión
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            self.logger.info("✅ Conexión a base de datos establecida")
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Error al conectar a la base de datos: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar de la base de datos"""
        try:
            self.engine.dispose()
            self.logger.info("✅ Conexión a base de datos cerrada")
        except Exception as e:
            self.logger.error(f"❌ Error al desconectar de la base de datos: {e}")
    
    async def create_tables(self):
        """Crear todas las tablas"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("✅ Tablas creadas/verificadas")
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Error al crear tablas: {e}")
            raise
    
    async def health_check(self):
        """Verificar salud de la base de datos"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Error en health check: {e}")
            return False
    
    def get_session(self) -> Session:
        """Obtener sesión de base de datos"""
        return self.SessionLocal()
    
    async def create_traceability_event(self, event_data: Dict[str, Any], user_id: str) -> TraceabilityEventDB:
        """Crear un evento de trazabilidad"""
        session = self.get_session()
        try:
            event = TraceabilityEventDB(
                product_id=event_data["product_id"],
                batch_id=event_data["batch_id"],
                event_type=event_data["event_type"],
                location=event_data["location"],
                timestamp=event_data["timestamp"],
                quantity=event_data.get("quantity"),
                unit=event_data.get("unit"),
                event_metadata=event_data.get("metadata", {}),
                operator_id=event_data.get("operator_id"),
                equipment_id=event_data.get("equipment_id"),
                created_by=user_id
            )
            
            session.add(event)
            session.commit()
            session.refresh(event)
            
            # Crear log de auditoría
            await self.create_audit_log(
                user_id=user_id,
                action="CREATE_TRACEABILITY_EVENT",
                resource_type="traceability_event",
                resource_id=str(event.id),
                details={"event_type": event.event_type, "product_id": event.product_id}
            )
            
            self.logger.info(f"Evento de trazabilidad creado: {event.id}")
            return event
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al crear evento de trazabilidad: {e}")
            raise
        finally:
            session.close()
    
    async def get_traceability_events(
        self,
        product_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TraceabilityEventDB]:
        """Obtener eventos de trazabilidad con filtros"""
        session = self.get_session()
        try:
            query = session.query(TraceabilityEventDB)
            
            if product_id:
                query = query.filter(TraceabilityEventDB.product_id == product_id)
            
            if batch_id:
                query = query.filter(TraceabilityEventDB.batch_id == batch_id)
            
            if event_type:
                query = query.filter(TraceabilityEventDB.event_type == event_type)
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(TraceabilityEventDB.timestamp >= start_dt)
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(TraceabilityEventDB.timestamp <= end_dt)
            
            events = query.order_by(TraceabilityEventDB.timestamp.desc()).offset(offset).limit(limit).all()
            return events
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener eventos de trazabilidad: {e}")
            raise
        finally:
            session.close()
    
    async def create_supply_chain_order(self, order_data: Dict[str, Any], user_id: str) -> SupplyChainOrderDB:
        """Crear una orden de cadena de suministro"""
        session = self.get_session()
        try:
            order = SupplyChainOrderDB(
                order_type=order_data["order_type"],
                supplier_id=order_data["supplier_id"],
                product_id=order_data.get("product_id"),
                quantity=order_data["quantity"],
                unit=order_data["unit"],
                expected_delivery_date=order_data["expected_delivery_date"],
                priority=order_data.get("priority", "NORMAL"),
                notes=order_data.get("notes"),
                order_metadata=order_data.get("metadata", {}),
                created_by=user_id
            )
            
            session.add(order)
            session.commit()
            session.refresh(order)
            
            # Crear log de auditoría
            await self.create_audit_log(
                user_id=user_id,
                action="CREATE_SUPPLY_CHAIN_ORDER",
                resource_type="supply_chain_order",
                resource_id=str(order.id),
                details={"order_type": order.order_type, "supplier_id": order.supplier_id}
            )
            
            self.logger.info(f"Orden de cadena de suministro creada: {order.id}")
            return order
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al crear orden de cadena de suministro: {e}")
            raise
        finally:
            session.close()
    
    async def get_supply_chain_order(self, order_id: str) -> Optional[SupplyChainOrderDB]:
        """Obtener una orden de cadena de suministro por ID"""
        session = self.get_session()
        try:
            order = session.query(SupplyChainOrderDB).filter(SupplyChainOrderDB.id == order_id).first()
            return order
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener orden de cadena de suministro: {e}")
            raise
        finally:
            session.close()
    
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLogDB:
        """Crear un log de auditoría"""
        session = self.get_session()
        try:
            audit_log = AuditLogDB(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            session.add(audit_log)
            session.commit()
            session.refresh(audit_log)
            
            return audit_log
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al crear log de auditoría: {e}")
            raise
        finally:
            session.close()
    
    async def get_audit_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogDB]:
        """Obtener logs de auditoría con filtros"""
        session = self.get_session()
        try:
            query = session.query(AuditLogDB)
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLogDB.timestamp >= start_dt)
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLogDB.timestamp <= end_dt)
            
            if user_id:
                query = query.filter(AuditLogDB.user_id == user_id)
            
            if action:
                query = query.filter(AuditLogDB.action == action)
            
            logs = query.order_by(AuditLogDB.timestamp.desc()).limit(limit).all()
            return logs
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener logs de auditoría: {e}")
            raise
        finally:
            session.close() 