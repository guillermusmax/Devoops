#!/usr/bin/env python3
"""
🥤 NovaLat - Script de Demostración
Demostración del sistema de trazabilidad alimentaria
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Configuración
API_BASE_URL = "http://localhost:8000"
DEMO_TOKEN = None

class NovaLatDemo:
    """Clase para demostrar el sistema NovaLat"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        self.token = None
    
    def login(self):
        """Obtener token de autenticación"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/auth/login",
                params={"username": "admin", "password": "password123"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                self.print_success(f"Login exitoso: {data['user']['username']}")
                return True
            else:
                self.print_error(f"Error en login: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error en login: {e}")
            return False
    
    def print_header(self, title: str):
        """Imprimir encabezado"""
        print("\n" + "="*60)
        print(f"🥤 {title}")
        print("="*60)
    
    def print_success(self, message: str):
        """Imprimir mensaje de éxito"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Imprimir mensaje de error"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Imprimir mensaje informativo"""
        print(f"ℹ️  {message}")
    
    def check_health(self) -> bool:
        """Verificar salud del sistema"""
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.print_success(f"Sistema saludable: {health_data['status']}")
                return True
            else:
                self.print_error(f"Error de salud: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error al conectar: {e}")
            return False
    
    def create_traceability_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear evento de trazabilidad"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/traceability/events",
                json=event_data
            )
            
            if response.status_code == 201:
                event = response.json()
                self.print_success(f"Evento creado: {event['id']}")
                return event
            else:
                self.print_error(f"Error al crear evento: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.print_error(f"Error en la petición: {e}")
            return None
    
    def get_product_traceability(self, product_id: str) -> Dict[str, Any]:
        """Obtener trazabilidad de un producto"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/v1/traceability/products/{product_id}")
            
            if response.status_code == 200:
                traceability = response.json()
                self.print_success(f"Trazabilidad obtenida para {product_id}")
                return traceability
            else:
                self.print_error(f"Error al obtener trazabilidad: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Error en la petición: {e}")
            return None
    
    def create_supply_chain_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear orden de cadena de suministro"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/supply-chain/orders",
                json=order_data
            )
            
            if response.status_code == 201:
                order = response.json()
                self.print_success(f"Orden creada: {order['id']}")
                return order
            else:
                self.print_error(f"Error al crear orden: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.print_error(f"Error en la petición: {e}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/v1/metrics/summary")
            
            if response.status_code == 200:
                metrics = response.json()
                self.print_success("Métricas obtenidas")
                return metrics
            else:
                self.print_error(f"Error al obtener métricas: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Error en la petición: {e}")
            return None
    
    def demo_traceability_workflow(self):
        """Demostrar flujo de trabajo de trazabilidad"""
        self.print_header("DEMOSTRACIÓN: Flujo de Trazabilidad Alimentaria")
        
        # 1. Evento de inicio de producción
        self.print_info("1. Registrando inicio de producción...")
        production_start_event = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": "PRODUCTION_START",
            "location": "PLANTA-SANTO-DOMINGO",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Juan Pérez",
                "equipment": "LINEA-01",
                "raw_materials": ["azúcar", "agua", "saborizantes"]
            },
            "operator_id": "OP-001",
            "equipment_id": "EQ-001"
        }
        
        event1 = self.create_traceability_event(production_start_event)
        if not event1:
            return
        
        time.sleep(1)
        
        # 2. Evento de control de calidad
        self.print_info("2. Registrando control de calidad...")
        quality_check_event = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": "QUALITY_CHECK",
            "location": "LABORATORIO-CALIDAD",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 24.8,
                "humidity": 58,
                "operator": "María García",
                "ph_level": 3.2,
                "brix_level": 11.5,
                "microbiological_test": "PASSED",
                "quality_score": 95
            },
            "operator_id": "OP-002",
            "equipment_id": "EQ-002"
        }
        
        event2 = self.create_traceability_event(quality_check_event)
        if not event2:
            return
        
        time.sleep(1)
        
        # 3. Evento de empaquetado
        self.print_info("3. Registrando empaquetado...")
        packaging_event = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": "PACKAGING",
            "location": "AREA-EMPAQUETADO",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 25.2,
                "humidity": 59,
                "operator": "Carlos Rodríguez",
                "package_type": "PET 500ml",
                "units_packaged": 2000,
                "lot_number": "LOT-2024-001",
                "expiration_date": "2025-01-15"
            },
            "operator_id": "OP-003",
            "equipment_id": "EQ-003"
        }
        
        event3 = self.create_traceability_event(packaging_event)
        if not event3:
            return
        
        time.sleep(1)
        
        # 4. Evento de almacenamiento
        self.print_info("4. Registrando almacenamiento...")
        storage_event = {
            "product_id": "NVL-001",
            "batch_id": "BATCH-2024-001",
            "event_type": "STORAGE_IN",
            "location": "ALMACEN-CENTRAL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quantity": 1000.0,
            "unit": "kg",
            "metadata": {
                "temperature": 18.5,
                "humidity": 45,
                "operator": "Ana López",
                "storage_zone": "ZONA-A",
                "rack_number": "RACK-01",
                "position": "A1-B2-C3"
            },
            "operator_id": "OP-004",
            "equipment_id": "EQ-004"
        }
        
        event4 = self.create_traceability_event(storage_event)
        if not event4:
            return
        
        # 5. Obtener trazabilidad completa
        self.print_info("5. Obteniendo trazabilidad completa del producto...")
        traceability = self.get_product_traceability("NVL-001")
        
        if traceability:
            print(f"\n📊 RESUMEN DE TRAZABILIDAD:")
            print(f"   Producto: {traceability['product_id']}")
            print(f"   Lote: {traceability['batch_id']}")
            print(f"   Total de eventos: {traceability['total_events']}")
            print(f"   Estado de cumplimiento: {traceability['compliance_status']}")
            print(f"   Puntuación de calidad: {traceability['quality_score']}")
            
            print(f"\n📋 EVENTOS REGISTRADOS:")
            for i, event in enumerate(traceability['events'], 1):
                print(f"   {i}. {event['event_type']} - {event['location']} - {event['timestamp']}")
    
    def demo_supply_chain_workflow(self):
        """Demostrar flujo de trabajo de cadena de suministro"""
        self.print_header("DEMOSTRACIÓN: Flujo de Cadena de Suministro")
        
        # 1. Crear orden de materia prima
        self.print_info("1. Creando orden de materia prima...")
        raw_material_order = {
            "order_type": "RAW_MATERIAL",
            "supplier_id": "SUP-001",
            "product_id": "NVL-001",
            "quantity": 5000.0,
            "unit": "kg",
            "expected_delivery_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "priority": "HIGH",
            "notes": "Material para producción de la semana próxima",
            "metadata": {
                "quality_requirements": "ISO 22000",
                "packaging_type": "BULK",
                "certification_required": True
            }
        }
        
        order1 = self.create_supply_chain_order(raw_material_order)
        if not order1:
            return
        
        time.sleep(1)
        
        # 2. Crear orden de empaque
        self.print_info("2. Creando orden de empaque...")
        packaging_order = {
            "order_type": "PACKAGING",
            "supplier_id": "SUP-002",
            "quantity": 10000.0,
            "unit": "units",
            "expected_delivery_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "priority": "NORMAL",
            "notes": "Botellas PET 500ml para refresco",
            "metadata": {
                "material": "PET",
                "capacity": "500ml",
                "color": "transparente",
                "certification": "FDA approved"
            }
        }
        
        order2 = self.create_supply_chain_order(packaging_order)
        if not order2:
            return
        
        # 3. Obtener métricas del sistema
        self.print_info("3. Obteniendo métricas del sistema...")
        metrics = self.get_metrics()
        
        if metrics:
            print(f"\n📈 MÉTRICAS DEL SISTEMA:")
            print(f"   Uptime: {metrics['uptime_seconds']:.0f} segundos")
            print(f"   Total de requests: {metrics['total_requests']}")
            print(f"   Eventos de trazabilidad: {metrics['total_traceability_events']}")
            print(f"   Órdenes de cadena de suministro: {metrics['total_supply_chain_orders']}")
            print(f"   Errores: {metrics['total_errors']}")
            print(f"   Conexiones activas: {metrics['active_connections']}")
    
    def demo_compliance_reporting(self):
        """Demostrar reportes de cumplimiento"""
        self.print_header("DEMOSTRACIÓN: Reportes de Cumplimiento Regulatorio")
        
        # Obtener trazabilidad para análisis de cumplimiento
        traceability = self.get_product_traceability("NVL-001")
        
        if traceability:
            print(f"\n🔍 ANÁLISIS DE CUMPLIMIENTO:")
            print(f"   Producto: {traceability['product_id']}")
            print(f"   Lote: {traceability['batch_id']}")
            print(f"   Estado: {traceability['compliance_status']}")
            print(f"   Calidad: {traceability['quality_score']}/100")
            
            # Simular reporte de cumplimiento
            print(f"\n📋 CUMPLIMIENTO REGULATORIO:")
            print(f"   ✅ DIGEMAPS (República Dominicana): CUMPLE")
            print(f"   ✅ Codex Alimentarius: CUMPLE")
            print(f"   ✅ ISO 22000: CUMPLE")
            print(f"   ✅ Auditoría de trazabilidad: COMPLETA")
            
            print(f"\n📊 EVENTOS DE CALIDAD:")
            quality_events = [e for e in traceability['events'] if e['event_type'] == 'QUALITY_CHECK']
            for event in quality_events:
                print(f"   • {event['timestamp']}: Control de calidad en {event['location']}")
                if 'quality_score' in event['metadata']:
                    print(f"     Puntuación: {event['metadata']['quality_score']}/100")
    
    def run_full_demo(self):
        """Ejecutar demostración completa"""
        self.print_header("🥤 NOVALAT - DEMOSTRACIÓN COMPLETA DEL SISTEMA")
        self.print_info("Sistema de Trazabilidad Alimentaria para Consumo Masivo")
        self.print_info("Cumplimiento: DIGEMAPS, Codex Alimentarius, ISO 22000")
        
        # Verificar salud del sistema
        if not self.check_health():
            self.print_error("El sistema no está disponible. Asegúrate de que esté ejecutándose.")
            return
        
        # Login para obtener token
        if not self.login():
            self.print_error("No se pudo autenticar. Verifica que el sistema esté funcionando.")
            return
        
        # Ejecutar demostraciones
        self.demo_traceability_workflow()
        self.demo_supply_chain_workflow()
        self.demo_compliance_reporting()
        
        self.print_header("DEMOSTRACIÓN COMPLETADA")
        self.print_success("¡Sistema NovaLat funcionando correctamente!")
        self.print_info("Puedes acceder a:")
        self.print_info("  • API: http://localhost:8000/docs")
        self.print_info("  • Grafana: http://localhost:3000 (admin/admin)")
        self.print_info("  • Prometheus: http://localhost:9090")
        self.print_info("  • Kibana: http://localhost:5601")


def main():
    """Función principal"""
    print("🥤 Iniciando demostración de NovaLat...")
    
    demo = NovaLatDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main() 