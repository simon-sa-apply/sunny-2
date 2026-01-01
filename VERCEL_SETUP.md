# 🔧 Configuración de BACKEND_URL en Vercel - Guía Paso a Paso

## 📋 Requisito Previo

Antes de comenzar, asegúrate de tener:
- ✅ Tu backend desplegado y funcionando (Railway, Render, etc.)
- ✅ La URL completa de tu backend (ej: `https://sunny-2-api.railway.app`)
- ✅ Acceso al dashboard de Vercel con permisos de administrador

---

## 🎯 Paso 1: Acceder a las Variables de Entorno

1. **Inicia sesión en Vercel**
   - Ve a [vercel.com](https://vercel.com)
   - Inicia sesión con tu cuenta

2. **Navega a tu proyecto**
   - En el dashboard, busca y haz clic en tu proyecto `sunny-2`

3. **Abre la configuración**
   - En la barra superior del proyecto, haz clic en **"Settings"**
   - En el menú lateral izquierdo, busca y haz clic en **"Environment Variables"**

---

## 🔑 Paso 2: Agregar la Variable BACKEND_URL

### 2.1. Campos a completar

En la sección "Environment Variables", verás un formulario con estos campos:

1. **Key (Nombre de la variable)**
   ```
   BACKEND_URL
   ```
   - ⚠️ **Importante:** Debe ser exactamente `BACKEND_URL` (mayúsculas, sin espacios)

2. **Value (Valor de la variable)**
   ```
   https://tu-backend-url.com
   ```
   - Reemplaza `https://tu-backend-url.com` con la URL real de tu backend
   - Ejemplos válidos:
     - `https://sunny-2-api.railway.app`
     - `https://sunny-2-api.up.railway.app`
     - `https://api.sunny-2.com`
   - ⚠️ **Importante:** 
     - NO incluyas trailing slash (`/`) al final
     - Debe empezar con `https://` o `http://`
     - No incluyas rutas como `/api` al final

3. **Environments (Entornos donde aplica)**
   - ✅ Marca **Production**
   - ✅ Marca **Preview** 
   - ✅ Marca **Development**
   - Esto asegura que la variable esté disponible en todos los entornos

### 2.2. Ejemplo visual del formulario

```
┌─────────────────────────────────────────────────┐
│ Key:                                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ BACKEND_URL                                  │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Value:                                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ https://sunny-2-api.railway.app             │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Environments:                                    │
│ ☑ Production                                    │
│ ☑ Preview                                        │
│ ☑ Development                                    │
│                                                  │
│         [ Save ]                                 │
└─────────────────────────────────────────────────┘
```

### 2.3. Guardar la variable

1. Haz clic en el botón **"Save"** o **"Add"**
2. Verás la variable agregada en la lista de variables de entorno

---

## 🔄 Paso 3: Hacer Redeploy

Después de agregar la variable, **debes hacer redeploy** para que los cambios surtan efecto:

### Opción A: Redeploy desde el Dashboard

1. Ve a la pestaña **"Deployments"** en tu proyecto
2. Encuentra el último deployment
3. Haz clic en el menú de tres puntos (`...`) a la derecha
4. Selecciona **"Redeploy"**
5. Confirma el redeploy

### Opción B: Redeploy con un nuevo commit

1. Haz un pequeño cambio en cualquier archivo (o simplemente haz commit de cambios pendientes)
2. Haz push a `main`:
   ```bash
   git push origin main
   ```
3. Vercel automáticamente detectará el cambio y hará un nuevo deploy

---

## ✅ Paso 4: Verificar que Funciona

### 4.1. Revisar los logs del deployment

1. Ve a **"Deployments"** → Haz clic en el último deployment
2. Abre la pestaña **"Build Logs"** o **"Function Logs"**
3. Busca en los logs:
   ```
   [Estimate API] Calling backend at: https://tu-backend-url.com/api/v1/estimate
   ```
   - ✅ Si ves esta línea con tu URL correcta → **¡Funciona!**
   - ❌ Si ves `localhost:8000` → La variable no está configurada correctamente

### 4.2. Probar la aplicación

1. Abre tu aplicación desplegada en Vercel
2. Intenta hacer una estimación solar
3. Si funciona correctamente → **¡Todo está bien!**
4. Si ves errores de conexión → Revisa los logs (ver sección de troubleshooting)

---

## 🐛 Troubleshooting

### Error: Sigue apareciendo `localhost:8000` en los logs

**Causas posibles:**
1. La variable no se guardó correctamente
2. No se hizo redeploy después de agregar la variable
3. El nombre de la variable está mal escrito

**Solución:**
1. Ve a Settings → Environment Variables
2. Verifica que `BACKEND_URL` esté en la lista con el valor correcto
3. Si no está, agrégala de nuevo
4. Haz redeploy del proyecto

### Error: `ECONNREFUSED` o `fetch failed`

**Causas posibles:**
1. La URL del backend es incorrecta
2. El backend no está accesible públicamente
3. Hay un problema de CORS

**Solución:**
1. Verifica que la URL del backend sea correcta:
   ```bash
   curl https://tu-backend-url.com/api/health
   ```
2. Si no responde, el backend puede no estar desplegado o no ser accesible
3. Verifica que el backend tenga configurado `CORS_ORIGINS` con tu dominio de Vercel

### Error: Variable no encontrada en runtime

**Causa:** La variable está configurada pero Next.js no la está leyendo

**Solución:**
1. Verifica que la variable esté marcada para el entorno correcto (Production)
2. Asegúrate de haber hecho redeploy después de agregar la variable
3. Los cambios en variables de entorno requieren un nuevo build

---

## 📝 Notas Importantes

### ⚠️ Variables Sensibles

- `BACKEND_URL` NO es una variable sensible (es una URL pública)
- Sin embargo, asegúrate de no exponer URLs internas o de desarrollo
- En producción, siempre usa HTTPS

### 🔄 Actualizar la Variable

Si necesitas cambiar la URL del backend:
1. Ve a Settings → Environment Variables
2. Encuentra `BACKEND_URL`
3. Haz clic en el ícono de edición (lápiz)
4. Cambia el valor
5. Guarda y haz redeploy

### 🌍 Múltiples Entornos

Si tienes diferentes backends para diferentes entornos:
- Puedes crear variables separadas:
  - `BACKEND_URL` para Production
  - `BACKEND_URL_PREVIEW` para Preview (y modificar el código para usarla)
- O usar la misma variable con diferentes valores según el entorno

---

## ✅ Checklist Final

Antes de considerar que está todo configurado:

- [ ] Variable `BACKEND_URL` agregada en Vercel
- [ ] Valor de la variable es la URL correcta del backend (sin trailing slash)
- [ ] Variable marcada para Production, Preview y Development
- [ ] Redeploy realizado después de agregar la variable
- [ ] Logs muestran la URL correcta (no `localhost:8000`)
- [ ] La aplicación funciona correctamente en producción
- [ ] No hay errores de conexión en la consola del navegador

---

## 🆘 ¿Necesitas Ayuda?

Si después de seguir estos pasos sigues teniendo problemas:

1. **Revisa los logs de Vercel:**
   - Deployments → Último deployment → Logs
   - Busca errores relacionados con `BACKEND_URL`

2. **Verifica la configuración del backend:**
   - Asegúrate de que el backend esté desplegado y accesible
   - Verifica que `/api/health` responda correctamente

3. **Revisa la documentación:**
   - `ENV_VARS.md` - Lista completa de variables
   - `DEPLOYMENT_CHECKLIST.md` - Checklist completo de despliegue

---

## 📚 Referencias

- [Documentación de Vercel sobre Variables de Entorno](https://vercel.com/docs/concepts/projects/environment-variables)
- [Documentación de Next.js sobre Variables de Entorno](https://nextjs.org/docs/basic-features/environment-variables)

