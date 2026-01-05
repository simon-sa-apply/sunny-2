# 🚂 Configuración de Railway - Backend API

Esta guía explica cómo configurar Railway para desplegar el backend de Sunny-2.

---

## 📋 Requisitos Previos

- [ ] Cuenta en Railway (https://railway.app)
- [ ] Base de datos PostgreSQL con PostGIS (Neon recomendado)
- [ ] Redis/Upstash configurado
- [ ] API keys de Copernicus CDSE
- [ ] API key de Google Gemini

---

## 🚀 Paso 1: Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) y crea un nuevo proyecto
2. Conecta tu repositorio de GitHub (o sube el código)
3. Railway detectará automáticamente el `Dockerfile` en `apps/api/`

---

## ⚙️ Paso 2: Configurar Variables de Entorno

Ve a tu proyecto Railway → **Variables** y agrega las siguientes variables:

### 🔴 Variables CRÍTICAS (Requeridas)

| Variable | Descripción | Ejemplo | Dónde Obtener |
|----------|-------------|---------|---------------|
| `DATABASE_URL` | PostgreSQL connection string con PostGIS | `postgresql://user:pass@host:5432/db?sslmode=require` | Neon Dashboard → Connection String |
| `UPSTASH_REDIS_REST_URL` | URL del endpoint REST de Upstash | `https://xxx.upstash.io` | Upstash Dashboard → REST API |
| `UPSTASH_REDIS_REST_TOKEN` | Token de autenticación de Upstash | `AXxxxxx...` | Upstash Dashboard → REST API |
| `COPERNICUS_API_KEY` | API Key de Copernicus CDSE | `xxxxx-xxxxx-xxxxx` | [Copernicus CDSE](https://cds.climate.copernicus.eu/) |
| `COPERNICUS_API_SECRET` | API Secret de Copernicus CDSE | `xxxxx-xxxxx-xxxxx` | [Copernicus CDSE](https://cds.climate.copernicus.eu/) |
| `GEMINI_API_KEY` | API Key de Google Gemini | `AIza...` | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `CRON_SECRET` | Secret para autenticar cron jobs | `a1b2c3d4...` | Generar con: `openssl rand -hex 32` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `https://sunny-2.vercel.app,https://*.vercel.app` | Tu dominio de Vercel |
| `FRONTEND_URL` | URL del frontend en Vercel | `https://sunny-2.vercel.app` | Tu dominio de Vercel |

### 🟡 Variables Opcionales (con valores por defecto)

| Variable | Valor Recomendado | Descripción |
|----------|-------------------|-------------|
| `ENVIRONMENT` | `production` | Ambiente de ejecución |
| `DEBUG` | `False` | Modo debug (desactivar en producción) |
| `HOST` | `0.0.0.0` | **NO CAMBIAR** - Railway lo maneja automáticamente |
| `PORT` | `8000` | **NO CAMBIAR** - Railway usa `$PORT` automáticamente |

---

## 🔧 Paso 3: Configuración de Railway

Railway debería detectar automáticamente la configuración desde `apps/api/railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### Verificar Configuración:

1. **Root Directory**: Debe ser `apps/api` (o configurar en Railway)
2. **Build Command**: Railway usa el Dockerfile automáticamente
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Health Check**: Railway verificará `/api/health` cada 30 segundos

---

## 📝 Paso 4: Generar CRON_SECRET

Ejecuta este comando en tu terminal para generar un secret seguro:

```bash
openssl rand -hex 32
```

Copia el resultado y configúralo como `CRON_SECRET` en Railway.

---

## 🌐 Paso 5: Configurar CORS_ORIGINS

El valor de `CORS_ORIGINS` debe incluir:

1. **Tu dominio de producción**: `https://sunny-2.vercel.app` (reemplaza con tu dominio real)
2. **Preview deployments**: `https://*.vercel.app` (permite todos los previews de Vercel)
3. **Localhost (opcional)**: `http://localhost:3000` (solo si necesitas desarrollo local)

**Ejemplo completo:**
```
https://sunny-2.vercel.app,https://*.vercel.app,http://localhost:3000
```

---

## ✅ Paso 6: Verificar Despliegue

### 1. Verificar Health Check

Railway debería mostrar el servicio como "Healthy" si el health check pasa:

```bash
curl https://tu-proyecto.railway.app/api/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production"
}
```

### 2. Verificar Logs

En Railway → **Deployments** → **View Logs**, deberías ver:

```
🌞 Starting sunny-2 API v0.1.0
📡 Environment: production
🗄️ Database connection initialized
📦 Redis cache initialized
🤖 AI Consultant (Gemini 2.0) initialized
```

### 3. Verificar URL del Backend

Railway te dará una URL como:
- `https://tu-proyecto.up.railway.app` (URL temporal)
- O puedes configurar un dominio personalizado

**Anota esta URL** - la necesitarás para configurar Vercel.

---

## 🔗 Paso 7: Configurar Vercel

Una vez que Railway esté funcionando:

1. Ve a Vercel → Settings → Environment Variables
2. Agrega `BACKEND_URL` con la URL completa de Railway:
   ```
   BACKEND_URL=https://tu-proyecto.up.railway.app
   ```
3. Haz redeploy del frontend

---

## 🐛 Troubleshooting

### Error: "Database connection failed"

**Causa:** `DATABASE_URL` incorrecta o base de datos no accesible

**Solución:**
1. Verifica que `DATABASE_URL` tenga el formato correcto
2. Asegúrate de que la base de datos tenga PostGIS habilitado
3. Verifica que la base de datos sea accesible desde Railway (no bloqueada por firewall)

### Error: "Redis cache failed"

**Causa:** Credenciales de Upstash incorrectas

**Solución:**
1. Verifica `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` en Upstash Dashboard
2. Asegúrate de usar la URL REST API, no la conexión TCP tradicional

### Error: "CORS policy blocked"

**Causa:** `CORS_ORIGINS` no incluye el dominio de Vercel

**Solución:**
1. Agrega tu dominio de Vercel a `CORS_ORIGINS`
2. Incluye también `https://*.vercel.app` para preview deployments
3. Haz redeploy del backend después de cambiar `CORS_ORIGINS`

### Error: Health check failed

**Causa:** El servidor no está respondiendo en `/api/health`

**Solución:**
1. Verifica los logs de Railway para ver errores de inicio
2. Asegúrate de que todas las variables críticas estén configuradas
3. Verifica que el puerto sea `$PORT` (Railway lo inyecta automáticamente)

### Error: "Port already in use"

**Causa:** El código está usando un puerto hardcodeado en lugar de `$PORT`

**Solución:**
- Railway inyecta `$PORT` automáticamente
- El `railway.json` ya está configurado correctamente
- No cambies el puerto manualmente

---

## 📊 Checklist Final

- [ ] Proyecto creado en Railway
- [ ] Repositorio conectado
- [ ] `DATABASE_URL` configurada (PostgreSQL con PostGIS)
- [ ] `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` configuradas
- [ ] `COPERNICUS_API_KEY` y `COPERNICUS_API_SECRET` configuradas
- [ ] `GEMINI_API_KEY` configurada
- [ ] `CRON_SECRET` generado y configurado
- [ ] `CORS_ORIGINS` incluye el dominio de Vercel
- [ ] `FRONTEND_URL` configurada
- [ ] `ENVIRONMENT=production` configurada
- [ ] `DEBUG=False` configurada
- [ ] Health check pasa (`/api/health`)
- [ ] Logs muestran inicialización correcta
- [ ] URL del backend anotada para configurar Vercel

---

## 🎯 Configuración Recomendada para Producción

```env
# Ambiente
ENVIRONMENT=production
DEBUG=False

# Base de datos (Neon)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Cache (Upstash)
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxxxx...

# APIs Externas
COPERNICUS_API_KEY=xxxxx-xxxxx-xxxxx
COPERNICUS_API_SECRET=xxxxx-xxxxx-xxxxx
GEMINI_API_KEY=AIza...

# Seguridad
CRON_SECRET=a1b2c3d4e5f6... (generado con openssl rand -hex 32)

# CORS
CORS_ORIGINS=https://sunny-2.vercel.app,https://*.vercel.app
FRONTEND_URL=https://sunny-2.vercel.app

# NO CONFIGURAR MANUALMENTE (Railway lo maneja)
# HOST=0.0.0.0
# PORT=8000
```

---

## 📚 Documentación Adicional

- **Variables de entorno detalladas:** Ver [ENV_VARS.md](./ENV_VARS.md)
- **Configuración de Neon:** Ver [SETUP_NEON_UPSTASH.md](./SETUP_NEON_UPSTASH.md)
- **Configuración de Vercel:** Ver [VERCEL_SETUP.md](./VERCEL_SETUP.md)
- **Railway Documentation:** https://docs.railway.app

---

## 🎉 Una vez completado

Tu backend debería estar:
- ✅ Desplegado en Railway
- ✅ Respondiendo en `/api/health`
- ✅ Conectado a PostgreSQL (Neon)
- ✅ Conectado a Redis (Upstash)
- ✅ Integrado con Copernicus y Gemini
- ✅ Listo para recibir requests de Vercel

