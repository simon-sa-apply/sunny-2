# 🗄️ Servicios de Base de Datos - Neon, Upstash y PostgreSQL

## 📋 Resumen Ejecutivo

Sunny-2 usa **dos servicios de almacenamiento** diferentes, cada uno con un propósito específico:

1. **PostgreSQL (Neon)** → Base de datos principal para persistencia
2. **Redis (Upstash)** → Cache en memoria para rendimiento

---

## 🐘 PostgreSQL (Base de Datos Principal)

### ¿Qué es PostgreSQL?

PostgreSQL es una base de datos relacional (SQL) que almacena datos de forma persistente. En Sunny-2 se usa para:

- ✅ Almacenar análisis solares históricos (`solar_analyses`)
- ✅ Guardar ubicaciones cacheadas con datos de interpolación (`cached_locations`)
- ✅ Gestionar API keys y uso (`api_keys`)
- ✅ Búsquedas geográficas con PostGIS (extensión espacial)

### ¿Qué es Neon?

**Neon** es un servicio de PostgreSQL serverless en la nube. Es una alternativa moderna a servicios tradicionales como Railway o Render.

**Ventajas de Neon:**
- 🚀 Serverless: Se escala automáticamente
- 💰 Plan gratuito generoso
- 🔄 Branching de bases de datos (como Git)
- ⚡ Auto-scaling: Se suspende cuando no se usa
- 🌍 Disponible en múltiples regiones

**Alternativas a Neon:**
- **Railway** (PostgreSQL managed)
- **Supabase** (PostgreSQL + extras)
- **Render** (PostgreSQL managed)
- **AWS RDS** (PostgreSQL managed)
- **Cualquier PostgreSQL** con PostGIS habilitado

### Configuración en Sunny-2

```python
# apps/api/app/core/config.py
DATABASE_URL: str = ""  # Connection string de PostgreSQL
```

**Ejemplo de DATABASE_URL para Neon:**
```
postgresql://usuario:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

**Ejemplo para Railway:**
```
postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

**Ejemplo para Supabase:**
```
postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

### Características Especiales

El código detecta automáticamente si usas Neon o Supabase y configura SSL correctamente:

```python
# apps/api/app/core/database.py (líneas 52-58)
if "neon.tech" in db_url or "supabase" in db_url:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
```

### Requisitos

- ✅ PostgreSQL 12+ (recomendado 14+)
- ✅ Extensión **PostGIS** habilitada (para búsquedas geográficas)
- ✅ SSL habilitado para conexiones remotas

---

## 🔴 Redis (Cache en Memoria)

### ¿Qué es Redis?

Redis es una base de datos en memoria (key-value) extremadamente rápida. En Sunny-2 se usa para:

- ⚡ Cache de cálculos recientes (hot cache)
- 🚀 Respuestas ultra-rápidas para ubicaciones frecuentes
- 📊 Reducir carga en APIs externas (Copernicus, PVGIS)

### ¿Qué es Upstash?

**Upstash** es un servicio de Redis serverless. Es ideal para aplicaciones serverless porque:

- 🚀 Serverless: No necesitas mantener servidores
- 💰 Plan gratuito generoso
- 🌍 Global: Edge locations en múltiples regiones
- 🔄 REST API: Funciona perfectamente con serverless (no necesita conexiones persistentes)

**Alternativas a Upstash:**
- **Redis Cloud** (Redis managed tradicional)
- **AWS ElastiCache** (Redis managed)
- **Railway Redis** (Redis managed)
- **Render Redis** (Redis managed)
- **Cualquier Redis** tradicional

### Configuración en Sunny-2

```python
# apps/api/app/core/config.py
UPSTASH_REDIS_REST_URL: str = ""   # URL del endpoint REST
UPSTASH_REDIS_REST_TOKEN: str = ""  # Token de autenticación
```

**Ejemplo de Upstash:**
```
UPSTASH_REDIS_REST_URL=https://xxx-xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxxxx...
```

### Características Especiales

Upstash usa una **REST API** en lugar de conexiones TCP tradicionales, lo que es perfecto para serverless:

```python
# apps/api/app/core/cache.py
from upstash_redis import Redis

redis = Redis(
    url=settings.UPSTASH_REDIS_REST_URL,
    token=settings.UPSTASH_REDIS_REST_TOKEN,
)
```

### TTL (Time To Live)

- **Redis (hot cache):** 1 hora (3600 segundos)
- **PostgreSQL (warm cache):** 30 días

---

## 🔄 Arquitectura de Cache en Capas

Sunny-2 usa una estrategia de **cache en capas** (layered caching):

```
Request → Redis (hot) → PostgreSQL (warm) → APIs Externas
           ⚡ 1 hora      📦 30 días         🌐 Fuente real
```

### Flujo de una Request

1. **Usuario solicita estimación** para una ubicación
2. **Redis (hot cache)** - Busca en cache reciente (última hora)
   - ✅ Si encuentra → Retorna inmediatamente (ultra-rápido)
   - ❌ Si no encuentra → Sigue al siguiente nivel
3. **PostgreSQL (warm cache)** - Busca en cache de largo plazo con PostGIS
   - Busca ubicaciones cercanas (radio de 5km)
   - ✅ Si encuentra cercana → Retorna (rápido)
   - ❌ Si no encuentra → Sigue al siguiente nivel
4. **APIs Externas** - Copernicus o PVGIS
   - Calcula datos reales
   - Guarda en Redis y PostgreSQL para futuras requests
   - Retorna resultado

---

## 📊 Comparación de Servicios

### PostgreSQL Providers

| Servicio | Ventajas | Desventajas | Mejor Para |
|----------|----------|-------------|------------|
| **Neon** | Serverless, branching, auto-scaling | Menos control sobre configuración | Proyectos modernos, desarrollo |
| **Railway** | Simple, rápido setup | Menos features avanzadas | Prototipos, proyectos pequeños |
| **Supabase** | PostgreSQL + Auth + Storage | Puede ser overkill | Apps que necesitan auth |
| **Render** | Similar a Railway | Menos features que Neon | Proyectos tradicionales |
| **AWS RDS** | Máximo control, enterprise | Más complejo, más caro | Producción enterprise |

### Redis Providers

| Servicio | Ventajas | Desventajas | Mejor Para |
|----------|----------|-------------|------------|
| **Upstash** | Serverless, REST API, global | Menos control sobre configuración | Aplicaciones serverless |
| **Redis Cloud** | Tradicional, más control | Requiere conexiones persistentes | Aplicaciones tradicionales |
| **AWS ElastiCache** | Enterprise, integración AWS | Más complejo, más caro | Producción enterprise |
| **Railway Redis** | Simple, rápido setup | Menos features | Prototipos |

---

## 🎯 Recomendación para Sunny-2

### Para Desarrollo/Producción Pequeña

**PostgreSQL:**
- ✅ **Neon** (recomendado) - Serverless, fácil, gratuito
- ✅ **Railway** - Alternativa simple

**Redis:**
- ✅ **Upstash** (recomendado) - Serverless, REST API, perfecto para serverless
- ✅ **Railway Redis** - Alternativa simple

### Para Producción Enterprise

**PostgreSQL:**
- ✅ **AWS RDS** o **Neon Enterprise**
- ✅ Con replicación y backups automáticos

**Redis:**
- ✅ **AWS ElastiCache** o **Redis Cloud Enterprise**
- ✅ Con alta disponibilidad

---

## 🔧 Configuración Paso a Paso

### Opción 1: Neon + Upstash (Recomendado)

#### 1. Crear base de datos en Neon

1. Ve a [neon.tech](https://neon.tech)
2. Crea una cuenta (gratis)
3. Crea un nuevo proyecto
4. Copia la connection string:
   ```
   postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```
5. Configura como `DATABASE_URL` en tu backend

#### 2. Crear Redis en Upstash

1. Ve a [upstash.com](https://upstash.com)
2. Crea una cuenta (gratis)
3. Crea un nuevo Redis database
4. Selecciona "Global" o una región cercana
5. Copia:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`
6. Configura en tu backend

### Opción 2: Railway (Todo en uno)

#### 1. Crear PostgreSQL en Railway

1. Ve a [railway.app](https://railway.app)
2. Crea un proyecto
3. Agrega servicio "PostgreSQL"
4. Copia la connection string
5. Configura como `DATABASE_URL`

#### 2. Crear Redis en Railway

1. En el mismo proyecto Railway
2. Agrega servicio "Redis"
3. Obtén la connection string
4. **Nota:** Railway Redis usa conexión TCP tradicional, no REST API
5. Necesitarías modificar el código para usar `redis-py` en lugar de `upstash-redis`

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar solo PostgreSQL sin Redis?

**Sí**, pero perderás rendimiento. Redis es opcional pero altamente recomendado para:
- Respuestas ultra-rápidas (<100ms)
- Reducir carga en APIs externas
- Mejor experiencia de usuario

El código maneja gracefully si Redis no está configurado:
```python
if cache.is_configured:
    # Usa Redis
else:
    # Salta directamente a PostgreSQL
```

### ¿Puedo usar solo Redis sin PostgreSQL?

**No**, PostgreSQL es requerido porque:
- Almacena datos persistentes (análisis históricos)
- Permite búsquedas complejas con PostGIS
- Gestiona API keys y autenticación

### ¿Qué pasa si no configuro ninguno?

La aplicación funcionará pero con limitaciones:
- ❌ No guardará análisis históricos
- ❌ No tendrá cache (más lento)
- ❌ Cada request calculará desde cero
- ✅ Funcionalidad básica seguirá funcionando

### ¿Neon es gratis?

**Sí**, Neon tiene un plan gratuito generoso:
- 0.5 GB de almacenamiento
- 192 MB RAM
- Auto-suspend cuando no se usa
- Perfecto para desarrollo y proyectos pequeños

### ¿Upstash es gratis?

**Sí**, Upstash tiene un plan gratuito:
- 10,000 comandos por día
- 256 MB de almacenamiento
- Perfecto para desarrollo y proyectos pequeños

---

## 📚 Recursos

- [Neon Documentation](https://neon.tech/docs)
- [Upstash Documentation](https://docs.upstash.com)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Redis Documentation](https://redis.io/docs/)

---

## ✅ Checklist de Configuración

- [ ] PostgreSQL creado (Neon, Railway, etc.)
- [ ] PostGIS habilitado en PostgreSQL
- [ ] `DATABASE_URL` configurado en backend
- [ ] Migraciones ejecutadas (`alembic upgrade head`)
- [ ] Redis creado (Upstash recomendado)
- [ ] `UPSTASH_REDIS_REST_URL` configurado
- [ ] `UPSTASH_REDIS_REST_TOKEN` configurado
- [ ] Backend puede conectarse a ambos servicios
- [ ] Health check muestra ambos servicios como "healthy"

