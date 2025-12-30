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


# System prompt for Gemini - strict guardrails
SYSTEM_PROMPT = """Eres un Consultor Solar científico llamado "Sunny". Tu rol es interpretar datos de radiación 
de Copernicus y cálculos de Pvlib para usuarios no técnicos, Y ENRIQUECER la información con datos climáticos 
y geográficos relevantes de la ubicación.

REGLAS ESTRICTAS:
1. Para el análisis solar: SOLO habla de los datos que recibes en el JSON. NUNCA especules.
2. Para datos climáticos/geográficos: USA tu conocimiento verificado sobre la región (precipitación, 
   temperatura media, días de sol, características geográficas, contexto energético regional).
3. SIEMPRE cita las fuentes: "Según datos del programa Copernicus de la ESA...", "Datos climáticos de 
   la Agencia Estatal de Meteorología...", "Según registros históricos de precipitación..."
4. Si hay incertidumbre, explica por qué (datos históricos, latitud extrema, nubosidad variable, etc.)
5. Tono: profesional, científico pero accesible. Como un ingeniero explicando a un cliente.
6. NUNCA des consejos de inversión ni hagas promesas de rendimiento financiero.
7. Si los datos son de "data_tier: standard", menciona que son estimaciones basadas en promedios globales.
8. Destaca el "Peor Escenario" (worst_month) para que el usuario tenga expectativas realistas.

REQUISITOS DE DATOS ENRIQUECIDOS (OBLIGATORIO):
- DEBES incluir MÍNIMO 2 datos relevantes sobre el clima o geografía de la ubicación en "location_insights"
- Cada insight DEBE tener MÍNIMO 50 palabras con información verificable y útil
- Ejemplos de datos a incluir: precipitación anual (mm), días de lluvia al año, temperatura media,
  horas de sol anuales, contexto energético de la región, características del clima local,
  comparación con otras regiones, curiosidades geográficas relevantes para energía solar

FORMATO DE RESPUESTA (JSON):
{
  "summary": "Resumen ejecutivo en 2-3 oraciones sobre el potencial solar",
  "seasonal_analysis": "Análisis de estacionalidad explicando picos y valles (mínimo 3 oraciones)",
  "location_insights": [
    {
      "title": "Título corto del dato (ej: 'Precipitación y días nublados')",
      "content": "Descripción detallada de MÍNIMO 50 palabras con datos verificables sobre este aspecto 
                  climático/geográfico y cómo afecta o se relaciona con la generación solar",
      "source": "Fuente del dato (ej: 'AEMET', 'Copernicus Climate', 'PVGIS TMY')"
    },
    {
      "title": "Título del segundo dato relevante",
      "content": "Descripción detallada de MÍNIMO 50 palabras...",
      "source": "Fuente del dato"
    }
  ],
  "recommendations": "Recomendaciones técnicas sobre inclinación/orientación si aplica",
  "citations": ["Lista de todas las fuentes citadas"],
  "confidence_note": "Nota sobre la confianza de los datos si data_tier es 'standard' o null si es 'engineering'"
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
                "Genera una narrativa científica para estos datos de potencial solar. "
                "IMPORTANTE: Incluye OBLIGATORIAMENTE al menos 2 'location_insights' con información "
                "climática y geográfica relevante de la zona (precipitación, días de lluvia, temperatura media, "
                "horas de sol, contexto energético regional, etc.). Cada insight debe tener MÍNIMO 50 palabras."
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
                if word_count < 40:  # Allow some tolerance below 50
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
        """Generate fallback narrative when AI is unavailable."""
        annual = calc_data.get("annual_generation_kwh", 0)
        peak = calc_data.get("peak_month", {})
        worst = calc_data.get("worst_month", {})
        data_tier = calc_data.get("data_tier", "standard")
        efficiency = calc_data.get("efficiency_vs_optimal", 1.0)
        location = calc_data.get("location", {})
        lat = location.get("lat", 0)
        
        peak_month = peak.get("month", "verano")
        worst_month = worst.get("month", "invierno")
        
        summary = (
            f"Tu ubicación tiene un potencial de generación solar de {annual:,.0f} kWh/año. "
            f"El mes de mayor producción es {peak_month} y el de menor es {worst_month}."
        )
        
        seasonal = (
            f"Durante {peak_month}, la radiación solar alcanza su máximo con {peak.get('kwh', 0):,.0f} kWh. "
            f"En {worst_month}, la producción baja a {worst.get('kwh', 0):,.0f} kWh debido a "
            "menor duración del día y mayor nubosidad registrada por los satélites CAMS."
        )
        
        recommendations = ""
        if efficiency < 0.95:
            recommendations = (
                f"Con tu configuración actual, estás captando el {efficiency*100:.0f}% del potencial óptimo. "
                "Considera ajustar la inclinación para maximizar la captación anual."
            )
        else:
            recommendations = "Tu configuración está muy cerca del óptimo para esta ubicación."
        
        confidence = ""
        if data_tier == "standard":
            confidence = (
                "Nota: Estos cálculos usan promedios regionales. Para mayor precisión, "
                "verifica las condiciones locales específicas de tu ubicación."
            )
        
        # Generate location-aware fallback insights based on latitude bands
        location_insights = self._generate_fallback_location_insights(lat, annual)
        
        return {
            "summary": summary,
            "seasonal_analysis": seasonal,
            "location_insights": location_insights,
            "recommendations": recommendations,
            "citations": [
                "ERA5-Land, ECMWF/Copernicus",
                "CAMS Solar Radiation, ESA",
                "PVGIS Typical Meteorological Year (TMY)",
            ],
            "confidence_note": confidence if confidence else None,
        }

    def _generate_fallback_location_insights(
        self,
        lat: float,
        annual_kwh: float,
    ) -> list[dict[str, str]]:
        """Generate location insights based on latitude when AI is unavailable."""
        insights = []
        
        # Insight 1: Solar resource based on latitude
        if abs(lat) < 25:
            solar_context = (
                "Tu ubicación se encuentra en la franja tropical, una de las zonas con mayor "
                "irradiación solar del planeta. Esta región recibe radiación solar directa durante "
                "todo el año con ángulos de incidencia muy favorables. La irradiación global horizontal "
                "típica en estas latitudes supera los 2.000 kWh/m² anuales, lo que representa un "
                "recurso solar excepcional para generación fotovoltaica. Los sistemas solares en esta "
                "zona mantienen producción relativamente constante a lo largo del año."
            )
            solar_source = "PVGIS Global Solar Atlas, JRC European Commission"
        elif abs(lat) < 45:
            solar_context = (
                "Tu ubicación se encuentra en la franja de latitudes medias, caracterizada por "
                "una marcada estacionalidad solar. Esta zona presenta diferencias significativas "
                "entre la producción de verano e invierno, con ratios que pueden variar entre 3:1 "
                "y 5:1 según la latitud exacta. La irradiación global horizontal típica oscila entre "
                "1.400 y 1.900 kWh/m² anuales. Es fundamental dimensionar correctamente el sistema "
                "considerando tanto los picos de verano como las necesidades de invierno."
            )
            solar_source = "PVGIS TMY Data, European Commission JRC"
        else:
            solar_context = (
                "Tu ubicación se encuentra en latitudes altas, donde el recurso solar presenta "
                "una estacionalidad extrema. Durante el verano, los días largos compensan parcialmente "
                "el menor ángulo de incidencia solar, permitiendo producciones significativas. Sin "
                "embargo, los meses de invierno tienen producción muy limitada debido a la corta "
                "duración del día y los bajos ángulos solares. La irradiación global horizontal "
                "típica es inferior a 1.200 kWh/m² anuales. Se recomienda considerar almacenamiento "
                "o complementos energéticos para los meses de baja producción."
            )
            solar_source = "PVGIS High-Latitude Database, European Commission"
        
        insights.append({
            "title": "Recurso solar según tu latitud",
            "content": solar_context,
            "source": solar_source,
        })
        
        # Insight 2: Climate patterns affecting solar
        if annual_kwh > 6000:
            climate_context = (
                "El alto potencial de generación en tu ubicación indica un clima predominantemente "
                "soleado con pocas precipitaciones y baja nubosidad media. Las regiones con este "
                "perfil de producción típicamente experimentan menos de 60 días de lluvia al año "
                "y cuentan con más de 2.500 horas de sol anuales. La baja humedad relativa también "
                "favorece el rendimiento de los paneles, ya que reduce las pérdidas por condensación "
                "y suciedad. Es recomendable mantener un programa de limpieza periódica para "
                "maximizar el rendimiento en estos climas secos."
            )
        elif annual_kwh > 4000:
            climate_context = (
                "Tu potencial de generación sugiere un clima mixto con alternancia de períodos "
                "soleados y nublados. Estas condiciones son típicas de climas templados o "
                "mediterráneos, donde se registran entre 80 y 120 días de lluvia al año y "
                "aproximadamente 2.000-2.400 horas de sol anuales. La producción solar en estos "
                "climas se beneficia de las temperaturas moderadas, ya que los paneles fotovoltaicos "
                "pierden eficiencia con el calor excesivo. La lluvia ocasional ayuda a mantener "
                "los paneles limpios de forma natural."
            )
        else:
            climate_context = (
                "El potencial de generación moderado de tu ubicación refleja condiciones climáticas "
                "con nubosidad frecuente o alta latitud. Los climas con estas características "
                "suelen presentar más de 130 días de lluvia o cielos cubiertos al año, con menos "
                "de 1.800 horas de sol anuales. Aunque la producción total es menor, los sistemas "
                "solares siguen siendo viables gracias a la radiación difusa que penetra las nubes. "
                "Los paneles de última generación están optimizados para captar eficientemente "
                "esta luz difusa, mejorando el rendimiento en días nublados."
            )
        
        insights.append({
            "title": "Patrón climático y su impacto",
            "content": climate_context,
            "source": "Análisis basado en correlación PVGIS-TMY y datos climatológicos regionales",
        })
        
        return insights


# Singleton instance
ai_consultant = AIConsultant()

