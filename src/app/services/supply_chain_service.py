"""
🥤 NovaLat - Servicio de Cadena de Suministro
Servicio para gestión de órdenes de abastecimiento y logística
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from ..models.traceability import (
    SupplyChainOrderCreate,
    SupplyChainOrder,
    OrderType,
    OrderStatus
)
from ..models.database import DatabaseManager, SupplyChainOrderDB

logger = logging.getLogger(__name__)

class SupplyChainService:
    """Servicio de cadena de suministro para NovaLat"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
        
        # Configuración de prioridades y tiempos de entrega
        self.priority_config = {
            "URGENT": {"max_delivery_days": 1, "auto_approval": False},
            "HIGH": {"max_delivery_days": 3, "auto_approval": False},
            "NORMAL": {"max_delivery_days": 7, "auto_approval": True},
            "LOW": {"max_delivery_days": 14, "auto_approval": True}
        }
        
        # Configuración de proveedores (simulado)
        self.suppliers = {
            "SUP-001": {
                "name": "Proveedor de Materias Primas S.A.",
                "category": "RAW_MATERIAL",
                "rating": 4.5,
                "delivery_time_avg": 3.2,
                "is_active": True
            },
            "SUP-002": {
                "name": "Empaque y Envases Dominicana",
                "category": "PACKAGING",
                "rating": 4.2,
                "delivery_time_avg": 2.8,
                "is_active": True
            },
            "SUP-003": {
                "name": "Equipos Industriales Caribe",
                "category": "EQUIPMENT",
                "rating": 4.7,
                "delivery_time_avg": 5.1,
                "is_active": True
            }
        }
    
    async def create_order(self, order: SupplyChainOrderCreate, user: Dict[str, Any]) -> SupplyChainOrder:
        """Crear una nueva orden de cadena de suministro"""
        try:
            self.logger.info(f"Creando orden de cadena de suministro: {order.order_type}")
            
            # Validar datos de la orden
            await self._validate_order_data(order)
            
            # Calcular fecha de entrega esperada si no se proporciona
            if not order.expected_delivery_date:
                order.expected_delivery_date = await self._calculate_expected_delivery_date(order)
            
            # Preparar datos para la base de datos
            order_data = {
                "order_type": order.order_type.value,
                "supplier_id": order.supplier_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "unit": order.unit,
                "expected_delivery_date": order.expected_delivery_date,
                "priority": order.priority,
                "notes": order.notes,
                "metadata": order.metadata
            }
            
            # Crear orden en base de datos
            db_order = await self.db.create_supply_chain_order(order_data, user["id"])
            
            # Aplicar lógica de negocio según prioridad
            await self._apply_business_rules(db_order)
            
            # Convertir a respuesta
            response = SupplyChainOrder(
                id=str(db_order.id),
                order_type=OrderType(db_order.order_type),
                supplier_id=db_order.supplier_id,
                product_id=db_order.product_id,
                quantity=db_order.quantity,
                unit=db_order.unit,
                expected_delivery_date=db_order.expected_delivery_date,
                priority=db_order.priority,
                notes=db_order.notes,
                metadata=db_order.order_metadata or {},
                status=OrderStatus(db_order.status),
                created_at=db_order.created_at,
                updated_at=db_order.updated_at,
                created_by=db_order.created_by,
                approved_by=db_order.approved_by,
                approved_at=db_order.approved_at,
                delivered_at=db_order.delivered_at,
                actual_quantity=db_order.actual_quantity,
                delivery_notes=db_order.delivery_notes
            )
            
            self.logger.info(f"Orden de cadena de suministro creada exitosamente: {response.id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error al crear orden de cadena de suministro: {e}")
            raise
    
    async def get_order(self, order_id: str) -> Optional[SupplyChainOrder]:
        """Obtener una orden de cadena de suministro por ID"""
        try:
            db_order = await self.db.get_supply_chain_order(order_id)
            
            if not db_order:
                return None
            
            # Convertir a respuesta
            response = SupplyChainOrder(
                id=str(db_order.id),
                order_type=OrderType(db_order.order_type),
                supplier_id=db_order.supplier_id,
                product_id=db_order.product_id,
                quantity=db_order.quantity,
                unit=db_order.unit,
                expected_delivery_date=db_order.expected_delivery_date,
                priority=db_order.priority,
                notes=db_order.notes,
                metadata=db_order.order_metadata or {},
                status=OrderStatus(db_order.status),
                created_at=db_order.created_at,
                updated_at=db_order.updated_at,
                created_by=db_order.created_by,
                approved_by=db_order.approved_by,
                approved_at=db_order.approved_at,
                delivered_at=db_order.delivered_at,
                actual_quantity=db_order.actual_quantity,
                delivery_notes=db_order.delivery_notes
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error al obtener orden {order_id}: {e}")
            raise
    
    async def update_order_status(self, order_id: str, new_status: OrderStatus, user: Dict[str, Any], **kwargs) -> SupplyChainOrder:
        """Actualizar el estado de una orden"""
        try:
            # Obtener orden actual
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Orden {order_id} no encontrada")
            
            # Validar transición de estado
            await self._validate_status_transition(order.status, new_status)
            
            # Aplicar lógica específica según el nuevo estado
            if new_status == OrderStatus.APPROVED:
                await self._handle_order_approval(order_id, user, **kwargs)
            elif new_status == OrderStatus.DELIVERED:
                await self._handle_order_delivery(order_id, user, **kwargs)
            elif new_status == OrderStatus.CANCELLED:
                await self._handle_order_cancellation(order_id, user, **kwargs)
            
            # Obtener orden actualizada
            updated_order = await self.get_order(order_id)
            
            self.logger.info(f"Estado de orden {order_id} actualizado a {new_status}")
            return updated_order
            
        except Exception as e:
            self.logger.error(f"Error al actualizar estado de orden {order_id}: {e}")
            raise
    
    async def _validate_order_data(self, order: SupplyChainOrderCreate) -> None:
        """Validar datos de la orden"""
        # Validar proveedor
        if order.supplier_id not in self.suppliers:
            raise ValueError(f"Proveedor {order.supplier_id} no encontrado")
        
        supplier = self.suppliers[order.supplier_id]
        if not supplier["is_active"]:
            raise ValueError(f"Proveedor {order.supplier_id} no está activo")
        
        # Validar tipo de orden vs categoría del proveedor
        if order.order_type.value != supplier["category"]:
            raise ValueError(f"Proveedor {order.supplier_id} no maneja órdenes de tipo {order.order_type}")
        
        # Validar cantidad
        if order.quantity <= 0:
            raise ValueError("Cantidad debe ser mayor a 0")
        
        # Validar fecha de entrega
        if order.expected_delivery_date:
            min_delivery_date = datetime.now(timezone.utc) + timedelta(days=1)
            if order.expected_delivery_date < min_delivery_date:
                raise ValueError("Fecha de entrega debe ser al menos 1 día en el futuro")
        
        # Validar prioridad
        if order.priority not in self.priority_config:
            raise ValueError(f"Prioridad debe ser una de: {list(self.priority_config.keys())}")
        
        self.logger.info("✅ Validación de orden completada exitosamente")
    
    async def _calculate_expected_delivery_date(self, order: SupplyChainOrderCreate) -> datetime:
        """Calcular fecha de entrega esperada basada en prioridad y proveedor"""
        supplier = self.suppliers[order.supplier_id]
        priority_config = self.priority_config[order.priority]
        
        # Calcular días de entrega basado en prioridad y tiempo promedio del proveedor
        delivery_days = min(
            priority_config["max_delivery_days"],
            supplier["delivery_time_avg"]
        )
        
        # Agregar margen de seguridad
        delivery_days = max(delivery_days, 2)
        
        expected_date = datetime.now(timezone.utc) + timedelta(days=delivery_days)
        return expected_date
    
    async def _apply_business_rules(self, db_order: SupplyChainOrderDB) -> None:
        """Aplicar reglas de negocio a la orden"""
        priority_config = self.priority_config[db_order.priority]
        
        # Auto-aprobación para órdenes de baja prioridad
        if priority_config["auto_approval"]:
            await self._auto_approve_order(db_order)
        
        # Notificar a proveedor si es urgente
        if db_order.priority == "URGENT":
            await self._notify_supplier_urgent(db_order)
        
        # Crear eventos de trazabilidad relacionados
        await self._create_traceability_events(db_order)
    
    async def _auto_approve_order(self, db_order: SupplyChainOrderDB) -> None:
        """Aprobar automáticamente una orden"""
        session = self.db.get_session()
        try:
            db_order.status = "APPROVED"
            db_order.approved_by = "SYSTEM"
            db_order.approved_at = datetime.now(timezone.utc)
            db_order.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            session.refresh(db_order)
            
            self.logger.info(f"Orden {db_order.id} aprobada automáticamente")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error al auto-aprobar orden: {e}")
            raise
        finally:
            session.close()
    
    async def _notify_supplier_urgent(self, db_order: SupplyChainOrderDB) -> None:
        """Notificar al proveedor sobre orden urgente"""
        # En un sistema real, esto enviaría una notificación
        supplier = self.suppliers[db_order.supplier_id]
        self.logger.info(f"🔔 Notificación urgente enviada a {supplier['name']} para orden {db_order.id}")
    
    async def _create_traceability_events(self, db_order: SupplyChainOrderDB) -> None:
        """Crear eventos de trazabilidad relacionados con la orden"""
        # Crear evento de creación de orden
        event_data = {
            "product_id": db_order.product_id or "SUPPLY-CHAIN",
            "batch_id": f"ORDER-{db_order.id}",
            "event_type": "SUPPLY_CHAIN_ORDER_CREATED",
            "location": "NOVALAT-HQ",
            "timestamp": db_order.created_at,
            "quantity": db_order.quantity,
            "unit": db_order.unit,
            "metadata": {
                "order_id": str(db_order.id),
                "supplier_id": db_order.supplier_id,
                "order_type": db_order.order_type,
                "priority": db_order.priority
            },
            "operator_id": db_order.created_by,
            "equipment_id": "SYSTEM"
        }
        
        try:
            await self.db.create_traceability_event(event_data, db_order.created_by)
            self.logger.info(f"Evento de trazabilidad creado para orden {db_order.id}")
        except Exception as e:
            self.logger.error(f"Error al crear evento de trazabilidad para orden: {e}")
    
    async def _validate_status_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> None:
        """Validar transición de estado de la orden"""
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.APPROVED, OrderStatus.CANCELLED, OrderStatus.REJECTED],
            OrderStatus.APPROVED: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
            OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],  # Estado final
            OrderStatus.CANCELLED: [],  # Estado final
            OrderStatus.REJECTED: []    # Estado final
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(f"Transición de estado inválida: {current_status} -> {new_status}")
    
    async def _handle_order_approval(self, order_id: str, user: Dict[str, Any], **kwargs) -> None:
        """Manejar aprobación de orden"""
        session = self.db.get_session()
        try:
            db_order = session.query(SupplyChainOrderDB).filter(SupplyChainOrderDB.id == order_id).first()
            if db_order:
                db_order.status = "APPROVED"
                db_order.approved_by = user["id"]
                db_order.approved_at = datetime.now(timezone.utc)
                db_order.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                
                # Crear evento de trazabilidad
                event_data = {
                    "product_id": db_order.product_id or "SUPPLY-CHAIN",
                    "batch_id": f"ORDER-{db_order.id}",
                    "event_type": "SUPPLY_CHAIN_ORDER_APPROVED",
                    "location": "NOVALAT-HQ",
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {
                        "order_id": str(db_order.id),
                        "approved_by": user["id"]
                    },
                    "operator_id": user["id"],
                    "equipment_id": "SYSTEM"
                }
                
                await self.db.create_traceability_event(event_data, user["id"])
                
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def _handle_order_delivery(self, order_id: str, user: Dict[str, Any], **kwargs) -> None:
        """Manejar entrega de orden"""
        session = self.db.get_session()
        try:
            db_order = session.query(SupplyChainOrderDB).filter(SupplyChainOrderDB.id == order_id).first()
            if db_order:
                db_order.status = "DELIVERED"
                db_order.delivered_at = datetime.now(timezone.utc)
                db_order.updated_at = datetime.now(timezone.utc)
                
                # Actualizar cantidad real si se proporciona
                if "actual_quantity" in kwargs:
                    db_order.actual_quantity = kwargs["actual_quantity"]
                
                # Actualizar notas de entrega si se proporciona
                if "delivery_notes" in kwargs:
                    db_order.delivery_notes = kwargs["delivery_notes"]
                
                session.commit()
                
                # Crear evento de trazabilidad
                event_data = {
                    "product_id": db_order.product_id or "SUPPLY-CHAIN",
                    "batch_id": f"ORDER-{db_order.id}",
                    "event_type": "SUPPLY_CHAIN_ORDER_DELIVERED",
                    "location": "NOVALAT-HQ",
                    "timestamp": datetime.now(timezone.utc),
                    "quantity": kwargs.get("actual_quantity", db_order.quantity),
                    "unit": db_order.unit,
                    "metadata": {
                        "order_id": str(db_order.id),
                        "delivery_notes": kwargs.get("delivery_notes", "")
                    },
                    "operator_id": user["id"],
                    "equipment_id": "SYSTEM"
                }
                
                await self.db.create_traceability_event(event_data, user["id"])
                
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def _handle_order_cancellation(self, order_id: str, user: Dict[str, Any], **kwargs) -> None:
        """Manejar cancelación de orden"""
        session = self.db.get_session()
        try:
            db_order = session.query(SupplyChainOrderDB).filter(SupplyChainOrderDB.id == order_id).first()
            if db_order:
                db_order.status = "CANCELLED"
                db_order.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                
                # Crear evento de trazabilidad
                event_data = {
                    "product_id": db_order.product_id or "SUPPLY-CHAIN",
                    "batch_id": f"ORDER-{db_order.id}",
                    "event_type": "SUPPLY_CHAIN_ORDER_CANCELLED",
                    "location": "NOVALAT-HQ",
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {
                        "order_id": str(db_order.id),
                        "cancellation_reason": kwargs.get("reason", "No especificado")
                    },
                    "operator_id": user["id"],
                    "equipment_id": "SYSTEM"
                }
                
                await self.db.create_traceability_event(event_data, user["id"])
                
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def get_supplier_performance(self, supplier_id: str) -> Dict[str, Any]:
        """Obtener métricas de rendimiento del proveedor"""
        if supplier_id not in self.suppliers:
            raise ValueError(f"Proveedor {supplier_id} no encontrado")
        
        supplier = self.suppliers[supplier_id]
        
        # En un sistema real, esto consultaría la base de datos para obtener métricas reales
        performance_metrics = {
            "supplier_id": supplier_id,
            "name": supplier["name"],
            "rating": supplier["rating"],
            "delivery_time_avg": supplier["delivery_time_avg"],
            "total_orders": 150,  # Simulado
            "on_time_deliveries": 142,  # Simulado
            "on_time_percentage": 94.7,  # Simulado
            "quality_score": 4.3,  # Simulado
            "is_active": supplier["is_active"]
        }
        
        return performance_metrics 