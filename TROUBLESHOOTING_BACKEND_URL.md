# 🔧 Solución: Error ECONNREFUSED localhost:8000

## 🎯 Diagnóstico del Problema

El error `ECONNREFUSED 127.0.0.1:8000` significa que:
- ❌ El frontend en Vercel está intentando conectarse a `localhost:8000`
- ❌ La variable `BACKEND_URL` NO está configurada o NO está disponible en runtime
- ❌ El código está usando el fallback de desarrollo

---

## ✅ Solución Paso a Paso

### Paso 1: Verificar Variables en Vercel

1. **Ve a Vercel Dashboard**
   - [https://vercel.com](https://vercel.com)
   - Selecciona tu proyecto `sunny-2`

2. **Ve a Settings → Environment Variables**
   - En el menú lateral, haz clic en **"Settings"**
   - Luego haz clic en **"Environment Variables"**

3. **Verifica que `BACKEND_URL` exista**
   - Busca en la lista la variable `BACKEND_URL`
   - Debe tener un valor como: `https://tu-backend.railway.app`
   - ⚠️ **NO debe ser:** `http://localhost:8000` o estar vacía

### Paso 2: Si NO Existe, Agregarla

1. **Haz clic en "Add New"**
2. **Completa el formulario:**
   - **Key:** `BACKEND_URL`
   - **Value:** `https://tu-backend-url.com` (reemplaza con tu URL real)
   - **Environments:** ✅ Production, ✅ Preview, ✅ Development
3. **Haz clic en "Save"**

### Paso 3: Verificar el Valor

**El valor debe ser:**
- ✅ URL completa con `https://` o `http://`
- ✅ Sin trailing slash (`/`) al final
- ✅ URL pública accesible (no localhost)
- ✅ Ejemplo válido: `https://sunny-2-api.railway.app`

**NO debe ser:**
- ❌ `http://localhost:8000`
- ❌ `localhost:8000`
- ❌ `127.0.0.1:8000`
- ❌ Vacío o undefined

### Paso 4: Hacer Redeploy

**⚠️ CRÍTICO:** Después de agregar/modificar variables, DEBES hacer redeploy:

#### Opción A: Redeploy Manual

1. Ve a **"Deployments"** en Vercel
2. Encuentra el último deployment
3. Haz clic en los tres puntos (`...`)
4. Selecciona **"Redeploy"**
5. Confirma el redeploy

#### Opción B: Redeploy con Commit

1. Haz un pequeño cambio en cualquier archivo
2. Haz commit y push:
   ```bash
   git add .
   git commit -m "trigger redeploy"
   git push origin main
   ```
3. Vercel automáticamente hará un nuevo deploy

### Paso 5: Verificar los Logs

Después del redeploy, verifica los logs:

1. Ve a **"Deployments"** → Último deployment
2. Haz clic en **"Functions"** o **"Logs"**
3. Busca logs que muestren:
   ```
   [Estimate API] Calling backend at: https://tu-backend-url.com/api/v1/estimate
   ```
   - ✅ Si ves tu URL correcta → **¡Funciona!**
   - ❌ Si ves `localhost:8000` → La variable aún no está disponible

---

## 🔍 Diagnóstico Avanzado

### Verificar Variables Disponibles en Runtime

El código ya tiene logging para diagnosticar. Busca en los logs de Vercel:

```
❌ Backend URL configuration error:
NEXT_PUBLIC_API_URL: NOT SET
BACKEND_URL: NOT SET
NODE_ENV: production
```

Si ves esto, significa que las variables no están disponibles en runtime.

### Posibles Causas

1. **Variable no configurada**
   - Solución: Agregar `BACKEND_URL` en Vercel

2. **Variable configurada pero no en el entorno correcto**
   - Solución: Asegúrate de marcar Production, Preview y Development

3. **Redeploy no realizado**
   - Solución: Hacer redeploy después de agregar la variable

4. **Variable con valor incorrecto**
   - Solución: Verificar que el valor sea una URL válida

5. **Problema con vercel.json**
   - El `vercel.json` usa `${BACKEND_URL}` que requiere que la variable esté configurada
   - Si no está configurada, `${BACKEND_URL}` será literalmente ese texto

---

## 🧪 Prueba Rápida

### Desde el Dashboard de Vercel

1. Ve a tu proyecto → **Settings** → **Environment Variables**
2. Verifica que `BACKEND_URL` exista y tenga un valor válido
3. Si no existe o está mal, corrígela
4. Ve a **Deployments** → **Redeploy** el último deployment
5. Espera a que termine el deploy
6. Prueba la aplicación

### Verificar que el Backend Funciona

Antes de configurar en Vercel, verifica que tu backend esté funcionando:

```bash
curl https://tu-backend-url.com/api/health
```

Deberías ver una respuesta JSON. Si no funciona, el problema está en el backend, no en Vercel.

---

## 📋 Checklist de Verificación

- [ ] `BACKEND_URL` existe en Vercel → Settings → Environment Variables
- [ ] El valor es una URL válida (no localhost)
- [ ] La variable está marcada para Production, Preview y Development
- [ ] Se hizo redeploy después de agregar/modificar la variable
- [ ] Los logs muestran la URL correcta (no localhost)
- [ ] El backend está accesible públicamente
- [ ] El backend responde en `/api/health`

---

## 🆘 Si Sigue Fallando

### Opción 1: Verificar vercel.json

El `vercel.json` tiene:
```json
"env": {
  "NEXT_PUBLIC_API_URL": "${BACKEND_URL}"
}
```

Esto significa que `NEXT_PUBLIC_API_URL` se genera automáticamente desde `BACKEND_URL`. Si `BACKEND_URL` no está configurada, `NEXT_PUBLIC_API_URL` será literalmente `${BACKEND_URL}` (texto).

**Solución:** Configura `BACKEND_URL` primero.

### Opción 2: Configurar Ambas Variables

Puedes configurar ambas variables manualmente:

1. `BACKEND_URL` = `https://tu-backend-url.com`
2. `NEXT_PUBLIC_API_URL` = `https://tu-backend-url.com` (mismo valor)

### Opción 3: Verificar el Backend

Asegúrate de que tu backend esté:
- ✅ Desplegado y funcionando
- ✅ Accesible públicamente
- ✅ Respondiendo en `/api/health`
- ✅ Sin errores de CORS

---

## 💡 Tips

1. **Siempre haz redeploy después de cambiar variables**
2. **Verifica los logs después de cada deploy**
3. **Usa URLs completas con protocolo (`https://`)**
4. **No uses localhost en producción**
5. **Verifica que el backend esté funcionando antes de configurar Vercel**

---

## 📞 ¿Necesitas Más Ayuda?

Si después de seguir estos pasos sigue fallando:

1. Comparte los logs de Vercel (especialmente los que muestran qué URL se está usando)
2. Verifica que el backend esté funcionando
3. Confirma que `BACKEND_URL` esté configurada correctamente en Vercel

