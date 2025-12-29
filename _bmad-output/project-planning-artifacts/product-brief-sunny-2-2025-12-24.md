---
stepsCompleted: [1, 2]
inputDocuments: ['bases.md', '_bmad-output/analysis/brainstorming-session-2025-12-24.md', '_bmad-output/project-planning-artifacts/research/technical-solar-mvp-research-2025-12-24.md']
workflowType: 'product-brief'
lastStep: 2
project_name: 'sunny-2'
user_name: 'Simon.salazar'
date: '2025-12-24'
---

# Product Brief: sunny-2

## Executive Summary

sunny-2 es una plataforma de diagnóstico solar de alta precisión diseñada para usuarios finales y potenciales adoptantes de energía fotovoltaica. A diferencia de las calculadoras convencionales, sunny-2 utiliza datos satelitales directos del programa Copernicus (CDSE) y una arquitectura de IA proactiva (Gemini 2.0) para entregar estimaciones con rigor científico. El MVP se centra en proporcionar una estimación exacta de generación basada en geolocalización, parámetros físicos (superficie, inclinación, orientación) y variables climáticas históricas, garantizando transparencia absoluta sobre la certeza de los datos.

---

## Core Vision

### Problem Statement

Los usuarios interesados en energía solar a menudo se encuentran con estimaciones genéricas que ignoran variables críticas como la orientación cardinal, la inclinación específica y, lo más importante, la variabilidad climática local (nubosidad acumulada, eventos climáticos extremos). Esta falta de precisión genera incertidumbre y frena la adopción de tecnologías limpias, ya que el usuario no tiene una base técnica confiable para calcular su retorno de inversión.

### Problem Impact

La imprecisión en las herramientas actuales lleva a:
1.  Expectativas de generación irreales (sobreestimación o subestimación).
2.  Desconfianza en los proveedores de paneles solares.
3.  Incapacidad de entender los límites reales de generación en meses críticos (invierno vs. verano).

### Why Existing Solutions Fall Short

Las soluciones actuales suelen basarse en promedios regionales amplios o bases de datos desactualizadas. Pocas herramientas integran datos de reanálisis climático en tiempo real o modelos de atmósfera (como aerosoles y nubosidad de CAMS) y casi ninguna explica proactivamente al usuario *por qué* una estimación puede tener un margen de error (ej. topografía compleja o microclimas).

### Proposed Solution

Un MVP basado en Python y Gemini 2.0 que integra:
- **Motor de Cálculo Determinista:** Basado en física solar y datos de Copernicus CDSE, permitiendo al usuario ajustar m², inclinación y orientación (opcional, con valores óptimos por defecto).
- **Visualización Interactiva:** Un mapa global para selección precisa y gráficos de límites de generación mensual.
- **Procesamiento Asíncrono:** Arquitectura de eventos con feedback visual de progreso técnico ("Conectando con satélite...", "Extrayendo capas...") para gestionar la latencia de CDSE.
- **Agente de IA Transparente:** Un consultor que utiliza Gemini 2.0 para explicar resultados, eventos climáticos y límites técnicos sin recurrir a mensajes de error negativos, manteniendo la coherencia científica.

### Key Differentiators

- **Rigor Científico:** Uso directo de ERA5-Land y CAMS de la Agencia Espacial Europea.
- **Transparencia Proactiva:** Comunicación clara de incertidumbres y límites geográficos (ej. Latitud > 60° donde la cobertura satelital es limitada).
- **Arquitectura Escalable:** Estructurado como un servidor de datos desacoplado, listo para integrarse vía MCP.
- **Validación Estricta:** Implementación de Guardrails para asegurar que la "voz" de la IA sea siempre fiel a los cálculos deterministas de Python.
