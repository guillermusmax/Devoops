#!/usr/bin/env python3
"""
🥤 NovaLat - Test Simple
Script simple para probar la API
"""

import requests
import json

# Configuración
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Probar endpoint de salud"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_login():
    """Probar login"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            params={"username": "admin", "password": "password123"}
        )
        print(f"✅ Login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

def test_create_event(token):
    """Probar crear evento"""
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        event_data = {
            "product_id": "NVL-TEST-001",
            "batch_id": "BATCH-TEST-001",
            "event_type": "PRODUCTION_START",
            "location": "PLANTA-TEST",
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "temperature": 25.5,
                "humidity": 60,
                "operator": "Test User"
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/traceability/events",
            headers=headers,
            json=event_data
        )
        print(f"✅ Create event: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   Event ID: {data['id']}")
            return data['id']
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Create event failed: {e}")
        return None

def test_get_traceability(token, product_id):
    """Probar obtener trazabilidad"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/v1/traceability/products/{product_id}",
            headers=headers
        )
        print(f"✅ Get traceability: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Product: {data['product_id']}")
            print(f"   Events: {data['total_events']}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get traceability failed: {e}")
        return False

def main():
    """Función principal"""
    print("🥤 NovaLat - Test Simple")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        return
    
    # Test 2: Login
    token = test_login()
    if not token:
        return
    
    # Test 3: Create event
    event_id = test_create_event(token)
    if not event_id:
        return
    
    # Test 4: Get traceability
    test_get_traceability(token, "NVL-TEST-001")
    
    print("\n🎉 Tests completados!")

if __name__ == "__main__":
    main() 