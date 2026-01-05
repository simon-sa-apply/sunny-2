# 🚀 Configuración Final para Producción

## ⚠️ ACCIÓN REQUERIDA EN VERCEL

El código está listo, pero **DEBES configurar la variable de entorno en Vercel manualmente**.

### Paso 1: Configurar BACKEND_URL en Vercel

1. **Ve a Vercel Dashboard**
   - [https://vercel.com](https://vercel.com)
   - Selecciona tu proyecto `sunny-2`

2. **Settings → Environment Variables**
   - Haz clic en "Settings"
   - Haz clic en "Environment Variables"

3. **Agrega la Variable**
   - Haz clic en "Add New"
   - **Key:** `BACKEND_URL`
   - **Value:** `https://sunny-2-api.railway.app`
   - **Environments:** ✅ Production ✅ Preview ✅ Development
   - Haz clic en "Save"

### Paso 2: Redeploy Obligatorio

**⚠️ CRÍTICO:** Después de agregar la variable, DEBES hacer redeploy:

1. Ve a **"Deployments"**
2. Encuentra el último deployment
3. Haz clic en los tres puntos (`...`)
4. Selecciona **"Redeploy"**
5. Espera a que termine (2-5 minutos)

### Paso 3: Verificar

Después del redeploy, verifica los logs:

1. Ve a **Deployments** → Último deployment → **Functions/Logs**
2. Busca esta línea:
   ```
   [Estimate API] Calling backend at: https://sunny-2-api.railway.app/api/v1/estimate
   ```
3. Si ves esta URL → ✅ **¡Funciona!**
4. Si ves `localhost:8000` → ❌ La variable no se aplicó, verifica el Paso 1

---

## ✅ Cambios Realizados en el Código

### 1. Mejoras en `route.ts`
- ✅ Validación mejorada de URLs
- ✅ Prevención de localhost en producción
- ✅ Limpieza automática de trailing slashes
- ✅ Mejor manejo de errores

### 2. Actualización de `vercel.json`
- ✅ Configuración explícita de `NEXT_PUBLIC_API_URL` en build time
- ✅ Soporte para `${BACKEND_URL}` en rewrites

### 3. Actualización de `package.json`
- ✅ Node.js 20.x especificado (elimina warning)

---

## 📋 Checklist Final

Antes de considerar que está funcionando:

- [ ] `BACKEND_URL` configurada en Vercel = `https://sunny-2-api.railway.app`
- [ ] Variable marcada para Production, Preview y Development
- [ ] Redeploy realizado después de configurar la variable
- [ ] Logs muestran la URL correcta (no localhost)
- [ ] La aplicación funciona correctamente en producción

---

## 🐛 Si Sigue Fallando

Si después de seguir estos pasos sigue mostrando `localhost:8000`:

1. **Verifica que la variable esté guardada:**
   - Ve a Settings → Environment Variables
   - Confirma que `BACKEND_URL` existe y tiene el valor correcto

2. **Verifica que no haya espacios:**
   - El valor debe ser exactamente: `https://sunny-2-api.railway.app`
   - Sin espacios antes o después
   - Sin trailing slash

3. **Intenta configurar ambas variables:**
   - `BACKEND_URL` = `https://sunny-2-api.railway.app`
   - `NEXT_PUBLIC_API_URL` = `https://sunny-2-api.railway.app`

4. **Verifica los logs del build:**
   - Ve a Deployments → Último deployment → Build Logs
   - Busca errores relacionados con variables de entorno

---

## 📞 ¿Necesitas Ayuda?

Si después de seguir estos pasos sigue fallando, comparte:
1. Screenshot de la configuración de variables en Vercel
2. Logs del deployment (especialmente la línea que muestra qué URL se está usando)
3. Cualquier error adicional que veas

