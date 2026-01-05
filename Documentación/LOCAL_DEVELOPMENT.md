# 💻 Desarrollo Local - sunny-2

Guía completa para ejecutar sunny-2 en tu máquina local.

---

## 📋 Requisitos Previos

- **Node.js** 20.x (verificado con `node --version`)
- **Python** 3.12+ (verificado con `python --version`)
- **PostgreSQL** con PostGIS (o cuenta en [Neon](https://neon.tech))
- **npm** 10.2.0+ (viene con Node.js)

---

## 🚀 Inicio Rápido

### Paso 1: Instalar Dependencias

```bash
# Desde la raíz del proyecto
npm install
```

Esto instalará las dependencias del monorepo usando Turborepo.

### Paso 2: Configurar Variables de Entorno

#### Backend (`apps/api/.env`)

Crea el archivo `apps/api/.env` con las siguientes variables:

```env
# Ambiente
ENVIRONMENT=development
DEBUG=True

# Base de datos (PostgreSQL con PostGIS)
# Opción 1: Neon (recomendado para desarrollo)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Opción 2: PostgreSQL local
# DATABASE_URL=postgresql://postgres:password@localhost:5432/sunny2

# Cache Redis (Upstash - opcional para desarrollo)
# Si no configuras esto, el sistema funcionará sin cache
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxxxx...

# APIs Externas
# Copernicus (opcional - si no está, usa PVGIS)
COPERNICUS_API_KEY=xxxxx-xxxxx-xxxxx
COPERNICUS_API_SECRET=xxxxx-xxxxx-xxxxx

# Gemini AI (opcional - si no está, no se generan insights de IA)
GEMINI_API_KEY=AIza...

# CORS (ya tiene valores por defecto para localhost)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# CRON_SECRET (solo necesario si pruebas cron jobs)
CRON_SECRET=dev-secret-key
```

**Nota:** Las variables marcadas como "opcional" permiten que la app funcione con funcionalidad limitada. Sin `GEMINI_API_KEY`, no se generarán insights de IA. Sin `COPERNICUS_API_KEY`, se usará PVGIS como fuente primaria.

#### Frontend (`apps/web/.env.local`)

Crea el archivo `apps/web/.env.local` (opcional):

```env
# El frontend usa localhost:8000 automáticamente en desarrollo
# Solo necesitas esto si quieres cambiar el puerto del backend
BACKEND_URL=http://localhost:8000
```

**Nota:** En desarrollo, el frontend detecta automáticamente `localhost:8000` si no hay `BACKEND_URL` configurada.

### Paso 3: Configurar Base de Datos (si usas PostgreSQL local)

Si usas PostgreSQL local, asegúrate de tener PostGIS habilitado:

```sql
-- Conectarte a tu base de datos
psql -U postgres -d sunny2

-- Habilitar PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
```

Si usas Neon, PostGIS ya viene habilitado.

### Paso 4: Ejecutar Migraciones de Base de Datos

```bash
cd apps/api

# Activar entorno virtual (si usas uno)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# o
.venv\Scripts\activate  # Windows

# Instalar dependencias del backend
pip install -e ".[all]"

# Ejecutar migraciones
alembic upgrade head
```

### Paso 5: Iniciar Servicios

Desde la raíz del proyecto:

```bash
npm run dev
```

Esto iniciará ambos servicios usando Turborepo:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000

---

## 🔍 Verificación

### 1. Verificar Backend

Abre en tu navegador:
- **Health Check:** http://localhost:8000/api/health
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

**Respuesta esperada del health check:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2. Verificar Frontend

Abre en tu navegador:
- **Frontend:** http://localhost:3000

Deberías ver la landing page de sunny-2.

### 3. Probar una Estimación

1. Selecciona una ubicación en el mapa (ej: Madrid, España)
2. Configura los parámetros (área, inclinación, etc.)
3. Haz clic en "Calcular"
4. Deberías ver los resultados de la estimación

---

## 🛠️ Ejecutar Servicios por Separado

Si prefieres ejecutar los servicios por separado:

### Backend Solo

```bash
cd apps/api

# Activar entorno virtual
source .venv/bin/activate  # Linux/macOS

# Iniciar servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend Solo

```bash
cd apps/web

# Iniciar servidor de desarrollo
npm run dev
```

---

## 🐛 Troubleshooting

### Error: "Cannot find module"

**Causa:** Dependencias no instaladas

**Solución:**
```bash
npm install
cd apps/api && pip install -e ".[all]"
```

### Error: "Port 8000 already in use"

**Causa:** Otro proceso está usando el puerto 8000

**Solución:**
```bash
# Encontrar el proceso
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Matar el proceso
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Error: "Database connection failed"

**Causa:** `DATABASE_URL` incorrecta o base de datos no accesible

**Solución:**
1. Verifica que `DATABASE_URL` tenga el formato correcto
2. Asegúrate de que PostgreSQL esté corriendo
3. Verifica credenciales y permisos

### Error: "ModuleNotFoundError: No module named 'app'"

**Causa:** No estás ejecutando desde el directorio correcto o no instalaste el paquete

**Solución:**
```bash
cd apps/api
pip install -e ".[all]"
```

### Error: Frontend no puede conectar al backend

**Causa:** Backend no está corriendo o `BACKEND_URL` incorrecta

**Solución:**
1. Verifica que el backend esté corriendo en http://localhost:8000
2. Verifica que `/api/health` responda correctamente
3. Revisa la consola del navegador para ver errores específicos

### Error: "PostGIS extension not found"

**Causa:** PostGIS no está instalado o habilitado en PostgreSQL

**Solución:**
```sql
-- En PostgreSQL
CREATE EXTENSION IF NOT EXISTS postgis;
```

Si usas Neon, PostGIS ya viene habilitado.

---

## 📝 Variables de Entorno Mínimas para Desarrollo

### Mínimo Funcional (sin IA ni cache)

```env
# apps/api/.env
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@host:5432/db
```

Con esto, la app funcionará usando PVGIS como fuente de datos (sin Copernicus) y sin insights de IA.

### Funcionalidad Completa

```env
# apps/api/.env
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@host:5432/db
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxxxx...
COPERNICUS_API_KEY=xxxxx-xxxxx-xxxxx
COPERNICUS_API_SECRET=xxxxx-xxxxx-xxxxx
GEMINI_API_KEY=AIza...
```

---

## 🧪 Ejecutar Tests

### Backend

```bash
cd apps/api
pytest
```

### Frontend

```bash
cd apps/web
npm test
```

---

## 📚 URLs de Desarrollo

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Aplicación web |
| Backend API | http://localhost:8000 | API REST |
| API Docs (Swagger) | http://localhost:8000/docs | Documentación interactiva |
| API Docs (ReDoc) | http://localhost:8000/redoc | Documentación alternativa |
| Health Check | http://localhost:8000/api/health | Estado del servidor |

---

## 💡 Tips de Desarrollo

1. **Hot Reload:** Ambos servicios tienen hot reload habilitado. Los cambios se reflejan automáticamente.

2. **Logs:** Los logs del backend aparecen en la terminal donde ejecutaste `npm run dev`. Los logs del frontend aparecen en la terminal y en la consola del navegador.

3. **Base de Datos:** Para desarrollo rápido, usa Neon (gratis) en lugar de instalar PostgreSQL localmente.

4. **Cache:** Si no configuras Redis/Upstash, la app funcionará pero sin cache. Esto puede hacer que las requests sean más lentas.

5. **API Keys:** Para desarrollo, puedes usar las mismas API keys de producción (Copernicus, Gemini) o crear cuentas de desarrollo separadas.

---

## ✅ Checklist de Desarrollo Local

- [ ] Node.js 20.x instalado
- [ ] Python 3.12+ instalado
- [ ] Dependencias instaladas (`npm install`)
- [ ] Backend dependencies instaladas (`pip install -e ".[all]"`)
- [ ] Base de datos PostgreSQL configurada (local o Neon)
- [ ] PostGIS habilitado en PostgreSQL
- [ ] Migraciones ejecutadas (`alembic upgrade head`)
- [ ] Variables de entorno configuradas (`apps/api/.env`)
- [ ] Backend corriendo en http://localhost:8000
- [ ] Frontend corriendo en http://localhost:3000
- [ ] Health check responde correctamente
- [ ] Puedes hacer una estimación desde el frontend

---

## 🎉 ¡Listo!

Una vez completado el checklist, deberías poder:
- ✅ Ver la landing page en http://localhost:3000
- ✅ Seleccionar ubicaciones en el mapa
- ✅ Calcular estimaciones solares
- ✅ Ver resultados y gráficos
- ✅ (Opcional) Ver insights de IA si configuraste `GEMINI_API_KEY`

---

## 📚 Documentación Adicional

- **Variables de entorno:** Ver [ENV_VARS.md](./ENV_VARS.md)
- **Configuración de producción:** Ver [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **Railway setup:** Ver [RAILWAY_SETUP.md](./RAILWAY_SETUP.md)
- **Vercel setup:** Ver [VERCEL_SETUP.md](./VERCEL_SETUP.md)

