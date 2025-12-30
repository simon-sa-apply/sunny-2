# Sprint Backlog - sunny-2 MVP

**Proyecto:** sunny-2 - Solar Generation Estimator
**Fecha:** 2025-12-24
**Versión:** MVP 1.0

---

## Resumen Ejecutivo

Este documento contiene el backlog completo para el MVP de sunny-2, organizado en **7 Épicas con 33 Historias de Usuario**. El objetivo es entregar una plataforma funcional de diagnóstico solar con precisión científica para usuarios finales (Luis) y desarrolladores externos (Alex).

**Estado Actual:** 100% completado (33/33 historias). MVP listo para producción.

---

## Épicas del MVP

```mermaid
gantt
    title sunny-2 MVP Roadmap
    dateFormat  YYYY-MM-DD
    section Infraestructura
    E1 Setup Monorepo     :done, e1, 2025-01-06, 5d
    section Motor Calculo
    E2 Copernicus + Pvlib :done, e2, after e1, 10d
    section API
    E3 Data Server        :done, e3, after e1, 7d
    section IA
    E4 Consultor Solar    :done, e4, after e2, 5d
    section Frontend
    E5 Dashboard          :done, e5, after e3, 7d
    section Interactividad
    E6 Reloj Solar        :done, e6, after e5, 3d
    section Persistencia
    E7 PostgreSQL + Admin :active, e7, 2025-12-30, 5d
```

---

## E1: Infraestructura Base 🔴 CRÍTICA

**Objetivo:** Establecer la base técnica del proyecto con monorepo, bases de datos y CI/CD.

### E1-S1: Setup Monorepo con Turborepo

**Como** desarrollador  
**Quiero** un monorepo configurado con Turborepo  
**Para** gestionar frontend y backend en un solo repositorio con builds optimizados

**Criterios de Aceptación:**
- [ ] Ejecutar `npx create-turbo@latest sunny-2 --example with-tailwind` exitosamente
- [ ] Carpeta `apps/web` contiene Next.js 14+ con App Router, TypeScript y Tailwind
- [ ] Carpeta `apps/api` contiene estructura base de FastAPI con Python 3.12+
- [ ] Comando `turbo dev` inicia ambas aplicaciones simultáneamente
- [ ] Comando `turbo build` genera builds de producción para ambas
- [ ] Archivo `turbo.json` configurado con pipelines de `build`, `dev`, `lint`, `test`
- [ ] `.gitignore` incluye `node_modules`, `.venv`, `__pycache__`, `.turbo`

**Notas Técnicas:**
```bash
# Comandos de inicialización
npx create-turbo@latest sunny-2 --example with-tailwind
cd sunny-2/apps/web
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd ../api
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
```

**Story Points:** 3  
**Prioridad:** P0 - Bloquea todo

---

### E1-S2: Configurar PostgreSQL + PostGIS en Neon/Supabase

**Como** desarrollador  
**Quiero** la base de datos PostgreSQL+PostGIS configurada en un proveedor serverless  
**Para** almacenar modelos de interpolación y datos geográficos

**Criterios de Aceptación:**
- [ ] Cuenta creada en Neon o Supabase con proyecto `sunny-2`
- [ ] Extensión PostGIS habilitada: `CREATE EXTENSION IF NOT EXISTS postgis;`
- [ ] Variables de entorno `DATABASE_URL` configuradas en `.env.local`
- [ ] Modelo SQLAlchemy base creado (`SolarAnalysis`, `CachedLocation`)
- [ ] Alembic inicializado con primera migración exitosa
- [ ] Test de conexión desde FastAPI funcionando

**Notas Técnicas:**
```python
# apps/api/app/models/solar_analysis.py
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

class CachedLocation(Base):
    __tablename__ = "cached_locations"
    id = Column(Integer, primary_key=True)
    geom = Column(Geometry('POINT', srid=4326))
    interpolation_model = Column(JSONB)
    data_tier = Column(String)  # 'engineering' | 'standard'
    created_at = Column(DateTime)
```

**Story Points:** 3  
**Prioridad:** P0 - Bloquea E2, E3

---

### E1-S3: Configurar Redis (Upstash) para Cache

**Como** desarrollador  
**Quiero** Redis configurado como cache de baja latencia  
**Para** almacenar modelos de interpolación y evitar re-cálculos costosos

**Criterios de Aceptación:**
- [ ] Cuenta creada en Upstash con base de datos Redis
- [ ] Variables de entorno `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` configuradas
- [ ] Cliente Redis inicializado en FastAPI usando `redis-py` o `upstash-redis`
- [ ] Test de `SET`/`GET` funcionando con TTL de 24 horas
- [ ] Helper function `get_cached_model(lat, lon, radius_km=5)` implementada

**Notas Técnicas:**
```python
# apps/api/app/core/cache.py
from upstash_redis import Redis

redis = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)

async def get_cached_model(lat: float, lon: float, radius_km: float = 5.0):
    # Redondear coordenadas para cache hit en área cercana
    cache_key = f"solar:{round(lat, 2)}:{round(lon, 2)}"
    return await redis.get(cache_key)
```

**Story Points:** 2  
**Prioridad:** P0 - Bloquea E2

---

### E1-S4: Configurar CI/CD en Vercel

**Como** desarrollador  
**Quiero** CI/CD configurado con Vercel  
**Para** tener preview deployments automáticos en cada PR

**Criterios de Aceptación:**
- [ ] Repositorio conectado a Vercel
- [ ] `vercel.json` configurado para monorepo (root directory, build commands)
- [ ] Variables de entorno de producción configuradas en Vercel Dashboard
- [ ] Preview deployment generado automáticamente en cada PR
- [ ] Deploy a producción en merge a `main`
- [ ] Health check endpoint `/api/health` respondiendo 200

**Notas Técnicas:**
```json
// vercel.json
{
  "buildCommand": "turbo build",
  "outputDirectory": "apps/web/.next",
  "framework": "nextjs",
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://api.sunny-2.vercel.app/:path*" }
  ]
}
```

**Story Points:** 5  
**Prioridad:** P1 - Importante para flujo de trabajo

---

## E2: Motor de Cálculo Solar 🔴 CRÍTICA

**Objetivo:** Implementar el core científico del producto con conexión a Copernicus y cálculos de Pvlib.

### E2-S1: Conexión a Copernicus CDSE (ERA5-Land/CAMS)

**Como** sistema  
**Quiero** conectarme a Copernicus CDSE  
**Para** descargar datos históricos de radiación solar de cualquier punto geográfico

**Criterios de Aceptación:**
- [ ] Credenciales de Copernicus API configuradas (cuenta registrada en CDS)
- [ ] Implementar request con estructura JSON correcta (sky_type, location, date, etc.)
- [ ] Descarga exitosa de datos para coordenadas de prueba (Santiago, Berlin)
- [ ] Parsing de respuesta CSV a DataFrame de Pandas
- [ ] Manejo de errores para coordenadas fuera de cobertura (lat > 60°)
- [ ] Logging de tiempo de respuesta de API

**Notas Técnicas:**
```python
# apps/api/app/services/copernicus.py
request_params = {
    "sky_type": "observed_cloud",
    "location": {
        "longitude": round(float(lon), 5),
        "latitude": round(float(lat), 5)
    },
    "altitude": ["-999."],
    "date": [f"{year}-01-01/{year}-12-31"],
    "time_step": "1hour",
    "time_reference": "universal_time",
    "data_format": "csv"
}
```

**Story Points:** 5  
**Prioridad:** P0 - Core del producto

---

### E2-S2: Cálculo de GHI/DNI con Pvlib

**Como** sistema  
**Quiero** calcular GHI (Global Horizontal Irradiance) y DNI (Direct Normal Irradiance)  
**Para** estimar la generación solar potencial de un punto geográfico

**Criterios de Aceptación:**
- [ ] Pvlib-python instalado y configurado
- [ ] Función `calculate_solar_potential(lat, lon, area_m2, tilt, orientation)` implementada
- [ ] Cálculo mensual (array de 12 valores) de generación estimada en kWh
- [ ] Aplicación de eficiencia de panel TOPCon (22-24%)
- [ ] Margen de error validado < 5% contra datos de referencia
- [ ] Output incluye `annual_generation_kwh`, `monthly_breakdown`, `peak_month`, `worst_month`

**Notas Técnicas:**
```python
# apps/api/app/services/solar_calculator.py
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location

def calculate_solar_potential(lat, lon, area_m2, tilt, orientation, panel_efficiency=0.22):
    location = Location(lat, lon)
    # ... implementación con pvlib
    return {
        "annual_generation_kwh": total,
        "monthly_breakdown": monthly_values,
        "peak_month": {"month": "December", "kwh": peak},
        "worst_month": {"month": "June", "kwh": worst}
    }
```

**Story Points:** 5  
**Prioridad:** P0 - Core del producto

---

### E2-S3: Modelo de Interpolación Local

**Como** sistema  
**Quiero** generar un modelo de interpolación local tras descargar datos de CDSE  
**Para** permitir simulaciones de inclinación/orientación sin re-llamar a la API externa

**Criterios de Aceptación:**
- [ ] Función `generate_interpolation_model(raw_data, lat, lon)` implementada
- [ ] Modelo almacena matriz de respuesta para inclinación (0-90°) y orientación (0-360°)
- [ ] Modelo serializable a JSON para almacenamiento en Redis/PostgreSQL
- [ ] Función `interpolate(model, tilt, orientation)` responde en < 200ms
- [ ] Validación: interpolación produce resultados coherentes con cálculo directo (±2%)

**Notas Técnicas:**
```python
# apps/api/app/services/interpolation.py
import numpy as np
from scipy.interpolate import RegularGridInterpolator

def generate_interpolation_model(solar_data, lat, lon):
    tilts = np.arange(0, 91, 5)  # 0° a 90° en pasos de 5°
    orientations = np.arange(0, 360, 15)  # 0° a 360° en pasos de 15°
    
    # Pre-calcular matriz de resultados
    results = np.zeros((len(tilts), len(orientations), 12))  # 12 meses
    for i, tilt in enumerate(tilts):
        for j, orient in enumerate(orientations):
            results[i, j, :] = calculate_for_params(solar_data, tilt, orient)
    
    return {
        "tilts": tilts.tolist(),
        "orientations": orientations.tolist(),
        "values": results.tolist(),
        "lat": lat,
        "lon": lon
    }
```

**Story Points:** 5  
**Prioridad:** P0 - Habilita E6

---

### E2-S4: Cache On-Demand Geográfico

**Como** sistema  
**Quiero** cachear datos de Copernicus con estrategia on-demand  
**Para** optimizar recursos y reducir latencia para consultas repetidas

**Criterios de Aceptación:**
- [ ] Check de cache antes de llamar a Copernicus
- [ ] Cache hit para puntos dentro de radio de 5km usa modelo existente
- [ ] Cache miss dispara descarga y procesamiento
- [ ] Modelo guardado en Redis con TTL de 30 días
- [ ] Modelo guardado en PostgreSQL para persistencia permanente
- [ ] Métricas de cache hit/miss logging

**Notas Técnicas:**
```python
# apps/api/app/services/cache_manager.py
async def get_or_create_model(lat: float, lon: float) -> InterpolationModel:
    # 1. Check Redis cache
    cached = await redis.get(cache_key(lat, lon))
    if cached:
        return InterpolationModel.parse_raw(cached)
    
    # 2. Check PostgreSQL for nearby point (5km radius)
    nearby = await db.query(CachedLocation).filter(
        func.ST_DWithin(CachedLocation.geom, point, 5000)
    ).first()
    if nearby:
        await redis.set(cache_key(lat, lon), nearby.interpolation_model)
        return nearby.interpolation_model
    
    # 3. Cache miss - fetch from Copernicus
    raw_data = await copernicus.fetch(lat, lon)
    model = generate_interpolation_model(raw_data, lat, lon)
    await save_to_cache(lat, lon, model)
    return model
```

**Story Points:** 3  
**Prioridad:** P1 - Optimización importante

---

### E2-S5: Plugins de Constantes por País

**Como** sistema  
**Quiero** aplicar constantes regulatorias específicas por país automáticamente  
**Para** entregar estimaciones localizadas (Net Billing, eficiencia de red, etc.)

---

### E2-S6: Integración PVGIS para Cobertura Global ✅ COMPLETADA

**Como** sistema  
**Quiero** integrar PVGIS como fuente de datos secundaria  
**Para** garantizar cobertura global de datos solares cuando CAMS no esté disponible

**Criterios de Aceptación:**
- [x] Servicio `PVGISService` implementado con endpoint `PVcalc`
- [x] Detección automática de base de datos óptima (NSRDB para Americas, ERA5 global)
- [x] Parsing correcto de respuesta JSON con datos mensuales
- [x] `SolarDataService` unificado con estrategia de cascada (CAMS → PVGIS → Mock)
- [x] Fallback automático cuando CAMS falla por ubicación fuera de cobertura
- [x] Test exitoso para Santiago (Chile), New York (USA), Sydney (Australia)
- [x] Documentación actualizada en `fundamentos-stack.md`

**Notas Técnicas:**
```python
# apps/api/app/services/pvgis.py
class PVGISService:
    BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_2"
    
    DATABASES = {
        "PVGIS-NSRDB": "Americas (1998-2019)",
        "PVGIS-SARAH2": "Europe/Africa (2005-2020)",
        "PVGIS-ERA5": "Global fallback (2005-2020)"
    }
    
    async def fetch_solar_radiation(self, lat, lon, year):
        database = self._select_database(lat, lon)
        response = await self._client.get(f"{self.BASE_URL}/PVcalc", params={...})
        return self._parse_response(response.json())
```

**Resultados de Prueba:**
| Ubicación | Fuente | GHI Anual | Estado |
|-----------|--------|-----------|--------|
| Madrid 🇪🇸 | CAMS | 1,825 kWh/m² | ✅ |
| Santiago 🇨🇱 | PVGIS-ERA5 | 2,086 kWh/m² | ✅ |
| New York 🇺🇸 | PVGIS-NSRDB | 1,460 kWh/m² | ✅ |
| Sydney 🇦🇺 | PVGIS-ERA5 | 1,708 kWh/m² | ✅ |

**Story Points:** 3  
**Prioridad:** P0 - Cobertura global
**Fecha Completada:** 2025-12-29

**Criterios de Aceptación:**
- [ ] Estructura de plugins en `apps/api/app/plugins/countries/`
- [ ] Plugin Chile: constantes de Net Billing (Ley 21.118), factor SEC
- [ ] Plugin Alemania: constantes DIN V 18599, factor de red
- [ ] Plugin Global: constantes genéricas para zonas sin plugin específico
- [ ] Detección automática de país por coordenadas (reverse geocoding o lookup table)
- [ ] Response incluye campo `applied_plugin` con metadata normativa

**Notas Técnicas:**
```python
# apps/api/app/plugins/countries/chile.py
PLUGIN_CONFIG = {
    "country_code": "CL",
    "name": "Chile",
    "data_tier": "engineering",
    "constants": {
        "net_billing_factor": 0.85,
        "grid_efficiency": 0.97,
        "co2_factor_kg_per_kwh": 0.42,
        "regulatory_reference": "Ley 21.118 - Net Billing"
    }
}
```

**Story Points:** 3  
**Prioridad:** P1 - Diferenciador clave

---

## E3: API & Data Server 🔴 CRÍTICA

**Objetivo:** Exponer el motor de cálculo como API REST con autenticación y documentación.

### E3-S1: Endpoint POST /estimate

**Como** Alex (developer)  
**Quiero** un endpoint que reciba coordenadas y parámetros  
**Para** obtener estimaciones solares programáticamente

**Criterios de Aceptación:**
- [ ] Endpoint `POST /api/v1/estimate` implementado
- [ ] Request body validado con Pydantic: `lat`, `lon`, `area_m2`, `tilt` (opcional), `orientation` (opcional)
- [ ] Response incluye: `annual_generation_kwh`, `monthly_breakdown`, `data_tier`, `confidence_score`, `ai_insights` (null si no disponible)
- [ ] OpenAPI spec generado automáticamente en `/docs`
- [ ] Errores retornan formato RFC 7807 Problem Details
- [ ] Response headers incluyen `X-Data-Tier` y `X-Confidence-Score`

**Notas Técnicas:**
```python
# apps/api/app/routers/estimate.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

class EstimateRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    area_m2: float = Field(..., gt=0, le=10000)
    tilt: float = Field(default=None, ge=0, le=90)
    orientation: str = Field(default=None, pattern="^(N|S|E|W|NE|NW|SE|SW)$")

class EstimateResponse(BaseModel):
    annual_generation_kwh: float
    monthly_breakdown: dict[str, float]
    data_tier: str  # 'engineering' | 'standard'
    confidence_score: float
    metadata: dict
    ai_insights: dict | None = None

@router.post("/estimate", response_model=EstimateResponse)
async def create_estimate(request: EstimateRequest):
    # ... implementación
```

**Story Points:** 3  
**Prioridad:** P0 - Core API

---

### E3-S2: Autenticación con API Keys

**Como** Alex  
**Quiero** autenticarme con una API Key  
**Para** acceder a los endpoints de forma segura

**Criterios de Aceptación:**
- [ ] Tabla `api_keys` en PostgreSQL con campos: `key`, `name`, `rate_limit`, `created_at`, `last_used`
- [ ] Middleware de validación de header `X-API-Key`
- [ ] Error 401 Unauthorized si key no existe o está desactivada
- [ ] Logging de uso por API Key
- [ ] Endpoint admin para crear/revocar keys (protegido)

**Notas Técnicas:**
```python
# apps/api/app/middleware/auth.py
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(request: Request, api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    
    key_record = await db.query(ApiKey).filter(ApiKey.key == api_key).first()
    if not key_record or not key_record.is_active:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return key_record
```

**Story Points:** 3  
**Prioridad:** P0 - Seguridad básica

---

### E3-S3: Rate Limiting con SlowAPI

**Como** sistema  
**Quiero** implementar rate limiting  
**Para** proteger las cuotas de Copernicus y evitar abusos

**Criterios de Aceptación:**
- [ ] SlowAPI configurado como middleware global
- [ ] Límite default: 100 requests/minuto por API Key
- [ ] Límite configurable por tier de API Key
- [ ] Response 429 Too Many Requests con header `Retry-After`
- [ ] Dashboard de métricas de rate limiting (opcional MVP)

**Notas Técnicas:**
```python
# apps/api/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_api_key_or_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/estimate")
@limiter.limit("100/minute")
async def estimate(request: Request):
    # ...
```

**Story Points:** 2  
**Prioridad:** P1 - Protección importante

---

### E3-S4: Server-Sent Events (SSE) para Progreso

**Como** Luis  
**Quiero** recibir actualizaciones de progreso en tiempo real  
**Para** saber que el sistema está trabajando mientras procesa mi solicitud

**Criterios de Aceptación:**
- [ ] Endpoint `GET /api/v1/estimate/{request_id}/progress` con SSE
- [ ] Eventos emitidos: `connecting`, `fetching_data`, `calculating`, `generating_insights`, `complete`
- [ ] Cada evento incluye `progress_percent` y `message`
- [ ] Conexión se cierra automáticamente al completar
- [ ] Cliente puede reconectarse con `Last-Event-ID` header
- [ ] Timeout de 5 minutos si no hay progreso

**Notas Técnicas:**
```python
# apps/api/app/routers/progress.py
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/estimate/{request_id}/progress")
async def stream_progress(request_id: str):
    async def event_generator():
        while True:
            progress = await get_progress(request_id)
            yield f"data: {progress.json()}\n\n"
            if progress.status == "complete":
                break
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**Story Points:** 3  
**Prioridad:** P1 - UX crítica

---

### E3-S5: Endpoint GET /geosearch

**Como** Luis  
**Quiero** buscar ubicaciones por texto  
**Para** encontrar mi dirección sin conocer las coordenadas exactas

**Criterios de Aceptación:**
- [ ] Endpoint `GET /api/v1/geosearch?q={query}` implementado
- [ ] Integración con servicio de geocoding (Nominatim, Mapbox, Google)
- [ ] Response incluye array de sugerencias con `name`, `lat`, `lon`, `country`
- [ ] Cache de búsquedas frecuentes en Redis (TTL 7 días)
- [ ] Límite de 5 resultados por búsqueda

**Notas Técnicas:**
```python
# apps/api/app/routers/geosearch.py
@router.get("/geosearch")
async def search_location(q: str = Query(..., min_length=3)):
    # Check cache
    cached = await redis.get(f"geo:{q.lower()}")
    if cached:
        return json.loads(cached)
    
    # Call geocoding service
    results = await geocoder.search(q, limit=5)
    
    # Cache results
    await redis.setex(f"geo:{q.lower()}", 604800, json.dumps(results))
    
    return results
```

**Story Points:** 2  
**Prioridad:** P2 - Nice to have

---

## E4: Consultor Solar (IA) 🟡 ALTA

**Objetivo:** Integrar Gemini 2.0 para generar narrativas interpretativas de los cálculos.

### E4-S1: Integración Gemini 2.0 SDK

**Como** sistema  
**Quiero** integrar Gemini 2.0 para generar narrativas  
**Para** transformar datos numéricos en consejos comprensibles

**Criterios de Aceptación:**
- [ ] `google-generativeai` SDK instalado y configurado
- [ ] API Key de Gemini configurada en variables de entorno
- [ ] System Prompt definido con guardrails (no especular, citar fuentes)
- [ ] Función `generate_narrative(calculation_data)` implementada
- [ ] Response estructurado en JSON con `summary`, `seasonal_analysis`, `recommendations`
- [ ] Timeout de 30 segundos con fallback graceful

**Notas Técnicas:**
```python
# apps/api/app/services/ai_consultant.py
import google.generativeai as genai

SYSTEM_PROMPT = """
Eres un Consultor Solar científico. Tu rol es interpretar datos de radiación 
de Copernicus y cálculos de Pvlib para usuarios no técnicos.

REGLAS:
1. SOLO habla de los datos que recibes. NUNCA especules.
2. SIEMPRE cita las fuentes (ESA, Copernicus, CAMS).
3. Si hay incertidumbre, explica por qué (datos históricos, latitud, etc.)
4. Tono: profesional, científico pero accesible.
"""

async def generate_narrative(calc_data: dict) -> dict:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = await model.generate_content_async(
        [SYSTEM_PROMPT, f"Datos de cálculo: {json.dumps(calc_data)}"]
    )
    return parse_structured_response(response.text)
```

**Story Points:** 3  
**Prioridad:** P0 - Diferenciador clave

---

### E4-S2: Narrativa Científica para Luis

**Como** Luis  
**Quiero** que el Consultor Solar me explique mis resultados claramente  
**Para** entender mi potencial solar sin necesitar conocimientos técnicos

**Criterios de Aceptación:**
- [ ] Narrativa explica estacionalidad (por qué algunos meses son mejores)
- [ ] Narrativa menciona "Peor Escenario" y "Mejor Escenario"
- [ ] Narrativa cita fuentes: "Según datos de la ESA/Copernicus..."
- [ ] Narrativa incluye recomendación de inclinación óptima si aplica
- [ ] Tono validado como "profesional pero accesible" (A/B testing futuro)

**Notas Técnicas:**
```json
// Ejemplo de output esperado
{
  "summary": "Tu ubicación en Santiago recibe una radiación solar excepcional, con un potencial anual de 4,250 kWh para tu superficie de 15 m².",
  "seasonal_analysis": "Durante el verano austral (diciembre-febrero), la generación alcanza su pico de 520 kWh/mes. El invierno (junio-agosto) representa tu 'Peor Escenario' con ~180 kWh/mes debido a la mayor nubosidad registrada por los satélites CAMS.",
  "recommendations": "Con tu inclinación actual de 20°, estás captando aproximadamente el 92% del potencial óptimo. Una inclinación de 30° podría mejorar la captación invernal sin sacrificar verano.",
  "citations": ["ERA5-Land, ECMWF", "CAMS McClear, Copernicus"]
}
```

**Story Points:** 3  
**Prioridad:** P1 - UX importante

---

### E4-S3: Validación de Coherencia Cálculo-IA

**Como** sistema  
**Quiero** validar que la narrativa de IA sea coherente con los cálculos de Python  
**Para** evitar "alucinaciones" o información incorrecta

**Criterios de Aceptación:**
- [ ] Función `validate_narrative(calc_data, ai_response)` implementada
- [ ] Validar que kWh mencionados coincidan con cálculos (±5%)
- [ ] Validar que meses mencionados sean correctos
- [ ] Si validación falla, regenerar narrativa (max 2 intentos)
- [ ] Logging de fallos de validación para análisis
- [ ] Fallback a narrativa genérica si validación falla 2 veces

**Notas Técnicas:**
```python
# apps/api/app/services/validation.py
def validate_narrative(calc_data: dict, narrative: dict) -> bool:
    # Check annual generation mentioned is within 5%
    mentioned_kwh = extract_kwh_from_text(narrative["summary"])
    actual_kwh = calc_data["annual_generation_kwh"]
    
    if abs(mentioned_kwh - actual_kwh) / actual_kwh > 0.05:
        logger.warning(f"Narrative mismatch: {mentioned_kwh} vs {actual_kwh}")
        return False
    
    # Check peak/worst months
    # ...
    
    return True
```

**Story Points:** 3  
**Prioridad:** P1 - Calidad crítica

---

### E4-S4: Smart Fallback para Zonas Standard

**Como** Luis en zona "Standard"  
**Quiero** que el Consultor me invite a ingresar mi tarifa eléctrica  
**Para** obtener un cálculo de ahorro económico aunque no haya plugin normativo

**Criterios de Aceptación:**
- [ ] Detectar `data_tier: standard` en response
- [ ] Narrativa incluye mensaje: "No tenemos las leyes de inyección de tu país integradas aún, pero puedes ingresar tu tarifa eléctrica para calcular tu ahorro estimado."
- [ ] UI muestra campo de input de tarifa (kWh precio)
- [ ] Cálculo de ahorro simple: `generation_kwh * tarifa`
- [ ] Botón "Votar por mi país" para feedback de demanda

**Notas Técnicas:**
```python
# En ai_consultant.py
if data_tier == "standard":
    narrative["fallback_message"] = {
        "type": "manual_input_required",
        "message": "Ingresa tu tarifa eléctrica para calcular tu ahorro estimado.",
        "input_field": "electricity_rate_per_kwh",
        "vote_button": {
            "text": "¿Quieres precisión de ingeniería para tu país?",
            "action": "vote_for_country"
        }
    }
```

**Story Points:** 4  
**Prioridad:** P2 - Mejora UX

---

## E5: Frontend Dashboard 🟡 ALTA

**Objetivo:** Construir la interfaz de usuario principal con mapa, formulario y visualizaciones.

### E5-S1: Mapa Interactivo con MapLibre GL

**Como** Luis  
**Quiero** ver un mapa interactivo donde pueda hacer clic para seleccionar mi ubicación  
**Para** indicar exactamente dónde están mis paneles solares

**Criterios de Aceptación:**
- [ ] MapLibre GL JS integrado en Next.js
- [ ] Mapa centrado en ubicación del usuario (geolocation API) o default global
- [ ] Click en mapa captura coordenadas `lat`, `lon`
- [ ] Marker visible en punto seleccionado
- [ ] Detección de WebGL con mensaje fallback para dispositivos sin soporte
- [ ] Mapa responsive (mobile-friendly)

**Notas Técnicas:**
```typescript
// apps/web/src/components/Map.tsx
'use client';
import maplibregl from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';

export function SolarMap({ onLocationSelect }: { onLocationSelect: (lat: number, lon: number) => void }) {
  const mapContainer = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!maplibregl.supported()) {
      // Show fallback message
      return;
    }
    
    const map = new maplibregl.Map({
      container: mapContainer.current!,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [0, 20],
      zoom: 2
    });
    
    map.on('click', (e) => {
      onLocationSelect(e.lngLat.lat, e.lngLat.lng);
    });
    
    return () => map.remove();
  }, []);
  
  return <div ref={mapContainer} className="w-full h-[400px] rounded-lg" />;
}
```

**Story Points:** 3  
**Prioridad:** P0 - Core UI

---

### E5-S2: Formulario de Parámetros

**Como** Luis  
**Quiero** ingresar mis parámetros (m², inclinación, orientación) claramente  
**Para** obtener una estimación personalizada para mi instalación

**Criterios de Aceptación:**
- [ ] Campo `area_m2` con validación (1-10000 m²)
- [ ] Campo `tilt` con slider (0-90°) y valor numérico
- [ ] Campo `orientation` con selector visual (N/S/E/O/NE/NW/SE/SW) o "Óptimo automático"
- [ ] Tooltips explicativos en cada campo
- [ ] Validación en tiempo real con React Hook Form + Zod
- [ ] Botón "Calcular" deshabilitado si formulario inválido

**Notas Técnicas:**
```typescript
// apps/web/src/components/ParameterForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  area_m2: z.number().min(1).max(10000),
  tilt: z.number().min(0).max(90).optional(),
  orientation: z.enum(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW', 'auto']).optional()
});

export function ParameterForm({ onSubmit }: Props) {
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { tilt: 30, orientation: 'auto' }
  });
  // ...
}
```

**Story Points:** 3  
**Prioridad:** P0 - Core UI

---

### E5-S3: Barra de Progreso con SSE

**Como** Luis  
**Quiero** ver el progreso de mi solicitud en tiempo real  
**Para** saber que el sistema está trabajando y no se colgó

**Criterios de Aceptación:**
- [ ] Componente `ProgressBar` con estados visuales distintos
- [ ] Conexión SSE establecida al iniciar cálculo
- [ ] Estados: "Conectando con satélites...", "Descargando datos...", "Calculando...", "Generando insights..."
- [ ] Porcentaje de progreso visible
- [ ] Reconnect automático si conexión se pierde
- [ ] Mensaje de error si timeout (> 2 minutos sin progreso)

**Notas Técnicas:**
```typescript
// apps/web/src/hooks/useProgress.ts
import { useEffect, useState } from 'react';

export function useProgress(requestId: string | null) {
  const [progress, setProgress] = useState({ percent: 0, message: '', status: 'idle' });
  
  useEffect(() => {
    if (!requestId) return;
    
    const eventSource = new EventSource(`/api/v1/estimate/${requestId}/progress`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
      if (data.status === 'complete') {
        eventSource.close();
      }
    };
    
    eventSource.onerror = () => {
      // Reconnect logic
    };
    
    return () => eventSource.close();
  }, [requestId]);
  
  return progress;
}
```

**Story Points:** 3  
**Prioridad:** P1 - UX importante

---

### E5-S4: Dashboard de 5 Contenedores

**Como** Luis  
**Quiero** ver un dashboard profesional con toda la información relevante  
**Para** tomar una decisión informada sobre mi inversión solar

**Criterios de Aceptación:**
- [ ] Layout responsive con 5 secciones: Mapa, Curva Mensual, Picos, Insights IA, Reloj Solar
- [ ] Mapa muestra ubicación seleccionada con marker
- [ ] Curva Mensual muestra gráfico de 12 meses
- [ ] Picos muestra "Mejor Mes" y "Peor Mes" destacados
- [ ] Insights IA muestra narrativa del Consultor Solar
- [ ] Reloj Solar muestra toggle interactivo (E6)
- [ ] Mobile: stack vertical; Desktop: grid 2x3

**Notas Técnicas:**
```typescript
// apps/web/src/components/Dashboard.tsx
export function Dashboard({ data }: { data: EstimateResponse }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <MapContainer location={data.location} />
      </div>
      <div>
        <PeaksCard best={data.peak_month} worst={data.worst_month} />
      </div>
      <div className="md:col-span-2">
        <MonthlyChart data={data.monthly_breakdown} />
      </div>
      <div>
        <SolarClockToggle model={data.interpolation_model} />
      </div>
      <div className="md:col-span-3">
        <AIInsightsCard insights={data.ai_insights} />
      </div>
    </div>
  );
}
```

**Story Points:** 5  
**Prioridad:** P0 - Core UI

---

### E5-S5: Gráfico de Curva Mensual con Recharts

**Como** Luis  
**Quiero** ver un gráfico de mi generación mensual estimada  
**Para** entender la variación estacional de mi producción solar

**Criterios de Aceptación:**
- [ ] Gráfico de área/línea con Recharts
- [ ] Eje X: meses del año (Ene-Dic)
- [ ] Eje Y: kWh generados
- [ ] Destacar visualmente mes de mayor y menor generación
- [ ] Tooltip con valor exacto al hover
- [ ] Responsive (se adapta a contenedor)
- [ ] Colores coherentes con tema de la aplicación

**Notas Técnicas:**
```typescript
// apps/web/src/components/MonthlyChart.tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function MonthlyChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([month, kwh]) => ({
    month,
    kwh,
    isPeak: kwh === Math.max(...Object.values(data)),
    isWorst: kwh === Math.min(...Object.values(data))
  }));
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Area 
          type="monotone" 
          dataKey="kwh" 
          stroke="#f59e0b" 
          fill="#fef3c7" 
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

**Story Points:** 2  
**Prioridad:** P1 - Visualización clave

---

## E6: Reloj Solar Interactivo 🟢 MEDIA

**Objetivo:** Permitir simulaciones en tiempo real de inclinación y orientación.

### E6-S1: Toggle de Inclinación

**Como** Luis  
**Quiero** un slider de inclinación que actualice la estimación instantáneamente  
**Para** explorar cómo diferentes ángulos afectan mi generación

**Criterios de Aceptación:**
- [ ] Slider de 0° a 90° con pasos de 5°
- [ ] Valor numérico visible junto al slider
- [ ] Actualización de estimación en < 200ms
- [ ] Gráfico mensual se actualiza en tiempo real
- [ ] Indicador visual de "inclinación óptima" sugerida

**Notas Técnicas:**
```typescript
// apps/web/src/components/SolarClock.tsx
export function TiltSlider({ model, onTiltChange }: Props) {
  const [tilt, setTilt] = useState(30);
  const debouncedTilt = useDebounce(tilt, 100);
  
  useEffect(() => {
    const result = interpolate(model, debouncedTilt, orientation);
    onTiltChange(result);
  }, [debouncedTilt]);
  
  return (
    <div className="flex items-center gap-4">
      <span className="text-sm">Inclinación</span>
      <input 
        type="range" 
        min={0} 
        max={90} 
        step={5}
        value={tilt}
        onChange={(e) => setTilt(Number(e.target.value))}
        className="w-full"
      />
      <span className="font-mono w-12">{tilt}°</span>
    </div>
  );
}
```

**Story Points:** 3  
**Prioridad:** P1 - Interactividad clave

---

### E6-S2: Toggle de Orientación

**Como** Luis  
**Quiero** un selector de orientación cardinal  
**Para** ver cómo la dirección de mis paneles afecta la captación

**Criterios de Aceptación:**
- [ ] Selector visual con 8 direcciones (N, NE, E, SE, S, SW, W, NW)
- [ ] Opción "Óptimo automático" que calcula mejor orientación
- [ ] Actualización de estimación en < 200ms
- [ ] Visual: brújula interactiva o grid de botones

**Notas Técnicas:**
```typescript
// apps/web/src/components/OrientationSelector.tsx
const ORIENTATIONS = [
  { value: 'N', degrees: 0 },
  { value: 'NE', degrees: 45 },
  { value: 'E', degrees: 90 },
  { value: 'SE', degrees: 135 },
  { value: 'S', degrees: 180 },
  { value: 'SW', degrees: 225 },
  { value: 'W', degrees: 270 },
  { value: 'NW', degrees: 315 },
];

export function OrientationSelector({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {ORIENTATIONS.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.degrees)}
          className={cn(
            "p-2 rounded border",
            value === o.degrees && "bg-amber-500 text-white"
          )}
        >
          {o.value}
        </button>
      ))}
    </div>
  );
}
```

**Story Points:** 2  
**Prioridad:** P1 - Interactividad clave

---

### E6-S3: Feedback Visual de Cambios

**Como** Luis  
**Quiero** ver visualmente cómo cambia mi captación solar al mover parámetros  
**Para** entender intuitivamente el impacto de cada ajuste

**Criterios de Aceptación:**
- [ ] Gráfico mensual se actualiza en tiempo real al mover sliders
- [ ] Indicador de "% de captación vs óptimo"
- [ ] Animación suave de transición (no saltos bruscos)
- [ ] Color del gráfico cambia según eficiencia (verde = óptimo, amarillo = aceptable, rojo = subóptimo)
- [ ] Valor anual de kWh se actualiza en tiempo real

**Notas Técnicas:**
```typescript
// apps/web/src/components/SolarClock.tsx
export function SolarClock({ model }: { model: InterpolationModel }) {
  const [tilt, setTilt] = useState(30);
  const [orientation, setOrientation] = useState(180); // South
  
  const result = useMemo(() => {
    return interpolate(model, tilt, orientation);
  }, [model, tilt, orientation]);
  
  const efficiency = result.annual_kwh / model.optimal_annual_kwh;
  
  return (
    <div className="space-y-4">
      <div className="text-center">
        <span className="text-4xl font-bold">{result.annual_kwh.toLocaleString()}</span>
        <span className="text-lg text-gray-500"> kWh/año</span>
        <div className={cn(
          "text-sm",
          efficiency > 0.9 ? "text-green-600" : efficiency > 0.7 ? "text-yellow-600" : "text-red-600"
        )}>
          {(efficiency * 100).toFixed(0)}% del óptimo
        </div>
      </div>
      <TiltSlider value={tilt} onChange={setTilt} />
      <OrientationSelector value={orientation} onChange={setOrientation} />
      <MonthlyChart data={result.monthly_breakdown} animate />
    </div>
  );
}
```

**Story Points:** 3  
**Prioridad:** P2 - Polish

---

## E7: Persistencia & Administración de Base de Datos 🔴 CRÍTICA

**Objetivo:** Habilitar PostgreSQL + PostGIS para persistencia de modelos de interpolación, gestión de API Keys y auditoría de análisis.

**Dependencias:** E1-S2 (Configurar PostgreSQL) debe estar completada para ejecutar estas historias.

---

### E7-S1: Configuración de Proveedor de Base de Datos (Neon)

**Como** desarrollador  
**Quiero** configurar Neon como proveedor de PostgreSQL serverless  
**Para** tener una base de datos de producción con PostGIS habilitado

**Criterios de Aceptación:**
- [ ] Cuenta creada en [neon.tech](https://neon.tech) con proyecto `sunny-2-prod`
- [ ] Base de datos `sunny2` creada en región cercana (us-east-1 o eu-central-1)
- [ ] Extensión PostGIS habilitada: `CREATE EXTENSION IF NOT EXISTS postgis;`
- [ ] Connection string copiado y configurado en `.env` local
- [ ] Variables de entorno configuradas en Vercel Dashboard (producción)
- [ ] Health check `/health` reporta `database: healthy`

**Notas Técnicas:**
```bash
# Formato del DATABASE_URL para Neon
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/sunny2?sslmode=require

# SQL para habilitar PostGIS (ejecutar en Neon SQL Editor)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

**Configuración Neon recomendada:**
| Setting | Valor |
|---------|-------|
| Postgres version | 17 (última estable) |
| Compute | 0.25 CU (autopilot) |
| Storage | 3GB (free tier) |
| Branching | Habilitado para dev/staging |

**Story Points:** 2  
**Prioridad:** P0 - Bloquea E7-S2 a E7-S6

---

### E7-S2: Migración Inicial de Esquema

**Como** sistema  
**Quiero** crear las tablas iniciales via Alembic  
**Para** tener estructura de datos lista para operación

**Criterios de Aceptación:**
- [ ] Ejecutar `alembic revision --autogenerate -m "initial_schema"`
- [ ] Revisión manual del archivo de migración generado
- [ ] Migración crea tablas: `cached_locations`, `solar_analyses`, `api_keys`
- [ ] Índices espaciales creados: `CREATE INDEX ix_cached_locations_geom ON cached_locations USING GIST (geom);`
- [ ] Ejecutar `alembic upgrade head` sin errores
- [ ] Verificar tablas en Neon SQL Editor

**Notas Técnicas:**
```bash
# Comandos de migración
cd apps/api
source .venv/bin/activate

# Generar migración automática
alembic revision --autogenerate -m "initial_schema"

# Revisar el archivo generado en alembic/versions/
# Asegurar que incluye índices PostGIS

# Aplicar migración
alembic upgrade head

# Verificar estado
alembic current
```

**Esquema esperado:**
```sql
-- cached_locations
CREATE TABLE cached_locations (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    interpolation_model JSONB NOT NULL,
    data_tier VARCHAR(20) NOT NULL DEFAULT 'standard',
    source_dataset VARCHAR(50) NOT NULL DEFAULT 'CAMS',
    country_code VARCHAR(3),
    cache_ttl_days INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice espacial para búsqueda por proximidad
CREATE INDEX ix_cached_locations_geom ON cached_locations USING GIST (geom);
```

**Story Points:** 2  
**Prioridad:** P0 - Bloquea E7-S3

---

### E7-S3: Servicio de Persistencia de Cache (CacheRepository)

**Como** sistema  
**Quiero** guardar modelos de interpolación en PostgreSQL  
**Para** persistir cache más allá del TTL de Redis y habilitar búsqueda geoespacial

**Criterios de Aceptación:**
- [ ] Clase `CacheRepository` implementada en `app/repositories/cache.py`
- [ ] Método `save_model(lat, lon, model, source)` guarda en DB
- [ ] Método `find_nearby(lat, lon, radius_km=5)` busca por proximidad con PostGIS
- [ ] Método `get_or_create(lat, lon)` implementa lógica: Redis → PostgreSQL → API externa
- [ ] Modelo guardado incluye geometría PostGIS para queries espaciales
- [ ] Tests unitarios con cobertura > 80%

**Notas Técnicas:**
```python
# apps/api/app/repositories/cache.py
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.solar_analysis import CachedLocation

class CacheRepository:
    """Repository for cached solar radiation models."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_nearby(
        self, 
        lat: float, 
        lon: float, 
        radius_km: float = 5.0
    ) -> CachedLocation | None:
        """Find cached model within radius using PostGIS."""
        # Convert km to meters for ST_DWithin
        radius_m = radius_km * 1000
        
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        
        stmt = select(CachedLocation).where(
            ST_DWithin(
                CachedLocation.geom,
                point,
                radius_m,
                use_spheroid=True
            )
        ).order_by(
            CachedLocation.created_at.desc()
        ).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_model(
        self,
        lat: float,
        lon: float,
        model: dict,
        source: str = "CAMS",
        data_tier: str = "standard",
        country_code: str | None = None,
    ) -> CachedLocation:
        """Save interpolation model to database."""
        from geoalchemy2.elements import WKTElement
        
        location = CachedLocation(
            latitude=lat,
            longitude=lon,
            geom=WKTElement(f"POINT({lon} {lat})", srid=4326),
            interpolation_model=model,
            source_dataset=source,
            data_tier=data_tier,
            country_code=country_code,
        )
        
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        
        return location
```

**Flujo de Cache Mejorado:**
```
Request(lat, lon)
    │
    ├─► Redis Cache ─► HIT ─► Return
    │        │
    │        └─► MISS
    │              │
    ├──────────────┼─► PostgreSQL (PostGIS) ─► HIT ─► Save to Redis ─► Return
    │              │           │
    │              │           └─► MISS
    │              │                 │
    └──────────────┴─────────────────┼─► CAMS/PVGIS API
                                     │
                                     └─► Save to PostgreSQL ─► Save to Redis ─► Return
```

**Story Points:** 3  
**Prioridad:** P1 - Optimización importante

---

### E7-S4: CRUD de API Keys (Administración)

**Como** administrador  
**Quiero** gestionar API Keys desde endpoints protegidos  
**Para** controlar acceso de desarrolladores externos (Alex)

**Criterios de Aceptación:**
- [ ] Endpoint `POST /admin/api-keys` - Crear nueva key (retorna key en plain text solo una vez)
- [ ] Endpoint `GET /admin/api-keys` - Listar keys activas (sin mostrar key completa)
- [ ] Endpoint `GET /admin/api-keys/{id}` - Detalles de una key (uso, límites)
- [ ] Endpoint `DELETE /admin/api-keys/{id}` - Revocar key (soft delete)
- [ ] Endpoint `PATCH /admin/api-keys/{id}` - Actualizar rate limit o nombre
- [ ] Todos los endpoints protegidos con `X-Master-Key` header
- [ ] API Key hasheada en DB (bcrypt o argon2), nunca plain text
- [ ] Logging de operaciones administrativas

**Notas Técnicas:**
```python
# apps/api/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import secrets
import hashlib

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])

class CreateApiKeyRequest(BaseModel):
    name: str
    rate_limit_per_minute: int = 100
    description: str | None = None

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str  # Solo primeros 8 caracteres
    rate_limit_per_minute: int
    total_requests: int
    is_active: bool
    created_at: datetime

class CreateApiKeyResponse(ApiKeyResponse):
    key: str  # Solo en creación, nunca más

async def verify_master_key(x_master_key: str = Header(...)):
    """Verify master API key for admin endpoints."""
    if x_master_key != settings.MASTER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid master key")
    return True

@router.post("/api-keys", response_model=CreateApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_master_key),
):
    """Create a new API key. The key is only shown once!"""
    # Generate secure random key
    raw_key = f"sunny2_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = ApiKey(
        name=request.name,
        key_hash=key_hash,
        key_prefix=raw_key[:12],
        rate_limit_per_minute=request.rate_limit_per_minute,
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return CreateApiKeyResponse(
        **api_key.to_dict(),
        key=raw_key,  # Solo esta vez
    )
```

**Modelo ApiKey actualizado:**
```python
# apps/api/app/models/api_keys.py
class ApiKey(Base):
    __tablename__ = "api_keys"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # Para identificación
    rate_limit_per_minute: Mapped[int] = mapped_column(default=100)
    total_requests: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Story Points:** 3  
**Prioridad:** P1 - Seguridad

---

### E7-S5: Historial de Análisis por API Key

**Como** Alex (developer)  
**Quiero** consultar mis análisis previos via API  
**Para** no recalcular ubicaciones ya procesadas y auditar mi uso

**Criterios de Aceptación:**
- [ ] Endpoint `GET /api/v1/analyses` - Lista análisis del API Key actual
- [ ] Query params: `?limit=20&offset=0&from_date=2025-01-01&to_date=2025-12-31`
- [ ] Query param opcional: `?lat=40.42&lon=-3.70&radius_km=10` para filtro geográfico
- [ ] Response paginada con `total_count`, `limit`, `offset`, `items[]`
- [ ] Cada item incluye `request_id` para recuperar detalles completos
- [ ] Endpoint `GET /api/v1/analyses/{request_id}` - Detalle de un análisis específico
- [ ] Solo retorna análisis del API Key que hace la solicitud

**Notas Técnicas:**
```python
# apps/api/app/routers/analyses.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/analyses", tags=["Analyses"])

class AnalysisListResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    items: list[AnalysisSummary]

@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_date: date | None = None,
    to_date: date | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
):
    """List analyses for the current API key."""
    stmt = select(SolarAnalysis).where(
        SolarAnalysis.api_key_id == api_key.id
    )
    
    if from_date:
        stmt = stmt.where(SolarAnalysis.created_at >= from_date)
    if to_date:
        stmt = stmt.where(SolarAnalysis.created_at <= to_date)
    
    # Filtro geográfico opcional
    if lat is not None and lon is not None:
        stmt = stmt.where(
            func.sqrt(
                func.pow(SolarAnalysis.latitude - lat, 2) +
                func.pow(SolarAnalysis.longitude - lon, 2)
            ) * 111  # Aproximación km por grado
            <= radius_km
        )
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    
    # Paginate
    stmt = stmt.order_by(SolarAnalysis.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    
    return AnalysisListResponse(
        total_count=total,
        limit=limit,
        offset=offset,
        items=[AnalysisSummary.from_orm(a) for a in result.scalars()],
    )
```

**Story Points:** 2  
**Prioridad:** P2 - Mejora UX para developers

---

### E7-S6: Job de Limpieza de Cache Expirado

**Como** sistema  
**Quiero** eliminar registros de cache expirados automáticamente  
**Para** mantener la base de datos optimizada y cumplir con políticas de retención

**Criterios de Aceptación:**
- [ ] Script `scripts/cleanup_expired_cache.py` implementado
- [ ] Elimina `cached_locations` donde `created_at + cache_ttl_days < NOW()`
- [ ] Elimina `solar_analyses` con status `error` mayores a 7 días
- [ ] Log estructurado de registros eliminados (count, tipos)
- [ ] Puede ejecutarse como Vercel Cron Job o manualmente
- [ ] Dry-run mode con `--dry-run` flag para preview

**Notas Técnicas:**
```python
# apps/api/scripts/cleanup_expired_cache.py
"""
Cleanup expired cache entries from PostgreSQL.

Usage:
    python -m scripts.cleanup_expired_cache [--dry-run]
    
Vercel Cron (vercel.json):
    {
      "crons": [
        {
          "path": "/api/cron/cleanup",
          "schedule": "0 3 * * *"
        }
      ]
    }
"""

import asyncio
import argparse
from datetime import datetime, timedelta

from sqlalchemy import delete, select, func
from app.core.database import db
from app.models.solar_analysis import CachedLocation, SolarAnalysis

async def cleanup_expired_cache(dry_run: bool = False) -> dict:
    """Remove expired cache entries."""
    db.init()
    
    async with db.session() as session:
        now = datetime.utcnow()
        
        # Find expired cached_locations
        expired_locations_stmt = select(CachedLocation).where(
            CachedLocation.created_at + func.make_interval(
                days=CachedLocation.cache_ttl_days
            ) < now
        )
        
        expired_locations = (await session.execute(expired_locations_stmt)).scalars().all()
        expired_count = len(expired_locations)
        
        # Find old error analyses (> 7 days)
        old_errors_stmt = select(SolarAnalysis).where(
            SolarAnalysis.status == "error",
            SolarAnalysis.created_at < now - timedelta(days=7)
        )
        
        old_errors = (await session.execute(old_errors_stmt)).scalars().all()
        errors_count = len(old_errors)
        
        if dry_run:
            print(f"[DRY RUN] Would delete:")
            print(f"  - {expired_count} expired cached_locations")
            print(f"  - {errors_count} old error analyses")
        else:
            # Delete expired locations
            if expired_locations:
                await session.execute(
                    delete(CachedLocation).where(
                        CachedLocation.id.in_([loc.id for loc in expired_locations])
                    )
                )
            
            # Delete old errors
            if old_errors:
                await session.execute(
                    delete(SolarAnalysis).where(
                        SolarAnalysis.id.in_([a.id for a in old_errors])
                    )
                )
            
            await session.commit()
            
            print(f"Cleanup completed:")
            print(f"  - Deleted {expired_count} expired cached_locations")
            print(f"  - Deleted {errors_count} old error analyses")
        
        return {
            "expired_locations_deleted": expired_count,
            "error_analyses_deleted": errors_count,
            "dry_run": dry_run,
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(cleanup_expired_cache(dry_run=args.dry_run))
```

**Vercel Cron Endpoint:**
```python
# apps/api/app/routers/cron.py
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/api/cron", tags=["Cron"])

@router.get("/cleanup")
async def cron_cleanup(
    authorization: str = Header(...),
):
    """Vercel Cron endpoint for cache cleanup."""
    # Vercel sends CRON_SECRET in Authorization header
    if authorization != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    from scripts.cleanup_expired_cache import cleanup_expired_cache
    result = await cleanup_expired_cache(dry_run=False)
    
    return {"status": "ok", **result}
```

**Story Points:** 2  
**Prioridad:** P2 - Mantenimiento

---

## Resumen del Backlog

| Épica | Stories | Story Points | Prioridad | Estado |
|-------|---------|--------------|-----------|--------|
| E1: Infraestructura Base | 4 | 13 | 🔴 Crítica | ✅ Completada |
| E2: Motor de Cálculo Solar | 6 | 24 | 🔴 Crítica | ✅ Completada |
| E3: API & Data Server | 5 | 13 | 🔴 Crítica | ✅ Completada |
| E4: Consultor Solar (IA) | 4 | 13 | 🟡 Alta | ✅ Completada |
| E5: Frontend Dashboard | 5 | 16 | 🟡 Alta | ✅ Completada |
| E6: Reloj Solar Interactivo | 3 | 8 | 🟢 Media | ✅ Completada |
| E7: Persistencia & Administración DB | 6 | 14 | 🔴 Crítica | ✅ Completada |
| **TOTAL MVP** | **33** | **101** | - | **100%** |

### Historias Agregadas Post-Planificación

| ID | Historia | Story Points | Razón |
|----|----------|--------------|-------|
| E2-S6 | Integración PVGIS | 3 | Cobertura global para Americas y fallback |
| E7-S1 a E7-S6 | Persistencia DB | 14 | Habilitar PostgreSQL + PostGIS para producción |

---

## Orden de Implementación Sugerido

```mermaid
flowchart LR
    E1S1["E1-S1 Monorepo"] --> E1S2["E1-S2 PostgreSQL"]
    E1S1 --> E1S3["E1-S3 Redis"]
    E1S2 --> E2S1["E2-S1 Copernicus"]
    E1S3 --> E2S1
    E2S1 --> E2S2["E2-S2 Pvlib Calc"]
    E2S2 --> E2S3["E2-S3 Interpolation"]
    E2S3 --> E3S1["E3-S1 /estimate"]
    E3S1 --> E3S2["E3-S2 API Keys"]
    E3S2 --> E4S1["E4-S1 Gemini"]
    E1S1 --> E5S1["E5-S1 Map"]
    E5S1 --> E5S2["E5-S2 Form"]
    E3S1 --> E5S4["E5-S4 Dashboard"]
    E2S3 --> E6S1["E6-S1 Tilt Toggle"]
    
    E1S2 --> E7S1["E7-S1 Neon Setup"]
    E7S1 --> E7S2["E7-S2 Migraciones"]
    E7S2 --> E7S3["E7-S3 CacheRepository"]
    E7S2 --> E7S4["E7-S4 Admin API Keys"]
    E7S3 --> E7S5["E7-S5 Historial"]
    E7S4 --> E7S6["E7-S6 Cleanup Job"]
    
    style E1S1 fill:#22c55e,color:#fff
    style E2S1 fill:#22c55e,color:#fff
    style E3S1 fill:#22c55e,color:#fff
    style E7S1 fill:#f59e0b,color:#fff
    style E7S2 fill:#f59e0b,color:#fff
    style E7S3 fill:#f59e0b,color:#fff
```

---

## Definición de Done (DoD)

Cada historia se considera "Done" cuando:

- [ ] Código implementado y funcionando
- [ ] Tests unitarios escritos (coverage > 80% para lógica crítica)
- [ ] Code review aprobado
- [ ] Documentación actualizada si aplica
- [ ] Deploy a staging exitoso
- [ ] QA verificado en staging
- [ ] Criterios de aceptación cumplidos

---

_Documento generado como parte del Sprint Planning de sunny-2. Fecha: 2025-12-24._

