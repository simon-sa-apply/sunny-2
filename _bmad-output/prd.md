---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: ['bases.md', '_bmad-output/analysis/brainstorming-session-2025-12-24.md', '_bmad-output/project-planning-artifacts/research/technical-solar-mvp-research-2025-12-24.md', '_bmad-output/project-planning-artifacts/product-brief-sunny-2-2025-12-24.md']
documentCounts:
  briefs: 1
  research: 1
  brainstorming: 1
  projectDocs: 0
workflowType: 'prd'
lastStep: 8
project_name: 'sunny-2'
user_name: 'Simon.salazar'
date: '2025-12-24'
---

# Product Requirements Document: sunny-2

## Executive Summary

sunny-2 es una plataforma de diagnóstico solar de alta precisión diseñada para usuarios finales y potenciales adoptantes de energía fotovoltaica. A diferencia de las calculadoras convencionales, sunny-2 utiliza datos satelitales directos del programa Copernicus (CDSE) y una arquitectura de IA proactiva (Gemini 2.0) para entregar estimaciones con rigor científico. El MVP se centra en proporcionar una estimación exacta de generación basada en geolocalización, parámetros físicos (superficie, inclinación, orientación) y variables climáticas históricas, garantizando transparencia absoluta sobre la certeza de los datos.

### What Makes This Special

Lo que define a sunny-2 es el compromiso inquebrantable con la **precisión científica y la transparencia proactiva**. No solo entrega números; entrega confianza al citar fuentes satelitales de la ESA y explicar de forma coherente y científica las razones técnicas cuando una estimación tiene una incertidumbre elevada o limitaciones geográficas (ej. latitudes > 60°), evitando respuestas genéricas o negativas.

## Project Classification

**Technical Type:** web_app / api_backend
**Domain:** energy
**Complexity:** high
**Project Context:** Greenfield - new project

El proyecto se clasifica como una aplicación web de alta complejidad técnica debido a la integración de modelos climáticos masivos (ERA5-Land/CAMS), procesamiento asíncrono para gestionar latencias de APIs científicas y una capa de inteligencia artificial (Gemini 2.0) diseñada para la interpretación de datos deterministas.

## Domain-Specific Requirements

### Energy Compliance & Regulatory Overview
sunny-2 operará en un dominio de alta precisión técnica, preparando el terreno para el dimensionamiento de sistemas inyectables a la red (Grid-tie). El producto se alinea con las expectativas de mercados avanzados (Alemania) y mercados de alta radiación (Chile).

### Key Domain Concerns
- **Disponibilidad de Datos y Modelado Predictivo:** Ante la ausencia de datos en tiempo real (ej. años 2023-2024) para ciertas latitudes, el sistema activará automáticamente el **Modo de Estimación Histórica (Forecasting)**.
    - **Ventana de Datos:** El modelo utilizará preferentemente **20 años** de información histórica de Copernicus, con un **mínimo mandatorio de 10 años** para garantizar validez estadística.
- **Impacto Ambiental:** El reporte incluirá el ahorro de CO2 estimado, siguiendo los factores de emisión regionales (Alemania vs. Chile) para mayor relevancia local.

### Data Science Strategy & Analytical Approach
- **Estrategia de Entrenamiento:** Implementación de métodos de ciencia de datos para entrenar modelos locales basados en los reanálisis de ERA5-Land.
- **Validación Predictiva:** Uso de "Backtesting" (comparar predicciones contra años históricos conocidos) para generar un **Score de Desviación** técnico.
- **Etiquetado de Certeza:** El sistema diferenciará visualmente entre "Datos de Tiempo Real", "Datos Recientes (< 2 años)" y "Modelo Predictivo (Basado en Histórico)".

### Compliance & Industry Standards
- **Lógica de Cálculo:** Alineada con el estándar **IEC 61724-1** y la metodología **PVWatts (NREL)**.
- **Arquitectura Modular de Constantes:** Implementación de un sistema de **Plugins por País** para cargar automáticamente:
    - **Chile:** Factores de Net Billing (Ley 21.118) y constantes de la SEC.
    - **Alemania:** Criterios de precisión de la norma DIN V 18599.
    - **Global:** Factores de pérdida por temperatura y eficiencia de red locales.
- **Fallback de Usuario (Zonas Standard):** Capacidad de ingreso manual de tarifa eléctrica (kWh) para habilitar cálculos de ahorro económico en regiones sin plugin normativo activo, sin bloquear el flujo principal.

### Implementation Considerations
- **Detección Geográfica:** El orquestador de Python detectará automáticamente el contexto nacional para aplicar el plugin correspondiente, asegurando que Luis reciba un reporte localizado y Alex obtenga un JSON con los metadatos normativos aplicados.
- **Feedback Loop de Demanda:** Inclusión de un mecanismo de "Voto por mi país" en el dashboard para zonas `standard`, permitiendo priorizar el roadmap de ingeniería basado en el interés real de los usuarios.

## Success Criteria

### User Success
- **"Aha!" Moment:** Se alcanza cuando el Agente de IA (Gemini 2.0) interpreta el gráfico mensual, explicando la relación entre la nubosidad histórica de Copernicus y la generación estimada.
- **Indicador de Confianza:** Medido por la interacción del usuario con los parámetros de optimización (inclinación/orientación) tras recibir el primer diagnóstico.
- **Resultado Final:** El usuario manifiesta sentirse empoderado para tomar una decisión de compra basada en datos, no solo en promedios.

### Business Success
- **Adopción MVP:** Alcanzar las primeras 100 llamadas/estimaciones exitosas.
- **Escalabilidad de Ecosistema:** El "Data Server" es consultado exitosamente por al menos 2 agentes externos (via simulación MCP o API), demostrando la arquitectura desacoplada.

### Technical Success
- **Precisión del Motor:** El margen de error entre el cálculo determinista de Python y los datos fuente de Copernicus (CAMS/ERA5) debe ser inferior al **5%**.
- **Disponibilidad:** 99% de éxito en la recuperación de datos cacheados para evitar re-latencia en puntos consultados previamente.

## Product Scope

### MVP - Minimum Viable Product
- Conexión a Copernicus CDSE (ERA5-Land y CAMS).
- Motor de cálculo solar en Python (GHI/DNI, eficiencia de paneles TOPCon).
- Mapa interactivo para selección de coordenadas.
- Parámetros de entrada: m², Inclinación, Orientación (opcional).
- Interfaz de Chat con Gemini 2.0 para interpretación científica.
- Procesamiento asíncrono con feedback de progreso.

### Growth Features (Post-MVP)
- **Reportes Exportables:** Generación de PDF/CSV con el diagnóstico técnico detallado.
- **Comparativa de Ubicaciones:** Capacidad de contrastar el potencial de dos puntos geográficos simultáneamente.
- **Integración MCP Full:** Servidor de herramientas (tools) para que cualquier LLM pueda usar el motor de cálculo.

### Vision (Future)
- **Análisis de Sombreado por Topografía:** Uso de modelos digitales de elevación (DEM) para detectar sombras de montañas o edificios cercanos.
- **Integración con Precios Locales:** Estimación de ROI basada en tarifas eléctricas por país/región.

## User Journeys

### Journey 1: Luis - La Búsqueda de la Certeza Solar
Luis es un propietario meticuloso que desea instalar paneles en su tejado de 15 m². Frustrado por presupuestos comerciales opacos, entra en **sunny-2**, marca su ubicación exacta y define: 15 m², orientación Norte e inclinación de 20°. Mientras el sistema analiza datos históricos de Copernicus, Luis recibe feedback visual del progreso técnico ("Conectando con satélite...", "Interpolando radiación...").

El resultado es un dashboard profesional con 5 contenedores clave:
1. **Mapa de Ubicación:** Confirmación visual del punto de análisis.
2. **Curva de Generación Mensual:** Una curva de campana que muestra la oscilación de la radiación durante el año.
3. **Picos Estacionales:** Análisis del "Peor Escenario" (mes de mínima generación) y el pico máximo de rendimiento.
4. **Insights de IA (Gemini 2.0):** Una narrativa científica que explica la oscilación horaria y por qué ciertos meses tienen mayor variabilidad climática.
5. **Toggle de Reloj Solar:** Una vista interactiva local que permite a Luis simular cambios en la inclinación/orientación y ver el impacto visual e inmediato en la captación.

Luis sale del proceso con un reporte completo, correcto y preciso, sintiéndose empoderado para decidir su compra.

### Journey 2: Alex - Integrando Inteligencia Solar vía MCP
Alex es un desarrollador construyendo un agente de IA para optimización inmobiliaria. Necesita datos solares validados. Conecta su agente directamente al **Data Server** de sunny-2 vía API/MCP. El servidor actúa como un "Buffer de Estabilidad", protegiendo a Alex de cambios en los formatos de Copernicus.

Alex recibe un JSON enriquecido con la "Respuesta Maestra", que incluye:
- Datos deterministas de irradiación.
- Un objeto `ai_insights` con la narrativa interpretativa, citas a las fuentes de datos y un `confidence_score` técnico.
Esto le permite procesar masivamente estimaciones con garantía científica.

### Journey Requirements Summary

- **Input Engine:** Soporte para m², inclinación y orientación cardinal (opcional, con fallback óptimo).
- **Interpolation Model (Python):** Generación de una función de respuesta local tras la descarga de datos de CDSE para permitir simulaciones en tiempo real sin latencia de API externa.
- **Visualization Suite:** Gráficos de curva de campana anual y componente de "Reloj Solar" interactivo.
- **Dashboard de 5 Contenedores:** Estructura de UI optimizada para análisis técnico y de "Peor Escenario", incluyendo **Tooltips Visuales** para parámetros complejos.
- **Unified Data API (Data Server):** Servidor basado en OpenAPI que actúa como capa de estabilidad y entrega JSON enriquecido con insights de IA y confianza técnica.
- **Security & Quota Protection:** Implementación de **Rate Limiting** y ofuscación de coordenadas en el caché para proteger la cuota de Copernicus CDSE.
- **AI Speculation Guardrail:** Uso de un **System Prompt** estricto para Gemini 2.0 que limite la narrativa a los datos deterministas de Python, gestionando la incertidumbre mediante el `confidence_score`.
- **Validation Layer:** Guardrails de coherencia entre los cálculos de Python y la narrativa de la IA.

## Innovation & Novel Patterns

### Detected Innovation Areas
- **IA Consultiva Transparente (Gemini 2.0):** A diferencia de bots genéricos, el agente actúa como un "Consultor Solar" que traduce telemetría satelital compleja en consejos accionables, manteniendo un tono profesional y científico.
- **Cruce Generación vs. Consumo:** Innovación funcional donde el usuario puede ingresar su consumo estimado (kWh/mes) para que el motor calcule el **Porcentaje de Cobertura Energética** en tiempo real, desglosado por mes y hora del día.
- **Motor de Interpolación de Baja Latencia:** Uso de modelos matemáticos locales en Python que permiten simulaciones instantáneas de parámetros físicos sobre una base de datos científica masiva.

### Market Context & Competitive Landscape
La mayoría de las herramientas competitivas se quedan en el "Potencial de Irradiación". sunny-2 innova al cerrar el ciclo del usuario: "Esto es lo que el sol da" + "Esto es lo que tú gastas" = "Este es tu nivel de independencia energética".

### Validation Approach
- **Validación del Algoritmo de Cobertura:** Comparativa de los cálculos de porcentaje de cobertura contra simuladores de grado industrial (ej. PVSyst) para asegurar que el consejo del "Consultor" sea preciso.
- **A/B Testing de Personalidad:** Pruebas de engagement para asegurar que el tono de "Consultor" genera más confianza que un tono puramente técnico.

### Risk Mitigation
- **Riesgo de Datos de Consumo:** El usuario puede no conocer su consumo exacto. 
- **Mitigación:** El Consultor ofrecerá perfiles de consumo promedio por país (Chile/Alemania) como "inputs inteligentes" para evitar bloqueos en el flujo del usuario.

## web_app / api_backend Specific Requirements

### Project-Type Overview
sunny-2 se estructura como un "Data-First Web App", donde el núcleo es un Servidor de Datos (Data Server) que alimenta tanto a la interfaz móvil del usuario final como a agentes de IA externos. El enfoque es entregar precisión científica con una experiencia de usuario fluida en dispositivos móviles.

### Functional Requirements

#### FR-1: Gestión de Coordenadas y Mapas
- El sistema debe permitir la selección de un punto geográfico mediante click en mapa o búsqueda por texto (`GET /geosearch`).
- Debe persistir las coordenadas con ofuscación en el caché para protección de cuota y privacidad.

#### FR-2: Motor de Ciencia de Datos (Copernicus CDSE)
- Debe descargar asíncronamente datos de ERA5-Land y CAMS para el punto seleccionado.
- Debe generar un modelo de interpolación local para simular cambios de inclinación (0-90°) y orientación (360°) sin nuevas llamadas a la API externa.
- Debe activar el "Cache On-Demand" de 10-20 años si los datos en tiempo real no están disponibles o para generar el modelo predictivo.

#### FR-3: Consultor Solar (Gemini 2.0)
- El agente debe recibir un contexto JSON con: Resultados deterministas de Python, `data_tier` (Engineering/Standard), y `confidence_score`.
- Debe generar una respuesta narrativa explicando los picos de generación, estacionalidad y limitaciones climáticas.
- Debe manejar el "Smart Fallback" invitando al usuario a ingresar su tarifa eléctrica si el tier es `standard`.

#### FR-4: Dashboard Asíncrono (SSE)
- La interfaz debe mostrar un progreso visual real de las etapas de cálculo ("Conectando satélites", "Calculando irradiación histórica", etc.) vía Server-Sent Events (SSE).

#### FR-5: Data Server & Conectividad (API para Alex)
- Debe entregar un JSON estructurado bajo contrato OpenAPI que incluya los cálculos deterministas y el objeto `ai_insights`.
- Debe implementar autenticación vía API Keys para consumidores externos.

### Non-Functional Requirements (NFR)

#### NFR-1: Precisión y Rigor Científico
- El motor de cálculo debe mantener un margen de error máximo del **5%** respecto a los datos fuente de Copernicus.
- Los cálculos deben seguir metodologías estándar de la industria (PVWatts/IEC 61724-1).

#### NFR-2: Rendimiento y Latencia
- El modelo de interpolación local debe responder en menos de **200ms** para permitir la interactividad del "Reloj Solar".
- El caché geográfico debe resolver consultas repetidas en un radio de 5km en menos de **500ms**.

#### NFR-3: Seguridad y Cuotas
- Implementación de **Rate Limiting** por IP y API Key para proteger la cuota de la API de Copernicus.
- Ofuscación de coordenadas en el almacenamiento de caché (redondeo de decimales).

#### NFR-4: Escalabilidad
- Arquitectura desacoplada que permita escalar el motor de procesamiento de datos independientemente del servidor web/frontend.

### Technical Architecture Considerations
- **Data Server Specification:** Uso de **OpenAPI (Swagger)** para la definición de contratos de datos, garantizando estabilidad y facilidad de integración para desarrolladores externos (Alex).
- **Asynchronous Feedback:** Implementación de **Server-Sent Events (SSE)** para informar el progreso técnico ("Conectando...", "Procesando...") a dispositivos móviles en tiempo real, optimizando el consumo de batería y la resiliencia en redes inestables.
- **Mobile-First Map:** Interfaz de mapa optimizada para uso en terreno, priorizando la ligereza y la velocidad de carga de coordenadas.

### API Endpoint Specification
- `POST /estimate`: Procesa coordenadas, superficie e inclinación para generar el cálculo base de irradiación.
- `POST /consumption`: Cruza el potencial solar calculado con el consumo estimado del hogar para determinar el porcentaje de cobertura energética.
- `POST /consultant/chat`: Endpoint orquestador que gestiona la conversación con Gemini 2.0, inyectando el contexto de los cálculos deterministas de Python.
- `GET /geosearch`: Servicio de búsqueda de ubicaciones por texto para facilitar la navegación en el mapa.

### Authentication Model (API Consumers)
- **Primary Method (MVP):** Autenticación mediante **API Keys** estáticas para desarrolladores y agentes externos, facilitando una integración rápida y segura.

### SEO & GEO Strategy
- **Localized Landing Pages:** Generación dinámica de URLs y contenido por país y región para maximizar el tráfico de búsqueda local.
- **Structured Data (JSON-LD):** Implementación de esquemas de datos estructurados para que los motores de búsqueda identifiquen a sunny-2 como una herramienta técnica de energía solar, mejorando la visibilidad mediante Rich Snippets.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Hybrid "Global Brain, Regional Heart" (Pensamiento C) - **ACTUALIZADO**

- **Cerebro Global con Cobertura Real:** El sistema utiliza una **estrategia de cascada de datos**:
  - **CAMS (Copernicus):** Datos horarios de alta precisión para Europa, África, Medio Oriente y Asia.
  - **PVGIS (EU JRC):** Datos mensuales de calidad para **Americas** (incluyendo Chile), y como fallback global.
  - **Mock Data:** Último recurso para garantizar respuesta siempre.
  
- **Corazón Regional (Grado de Ingeniería):** Las funcionalidades avanzadas de "Consultor de IA", plugins normativos (Net Billing) y constantes locales están optimizadas inicialmente para **Chile y Alemania**.

- **Data Tiering:** La API/Data Server informará explícitamente el rigor del dato mediante el campo `data_tier: ["engineering", "standard"]`.

- **Cobertura Verificada:**
  | Región | Fuente | Tipo de Datos |
  |--------|--------|---------------|
  | Europa | CAMS | Horario (8760 pts/año) |
  | Chile/Americas | PVGIS-NSRDB/ERA5 | Mensual (12 pts/año) |
  | Global | PVGIS-ERA5 | Mensual (12 pts/año) |

**Resource Requirements:** Equipo pequeño de alto rendimiento (1 PM/Analyst, 1 Arquitecto, 1-2 Devs Fullstack con enfoque en Python/Data Science).

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Luis: Selección global en mapa, input de 15m2/inclinación/orientación, feedback asíncrono (SSE), dashboard de 5 contenedores, toggle de reloj solar, reporte preciso en regiones soportadas.
- Alex: Integración vía Data Server (API Keys), contrato OpenAPI, JSON enriquecido con IA y metadatos de `data_tier`.

**Must-Have Capabilities:**
- Conexión global a Copernicus CDSE (ERA5-Land/CAMS).
- Motor de cálculo solar determinista (Python) con interpolación local.
- **Cache On-Demand Geográfico:** Estrategia de procesamiento histórico (10-20 años) activada por demanda de usuario para optimizar recursos.
- Modo Forecasting para zonas sin datos actuales.
- Soporte multi-país (global) con plugins de constantes locales iniciales para Chile y Alemania.
- Dashboard interactivo móvil-friendly con 5 contenedores y tooltips.
- Sistema de Guardrails para la narrativa de Gemini 2.0.

### Post-MVP Features

**Phase 2 (Growth):**
- **GEO-SEO Strategy:** Generación dinámica de páginas de ubicación integradas con datos GEO para capturar tráfico especializado.
- Multimodalidad: Subida de fotos del techo para detección automática de inclinación/obstáculos.
- Comparativa de múltiples ubicaciones en un solo dashboard.
- Exportación de reportes técnicos avanzados (PDF/CSV) para instaladores.

**Phase 3 (Expansion):**
- Análisis de sombreado avanzado usando Modelos Digitales de Elevación (DEM).
- Integración con APIs de precios eléctricos locales para cálculo de ROI exacto.
- Integración MCP Full (Server Tools) para ecosistemas de agentes autónomos.

### Risk Mitigation Strategy

**Technical Risks:** Latencia de APIs externas y escalabilidad del procesamiento histórico.
- *Mitigación:* Procesamiento asíncrono (SSE) y estrategia de **Cache On-Demand** para el motor de ciencia de datos.

**Market Risks:** Desconfianza en los datos fuera de las regiones "Engineering Grade".
- *Mitigación:* Transparencia técnica mediante `data_tier` y avisos claros sobre la naturaleza beta/estándar de ciertas coordenadas.

---

### Apéndice de Scoping: Justificación de Estrategia Híbrida
Aunque la visión objetivo (Pensamiento A) es un producto con precisión de ingeniería global desde el día 1, se ha seleccionado el **Pensamiento C (Híbrido)** para el MVP por las siguientes razones:
1. **Validación Normativa:** La complejidad de las leyes de inyección (Net Billing) varía drásticamente por país. Iniciar con Chile y Alemania permite validar el modelo en dos extremos climáticos y regulatorios antes de escalar.
2. **Optimización de Recursos:** Procesar el histórico de 20 años para todo el globo sin demanda previa es ineficiente. El enfoque híbrido permite un crecimiento orgánico del caché científico.
3. **Protección de Marca:** Garantiza que el "Consultor" sea infalible en los mercados de lanzamiento, manteniendo una base de datos estándar funcional para el resto del mundo.
