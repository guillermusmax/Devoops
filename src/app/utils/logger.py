"""
🥤 NovaLat - Configuración de Logging
Configuración centralizada de logging para el sistema
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configurar logger para NovaLat
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    # Obtener nivel de logging desde variables de entorno
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Crear formato de log
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (si está configurado)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Handler de archivo con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_structured_logging(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configurar logger con formato estructurado (JSON)
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
    
    Returns:
        Logger configurado con formato JSON
    """
    import json
    
    class StructuredFormatter(logging.Formatter):
        """Formateador para logs estructurados en JSON"""
        
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "logger": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Agregar campos adicionales si existen
            if hasattr(record, 'traceability_event'):
                log_entry['traceability_event'] = record.traceability_event
            
            if hasattr(record, 'supply_chain_order'):
                log_entry['supply_chain_order'] = record.supply_chain_order
            
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            
            if hasattr(record, 'request_id'):
                log_entry['request_id'] = record.request_id
            
            # Agregar excepción si existe
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry)
    
    # Obtener nivel de logging
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Crear logger
    logger = logging.getLogger(f"{name}_structured")
    logger.setLevel(getattr(logging, log_level))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formateador estructurado
    formatter = StructuredFormatter()
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo JSON (si está configurado)
    json_log_file = os.getenv("JSON_LOG_FILE")
    if json_log_file:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(json_log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Handler de archivo JSON con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_traceability_event(logger: logging.Logger, event_type: str, product_id: str, batch_id: str, **kwargs):
    """
    Log especializado para eventos de trazabilidad
    
    Args:
        logger: Logger a usar
        event_type: Tipo de evento
        product_id: ID del producto
        batch_id: ID del lote
        **kwargs: Campos adicionales
    """
    extra = {
        'traceability_event': {
            'event_type': event_type,
            'product_id': product_id,
            'batch_id': batch_id,
            **kwargs
        }
    }
    logger.info(f"Evento de trazabilidad: {event_type} | Producto: {product_id} | Lote: {batch_id}", extra=extra)

def log_supply_chain_order(logger: logging.Logger, order_type: str, supplier_id: str, order_id: str, **kwargs):
    """
    Log especializado para órdenes de cadena de suministro
    
    Args:
        logger: Logger a usar
        order_type: Tipo de orden
        supplier_id: ID del proveedor
        order_id: ID de la orden
        **kwargs: Campos adicionales
    """
    extra = {
        'supply_chain_order': {
            'order_type': order_type,
            'supplier_id': supplier_id,
            'order_id': order_id,
            **kwargs
        }
    }
    logger.info(f"Orden de cadena de suministro: {order_type} | Proveedor: {supplier_id} | Orden: {order_id}", extra=extra)

def log_user_action(logger: logging.Logger, user_id: str, action: str, resource_type: str, resource_id: str, **kwargs):
    """
    Log especializado para acciones de usuario
    
    Args:
        logger: Logger a usar
        user_id: ID del usuario
        action: Acción realizada
        resource_type: Tipo de recurso
        resource_id: ID del recurso
        **kwargs: Campos adicionales
    """
    extra = {
        'user_id': user_id,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        **kwargs
    }
    logger.info(f"Acción de usuario: {action} | Usuario: {user_id} | Recurso: {resource_type}/{resource_id}", extra=extra)

def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, duration: float, user_id: Optional[str] = None, **kwargs):
    """
    Log especializado para requests de API
    
    Args:
        logger: Logger a usar
        method: Método HTTP
        path: Ruta de la API
        status_code: Código de estado HTTP
        duration: Duración de la request
        user_id: ID del usuario (opcional)
        **kwargs: Campos adicionales
    """
    extra = {
        'request_id': kwargs.get('request_id'),
        'user_id': user_id,
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration': duration,
        **kwargs
    }
    
    level = logging.ERROR if status_code >= 400 else logging.INFO
    logger.log(level, f"API Request: {method} {path} | Status: {status_code} | Duration: {duration:.3f}s", extra=extra)

def log_database_operation(logger: logging.Logger, operation: str, table: str, duration: float, **kwargs):
    """
    Log especializado para operaciones de base de datos
    
    Args:
        logger: Logger a usar
        operation: Tipo de operación (SELECT, INSERT, UPDATE, DELETE)
        table: Nombre de la tabla
        duration: Duración de la operación
        **kwargs: Campos adicionales
    """
    extra = {
        'database_operation': {
            'operation': operation,
            'table': table,
            'duration': duration,
            **kwargs
        }
    }
    
    level = logging.WARNING if duration > 1.0 else logging.DEBUG
    logger.log(level, f"DB Operation: {operation} | Table: {table} | Duration: {duration:.3f}s", extra=extra)

def log_security_event(logger: logging.Logger, event_type: str, user_id: Optional[str] = None, ip_address: Optional[str] = None, **kwargs):
    """
    Log especializado para eventos de seguridad
    
    Args:
        logger: Logger a usar
        event_type: Tipo de evento de seguridad
        user_id: ID del usuario (opcional)
        ip_address: Dirección IP (opcional)
        **kwargs: Campos adicionales
    """
    extra = {
        'security_event': {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            **kwargs
        }
    }
    
    level = logging.WARNING if event_type in ['failed_login', 'unauthorized_access'] else logging.INFO
    logger.log(level, f"Security Event: {event_type} | User: {user_id} | IP: {ip_address}", extra=extra)

# Configurar logging root
def setup_root_logging():
    """Configurar logging root para toda la aplicación"""
    # Configurar logging root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Evitar duplicar handlers
    if not root_logger.handlers:
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Configurar logging de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Inicializar logging al importar el módulo
setup_root_logging() 