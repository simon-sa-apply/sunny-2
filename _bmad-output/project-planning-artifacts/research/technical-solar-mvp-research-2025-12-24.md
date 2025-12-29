---
stepsCompleted: [1]
inputDocuments: ['bases.md', 'brainstorming-session-2025-12-24.md']
workflowType: 'research'
lastStep: 1
research_type: 'Technical & Domain'
research_topic: 'Copernicus CDSE, Gemini 2.0 Integration, and 2024-25 Solar Metrics'
research_goals: 'Validate technical feasibility of CDSE API, define Gemini 2.0 implementation strategy, and establish updated solar generation constants.'
user_name: 'Simon.salazar'
date: '2025-12-24'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical & Domain - Solar Generation MVP

**Date:** 2025-12-24
**Author:** Simon.salazar
**Research Type:** Technical & Domain

---

## Executive Summary
This research consolidates the technical and domain requirements for the Solar Generation Estimator MVP. It focuses on the integration with the Copernicus Data Space Ecosystem (CDSE), the implementation of Gemini 2.0 for proactive communication, and the standardization of solar energy metrics for 2024-2025.

---

## 1. Technical Research: Copernicus CDSE Integration

### 1.1 Data Sources and APIs
The Copernicus Data Space Ecosystem (CDSE) provides several interfaces. For high-resolution solar radiation and climate variables, the following are identified:
- **ERA5-Land:** Provides hourly global climate variables at ~9km resolution. Crucial for historical radiation data.
- **CAMS (Copernicus Atmosphere Monitoring Service):** Provides specific Solar Radiation Services (McClear model) for GHI and DNI with high accuracy, accounting for aerosols and clouds.
- **Interface:** The MVP should utilize the **OData API** for metadata discovery and the **S3 interface** or **OpenSearch** for data retrieval.
- **Python Library:** Use of `cdsapi` for Direct Climate Data Store access or `sentinelsat`/`eodag` for broader CDSE integration.

### 1.2 Connectivity Strategy
- **Authentication:** Keycloak-based OAuth2.0.
- **Optimization:** A **Caching Layer** (SQLite or Redis) is mandatory to store coordinates-based radiation profiles and minimize API latency (which can range from seconds to minutes for processed products).

---

## 2. AI Research: Gemini 2.0 Implementation

### 2.1 Agent Architecture
Gemini 2.0 introduces significant improvements in multimodal reasoning and function calling.
- **Function Calling:** The MVP will define a `get_solar_calculation(lat, lon, area)` tool in Python. Gemini will call this tool instead of attempting to calculate radiation itself.
- **Grounding & Transparency:** Gemini will be prompted to cite the specific Copernicus dataset (e.g., "ERA5-Land via CDSE") and the margin of error (typically 5-15% for satellite-derived radiation).
- **Proactive Warnings:** Using its advanced reasoning, Gemini 2.0 can identify if a point is in a high-relief area (using DEM data) and warn about "Shading Effects" not fully captured by the GHI model.

---

## 3. Domain Research: Solar Metrics 2024-2025

### 3.1 Efficiency and Constants
Updated standards for 2024-2025 residential installations:
- **Panel Efficiency:** Residential N-type TOPCon or HJT panels now average **22.5% to 23.8%** efficiency.
- **Standard Power Density:** ~420W to 450W per standard panel size (approx. 2m²), translating to **~210W - 225W per m²** under STC (Standard Test Conditions).
- **Performance Ratio (PR):** A conservative PR of **0.75 to 0.80** should be used for estimations to account for inverter losses, wiring, and temperature degradation.

### 3.2 Calculation Logic
- **Formula:** $E = A \times r \times H \times PR$
  - $E$: Energy (kWh)
  - $A$: Total solar panel area ($m^2$)
  - $r$: Solar panel yield or efficiency (%)
  - $H$: Annual average solar radiation on tilted panels (shadings not included)
  - $PR$: Performance ratio (coefficient for losses)

---

## 4. Conclusions
The technical path is clear: a decoupled Python backend handling CDSE data and deterministic math, with Gemini 2.0 acting as a sophisticated, transparent interface. The focus on TOPCon efficiency and CAMS radiation data ensures the MVP is state-of-the-art.

---

## Sources & Citations
1. [Copernicus Data Space Ecosystem Documentation](https://dataspace.copernicus.eu/explore-data/documentation)
2. [Gemini 2.0 API Reference](https://ai.google.dev/gemini/docs)
3. [IEA PVPS Trends in Photovoltaic Applications 2024](https://iea-pvps.org/)
4. [CAMS Solar Radiation Services](https://ads.atmosphere.copernicus.eu/)

