<p align="center">
  <img src="https://img.shields.io/badge/sunny--2-Solar%20Estimator-f59e0b?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0Ii8+PHBhdGggZD0iTTEyIDJ2MiIvPjxwYXRoIGQ9Ik0xMiAyMHYyIi8+PHBhdGggZD0ibTQuOTMgNC45MyAxLjQxIDEuNDEiLz48cGF0aCBkPSJtMTcuNjYgMTcuNjYgMS40MSAxLjQxIi8+PHBhdGggZD0iTTIgMTJoMiIvPjxwYXRoIGQ9Ik0yMCAxMmgyIi8+PHBhdGggZD0ibTYuMzQgMTcuNjYtMS40MSAxLjQxIi8+PHBhdGggZD0ibTE5LjA3IDQuOTMtMS40MSAxLjQxIi8+PC9zdmc+" alt="sunny-2">
</p>

<h1 align="center">☀️ sunny-2</h1>

<p align="center">
  <strong>Estimación fotovoltaica basada en observación satelital</strong>
</p>

<p align="center">
  <a href="#-qué-es-sunny-2">Qué es</a> •
  <a href="#-por-qué-sunny-2">Por qué</a> •
  <a href="#-características">Características</a> •
  <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-licencia">Licencia</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Copernicus-ESA-blue?style=flat-square" alt="Copernicus">
  <img src="https://img.shields.io/badge/Gemini%202.0-AI-8b5cf6?style=flat-square" alt="Gemini">
  <img src="https://img.shields.io/badge/License-BSL%201.1-green?style=flat-square" alt="License">
</p>

---

## 🎯 Qué es sunny-2

**sunny-2** es una plataforma de diagnóstico solar que te dice cuánta energía pueden generar paneles solares en tu ubicación, usando datos reales de satélites — no promedios genéricos.

Ingresa tu ubicación, el área disponible y la inclinación de tu techo. En segundos obtienes:

- **Generación anual estimada** en kWh
- **Desglose mensual** para planificar mejor
- **Ahorro económico** y reducción de CO₂
- **Análisis de IA** con contexto climático de tu zona

---

## 💡 Por qué sunny-2

Las calculadoras solares tradicionales usan **promedios regionales** que pueden variar hasta un 30% de la realidad. sunny-2 es diferente:

| Calculadora típica | sunny-2 |
|--------------------|---------|
| Promedios por país/región | Datos satelitales de tu ubicación exacta |
| "Estimación aproximada" | Cita fuentes científicas (Copernicus, PVGIS) |
| Resultados genéricos | Análisis de IA contextualizado a tu clima |
| Sin explicación | Transparencia total sobre incertidumbre |

**El objetivo:** Que tomes una decisión de compra informada, basada en datos científicos — no en promesas comerciales.

---

## ✨ Características

- 🛰️ **Datos de Copernicus** — Radiación solar de satélites de la ESA con 20+ años de histórico
- 🤖 **Consultor AI** — Gemini 2.0 interpreta resultados y da contexto climático local
- 🗺️ **Mapa interactivo** — Click o búsqueda de dirección para seleccionar ubicación
- 📊 **Análisis mensual** — Visualiza picos y valles de producción
- ☀️ **Reloj Solar** — Ajusta inclinación y orientación en tiempo real
- 💰 **Ahorro económico** — Cálculos con regulaciones por país (Chile, Alemania, etc.)
- 🌍 **Impacto ambiental** — kg de CO₂ evitados y equivalencias tangibles
- 🌐 **Multiidioma** — Español e Inglés

---

## 🛠️ Tech Stack

```
Frontend          Backend           Data Sources
─────────────     ─────────────     ─────────────
Next.js 14        FastAPI           Copernicus CAMS
TypeScript        Python 3.12       PVGIS (JRC)
Tailwind CSS      PostgreSQL        ERA5-Land
MapLibre GL       Redis             
Framer Motion     Gemini 2.0        
```

**Infraestructura:** Monorepo con Turborepo · Vercel (frontend) · Railway/Render (API) · Neon (PostgreSQL)

---

## 🚀 Quick Start

### Requisitos
- Node.js 18+
- Python 3.12+
- PostgreSQL (o cuenta en [Neon](https://neon.tech))

### Instalación

```bash
# Clona el repositorio
git clone https://github.com/your-org/sunny-2.git
cd sunny-2

# Instala dependencias
npm install

# Configura variables de entorno
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Inicia desarrollo
npm run dev
```

### URLs de desarrollo

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Variables de entorno requeridas

```env
# apps/api/.env
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...           # Google AI Studio
COPERNICUS_CLIENT_ID=...     # Copernicus CDSE (opcional)
COPERNICUS_CLIENT_SECRET=... # Copernicus CDSE (opcional)

# apps/web/.env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Nota:** Sin credenciales de Copernicus, el sistema usa PVGIS como fuente primaria (cobertura global).

---

## 📡 Fuentes de datos

| Fuente | Proveedor | Cobertura | Uso |
|--------|-----------|-----------|-----|
| **CAMS Radiation** | Copernicus/ESA | Global | Radiación solar histórica |
| **PVGIS TMY** | JRC (Comisión Europea) | Global | Año meteorológico típico |
| **ERA5-Land** | ECMWF/Copernicus | Global | Reanálisis climático |

Todos los cálculos siguen metodología **PVWatts (NREL)** y estándares **IEC 61724-1**.

---

## 📂 Estructura del proyecto

```
sunny-2/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── routers/     # Endpoints REST
│   │   │   ├── services/    # Lógica de negocio
│   │   │   ├── plugins/     # Regulaciones por país
│   │   │   └── models/      # SQLAlchemy models
│   │   └── alembic/         # Migraciones DB
│   │
│   └── web/                 # Next.js frontend
│       └── src/
│           ├── app/         # App Router
│           └── components/  # React components
│
├── _bmad/                   # Documentación del proyecto
└── _bmad-output/            # Artifacts generados
```

---

## 🔒 Licencia

Este proyecto está bajo **Business Source License 1.1** (BSL-1.1).

| ✅ Permitido | ❌ Restringido |
|--------------|----------------|
| Evaluación interna | Servicios comerciales de estimación solar |
| Investigación y educación | Redistribución como SaaS |
| Uso personal no comercial | |

**Fecha de cambio:** 30 de diciembre de 2028 → Apache 2.0

Ver [LICENSE](./LICENSE) para términos completos.

---

## 🤝 Contribuir

¿Ideas o mejoras? Abre un issue o PR. Áreas de interés:

- 🌍 Plugins para nuevos países (regulaciones eléctricas)
- 🌐 Traducciones a más idiomas
- 📊 Mejoras en visualizaciones
- 🔬 Validación contra datos reales

---

<p align="center">
  <strong>sunny-2</strong> · Hecho con ☀️ por <a href="https://applydigital.com">Apply Digital</a>
</p>

<p align="center">
  <sub>© 2024-2025 Apply Digital. Todos los derechos reservados.</sub>
</p>
