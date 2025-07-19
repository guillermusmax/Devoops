# 🥤 NovaLat - Sistema de Trazabilidad Alimentaria

**Sistema completo para rastrear productos alimentarios desde la producción hasta el consumidor**

---

## 🚀 Inicio Rápido (3 Pasos)

### **Paso 1: Instalar Docker**
1. Descargar [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Instalar y reiniciar la computadora
3. Verificar que Docker esté ejecutándose (icono verde)

### **Paso 2: Ejecutar el Sistema**
```bash
docker-compose -f docker-compose-simple.yml up -d
```

### **Paso 3: Acceder al Sistema**
- **API:** http://localhost:8000/docs
- **Dashboards:** http://localhost:3000 (admin/admin)
- **Métricas:** http://localhost:9090

---

## 🎯 Cómo Usar

### **1. Ver el Sistema Funcionando**
Ir a: http://localhost:8000/health
**Deberías ver:** `{"status": "healthy"}`

### **2. Explorar la API**
1. Ir a: http://localhost:8000/docs
2. Hacer clic en "Authorize" (🔒)
3. Pegar: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTc1Mjg5MzcxMn0.hIGNNnJ-6bQQ9rZhewoixrKeGNMczKx2pn-XyCwoSP0`
4. Hacer clic en "Authorize"

### **3. Probar Endpoints**
- **Ver eventos:** `GET /api/v1/traceability/events` → "Try it out" → "Execute"
- **Crear evento:** `POST /api/v1/traceability/events` → "Try it out" → usar ejemplo

### **4. Ver Dashboards**
1. Ir a: http://localhost:3000
2. Login: admin / admin
3. Explorar dashboards de trazabilidad

---

## 📈 Demo Automático

```bash
python demo.py
```

**Verás:** Creación automática de eventos, órdenes y reportes de cumplimiento.

---

## 🛠️ Comandos Útiles

```bash
# Iniciar sistema
docker-compose -f docker-compose-simple.yml up -d

# Detener sistema
docker-compose -f docker-compose-simple.yml down

# Ver logs
docker-compose -f docker-compose-simple.yml logs

# Reconstruir
docker-compose -f docker-compose-simple.yml up -d --build
```

---

## ❗ Problemas Comunes

### **Docker no inicia**
- Reiniciar Docker Desktop
- Reiniciar computadora

### **Puerto ocupado**
- Cambiar puerto en `docker-compose-simple.yml`
- O detener otros servicios

### **Error 500**
```bash
docker-compose -f docker-compose-simple.yml logs api
```

---

## 📊 ¿Qué Incluye?

- ✅ **API REST** para gestión de eventos
- ✅ **Base de datos** PostgreSQL
- ✅ **Dashboards** Grafana en tiempo real
- ✅ **Métricas** Prometheus
- ✅ **Autenticación** JWT
- ✅ **Cumplimiento** DIGEMAPS, Codex, ISO 22000

---

## 🎉 ¡Listo!

**El sistema está funcionando en:**
- **API:** http://localhost:8000/docs
- **Dashboards:** http://localhost:3000
- **Métricas:** http://localhost:9090

**¡Puedes empezar a crear eventos de trazabilidad!** 🚀