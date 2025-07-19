"""
🥤 NovaLat - Microservicio de Trazabilidad Alimentaria
Sistema de trazabilidad para cumplimiento regulatorio (DIGEMAPS, Codex, ISO 22000)
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import json

# Importar modelos y servicios
from .models.traceability import (
    TraceabilityEvent, 
    TraceabilityEventCreate, 
    TraceabilityEventResponse,
    ProductTraceability,
    BatchTraceability,
    SupplyChainOrder,
    SupplyChainOrderCreate
)
from .models.database import DatabaseManager
from .services.traceability_service import TraceabilityService
from .services.supply_chain_service import SupplyChainService
from .services.auth_service import AuthService
from .utils.metrics import MetricsCollector
from .utils.logger import setup_logger

# Configurar logging
logger = setup_logger(__name__)

# Configurar métricas
metrics = MetricsCollector()

# Configurar autenticación
security = HTTPBearer()

# Variables globales
app_config = {
    "title": "NovaLat Trazabilidad API",
    "description": "API de trazabilidad alimentaria para NovaLat - Cumplimiento DIGEMAPS, Codex, ISO 22000",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando NovaLat Trazabilidad API...")
    
    # Inicializar servicios
    app.state.db = DatabaseManager()
    app.state.traceability_service = TraceabilityService(app.state.db)
    app.state.supply_chain_service = SupplyChainService(app.state.db)
    app.state.auth_service = AuthService()
    
    # Conectar a base de datos
    await app.state.db.connect()
    logger.info("✅ Base de datos conectada")
    
    # Crear tablas si no existen
    await app.state.db.create_tables()
    logger.info("✅ Tablas creadas/verificadas")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando NovaLat Trazabilidad API...")
    await app.state.db.disconnect()

# Crear aplicación FastAPI
app = FastAPI(**app_config, lifespan=lifespan)

# Configurar middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts específicos
)

# Middleware para métricas
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de respuesta
    process_time = time.time() - start_time
    
    # Registrar métricas
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=process_time
    )
    
    # Agregar headers de métricas
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Dependencia para autenticación
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar token JWT y obtener usuario actual"""
    try:
        token = credentials.credentials
        user = app.state.auth_service.verify_token(token)
        return user
    except Exception as e:
        logger.error(f"Error de autenticación: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Endpoints de salud
@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "novalat-traceability",
        "version": app_config["version"]
    }

@app.get("/ready")
async def readiness_check():
    """Endpoint de readiness para Kubernetes"""
    try:
        # Verificar conexión a base de datos
        await app.state.db.health_check()
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Error en readiness check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

@app.post("/api/v1/auth/login")
async def login(username: str = "admin", password: str = "password123"):
    """Endpoint de login para pruebas (solo desarrollo)"""
    try:
        user = app.state.auth_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        token = app.state.auth_service.create_access_token({"sub": user["id"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            }
        }
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# Endpoints de trazabilidad
@app.post("/api/v1/traceability/events", 
          response_model=TraceabilityEventResponse,
          status_code=status.HTTP_201_CREATED)
async def create_traceability_event(
    event: TraceabilityEventCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Registrar un nuevo evento de trazabilidad alimentaria
    
    Cumple con estándares:
    - DIGEMAPS (República Dominicana)
    - Codex Alimentarius
    - ISO 22000
    """
    try:
        logger.info(f"Registrando evento de trazabilidad: {event.event_type} para producto {event.product_id}")
        
        # Validar datos según regulaciones
        await app.state.traceability_service.validate_event_data(event)
        
        # Crear evento
        created_event = await app.state.traceability_service.create_event(event, current_user)
        
        # Registrar métricas
        metrics.record_traceability_event(event.event_type)
        
        logger.info(f"Evento registrado exitosamente: {created_event.id}")
        return created_event
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al crear evento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/api/v1/traceability/products/{product_id}", 
         response_model=ProductTraceability)
async def get_product_traceability(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener trazabilidad completa de un producto"""
    try:
        logger.info(f"Consultando trazabilidad para producto: {product_id}")
        
        traceability = await app.state.traceability_service.get_product_traceability(product_id)
        
        if not traceability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {product_id} no encontrado"
            )
        
        return traceability
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener trazabilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/api/v1/traceability/batch/{batch_id}", 
         response_model=BatchTraceability)
async def get_batch_traceability(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener trazabilidad de un lote específico"""
    try:
        logger.info(f"Consultando trazabilidad para lote: {batch_id}")
        
        traceability = await app.state.traceability_service.get_batch_traceability(batch_id)
        
        if not traceability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )
        
        return traceability
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener trazabilidad de lote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/api/v1/traceability/events", 
         response_model=List[TraceabilityEventResponse])
async def list_traceability_events(
    product_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Listar eventos de trazabilidad con filtros"""
    try:
        logger.info("Listando eventos de trazabilidad")
        
        events = await app.state.traceability_service.list_events(
            product_id=product_id,
            batch_id=batch_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return events
        
    except Exception as e:
        logger.error(f"Error al listar eventos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# Endpoints de cadena de suministro
@app.post("/api/v1/supply-chain/orders", 
          response_model=SupplyChainOrder,
          status_code=status.HTTP_201_CREATED)
async def create_supply_chain_order(
    order: SupplyChainOrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear una nueva orden de abastecimiento"""
    try:
        logger.info(f"Creando orden de abastecimiento: {order.order_type}")
        
        created_order = await app.state.supply_chain_service.create_order(order, current_user)
        
        # Registrar métricas
        metrics.record_supply_chain_order(order.order_type)
        
        logger.info(f"Orden creada exitosamente: {created_order.id}")
        return created_order
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al crear orden: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/api/v1/supply-chain/orders/{order_id}", 
         response_model=SupplyChainOrder)
async def get_supply_chain_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener detalles de una orden de abastecimiento"""
    try:
        logger.info(f"Consultando orden: {order_id}")
        
        order = await app.state.supply_chain_service.get_order(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orden {order_id} no encontrada"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener orden: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# Endpoints de métricas
@app.get("/metrics")
async def get_metrics():
    """Obtener métricas del servicio (formato Prometheus)"""
    return metrics.get_prometheus_metrics()

@app.get("/api/v1/metrics/summary")
async def get_metrics_summary():
    """Obtener resumen de métricas en formato JSON"""
    return metrics.get_summary()

@app.get("/api/v1/test/traceability/{product_id}")
async def test_traceability(product_id: str):
    """Endpoint de prueba para trazabilidad (sin autenticación)"""
    try:
        # Obtener eventos directamente de la base de datos
        events_db = await app.state.db.get_traceability_events(product_id=product_id, limit=10)
        
        if not events_db:
            return {"message": "No events found", "product_id": product_id, "events": []}
        
        # Convertir a formato simple
        events = []
        for event_db in events_db:
            event = {
                "id": str(event_db.id),
                "product_id": event_db.product_id,
                "batch_id": event_db.batch_id,
                "event_type": event_db.event_type,
                "location": event_db.location,
                "timestamp": event_db.timestamp.isoformat() if event_db.timestamp else None,
                "metadata": event_db.event_metadata or {}
            }
            events.append(event)
        
        return {
            "product_id": product_id,
            "total_events": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error en test traceability: {e}")
        return {"error": str(e)}

# Endpoints de auditoría
@app.get("/api/v1/audit/logs")
async def get_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Obtener logs de auditoría (solo usuarios autorizados)"""
    try:
        # Verificar permisos de auditoría
        if not app.state.auth_service.has_audit_permission(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permisos para acceder a logs de auditoría"
            )
        
        logs = await app.state.db.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action=action,
            limit=limit
        )
        
        return {"logs": logs, "total": len(logs)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener logs de auditoría: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 