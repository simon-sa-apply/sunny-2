# ✅ Checklist de Despliegue - Sunny-2

## 🎯 Resumen Rápido

### Frontend (Vercel)
**Variable crítica:** `BACKEND_URL` → URL completa del backend API

### Backend (Railway/Render/etc)
**Variables críticas:**
- `DATABASE_URL` → PostgreSQL con PostGIS
- `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` → Redis cache
- `COPERNICUS_API_KEY` + `COPERNICUS_API_SECRET` → Datos satelitales
- `GEMINI_API_KEY` → AI insights
- `CRON_SECRET` → Autenticación de cron jobs
- `CORS_ORIGINS` → Dominios permitidos (incluir Vercel)
- `FRONTEND_URL` → URL del frontend en Vercel

---

## 📋 Checklist Paso a Paso

### 1️⃣ Backend - Configuración Inicial

- [ ] **Desplegar backend** en Railway/Render/etc
- [ ] **Configurar `DATABASE_URL`**
  - Base de datos PostgreSQL con extensión PostGIS
  - Ejemplo: `postgresql://user:pass@host:5432/db?sslmode=require`
- [ ] **Configurar Redis (Upstash)**
  - `UPSTASH_REDIS_REST_URL`: URL del endpoint REST
  - `UPSTASH_REDIS_REST_TOKEN`: Token de autenticación
- [ ] **Configurar Copernicus CDSE**
  - Registrarse en: https://cds.climate.copernicus.eu/
  - Obtener `COPERNICUS_API_KEY` y `COPERNICUS_API_SECRET`
- [ ] **Configurar Google Gemini**
  - Obtener API key en: https://makersuite.google.com/app/apikey
  - Configurar `GEMINI_API_KEY`
- [ ] **Generar `CRON_SECRET`**
  ```bash
  openssl rand -hex 32
  ```
- [ ] **Configurar CORS**
  - `CORS_ORIGINS`: Comma-separated string con dominios permitidos
  - Ejemplo: `https://sunny-2.vercel.app,https://*.vercel.app,http://localhost:3000`
- [ ] **Configurar `FRONTEND_URL`**
  - URL del frontend en Vercel (ej: `https://sunny-2.vercel.app`)
- [ ] **Configurar variables opcionales**
  - `ENVIRONMENT=production`
  - `DEBUG=False` (recomendado)

### 2️⃣ Backend - Verificación

- [ ] Backend responde en `/api/health`
- [ ] Logs muestran inicialización correcta:
  ```
  🌞 Starting sunny-2 API v0.1.0
  📡 Environment: production
  🗄️ Database connection initialized
  📦 Redis cache initialized
  🤖 AI Consultant (Gemini 2.0) initialized
  ```
- [ ] Anotar la URL del backend (ej: `https://sunny-2-api.railway.app`)

### 3️⃣ Frontend - Configuración en Vercel

- [ ] **Conectar repositorio** en Vercel
- [ ] **Configurar `BACKEND_URL`**
  - Settings → Environment Variables
  - Key: `BACKEND_URL`
  - Value: URL completa del backend (sin trailing slash)
  - Environments: ✅ Production, ✅ Preview, ✅ Development
- [ ] **Verificar configuración del proyecto**
  - Framework: Next.js (detectado automáticamente)
  - Root Directory: `/` (raíz del monorepo)
  - Build Command: `cd apps/web && npm run build` (ya en vercel.json)
  - Output Directory: `apps/web/.next` (ya en vercel.json)

### 4️⃣ Frontend - Despliegue

- [ ] **Hacer deploy inicial** o redeploy después de configurar variables
- [ ] **Verificar logs del deploy**
  - Buscar: `[Estimate API] Calling backend at: https://...`
  - No debe aparecer `localhost:8000` en producción
- [ ] **Probar endpoint**
  - Hacer una request de prueba desde la UI
  - Verificar que no hay errores de conexión

### 5️⃣ Integración - Verificación Final

- [ ] **CORS funcionando**
  - Requests desde Vercel al backend no fallan por CORS
  - Verificar headers en Network tab del navegador
- [ ] **API funcionando**
  - `/api/estimate` responde correctamente
  - Datos se muestran en la UI
- [ ] **AI Insights funcionando**
  - Los insights de Gemini se generan y muestran
- [ ] **Cron Job configurado**
  - Verificar que Vercel ejecuta el cron según schedule (diario a las 3 AM UTC)
  - Verificar logs del backend para confirmar ejecución

---

## 🐛 Troubleshooting Común

### Error: `ECONNREFUSED 127.0.0.1:8000`
**Causa:** `BACKEND_URL` no configurada en Vercel  
**Solución:** Configurar variable y hacer redeploy

### Error: CORS policy blocked
**Causa:** Backend no tiene el dominio de Vercel en `CORS_ORIGINS`  
**Solución:** Agregar dominio a `CORS_ORIGINS` en el backend

### Error: Database connection failed
**Causa:** `DATABASE_URL` incorrecta o base de datos no accesible  
**Solución:** Verificar URL y credenciales, asegurar que PostGIS esté habilitado

### Error: Redis cache failed
**Causa:** Credenciales de Upstash incorrectas  
**Solución:** Verificar `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN`

### Error: AI insights no se generan
**Causa:** `GEMINI_API_KEY` no configurada o inválida  
**Solución:** Verificar API key en Google AI Studio

---

## 📚 Documentación Adicional

- **Variables de entorno detalladas:** Ver [ENV_VARS.md](./ENV_VARS.md)
- **README del proyecto:** Ver [../README.md](../README.md)
- **Configuración de Vercel:** Ver `vercel.json`

---

## 🎉 Una vez completado

Tu aplicación debería estar funcionando en producción con:
- ✅ Frontend desplegado en Vercel
- ✅ Backend desplegado y accesible
- ✅ Base de datos PostgreSQL funcionando
- ✅ Cache Redis funcionando
- ✅ Integración con APIs externas (Copernicus, Gemini)
- ✅ Cron jobs programados y funcionando

