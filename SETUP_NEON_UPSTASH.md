# 🚀 Configuración de Neon y Upstash - Guía Paso a Paso

## 📋 Requisitos Previos

- ✅ Cuenta de email (para registrarse)
- ✅ Navegador web
- ✅ Acceso a internet

---

## 🐘 Parte 1: Configurar Neon (PostgreSQL)

### Paso 1: Crear Cuenta en Neon

1. **Ve a Neon**
   - Abre tu navegador y ve a: [https://neon.tech](https://neon.tech)
   - Haz clic en **"Sign Up"** o **"Get Started"**

2. **Registrarse**
   - Opción A: Con GitHub (recomendado)
     - Haz clic en **"Sign in with GitHub"**
     - Autoriza Neon para acceder a tu cuenta de GitHub
   - Opción B: Con Email
     - Ingresa tu email
     - Crea una contraseña
     - Confirma tu email

### Paso 2: Crear un Proyecto

1. **Dashboard de Neon**
   - Después de iniciar sesión, verás el dashboard
   - Haz clic en **"Create Project"** o **"New Project"**

2. **Configurar el Proyecto**
   - **Project Name:** `sunny-2` (o el nombre que prefieras)
   - **Region:** Selecciona la región más cercana a tus usuarios
     - Ejemplos: `US East (Ohio)`, `EU (Frankfurt)`, `US West (Oregon)`
   - **PostgreSQL Version:** `15` o `16` (recomendado)
   - Haz clic en **"Create Project"**

3. **Esperar la Creación**
   - Neon creará automáticamente tu base de datos
   - Esto toma aproximadamente 1-2 minutos

### Paso 3: Obtener la Connection String

1. **En el Dashboard del Proyecto**
   - Una vez creado, verás la página de tu proyecto
   - Busca la sección **"Connection Details"** o **"Connection String"**

2. **Copiar la Connection String**
   - Verás algo como:
     ```
     postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
   - Haz clic en el botón **"Copy"** o selecciona y copia toda la cadena
   - ⚠️ **IMPORTANTE:** Guarda esta cadena de forma segura (será tu `DATABASE_URL`)

3. **Verificar PostGIS**
   - Neon incluye PostGIS por defecto en versiones recientes
   - Si necesitas verificar, puedes ejecutar en el SQL Editor:
     ```sql
     SELECT PostGIS_version();
     ```
   - Si no está instalado, ejecuta:
     ```sql
     CREATE EXTENSION IF NOT EXISTS postgis;
     ```

### Paso 4: Configurar Variables de Entorno

**En tu Backend (Railway/Render):**
- Variable: `DATABASE_URL`
- Valor: La connection string que copiaste de Neon
- Ejemplo:
  ```
  DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
  ```

---

## 🔴 Parte 2: Configurar Upstash (Redis)

### Paso 1: Crear Cuenta en Upstash

1. **Ve a Upstash**
   - Abre tu navegador y ve a: [https://upstash.com](https://upstash.com)
   - Haz clic en **"Sign Up"** o **"Get Started"**

2. **Registrarse**
   - Opción A: Con GitHub (recomendado)
     - Haz clic en **"Sign in with GitHub"**
     - Autoriza Upstash para acceder a tu cuenta
   - Opción B: Con Email
     - Ingresa tu email
     - Crea una contraseña
     - Confirma tu email

### Paso 2: Crear una Redis Database

1. **Dashboard de Upstash**
   - Después de iniciar sesión, verás el dashboard
   - Haz clic en **"Create Database"** o **"New Database"**

2. **Configurar la Database**
   - **Database Name:** `sunny-2-cache` (o el nombre que prefieras)
   - **Type:** `Regional` o `Global`
     - **Regional:** Más rápido, menor latencia (recomendado para empezar)
     - **Global:** Replicación global, mejor para usuarios distribuidos
   - **Region:** Selecciona la misma región que Neon (si es posible)
     - Ejemplos: `us-east-1`, `eu-west-1`, `us-west-2`
   - **Primary Region:** Selecciona la región principal
   - Haz clic en **"Create"**

3. **Esperar la Creación**
   - Upstash creará automáticamente tu Redis database
   - Esto toma aproximadamente 30 segundos

### Paso 3: Obtener las Credenciales

1. **En la Página de la Database**
   - Una vez creada, verás los detalles de tu database
   - Busca la sección **"REST API"** o **"Connection Details"**

2. **Copiar las Credenciales**
   - Verás dos valores importantes:
     - **UPSTASH_REDIS_REST_URL:**
       ```
       https://xxx-xxx.upstash.io
       ```
     - **UPSTASH_REDIS_REST_TOKEN:**
       ```
       AXxxxxx... (token largo)
       ```
   - Haz clic en los botones **"Copy"** para cada uno
   - ⚠️ **IMPORTANTE:** Guarda ambos valores de forma segura

3. **Verificar la Conexión (Opcional)**
   - Puedes probar la conexión desde el dashboard
   - Haz clic en **"Console"** y ejecuta:
     ```
     PING
     ```
   - Deberías ver: `PONG`

### Paso 4: Configurar Variables de Entorno

**En tu Backend (Railway/Render):**
- Variable 1: `UPSTASH_REDIS_REST_URL`
  - Valor: La URL que copiaste (ej: `https://xxx-xxx.upstash.io`)
- Variable 2: `UPSTASH_REDIS_REST_TOKEN`
  - Valor: El token que copiaste (ej: `AXxxxxx...`)

---

## ✅ Verificación

### Verificar Neon

1. **Desde el Dashboard de Neon:**
   - Ve a tu proyecto
   - Haz clic en **"SQL Editor"**
   - Ejecuta:
     ```sql
     SELECT version();
     ```
   - Deberías ver la versión de PostgreSQL

2. **Verificar PostGIS:**
   ```sql
   SELECT PostGIS_version();
   ```
   - Deberías ver la versión de PostGIS

### Verificar Upstash

1. **Desde el Dashboard de Upstash:**
   - Ve a tu database
   - Haz clic en **"Console"**
   - Ejecuta:
     ```
     SET test "hello"
     GET test
     ```
   - Deberías ver: `"hello"`

---

## 🔧 Configuración en el Backend

### Para Railway

1. **Ve a tu proyecto en Railway**
2. **Settings → Variables**
3. **Agrega las siguientes variables:**

   ```
   DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require
   UPSTASH_REDIS_REST_URL=https://xxx-xxx.upstash.io
   UPSTASH_REDIS_REST_TOKEN=AXxxxxx...
   ```

4. **Guarda y haz redeploy**

### Para Render

1. **Ve a tu servicio en Render**
2. **Environment → Environment Variables**
3. **Agrega las mismas variables que arriba**
4. **Guarda y haz redeploy**

---

## 🧪 Probar la Configuración

### Desde el Backend

Una vez configuradas las variables, el backend debería mostrar en los logs:

```
🌞 Starting sunny-2 API v0.1.0
📡 Environment: production
🗄️ Database connection initialized
📦 Redis cache initialized
```

Si ves estos mensajes, ¡todo está configurado correctamente!

### Endpoint de Health Check

Puedes verificar que todo funciona:

```bash
curl https://tu-backend-url.com/api/health
```

Deberías ver una respuesta JSON con:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "healthy"
}
```

---

## 🐛 Troubleshooting

### Problema: No puedo conectarme a Neon

**Solución:**
1. Verifica que la connection string esté completa
2. Asegúrate de incluir `?sslmode=require` al final
3. Verifica que el proyecto esté activo en Neon
4. Revisa que la región sea accesible desde tu ubicación

### Problema: Redis no funciona

**Solución:**
1. Verifica que `UPSTASH_REDIS_REST_URL` empiece con `https://`
2. Verifica que `UPSTASH_REDIS_REST_TOKEN` esté completo (no cortado)
3. Asegúrate de usar la REST API, no la conexión TCP tradicional
4. Verifica que la database esté activa en Upstash

### Problema: PostGIS no está disponible

**Solución:**
1. Ve al SQL Editor de Neon
2. Ejecuta:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Verifica con:
   ```sql
   SELECT PostGIS_version();
   ```

---

## 💰 Planes Gratuitos

### Neon Free Tier

- ✅ 0.5 GB de almacenamiento
- ✅ 192 MB RAM
- ✅ Auto-suspend cuando no se usa
- ✅ Perfecto para desarrollo y proyectos pequeños

### Upstash Free Tier

- ✅ 10,000 comandos por día
- ✅ 256 MB de almacenamiento
- ✅ Perfecto para desarrollo y proyectos pequeños

---

## 📚 Recursos Adicionales

- [Neon Documentation](https://neon.tech/docs)
- [Upstash Documentation](https://docs.upstash.com)
- [PostGIS Documentation](https://postgis.net/documentation/)

---

## ✅ Checklist Final

### Neon
- [ ] Cuenta creada en Neon
- [ ] Proyecto creado
- [ ] Connection string copiada
- [ ] PostGIS verificado/instalado
- [ ] `DATABASE_URL` configurado en backend

### Upstash
- [ ] Cuenta creada en Upstash
- [ ] Redis database creada
- [ ] `UPSTASH_REDIS_REST_URL` copiada
- [ ] `UPSTASH_REDIS_REST_TOKEN` copiado
- [ ] Ambas variables configuradas en backend

### Verificación
- [ ] Backend muestra "Database connection initialized"
- [ ] Backend muestra "Redis cache initialized"
- [ ] Health check responde correctamente
- [ ] No hay errores en los logs

---

¡Listo! Una vez completado este checklist, Neon y Upstash estarán configurados y funcionando. 🎉

