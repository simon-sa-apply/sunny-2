# Análisis de Problemas del CI Workflow

## Resumen Ejecutivo

**Workflow analizado:** `.github/workflows/ci.yml`  
**Job que falla:** `lint-and-test-api`  
**Etapas del workflow:** 5 etapas principales

---

## Problemas Identificados por Etapa

### 🔴 ETAPA 1: Setup Python (Líneas 46-51)
**Status:** ⚠️ Problemas menores

#### Problema 1.1: Cache de pip
- **Descripción:** `cache-dependency-path: 'apps/api/pyproject.toml'` puede no funcionar correctamente
- **Razón:** GitHub Actions cache busca archivos en la raíz del repo por defecto
- **Impacto:** Cache ineficiente (no bloqueante)
- **Solución:** Usar path absoluto o mover cache step después de checkout

#### Problema 1.2: Versión de Python
- **Status:** ✅ Correcto
- **Nota:** `python-version: '3.12'` coincide con `requires-python = ">=3.12"`

---

### 🔴 ETAPA 2: Install Dependencies (Líneas 53-57) ⚠️ CRÍTICO
**Status:** 🔴 Problemas críticos identificados

#### Problema 2.1: Modo Editable con Hatchling
- **Descripción:** `pip install -e ".[dev,science,db,cache]"` requiere:
  - Hatchling instalado y disponible
  - Capacidad de construir el paquete en modo editable
  - Resolución correcta de dependencias opcionales
  
- **Errores posibles:**
  ```
  ERROR: File "setup.py" or "setup.cfg" not found
  ERROR: Could not find a version that satisfies the requirement
  ERROR: Failed building wheel
  ```

- **Causas raíz:**
  1. Hatchling no está en PATH después de instalación
  2. Conflicto entre versión de pip y hatchling
  3. Dependencias opcionales mal resueltas

#### Problema 2.2: Instalación de Build Tools
- **Descripción:** `pip install hatchling build` puede fallar silenciosamente
- **Errores posibles:**
  ```
  ERROR: Could not install packages due to an EnvironmentError
  WARNING: The script hatchling is installed in '/path' which is not on PATH
  ```

#### Problema 2.3: Dependencias con Compilación
- **Descripción:** `numpy`, `pandas`, `scipy` requieren compilación
- **Requisitos:** Build tools del sistema (gcc, g++, etc.)
- **Errores posibles:**
  ```
  ERROR: Failed building wheel for numpy
  ERROR: Microsoft Visual C++ 14.0 or greater is required
  ```

#### Problema 2.4: Working Directory Context
- **Descripción:** `working-directory: apps/api` puede causar problemas con:
  - Resolución de paths relativos
  - Cache de pip
  - Imports del paquete

---

### 🟡 ETAPA 3: Lint with Ruff (Línea 60)
**Status:** 🟡 Depende de etapa anterior

#### Problema 3.1: Ruff no instalado
- **Causa:** Si etapa 2 falla, ruff no está disponible
- **Error:** `ruff: command not found`

#### Problema 3.2: Paths incorrectos
- **Causa:** `ruff check app tests` puede fallar si paths no existen
- **Error:** `Error: No such file or directory`

---

### 🟡 ETAPA 4: Run Tests (Línea 63)
**Status:** 🟡 Depende de etapas anteriores

#### Problema 4.1: Dependencias faltantes
- **Causa:** Si instalación falla, imports fallarán
- **Error:** `ModuleNotFoundError: No module named 'X'`

#### Problema 4.2: Variables de entorno faltantes
- **Causa:** Tests pueden requerir env vars no configuradas
- **Error:** `KeyError` o `ValidationError` en config

#### Problema 4.3: Coverage report no generado
- **Causa:** Si tests fallan, `coverage.xml` no se crea
- **Impacto:** Siguiente step falla

---

### 🟡 ETAPA 5: Upload Coverage (Líneas 65-69)
**Status:** 🟡 Depende de etapa anterior

#### Problema 5.1: Archivo no encontrado
- **Causa:** `./coverage.xml` puede no existir si tests fallan
- **Error:** `File not found`
- **Mitigación:** `fail_ci_if_error: false` (ya aplicado)

---

## Soluciones Disponibles

### ✅ Solución 1: Instalación Directa (RECOMENDADA)
**Complejidad:** ⭐ Baja  
**Riesgo:** ⭐ Bajo  
**Performance:** ⭐⭐⭐ Buena

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install fastapi uvicorn pydantic pydantic-settings python-dotenv httpx slowapi
    pip install pytest pytest-asyncio pytest-cov ruff
    pip install numpy pandas scipy pvlib
    pip install sqlalchemy asyncpg alembic geoalchemy2
    pip install upstash-redis
```

**Pros:**
- Simple y directo
- Menos propenso a errores
- Fácil de debuggear

**Contras:**
- No instala el paquete local
- Requiere mantener lista manualmente

---

### ✅ Solución 2: Modo Editable Mejorado
**Complejidad:** ⭐⭐ Media  
**Riesgo:** ⭐⭐ Medio  
**Performance:** ⭐⭐ Media

```yaml
- name: Install build tools
  run: |
    python -m pip install --upgrade pip setuptools wheel
    pip install hatchling build
    python -c "import hatchling; print('hatchling OK')"
    
- name: Install dependencies
  run: |
    pip install -e ".[dev,science,db,cache]"
```

**Pros:**
- Instala el paquete local
- Usa pyproject.toml como fuente de verdad

**Contras:**
- Más complejo
- Puede fallar con problemas de build

---

### ✅ Solución 3: Instalación en Dos Pasos
**Complejidad:** ⭐⭐ Media  
**Riesgo:** ⭐ Bajo  
**Performance:** ⭐⭐⭐ Buena

```yaml
- name: Install build tools
  run: |
    python -m pip install --upgrade pip
    pip install build hatchling
    
- name: Install base dependencies
  run: |
    pip install fastapi uvicorn pydantic pydantic-settings python-dotenv httpx slowapi
    
- name: Install dev dependencies
  run: |
    pip install pytest pytest-asyncio pytest-cov ruff
    
- name: Install science dependencies
  run: |
    pip install numpy pandas scipy pvlib
    
- name: Install db dependencies
  run: |
    pip install sqlalchemy asyncpg alembic geoalchemy2
    
- name: Install cache dependencies
  run: |
    pip install upstash-redis
```

**Pros:**
- Mejor control y debugging
- Fácil identificar qué grupo falla
- Permite continuar aunque un grupo falle

**Contras:**
- Más verboso
- Requiere mantener sincronizado con pyproject.toml

---

### ✅ Solución 4: Usar uv (Moderno y Rápido)
**Complejidad:** ⭐⭐⭐ Alta  
**Riesgo:** ⭐⭐ Medio  
**Performance:** ⭐⭐⭐⭐⭐ Excelente

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4
  with:
    version: "latest"
    
- name: Install dependencies
  run: |
    uv pip install -e ".[dev,science,db,cache]"
```

**Pros:**
- Muy rápido (10-100x más rápido que pip)
- Mejor resolución de dependencias
- Manejo automático de build tools

**Contras:**
- Requiere acción adicional
- Menos común (puede tener bugs)

---

## Recomendación Final

### 🎯 Opción A: Solución 1 (Instalación Directa)
**Para:** Fix rápido e inmediato  
**Cuándo usar:** Ahora mismo para resolver el CI

### 🎯 Opción B: Solución 3 (Instalación en Dos Pasos)
**Para:** Mejor práctica a largo plazo  
**Cuándo usar:** Si quieres mejor debugging y control

### 🎯 Opción C: Solución 4 (uv)
**Para:** Optimización futura  
**Cuándo usar:** Después de que el CI esté estable

---

## Checklist de Verificación

Antes de implementar cualquier solución, verificar:

- [ ] ¿Qué error específico muestra el CI? (revisar logs)
- [ ] ¿En qué etapa exacta falla?
- [ ] ¿Hay variables de entorno requeridas?
- [ ] ¿Los tests requieren servicios externos?
- [ ] ¿Hay dependencias opcionales que pueden omitirse?

---

## Próximos Pasos

1. **Revisar logs del CI** para identificar error exacto
2. **Elegir solución** basada en error específico
3. **Implementar solución** elegida
4. **Verificar** que CI pasa
5. **Documentar** cambios para futuro

