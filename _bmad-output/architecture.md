---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['_bmad-output/prd.md', '_bmad-output/project-planning-artifacts/product-brief-sunny-2-2025-12-24.md', '_bmad-output/project-planning-artifacts/research/technical-solar-mvp-research-2025-12-24.md', '_bmad-output/analysis/brainstorming-session-2025-12-24.md', 'bases.md']
workflowType: 'architecture'
project_name: 'sunny-2'
user_name: 'Simon.salazar'
date: '2025-12-24'
deployment_platform: 'Vercel'
repo_structure: 'Monorepo'
database_provider: 'Neon/Supabase'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (5):**

| ID | Requisito | Implicación Arquitectónica |
|----|-----------|---------------------------|
| FR-1 | Gestión de Coordenadas y Mapas | Capa de presentación con mapa interactivo + API de geocodificación |
| FR-2 | Motor de Ciencia de Datos (Copernicus) | Servicio de datos asíncrono + modelo de interpolación local |
| FR-3 | Consultor Solar (Gemini 2.0) | Orquestador de IA con System Prompts + validación de coherencia |
| FR-4 | Dashboard Asíncrono (SSE) | Arquitectura de eventos servidor-cliente en tiempo real |
| FR-5 | Data Server & API | Capa de API REST con OpenAPI + autenticación por API Keys |

**Non-Functional Requirements (4):**

| ID | Requisito | Constraint Arquitectónico |
|----|-----------|--------------------------|
| NFR-1 | Precisión 5% | Metodología PVWatts/IEC 61724-1, validación de cálculos |
| NFR-2 | Latencia <200ms (interpolación), <500ms (cache) | Modelo local en memoria, Redis para cache geográfico |
| NFR-3 | Seguridad y Cuotas | Rate Limiting por IP/API Key, ofuscación de coordenadas |
| NFR-4 | Escalabilidad | Arquitectura desacoplada (microservicios o modular) |

### Scale & Complexity Assessment

- **Primary Domain:** Full-Stack (Web App + API Backend + Data Science Engine)
- **Complexity Level:** High
- **Estimated Architectural Components:** 7 (Frontend, API Gateway, Calculation Engine, Data Science Layer, AI Orchestrator, Cache Layer, Persistence)

### Technical Constraints & Dependencies

| Constraint | Descripción | Mitigación |
|------------|-------------|------------|
| API Copernicus Latency | Descargas de 20 años pueden tomar segundos/minutos | Cache On-Demand + SSE para feedback |
| CAMS Geographic Coverage | Meteosat solo cubre Europa/África/Asia | **PVGIS como fallback para Americas y global** |
| Gemini 2.0 Rate Limits | Límites de llamadas por minuto | Cola de procesamiento + fallback cache |
| Data Tiering | Diferentes niveles de precisión por región | Campo `data_tier` en respuestas API |
| Regulatory Plugins | Constantes legales varían por país | Arquitectura modular de plugins |

### Cross-Cutting Concerns Identified

1. **Observabilidad:** Logging estructurado para auditar cálculos científicos.
2. **Gestión de Errores:** Manejo graceful de fallos de APIs externas con fallbacks.
3. **Seguridad:** Protección de cuotas de Copernicus, autenticación de consumidores API.
4. **Performance:** Balance entre precisión y velocidad (modelo de interpolación local).
5. **Transparencia de IA:** Guardrails para evitar especulación fuera de datos deterministas.
6. **Progressive Disclosure (UX):** SSE como mecanismo de confianza visual, no solo técnico.

### Architectural Decisions Pending (From Party Mode)

| Decisión | Opciones | Impacto |
|----------|----------|---------|
| Patrón Cálculo-IA | Síncrono vs Pipeline/Saga | Resiliencia ante fallos de Gemini |
| Estrategia Warm-Up | Pre-carga vs Solo On-Demand | UX de primer usuario en regiones populares |
| Fallback de Narrativa | Cache de narrativas vs Generación fallback | Disponibilidad del Consultor Solar |

## Starter Template Evaluation

### Primary Technology Domain

Full-Stack Híbrido (Next.js Frontend + FastAPI/Python Backend) basado en los requisitos del proyecto.

### Starter Options Considered

| Opción | Evaluación | Resultado |
|--------|------------|-----------|
| T3 Stack | Solo Node.js, no soporta Python | ❌ Descartado |
| RedwoodJS | Monolítico, no compatible con FastAPI | ❌ Descartado |
| FastAPI-React-Template | Desactualizado, sin Tailwind/App Router | ❌ Descartado |
| Custom Monorepo (Turborepo) | Control total, Vercel-compatible | ✅ Seleccionado |

### Selected Starter: Custom Monorepo with Turborepo

**Rationale for Selection:**
- sunny-2 requiere un backend de Python con librerías de ciencia de datos (Xarray, Pvlib) que no están disponibles en ecosistemas Node.js.
- Turborepo proporciona gestión de monorepo eficiente con caching inteligente.
- Vercel tiene soporte nativo para Turborepo y despliegue de Python serverless.
- Estructura flexible que permite escalar frontend y backend independientemente.

**Project Structure:**

```
sunny-2/
├── apps/
│   ├── web/                    # Next.js 14+ (App Router)
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   └── api/                    # FastAPI Python Backend
│       ├── app/
│       │   ├── main.py
│       │   ├── routers/
│       │   ├── services/
│       │   ├── models/
│       │   └── core/
│       ├── pyproject.toml
│       └── requirements.txt
├── packages/
│   └── shared-types/           # TypeScript types compartidos
├── turbo.json                  # Configuración Turborepo
├── package.json                # Root package.json
├── vercel.json                 # Configuración Vercel
└── README.md
```

**Initialization Commands:**

```bash
# Crear monorepo con Turborepo
npx create-turbo@latest sunny-2 --example with-tailwind

# Configurar Next.js (apps/web)
cd apps/web && npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Configurar FastAPI (apps/api)
cd ../api && python -m venv .venv && pip install fastapi uvicorn xarray pandas pvlib-python redis google-generativeai
```

### Architectural Decisions Provided by Starter

**Language & Runtime:**
- Frontend: TypeScript 5.x con Next.js 14+ (App Router)
- Backend: Python 3.12+ con FastAPI 0.100+

**Styling Solution:**
- Tailwind CSS 3.x con configuración de diseño moderno

**Build Tooling:**
- Turborepo para orquestación de builds
- Vercel para deployment (Frontend serverless + Python Functions)

**Testing Framework:**
- Frontend: Vitest + React Testing Library
- Backend: Pytest + httpx

**Code Organization:**
- Monorepo con `apps/` para aplicaciones y `packages/` para código compartido
- Separación clara de responsabilidades

**Development Experience:**
- Hot reload en ambos frontends
- Turborepo cache para builds rápidos
- Configuración de ESLint/Prettier compartida

**Note:** La inicialización del proyecto usando estos comandos debe ser la primera historia de implementación.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- ORM y persistencia de datos (SQLAlchemy 2.0 + Alembic)
- Autenticación de usuarios y API consumers (NextAuth.js + API Keys)
- Patrón de comunicación asíncrona (SSE via FastAPI)

**Important Decisions (Shape Architecture):**
- State management del frontend (React Query + Zustand)
- Librería de mapas y visualización (MapLibre GL + Recharts)
- Estrategia de error handling (RFC 7807)

**Deferred Decisions (Post-MVP):**
- WebSocket para features colaborativas
- OAuth2 para integraciones enterprise
- GraphQL subscriptions

### Data Architecture

| Componente | Decisión | Versión | Rationale |
|------------|----------|---------|-----------|
| ORM | SQLAlchemy 2.0 | 2.0.x | Async support nativo, madurez, amplia comunidad |
| Migraciones | Alembic | 1.13.x | Estándar de facto con SQLAlchemy, versionado de esquema |
| Validación | Pydantic v2 | 2.5.x | Integración nativa con FastAPI, performance mejorado |
| Database | PostgreSQL + PostGIS (Neon/Supabase) | 16.x | Capacidades geoespaciales, serverless-ready |
| Cache | Redis (Upstash) | 7.x | Cache de baja latencia, serverless-compatible |

**Data Flow Pattern:**
```
Request → Pydantic Validation → SQLAlchemy Model → PostgreSQL/PostGIS
                                      ↓
                              Redis Cache (On-Demand)
```

### Authentication & Security

| Componente | Decisión | Versión | Rationale |
|------------|----------|---------|-----------|
| Frontend Auth | NextAuth.js (Auth.js) | 5.x | Gratuito, flexible, soporte OAuth providers |
| API Auth | API Keys | Custom | Simple para MVP, fácil gestión para Alex |
| Rate Limiting | SlowAPI | 0.1.x | Integración directa con FastAPI |
| Session | JWT + HTTP-only cookies | - | Seguridad estándar para web apps |

**Security Layers:**
- **Luis (Frontend):** NextAuth.js → JWT → API Gateway
- **Alex (API):** API Key Header → Rate Limiter → API Gateway

### API & Communication Patterns

| Componente | Decisión | Versión | Rationale |
|------------|----------|---------|-----------|
| API Design | OpenAPI-first | 3.1.x | Contrato claro, generación automática de docs |
| Async Feedback | Server-Sent Events (SSE) | Native FastAPI | Más simple que WebSockets, suficiente para progreso |
| Error Format | RFC 7807 Problem Details | Standard | Respuestas de error consistentes y parseables |
| Documentation | Swagger UI + ReDoc | Auto-generated | Incluido en FastAPI, zero config |

**SSE Resilience (From Advanced Elicitation):**
- Implementar reconnect automático en cliente
- State recovery tras desconexión
- Heartbeat cada 30 segundos

### Frontend Architecture

| Componente | Decisión | Versión | Rationale |
|------------|----------|---------|-----------|
| Server State | React Query (TanStack) | 5.x | Cache inteligente, refetch automático |
| Client State | Zustand | 4.x (opcional MVP) | Ligero, sin boilerplate, solo si necesario |
| Maps | MapLibre GL JS | 4.x | GPU-accelerated, 60 FPS, mejor para interactividad |
| Charts | Recharts | 2.x | React-native, composable, responsive |
| Forms | React Hook Form | 7.x | Performance, validación con Zod |

**State Architecture:**
```
Server State (React Query) ←→ API
        ↓
Client State (Zustand) ←→ UI Components (solo si necesario)
        ↓
Local State (useState) ←→ Form Inputs
```

**WebGL Fallback (From Party Mode):**
- Detección de WebGL al cargar MapLibre
- Mensaje amigable para dispositivos sin soporte
- Considerar fallback a imagen estática del mapa

### Infrastructure & Deployment

| Componente | Decisión | Rationale |
|------------|----------|-----------|
| Frontend Hosting | Vercel (Edge) | Nativo para Next.js, CDN global |
| Backend Hosting | Vercel Serverless Functions (Python) | Monorepo deployment, auto-scaling |
| Database | Neon PostgreSQL / Supabase | Serverless PostgreSQL con PostGIS habilitado |
| Redis | Upstash Redis | Serverless Redis, compatible Vercel |
| CI/CD | Vercel Git Integration | Zero-config, preview deployments |

**Cold Start Mitigation (From Advanced Elicitation):**
- Endpoint de warmup para funciones Python
- Configurar `@vercel/python` con optimizaciones
- Considerar Vercel Pro para funciones más rápidas

### Decision Impact Analysis

**Implementation Sequence:**
1. Setup Monorepo (Turborepo) → Primera historia
2. Configurar Neon PostgreSQL + Upstash Redis → Dependencia de todos los features
3. Implementar Auth (NextAuth + API Keys) → Gate para todas las APIs
4. Core API endpoints con OpenAPI → Base para frontend
5. Frontend con React Query + MapLibre → UI principal

**Cross-Component Dependencies:**
- SQLAlchemy models → Pydantic schemas → OpenAPI spec → React Query types
- NextAuth session → API Key management → Rate Limiting (SlowAPI)
- SSE events → React Query cache invalidation → UI updates

### Refinements from Advanced Elicitation & Party Mode

| Área | Refinamiento | Origen |
|------|--------------|--------|
| Database Provider | Neon/Supabase en lugar de Vercel Postgres | Winston (Party Mode) |
| Zustand | Opcional para MVP, solo si se necesita estado complejo | John (Party Mode) |
| WebGL Fallback | Mensaje amigable para dispositivos legacy | Sally (Party Mode) |
| SSE Resilience | Reconnect automático + state recovery | Advanced Elicitation |
| Cold Starts | Warmup endpoints para Python serverless | Advanced Elicitation |

