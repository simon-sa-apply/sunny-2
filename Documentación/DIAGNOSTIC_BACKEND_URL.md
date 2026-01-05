# 🔍 Diagnóstico: Error ECONNREFUSED localhost:8000

## ❓ Preguntas de Diagnóstico

Responde estas preguntas para identificar el problema:

### 1. ¿Configuraste BACKEND_URL en Vercel?

- [ ] Sí, configuré `BACKEND_URL` en Vercel → Settings → Environment Variables
- [ ] No, aún no lo he configurado
- [ ] No estoy seguro

**Si NO está configurada:**
1. Ve a Vercel → Tu proyecto → Settings → Environment Variables
2. Agrega:
   - Key: `BACKEND_URL`
   - Value: `https://sunny-2-api.railway.app`
   - Environments: Production, Preview, Development
3. Guarda

### 2. ¿Hiciste redeploy después de configurar la variable?

- [ ] Sí, hice redeploy después de agregar la variable
- [ ] No, solo agregué la variable pero no redeploy
- [ ] No estoy seguro

**Si NO hiciste redeploy:**
1. Ve a Deployments
2. Haz clic en `...` del último deployment
3. Selecciona "Redeploy"
4. Espera a que termine

### 3. ¿Qué valor tiene BACKEND_URL en Vercel?

Verifica en Vercel → Settings → Environment Variables:

- [ ] `https://sunny-2-api.railway.app` ✅ Correcto
- [ ] `http://localhost:8000` ❌ Incorrecto
- [ ] Vacío o undefined ❌ Incorrecto
- [ ] Otro valor: _______________

### 4. ¿Qué muestran los logs de Vercel?

Ve a Vercel → Deployments → Último deployment → Functions/Logs

Busca estas líneas en los logs:

**Si ves esto (✅ Correcto):**
```
[Estimate API] Calling backend at: https://sunny-2-api.railway.app/api/v1/estimate
```

**Si ves esto (❌ Problema):**
```
[Estimate API] Calling backend at: http://localhost:8000/api/v1/estimate
```

**Si ves esto (❌ Variable no configurada):**
```
❌ Backend URL configuration error:
NEXT_PUBLIC_API_URL: NOT SET
BACKEND_URL: NOT SET
```

---

## 🔧 Soluciones Según el Problema

### Problema 1: Variable NO configurada

**Síntoma:** Logs muestran "NOT SET" o error de configuración

**Solución:**
1. Ve a Vercel → Settings → Environment Variables
2. Agrega `BACKEND_URL` = `https://sunny-2-api.railway.app`
3. Marca Production, Preview, Development
4. Guarda
5. **Haz redeploy**

### Problema 2: Variable configurada pero no redeploy

**Síntoma:** Variable existe pero logs siguen mostrando localhost

**Solución:**
1. Verifica que la variable esté guardada correctamente
2. Ve a Deployments → Redeploy
3. Espera a que termine el deploy
4. Verifica los logs del nuevo deploy

### Problema 3: Variable con valor incorrecto

**Síntoma:** Variable existe pero tiene valor incorrecto

**Solución:**
1. Edita la variable en Vercel
2. Cambia el valor a: `https://sunny-2-api.railway.app`
3. Asegúrate de que NO tenga trailing slash (`/`)
4. Guarda
5. **Haz redeploy**

### Problema 4: Variable solo en un entorno

**Síntoma:** Funciona en un entorno pero no en otro

**Solución:**
1. Verifica que la variable esté marcada para:
   - ✅ Production
   - ✅ Preview
   - ✅ Development
2. Si falta alguno, edita la variable y marca todos
3. Guarda y redeploy

---

## 🧪 Prueba Rápida

### Paso 1: Verificar Backend

```bash
curl https://sunny-2-api.railway.app/api/health
```

Si esto funciona, el backend está bien. Si no, el problema está en el backend.

### Paso 2: Verificar Variable en Vercel

1. Ve a Vercel → Settings → Environment Variables
2. Busca `BACKEND_URL`
3. Verifica que el valor sea exactamente: `https://sunny-2-api.railway.app`
4. Verifica que esté marcada para Production

### Paso 3: Verificar Logs

1. Ve a Deployments → Último deployment
2. Abre "Functions" o "Logs"
3. Busca la línea que dice `[Estimate API] Calling backend at:`
4. ¿Qué URL muestra?

---

## 📋 Checklist Completo

- [ ] Backend está funcionando (curl funciona)
- [ ] `BACKEND_URL` está configurada en Vercel
- [ ] Valor es `https://sunny-2-api.railway.app` (sin trailing slash)
- [ ] Variable marcada para Production, Preview y Development
- [ ] Se hizo redeploy después de configurar
- [ ] Logs muestran la URL correcta (no localhost)
- [ ] No hay errores en los logs del deploy

---

## 🆘 Si Nada Funciona

Si después de seguir todos los pasos sigue fallando:

1. **Comparte los logs completos** de Vercel (especialmente la parte donde muestra qué URL está usando)

2. **Verifica el vercel.json:**
   - El `vercel.json` tiene `"NEXT_PUBLIC_API_URL": "${BACKEND_URL}"`
   - Esto requiere que `BACKEND_URL` esté configurada primero

3. **Intenta configurar ambas variables:**
   - `BACKEND_URL` = `https://sunny-2-api.railway.app`
   - `NEXT_PUBLIC_API_URL` = `https://sunny-2-api.railway.app` (mismo valor)

4. **Verifica que no haya espacios o caracteres extraños** en el valor de la variable

