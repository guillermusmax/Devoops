"""
🥤 NovaLat - Colector de Métricas
Métricas para Prometheus y monitoreo del sistema
"""

import time
import logging
from typing import Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Colector de métricas para NovaLat"""
    
    def __init__(self):
        self.logger = logger
        
        # Métricas de requests HTTP
        self.request_counts = Counter()
        self.request_durations = defaultdict(list)
        self.request_status_codes = Counter()
        
        # Métricas de trazabilidad
        self.traceability_events = Counter()
        self.traceability_event_types = Counter()
        
        # Métricas de cadena de suministro
        self.supply_chain_orders = Counter()
        self.supply_chain_order_types = Counter()
        
        # Métricas de errores
        self.error_counts = Counter()
        self.error_types = Counter()
        
        # Métricas de rendimiento
        self.active_connections = 0
        self.database_queries = Counter()
        self.database_query_durations = defaultdict(list)
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Timestamp de inicio
        self.start_time = datetime.now(timezone.utc)
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Registrar métricas de request HTTP"""
        with self.lock:
            # Contador de requests por método y path
            key = f"{method}_{path}"
            self.request_counts[key] += 1
            
            # Duración de requests
            self.request_durations[key].append(duration)
            
            # Códigos de estado
            self.request_status_codes[status_code] += 1
            
            # Limitar el tamaño de las listas de duración
            if len(self.request_durations[key]) > 1000:
                self.request_durations[key] = self.request_durations[key][-1000:]
    
    def record_traceability_event(self, event_type: str):
        """Registrar evento de trazabilidad"""
        with self.lock:
            self.traceability_events["total"] += 1
            self.traceability_event_types[event_type] += 1
    
    def record_supply_chain_order(self, order_type: str):
        """Registrar orden de cadena de suministro"""
        with self.lock:
            self.supply_chain_orders["total"] += 1
            self.supply_chain_order_types[order_type] += 1
    
    def record_error(self, error_type: str, error_message: str = ""):
        """Registrar error"""
        with self.lock:
            self.error_counts["total"] += 1
            self.error_types[error_type] += 1
    
    def record_database_query(self, query_type: str, duration: float):
        """Registrar consulta de base de datos"""
        with self.lock:
            self.database_queries[query_type] += 1
            self.database_query_durations[query_type].append(duration)
            
            # Limitar el tamaño de las listas de duración
            if len(self.database_query_durations[query_type]) > 1000:
                self.database_query_durations[query_type] = self.database_query_durations[query_type][-1000:]
    
    def set_active_connections(self, count: int):
        """Establecer número de conexiones activas"""
        with self.lock:
            self.active_connections = count
    
    def get_prometheus_metrics(self) -> str:
        """Generar métricas en formato Prometheus"""
        with self.lock:
            metrics = []
            
            # Métricas de uptime
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            metrics.append(f"# HELP novalat_uptime_seconds Uptime del servicio en segundos")
            metrics.append(f"# TYPE novalat_uptime_seconds counter")
            metrics.append(f"novalat_uptime_seconds {uptime}")
            
            # Métricas de requests HTTP
            metrics.append(f"# HELP novalat_http_requests_total Total de requests HTTP")
            metrics.append(f"# TYPE novalat_http_requests_total counter")
            for key, count in self.request_counts.items():
                method, path = key.split("_", 1)
                metrics.append(f'novalat_http_requests_total{{method="{method}",path="{path}"}} {count}')
            
            # Métricas de duración de requests
            metrics.append(f"# HELP novalat_http_request_duration_seconds Duración de requests HTTP")
            metrics.append(f"# TYPE novalat_http_request_duration_seconds histogram")
            for key, durations in self.request_durations.items():
                if durations:
                    method, path = key.split("_", 1)
                    avg_duration = sum(durations) / len(durations)
                    metrics.append(f'novalat_http_request_duration_seconds{{method="{method}",path="{path}"}} {avg_duration}')
            
            # Métricas de códigos de estado
            metrics.append(f"# HELP novalat_http_status_codes_total Total de códigos de estado HTTP")
            metrics.append(f"# TYPE novalat_http_status_codes_total counter")
            for status_code, count in self.request_status_codes.items():
                metrics.append(f'novalat_http_status_codes_total{{status_code="{status_code}"}} {count}')
            
            # Métricas de eventos de trazabilidad
            metrics.append(f"# HELP novalat_traceability_events_total Total de eventos de trazabilidad")
            metrics.append(f"# TYPE novalat_traceability_events_total counter")
            for event_type, count in self.traceability_event_types.items():
                metrics.append(f'novalat_traceability_events_total{{event_type="{event_type}"}} {count}')
            
            # Métricas de órdenes de cadena de suministro
            metrics.append(f"# HELP novalat_supply_chain_orders_total Total de órdenes de cadena de suministro")
            metrics.append(f"# TYPE novalat_supply_chain_orders_total counter")
            for order_type, count in self.supply_chain_order_types.items():
                metrics.append(f'novalat_supply_chain_orders_total{{order_type="{order_type}"}} {count}')
            
            # Métricas de errores
            metrics.append(f"# HELP novalat_errors_total Total de errores")
            metrics.append(f"# TYPE novalat_errors_total counter")
            for error_type, count in self.error_types.items():
                metrics.append(f'novalat_errors_total{{error_type="{error_type}"}} {count}')
            
            # Métricas de base de datos
            metrics.append(f"# HELP novalat_database_queries_total Total de consultas de base de datos")
            metrics.append(f"# TYPE novalat_database_queries_total counter")
            for query_type, count in self.database_queries.items():
                metrics.append(f'novalat_database_queries_total{{query_type="{query_type}"}} {count}')
            
            # Métricas de conexiones activas
            metrics.append(f"# HELP novalat_active_connections Conexiones activas")
            metrics.append(f"# TYPE novalat_active_connections gauge")
            metrics.append(f"novalat_active_connections {self.active_connections}")
            
            return "\n".join(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas en formato JSON"""
        with self.lock:
            # Calcular estadísticas de duración de requests
            request_stats = {}
            for key, durations in self.request_durations.items():
                if durations:
                    method, path = key.split("_", 1)
                    request_stats[f"{method} {path}"] = {
                        "count": self.request_counts[key],
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations),
                        "p95_duration": sorted(durations)[int(len(durations) * 0.95)]
                    }
            
            # Calcular estadísticas de consultas de base de datos
            db_stats = {}
            for query_type, durations in self.database_query_durations.items():
                if durations:
                    db_stats[query_type] = {
                        "count": self.database_queries[query_type],
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations)
                    }
            
            return {
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                "total_requests": sum(self.request_counts.values()),
                "total_traceability_events": self.traceability_events["total"],
                "total_supply_chain_orders": self.supply_chain_orders["total"],
                "total_errors": self.error_counts["total"],
                "active_connections": self.active_connections,
                "request_stats": request_stats,
                "database_stats": db_stats,
                "error_types": dict(self.error_types),
                "traceability_event_types": dict(self.traceability_event_types),
                "supply_chain_order_types": dict(self.supply_chain_order_types),
                "status_codes": dict(self.request_status_codes)
            }
    
    def reset_metrics(self):
        """Resetear todas las métricas"""
        with self.lock:
            self.request_counts.clear()
            self.request_durations.clear()
            self.request_status_codes.clear()
            self.traceability_events.clear()
            self.traceability_event_types.clear()
            self.supply_chain_orders.clear()
            self.supply_chain_order_types.clear()
            self.error_counts.clear()
            self.error_types.clear()
            self.database_queries.clear()
            self.database_query_durations.clear()
            self.active_connections = 0
            self.start_time = datetime.now(timezone.utc)
            
            self.logger.info("Métricas reseteadas")
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de salud del sistema"""
        with self.lock:
            total_requests = sum(self.request_counts.values())
            total_errors = self.error_counts["total"]
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Calcular tiempo de respuesta promedio
            all_durations = []
            for durations in self.request_durations.values():
                all_durations.extend(durations)
            
            avg_response_time = sum(all_durations) / len(all_durations) if all_durations else 0
            
            return {
                "status": "healthy" if error_rate < 5 else "degraded",
                "error_rate_percent": round(error_rate, 2),
                "avg_response_time_seconds": round(avg_response_time, 3),
                "active_connections": self.active_connections,
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                "total_requests": total_requests,
                "total_errors": total_errors
            } 