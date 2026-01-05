# 🔍 Análisis Profundo: Estado de MCP en Sunny-2

## 📊 Estado Actual - Investigación Completa

### ✅ Lo que SÍ existe (Base para MCP)

1. **Backend FastAPI Funcional**
   - ✅ Endpoint `/api/v1/estimate` implementado y funcionando
   - ✅ Servicios core disponibles:
     - `SolarCalculator` - Cálculos solares
     - `AIConsultant` - Narrativas con Gemini 2.0
     - `SolarDataService` - Integración con Copernicus/PVGIS
   - ✅ Autenticación con API Keys
   - ✅ Rate limiting implementado
   - ✅ OpenAPI/Swagger docs disponibles

2. **Funcionalidades Core Implementadas**
   - ✅ Cálculo de potencial solar (`calculate_solar_potential` equivalente)
   - ✅ Generación de narrativas AI (`get_consultant_narrative` equivalente)
   - ✅ Búsqueda geográfica (`/api/v1/geosearch`)
   - ✅ Cache con Redis y PostgreSQL
   - ✅ Análisis históricos (`/api/v1/analyses`)

### ❌ Lo que NO existe (MCP Server)

1. **Servidor MCP**
   - ❌ No hay servidor MCP implementado
   - ❌ No hay dependencias MCP en `pyproject.toml`
   - ❌ No hay código relacionado con MCP en el proyecto
   - ❌ No hay configuración MCP

2. **Herramientas MCP**
   - ❌ `calculate_solar_potential` como tool MCP
   - ❌ `get_consultant_narrative` como tool MCP
   - ❌ Resources MCP (`solar://site-analysis/{lat},{lon}`)

3. **Integración MCP**
   - ❌ No hay cliente MCP configurado
   - ❌ No hay tests de integración MCP
   - ❌ No hay documentación de uso MCP

---

## 🎯 Análisis: ¿Por qué no se implementó?

### Razones Probables

1. **Priorización MVP**
   - El MVP se enfocó en la web app funcional
   - MCP era una feature "nice-to-have" para el futuro
   - No había usuarios inmediatos que necesitaran MCP

2. **Complejidad vs. Valor**
   - MCP requiere aprendizaje de un nuevo protocolo
   - La API REST actual ya permite integraciones
   - El ROI de MCP no estaba claro en el MVP

3. **Dependencias Adicionales**
   - MCP requiere SDK específico de Python
   - Necesita configuración adicional
   - Añade complejidad al stack

4. **Falta de Casos de Uso Inmediatos**
   - El caso de uso "Alex" (agente externo) era hipotético
   - No había demanda real de integración MCP
   - La API REST era suficiente para integraciones básicas

---

## 📋 Plan de Implementación MCP

### Fase 1: Setup y Dependencias (1-2 horas)

#### 1.1 Instalar SDK MCP

```bash
cd apps/api
pip install mcp
```

O usar el SDK oficial de Anthropic:
```bash
pip install anthropic-mcp
```

#### 1.2 Actualizar `pyproject.toml`

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=0.1.0",  # O el SDK oficial cuando esté disponible
]
```

### Fase 2: Crear Servidor MCP (4-6 horas)

#### 2.1 Estructura de Archivos

```
apps/api/app/
├── mcp/
│   ├── __init__.py
│   ├── server.py          # Servidor MCP principal
│   ├── tools.py            # Definición de herramientas
│   └── resources.py        # Definición de recursos
```

#### 2.2 Implementar Servidor Base

**Archivo: `apps/api/app/mcp/server.py`**

```python
"""
MCP Server for Sunny-2
Exposes solar calculation tools via Model Context Protocol
"""
import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, Resource

from app.services.solar_calculator import SolarCalculator
from app.services.ai_consultant import ai_consultant
from app.services.solar_data import solar_data_service

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp_server = Server("sunny-2")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="calculate_solar_potential",
            description="Calculate solar generation potential for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude (-90 to 90)"},
                    "longitude": {"type": "number", "description": "Longitude (-180 to 180)"},
                    "area_m2": {"type": "number", "description": "Panel area in square meters"},
                    "tilt": {"type": "number", "description": "Panel tilt in degrees (0-90)"},
                    "orientation": {"type": "number", "description": "Panel orientation in degrees (0-360, 0=North)"},
                },
                "required": ["latitude", "longitude", "area_m2"],
            },
        ),
        Tool(
            name="get_consultant_narrative",
            description="Generate AI-powered solar consultant narrative from calculation data",
            inputSchema={
                "type": "object",
                "properties": {
                    "calculation_data": {
                        "type": "object",
                        "description": "Solar calculation results from calculate_solar_potential",
                    },
                    "country_plugin": {"type": "string", "description": "Country code (optional)"},
                },
                "required": ["calculation_data"],
            },
        ),
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Handle tool calls."""
    if name == "calculate_solar_potential":
        return await handle_calculate_solar_potential(arguments)
    elif name == "get_consultant_narrative":
        return await handle_get_consultant_narrative(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def handle_calculate_solar_potential(args: dict[str, Any]) -> list[dict[str, Any]]:
    """Handle calculate_solar_potential tool call."""
    lat = args["latitude"]
    lon = args["longitude"]
    area_m2 = args["area_m2"]
    tilt = args.get("tilt", 30)
    orientation = args.get("orientation", 180)
    
    # Use existing services
    solar_data = await solar_data_service.get_solar_data(lat, lon)
    calculator = SolarCalculator()
    result = calculator.calculate(
        solar_data=solar_data,
        area_m2=area_m2,
        tilt=tilt,
        orientation=orientation,
    )
    
    return [{
        "content": [{
            "type": "text",
            "text": json.dumps({
                "annual_generation_kwh": result.annual_generation_kwh,
                "monthly_breakdown": result.monthly_breakdown,
                "data_tier": result.data_tier,
                "confidence_score": result.confidence_score,
            }, indent=2),
        }],
    }]

async def handle_get_consultant_narrative(args: dict[str, Any]) -> list[dict[str, Any]]:
    """Handle get_consultant_narrative tool call."""
    calculation_data = args["calculation_data"]
    country_plugin = args.get("country_plugin")
    
    narrative = await ai_consultant.generate_narrative(
        calculation_data=calculation_data,
        country_plugin=country_plugin,
    )
    
    return [{
        "content": [{
            "type": "text",
            "text": json.dumps(narrative, indent=2),
        }],
    }]
```

#### 2.3 Implementar Resources

**Archivo: `apps/api/app/mcp/resources.py`**

```python
"""
MCP Resources for Sunny-2
Exposes cached solar analyses as resources
"""
from mcp.types import Resource

@mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources."""
    return [
        Resource(
            uri="solar://site-analysis/{lat},{lon}",
            name="Solar Site Analysis",
            description="Cached solar analysis for a specific location",
            mimeType="application/json",
        ),
    ]

@mcp_server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    if uri.startswith("solar://site-analysis/"):
        # Extract lat,lon from URI
        coords = uri.replace("solar://site-analysis/", "").split(",")
        lat, lon = float(coords[0]), float(coords[1])
        
        # Get cached analysis from database
        from app.repositories.cache_repository import cache_repository
        cached = await cache_repository.find_nearby(lat, lon, radius_km=0.1)
        
        if cached:
            return json.dumps(cached.interpolation_model, indent=2)
        else:
            return json.dumps({"error": "No cached analysis found for this location"})
    
    raise ValueError(f"Unknown resource URI: {uri}")
```

### Fase 3: Integración con FastAPI (2-3 horas)

#### 3.1 Crear Endpoint MCP

**Archivo: `apps/api/app/routers/mcp.py`**

```python
"""
MCP Router - Expose MCP server via HTTP/SSE
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.mcp.server import mcp_server

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])

@router.post("/call")
async def mcp_call(request: dict):
    """Handle MCP tool calls via HTTP."""
    # Convert HTTP request to MCP format
    # Call mcp_server.call_tool()
    # Return response
    pass

@router.get("/tools")
async def list_mcp_tools():
    """List available MCP tools."""
    tools = await mcp_server.list_tools()
    return {"tools": tools}
```

#### 3.2 Agregar al Main App

```python
# apps/api/app/main.py
from app.routers import mcp

app.include_router(mcp.router)
```

### Fase 4: Testing y Documentación (2-3 horas)

#### 4.1 Tests Unitarios

```python
# tests/test_mcp.py
import pytest
from app.mcp.server import call_tool

@pytest.mark.asyncio
async def test_calculate_solar_potential():
    result = await call_tool(
        "calculate_solar_potential",
        {
            "latitude": -33.4489,
            "longitude": -70.6693,
            "area_m2": 15,
            "tilt": 20,
        }
    )
    assert "annual_generation_kwh" in result[0]["content"][0]["text"]
```

#### 4.2 Documentación

- Crear `docs/MCP_INTEGRATION.md`
- Ejemplos de uso con diferentes clientes MCP
- Guía de autenticación

### Fase 5: Configuración y Deployment (1-2 horas)

#### 5.1 Variables de Entorno

```env
# MCP Configuration
MCP_ENABLED=true
MCP_SERVER_NAME=sunny-2
MCP_AUTH_TOKEN=...  # Para autenticación de clientes
```

#### 5.2 Docker/Deployment

- Asegurar que el servidor MCP se inicie con FastAPI
- Configurar health check para MCP
- Documentar cómo conectar clientes externos

---

## 📊 Estimación de Esfuerzo

| Fase | Tiempo Estimado | Complejidad |
|------|----------------|------------|
| Setup y Dependencias | 1-2 horas | Baja |
| Crear Servidor MCP | 4-6 horas | Media |
| Integración FastAPI | 2-3 horas | Media |
| Testing y Docs | 2-3 horas | Baja |
| Configuración | 1-2 horas | Baja |
| **TOTAL** | **10-16 horas** | **Media** |

---

## 🎯 Decisiones de Diseño

### Opción A: Servidor MCP Independiente (Recomendado)

**Ventajas:**
- Separación de responsabilidades
- Puede ejecutarse en proceso separado
- Más fácil de escalar independientemente

**Desventajas:**
- Más complejo de configurar
- Requiere gestión de procesos adicional

### Opción B: Integrado en FastAPI (Más Simple)

**Ventajas:**
- Más simple de implementar
- Comparte autenticación y rate limiting
- Un solo proceso para gestionar

**Desventajas:**
- Acoplamiento con FastAPI
- Menos flexible para futuras necesidades

**Recomendación:** Opción B para MVP, migrar a Opción A si hay demanda.

---

## ✅ Checklist de Implementación

### Setup
- [ ] Instalar SDK MCP
- [ ] Actualizar `pyproject.toml`
- [ ] Crear estructura de carpetas `app/mcp/`

### Servidor MCP
- [ ] Implementar `server.py` con servidor base
- [ ] Implementar `tools.py` con definiciones
- [ ] Implementar `resources.py` con recursos
- [ ] Tool: `calculate_solar_potential`
- [ ] Tool: `get_consultant_narrative`
- [ ] Resource: `solar://site-analysis/{lat},{lon}`

### Integración
- [ ] Crear router MCP en FastAPI
- [ ] Agregar endpoint `/api/v1/mcp/tools`
- [ ] Agregar endpoint `/api/v1/mcp/call`
- [ ] Integrar con autenticación existente
- [ ] Integrar con rate limiting

### Testing
- [ ] Tests unitarios para tools
- [ ] Tests de integración MCP
- [ ] Test con cliente MCP real
- [ ] Validar autenticación

### Documentación
- [ ] `docs/MCP_INTEGRATION.md`
- [ ] Ejemplos de uso
- [ ] Guía de autenticación
- [ ] Actualizar README principal

### Deployment
- [ ] Variables de entorno MCP
- [ ] Health check MCP
- [ ] Logging y monitoreo
- [ ] Documentar configuración en producción

---

## 🚀 Próximos Pasos Recomendados

1. **Validar Necesidad Real**
   - ¿Hay usuarios que necesiten MCP ahora?
   - ¿La API REST es suficiente?
   - ¿Cuál es el ROI esperado?

2. **Si se decide implementar:**
   - Empezar con Fase 1 (Setup)
   - Implementar Fase 2 (Servidor básico)
   - Probar con un cliente MCP simple
   - Iterar según feedback

3. **Alternativa Rápida:**
   - Crear un wrapper simple que convierta llamadas MCP a llamadas REST
   - Menos código, más rápido de implementar
   - Puede migrarse a servidor MCP completo después

---

## 📚 Referencias

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Anthropic MCP Documentation](https://docs.anthropic.com/mcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## 💡 Conclusión

**Estado Actual:** MCP estaba planificado pero no implementado. La base técnica existe (FastAPI + servicios), pero falta el servidor MCP.

**Recomendación:** 
- Si hay demanda real → Implementar siguiendo este plan
- Si es para el futuro → Mantenerlo como feature pendiente
- Alternativa rápida → Wrapper MCP→REST para validar necesidad

¿Quieres que proceda con la implementación o prefieres validar primero si hay demanda real?

