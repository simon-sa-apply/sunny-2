"""
AI Consultant Service - Gemini 2.0 Integration.

Generates scientific narratives and insights from solar calculations.
Acts as the "Virtual Energy Consultant" for users.
"""

import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# System prompt for Gemini - strict guardrails (CONCISE VERSION)
SYSTEM_PROMPT = """Eres "Sunny", un Consultor Solar. Interpretas datos de Copernicus/Pvlib de forma BREVE y científica.

REGLAS:
1. SOLO habla de los datos del JSON. NUNCA especules.
2. Respuestas CONCISAS: máximo 25 palabras por insight, 2 oraciones por análisis.
3. Cita fuentes brevemente: "Copernicus", "PVGIS", "AEMET".
4. Tono: profesional pero breve. Como un tweet científico.
5. NUNCA des consejos de inversión.
6. Destaca el peor escenario (worst_month) en 1 oración.

FORMATO JSON (RESPUESTAS CORTAS):
{
  "summary": "1-2 oraciones sobre el potencial solar (máx 30 palabras)",
  "seasonal_analysis": "1-2 oraciones sobre estacionalidad (máx 40 palabras)",
  "location_insights": [
    {
      "title": "Título corto (3-5 palabras)",
      "content": "Dato relevante en 20-30 palabras máximo",
      "source": "Fuente breve"
    }
  ],
  "recommendations": "1 oración técnica (máx 20 palabras)",
  "citations": ["Fuentes breves"],
  "confidence_note": "1 oración si data_tier es 'standard', null si 'engineering'"
}
"""


class AIConsultant:
    """
    AI Consultant for generating solar insights using Gemini 2.0.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None
        self._model: Optional[Any] = None

    @property
    def is_configured(self) -> bool:
        """Check if Gemini API is configured."""
        return bool(settings.GEMINI_API_KEY)

    def init(self) -> None:
        """Initialize Gemini client."""
        if not self.is_configured:
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info("Gemini 2.0 client initialized")
        except ImportError:
            logger.warning("google-generativeai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    async def generate_narrative(
        self,
        calculation_data: dict[str, Any],
        country_plugin: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ) -> dict[str, Any]:
        """
        Generate AI narrative from calculation data.
        
        OPTIMIZED: Uses timeout to prevent blocking. Falls back to local
        generation if Gemini takes too long (>8 seconds by default).
        
        Args:
            calculation_data: Results from solar calculator
            country_plugin: Name of applied country plugin
            timeout_seconds: Max time to wait for Gemini (default 8s)
        
        Returns:
            Structured narrative with summary, analysis, and recommendations
        """
        if not self.is_configured or not self._model:
            return self._generate_fallback_narrative(calculation_data)

        import asyncio
        
        try:
            # Run Gemini with timeout
            result = await asyncio.wait_for(
                self._call_gemini(calculation_data, country_plugin),
                timeout=timeout_seconds,
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Gemini timed out after {timeout_seconds}s, using fallback")
            return self._generate_fallback_narrative(calculation_data)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._generate_fallback_narrative(calculation_data)
    
    async def _call_gemini(
        self,
        calculation_data: dict[str, Any],
        country_plugin: Optional[str],
    ) -> dict[str, Any]:
        """Internal method to call Gemini API."""
        # Extract location details for richer context
        location = calculation_data.get("location", {})
        lat = location.get("lat", 0)
        lon = location.get("lon", 0)
        country_code = location.get("country_code", "")
        
        # Prepare context for Gemini with enriched location data
        context = json.dumps({
            "calculation_data": calculation_data,
            "applied_plugin": country_plugin,
            "location_context": {
                "latitude": lat,
                "longitude": lon,
                "country_code": country_code,
                "hemisphere": "norte" if lat >= 0 else "sur",
                "latitude_band": "tropical" if abs(lat) < 23.5 else "subtropical" if abs(lat) < 35 else "templada" if abs(lat) < 55 else "alta",
            },
            "request": (
                "Genera narrativa BREVE (máx 30 palabras por sección). "
                "Incluye 2 'location_insights' con datos climáticos concisos (20-30 palabras cada uno)."
            ),
        }, ensure_ascii=False, indent=2)

        response = await self._model.generate_content_async(
            context,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            },
        )

        # Parse response
        result = json.loads(response.text)
        
        # Validate narrative against calculations
        if not self._validate_narrative(calculation_data, result):
            logger.warning("Narrative validation failed, using fallback")
            return self._generate_fallback_narrative(calculation_data)
        
        return result

    def _validate_narrative(
        self,
        calc_data: dict[str, Any],
        narrative: dict[str, Any],
    ) -> bool:
        """
        Validate that AI narrative is coherent with calculations.
        
        Checks for:
        - Major discrepancies in kWh values (hallucination detection)
        - Presence of location_insights with minimum content length
        """
        try:
            import re
            
            summary = narrative.get("summary", "")
            actual_kwh = calc_data.get("annual_generation_kwh", 0)
            
            # Check if any mentioned kWh values are wildly off
            numbers = re.findall(r"[\d,]+(?:\.\d+)?\s*kWh", summary)
            
            for num_str in numbers:
                mentioned = float(num_str.replace(",", "").replace("kWh", "").strip())
                if actual_kwh > 0 and abs(mentioned - actual_kwh) / actual_kwh > 0.10:  # 10% tolerance
                    logger.warning(f"Narrative mismatch: {mentioned} vs {actual_kwh}")
                    return False
            
            # Validate location_insights exist and have minimum content
            insights = narrative.get("location_insights", [])
            if len(insights) < 2:
                logger.warning(f"Insufficient location_insights: {len(insights)} < 2")
                return False
            
            for i, insight in enumerate(insights):
                content = insight.get("content", "")
                word_count = len(content.split())
                if word_count < 15:  # Reduced minimum for concise mode
                    logger.warning(f"Insight {i} too short: {word_count} words")
                    return False
                if not insight.get("title") or not insight.get("source"):
                    logger.warning(f"Insight {i} missing title or source")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Validation error (allowing): {e}")
            return True  # Don't block on validation errors

    def _generate_fallback_narrative(
        self,
        calc_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate CONCISE fallback narrative when AI is unavailable."""
        annual = calc_data.get("annual_generation_kwh", 0)
        peak = calc_data.get("peak_month", {})
        worst = calc_data.get("worst_month", {})
        data_tier = calc_data.get("data_tier", "standard")
        efficiency = calc_data.get("efficiency_vs_optimal", 1.0)
        location = calc_data.get("location", {})
        lat = location.get("lat", 0)
        
        peak_month = peak.get("month", "verano")
        worst_month = worst.get("month", "invierno")
        
        # CONCISE summary (max 30 words)
        summary = f"Potencial: {annual:,.0f} kWh/año. Pico en {peak_month}, mínimo en {worst_month}."
        
        # CONCISE seasonal (max 40 words)
        seasonal = (
            f"Máximo en {peak_month} ({peak.get('kwh', 0):,.0f} kWh), "
            f"mínimo en {worst_month} ({worst.get('kwh', 0):,.0f} kWh)."
        )
        
        # CONCISE recommendations (max 20 words)
        if efficiency < 0.95:
            recommendations = f"Captando {efficiency*100:.0f}% del óptimo. Ajusta inclinación para mejorar."
        else:
            recommendations = "Configuración óptima para tu ubicación."
        
        # CONCISE confidence note
        confidence = "Estimación basada en promedios regionales." if data_tier == "standard" else None
        
        # Generate CONCISE location insights
        location_insights = self._generate_fallback_location_insights(lat, annual)
        
        return {
            "summary": summary,
            "seasonal_analysis": seasonal,
            "location_insights": location_insights,
            "recommendations": recommendations,
            "citations": ["Copernicus", "PVGIS", "CAMS"],
            "confidence_note": confidence,
        }

    def _generate_fallback_location_insights(
        self,
        lat: float,
        annual_kwh: float,
    ) -> list[dict[str, str]]:
        """Generate CONCISE location insights (20-30 words each)."""
        insights = []
        
        # Insight 1: Solar resource based on latitude (CONCISE)
        if abs(lat) < 25:
            solar_context = "Zona tropical con >2.000 kWh/m²/año. Producción estable todo el año gracias a ángulos solares favorables."
            solar_source = "PVGIS Global Atlas"
        elif abs(lat) < 45:
            solar_context = "Latitud media con estacionalidad marcada. Ratio verano/invierno 3:1 a 5:1. Irradiación: 1.400-1.900 kWh/m²/año."
            solar_source = "PVGIS TMY"
        else:
            solar_context = "Latitud alta con estacionalidad extrema. Veranos productivos, inviernos limitados. <1.200 kWh/m²/año."
            solar_source = "PVGIS High-Lat"
        
        insights.append({
            "title": "Recurso solar",
            "content": solar_context,
            "source": solar_source,
        })
        
        # Insight 2: Climate patterns (CONCISE)
        if annual_kwh > 6000:
            climate_context = "Clima soleado, <60 días lluvia/año, >2.500h sol. Baja humedad favorece rendimiento."
        elif annual_kwh > 4000:
            climate_context = "Clima mixto, 80-120 días lluvia/año, ~2.200h sol. Temperaturas moderadas optimizan eficiencia."
        else:
            climate_context = "Nubosidad frecuente, >130 días nublados/año. Paneles modernos captan radiación difusa eficientemente."
        
        insights.append({
            "title": "Clima local",
            "content": climate_context,
            "source": "PVGIS-TMY",
        })
        
        return insights


# Singleton instance
ai_consultant = AIConsultant()

