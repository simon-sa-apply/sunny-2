# 🏗️ Arquitectura de Despliegue - Sunny-2

## ❌ Confusión Común

**Neon y Upstash NO se despliegan en Vercel.** Son servicios externos independientes que se configuran mediante variables de entorno.

---

## 🎯 Arquitectura Real

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA SUNNY-2                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   VERCEL     │         │   RAILWAY    │         │   NEON       │
│              │         │   / RENDER   │         │              │
│  Frontend    │────────▶│   Backend    │────────▶│  PostgreSQL  │
│  (Next.js)   │  HTTP   │  (FastAPI)   │  SQL    │  + PostGIS   │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                │ REST API
                                ▼
                         ┌──────────────┐
                         │   UPSTASH    │
                         │              │
                         │    Redis     │
                         │   (Cache)    │
                         └──────────────┘
```

---

## 📍 Dónde se Despliega Cada Componente

### 1. Frontend (Next.js) → **Vercel**

**Qué se despliega:**
- Aplicación Next.js completa
- Archivos estáticos
- Serverless functions (API routes)

**Variables de entorno en Vercel:**
- ✅ `BACKEND_URL` → URL del backend (Railway/Render)
- ✅ `NEXT_PUBLIC_API_URL` → (Opcional) Misma que BACKEND_URL

**NO incluye:**
- ❌ Neon (PostgreSQL)
- ❌ Upstash (Redis)
- ❌ Backend (FastAPI)

---

### 2. Backend (FastAPI) → **Railway / Render / etc.**

**Qué se despliega:**
- API FastAPI completa
- Servidor Python con uvicorn
- Lógica de negocio

**Variables de entorno en Railway/Render:**
- ✅ `DATABASE_URL` → Connection string de Neon (o PostgreSQL)
- ✅ `UPSTASH_REDIS_REST_URL` → URL de Upstash Redis
- ✅ `UPSTASH_REDIS_REST_TOKEN` → Token de Upstash
- ✅ `COPERNICUS_API_KEY` + `COPERNICUS_API_SECRET`
- ✅ `GEMINI_API_KEY`
- ✅ `CRON_SECRET`
- ✅ `CORS_ORIGINS`
- ✅ `FRONTEND_URL`

**Configuración:**
- `railway.json` → Configuración de Railway
- `Dockerfile` → Imagen Docker para el backend

---

### 3. PostgreSQL → **Neon (Servicio Externo)**

**Qué es:**
- Servicio de base de datos PostgreSQL serverless
- NO se despliega, es un servicio SaaS (Software as a Service)
- Se crea una cuenta y proyecto en neon.tech

**Cómo se configura:**
1. Crear cuenta en [neon.tech](https://neon.tech)
2. Crear proyecto
3. Copiar connection string
4. Configurar como `DATABASE_URL` en el **BACKEND** (Railway/Render)

**NO se configura en Vercel** ❌

---

### 4. Redis → **Upstash (Servicio Externo)**

**Qué es:**
- Servicio de Redis serverless
- NO se despliega, es un servicio SaaS
- Se crea una cuenta y database en upstash.com

**Cómo se configura:**
1. Crear cuenta en [upstash.com](https://upstash.com)
2. Crear Redis database
3. Copiar `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN`
4. Configurar en el **BACKEND** (Railway/Render)

**NO se configura en Vercel** ❌

---

## 🔄 Flujo de Configuración Correcto

### Paso 1: Crear Servicios Externos (Neon + Upstash)

Estos son servicios independientes que NO se despliegan:

1. **Neon:**
   - Ve a neon.tech
   - Crea proyecto
   - Copia `DATABASE_URL`

2. **Upstash:**
   - Ve a upstash.com
   - Crea Redis database
   - Copia `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN`

### Paso 2: Desplegar Backend (Railway/Render)

1. Despliega el backend en Railway o Render
2. Configura TODAS las variables de entorno:
   - `DATABASE_URL` (de Neon)
   - `UPSTASH_REDIS_REST_URL` (de Upstash)
   - `UPSTASH_REDIS_REST_TOKEN` (de Upstash)
   - Y todas las demás...

### Paso 3: Desplegar Frontend (Vercel)

1. Despliega el frontend en Vercel
2. Configura SOLO:
   - `BACKEND_URL` → URL del backend desplegado en Railway/Render

---

## 📊 Tabla de Configuración

| Componente | Dónde se Despliega | Variables de Entorno | Dónde se Configuran |
|------------|-------------------|---------------------|---------------------|
| **Frontend** | Vercel | `BACKEND_URL` | Vercel Dashboard |
| **Backend** | Railway/Render | `DATABASE_URL`, `UPSTASH_REDIS_*`, etc. | Railway/Render Dashboard |
| **PostgreSQL** | Neon (SaaS) | Connection string | Se obtiene de Neon, se configura en Backend |
| **Redis** | Upstash (SaaS) | REST URL + Token | Se obtiene de Upstash, se configura en Backend |

---

## ❌ Errores Comunes

### Error 1: Intentar configurar Neon en Vercel

**Incorrecto:**
```
Vercel → Environment Variables → DATABASE_URL
```

**Correcto:**
```
Railway/Render → Environment Variables → DATABASE_URL
```

### Error 2: Pensar que Neon se despliega

**Incorrecto:**
- "Neon se despliega en Vercel"
- "Upstash se despliega en Railway"

**Correcto:**
- Neon y Upstash son servicios SaaS externos
- Solo necesitas crear cuenta y obtener credenciales
- Las credenciales se configuran en el BACKEND, no en Vercel

### Error 3: Configurar variables del backend en Vercel

**Incorrecto:**
```
Vercel → Environment Variables:
- DATABASE_URL
- UPSTASH_REDIS_REST_URL
- GEMINI_API_KEY
```

**Correcto:**
```
Vercel → Environment Variables:
- BACKEND_URL (solo esta)

Railway/Render → Environment Variables:
- DATABASE_URL
- UPSTASH_REDIS_REST_URL
- GEMINI_API_KEY
- (todas las demás)
```

---

## ✅ Checklist Correcto

### Servicios Externos (No se Despliegan)

- [ ] Cuenta creada en Neon
- [ ] Proyecto PostgreSQL creado en Neon
- [ ] Connection string copiado de Neon
- [ ] Cuenta creada en Upstash
- [ ] Redis database creado en Upstash
- [ ] Credenciales de Upstash copiadas

### Backend (Railway/Render)

- [ ] Backend desplegado en Railway/Render
- [ ] `DATABASE_URL` configurado (de Neon)
- [ ] `UPSTASH_REDIS_REST_URL` configurado (de Upstash)
- [ ] `UPSTASH_REDIS_REST_TOKEN` configurado (de Upstash)
- [ ] Todas las demás variables configuradas
- [ ] Backend responde en `/api/health`

### Frontend (Vercel)

- [ ] Frontend desplegado en Vercel
- [ ] `BACKEND_URL` configurado (URL del backend)
- [ ] Frontend puede hacer requests al backend

---

## 🎯 Resumen

| Pregunta | Respuesta |
|----------|-----------|
| ¿Neon se despliega en Vercel? | ❌ NO - Neon es un servicio externo SaaS |
| ¿Upstash se despliega en Vercel? | ❌ NO - Upstash es un servicio externo SaaS |
| ¿Dónde se configuran Neon y Upstash? | ✅ En el BACKEND (Railway/Render), no en Vercel |
| ¿Qué se despliega en Vercel? | ✅ Solo el FRONTEND (Next.js) |
| ¿Qué se despliega en Railway/Render? | ✅ Solo el BACKEND (FastAPI) |
| ¿Neon y Upstash necesitan despliegue? | ❌ NO - Son servicios SaaS, solo necesitas cuenta y credenciales |

---

## 📚 Referencias

- [Neon Documentation](https://neon.tech/docs)
- [Upstash Documentation](https://docs.upstash.com)
- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)

