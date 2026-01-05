
# Variables de Entorno - Configuración para Producción

Este documento lista todas las variables de entorno necesarias para desplegar Sunny-2 en producción.

## 🎨 Frontend (Vercel)

### Variables Requeridas

| Variable | Descripción | Ejemplo | Dónde Configurar |
|----------|-------------|---------|------------------|
| `BACKEND_URL` | URL completa del backend API (sin trailing slash) | `https://sunny-2-api.railway.app` | Vercel → Settings → Environment Variables |
| `NEXT_PUBLIC_API_URL` | (Opcional) Misma que BACKEND_URL, para uso en cliente | `https://sunny-2-api.railway.app` | Vercel → Settings → Environment Variables |

**Nota:** El código usa `NEXT_PUBLIC_API_URL` primero, luego `BACKEND_URL`, y finalmente localhost solo en desarrollo.

### Configuración en Vercel

1. Ve a tu proyecto en Vercel → **Settings** → **Environment Variables**
2. Agrega las siguientes variables:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://tu-backend-url.com` (reemplaza con tu URL real)
   - **Environments:** ✅ Production, ✅ Preview, ✅ Development
3. (Opcional) Si también quieres `NEXT_PUBLIC_API_URL`:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** Misma URL que `BACKEND_URL`
   - **Environments:** ✅ Production, ✅ Preview, ✅ Development

### Verificación

Después de configurar las variables, haz un redeploy. Los logs deberían mostrar:
```
[Estimate API] Calling backend at: https://tu-backend-url.com/api/v1/estimate
```

---

## ⚙️ Backend (Railway/Render/etc)

### Variables Requeridas

| Variable | Descripción | Ejemplo | Dónde Obtener |
|----------|-------------|---------|---------------|
| `DATABASE_URL` | PostgreSQL connection string con PostGIS | `postgresql://user:pass@host:5432/db?sslmode=require` | Neon, Railway, Supabase |
| `UPSTASH_REDIS_REST_URL` | URL del endpoint REST de Upstash Redis | `https://xxx.upstash.io` | Upstash Dashboard |
| `UPSTASH_REDIS_REST_TOKEN` | Token de autenticación de Upstash | `AXxxxxx...` | Upstash Dashboard |
| `COPERNICUS_API_KEY` | API Key de Copernicus CDSE | `xxxxx-xxxxx-xxxxx` | [Copernicus CDSE](https://cds.climate.copernicus.eu/) |
| `COPERNICUS_API_SECRET` | API Secret de Copernicus CDSE | `xxxxx-xxxxx-xxxxx` | [Copernicus CDSE](https://cds.climate.copernicus.eu/) |
| `GEMINI_API_KEY` | API Key de Google Gemini | `AIza...` | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `CRON_SECRET` | Secret para autenticar cron jobs de Vercel | `tu-secret-random-aqui` | Generar con: `openssl rand -hex 32` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `https://sunny-2.vercel.app,https://*.vercel.app` | Tu dominio de Vercel |
| `FRONTEND_URL` | URL del frontend en Vercel | `https://sunny-2.vercel.app` | Tu dominio de Vercel |

### Variables Opcionales (con valores por defecto)

| Variable | Valor por Defecto | Descripción |
|----------|-------------------|-------------|
| `ENVIRONMENT` | `development` | `production` en prod |
| `DEBUG` | `True` | `False` en prod |
| `HOST` | `0.0.0.0` | No cambiar |
| `PORT` | `8000` | Puerto del servidor |
| `RATE_LIMIT_PER_MINUTE` | `100` | Límite de requests/min para usuarios autenticados |
| `RATE_LIMIT_ANONYMOUS` | `30` | Límite de requests/min para usuarios anónimos |
| `REDIS_TTL_SECONDS` | `3600` | TTL del cache Redis (1 hora) |
| `DB_CACHE_TTL_DAYS` | `30` | TTL del cache en DB (30 días) |

### Configuración en Railway/Render

1. Ve a tu proyecto → **Variables** o **Environment**
2. Agrega todas las variables requeridas listadas arriba
3. Para `CRON_SECRET`, genera un valor seguro:
   ```bash
   openssl rand -hex 32
   ```
4. Para `CORS_ORIGINS`, incluye:
   - Tu dominio de producción: `https://sunny-2.vercel.app`
   - Preview deployments: `https://*.vercel.app`
   - (Opcional) Localhost para desarrollo: `http://localhost:3000`

---

## 🔄 Flujo de Configuración

### Paso 1: Backend
1. Despliega el backend primero (Railway, Render, etc.)
2. Configura todas las variables del backend
3. Verifica que el backend responda en `/api/health`
4. Anota la URL del backend (ej: `https://sunny-2-api.railway.app`)

### Paso 2: Frontend
1. En Vercel, configura `BACKEND_URL` con la URL del backend
2. Haz redeploy del frontend
3. Verifica que las llamadas funcionen revisando los logs

### Paso 3: Cron Jobs
1. En Vercel, configura el cron job (ya está en `vercel.json`)
2. El endpoint `/api/cron/cleanup` debe estar protegido con `CRON_SECRET`
3. Verifica que el header `X-Cron-Secret` coincida con `CRON_SECRET` del backend

---

## ✅ Checklist de Verificación

### Frontend (Vercel)
- [ ] `BACKEND_URL` configurada con la URL completa del backend
- [ ] Variable disponible en Production, Preview y Development
- [ ] Redeploy realizado después de configurar variables
- [ ] Logs muestran la URL correcta del backend
- [ ] Las llamadas a `/api/estimate` funcionan

### Backend (Railway/Render)
- [ ] `DATABASE_URL` configurada (PostgreSQL con PostGIS)
- [ ] `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` configuradas
- [ ] `COPERNICUS_API_KEY` y `COPERNICUS_API_SECRET` configuradas
- [ ] `GEMINI_API_KEY` configurada
- [ ] `CRON_SECRET` generado y configurado
- [ ] `CORS_ORIGINS` incluye el dominio de Vercel
- [ ] `FRONTEND_URL` configurada
- [ ] `ENVIRONMENT=production` configurada
- [ ] `DEBUG=False` configurada (opcional pero recomendado)

### Integración
- [ ] Backend responde en `/api/health`
- [ ] Frontend puede hacer requests al backend
- [ ] CORS está configurado correctamente
- [ ] Cron job está programado y funcionando

---

## 🐛 Troubleshooting

### Error: `ECONNREFUSED 127.0.0.1:8000`
**Causa:** La variable `BACKEND_URL` no está configurada en Vercel.
**Solución:** Configura `BACKEND_URL` en Vercel → Settings → Environment Variables y haz redeploy.

### Error: `CORS policy: No 'Access-Control-Allow-Origin'`
**Causa:** El backend no tiene configurado `CORS_ORIGINS` con el dominio de Vercel.
**Solución:** Agrega tu dominio de Vercel a `CORS_ORIGINS` en el backend.

### Error: `CRON_SECRET` inválido
**Causa:** El secret del cron job no coincide entre Vercel y el backend.
**Solución:** Verifica que `CRON_SECRET` en el backend coincida con el configurado en Vercel (si es necesario).

---

## 📝 Notas Importantes

1. **Variables `NEXT_PUBLIC_*`**: Estas variables son expuestas al cliente. No uses secrets aquí.
2. **Variables del servidor**: `BACKEND_URL` en el route handler de Next.js solo está disponible en el servidor, no se expone al cliente.
3. **Cron Jobs**: Vercel ejecuta cron jobs automáticamente según el schedule en `vercel.json`. El backend debe validar el `X-Cron-Secret` header.
4. **CORS**: Asegúrate de incluir todos los dominios necesarios en `CORS_ORIGINS`, incluyendo preview deployments (`*.vercel.app`).

