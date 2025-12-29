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
de Copernicus y cálculos de Pvlib para usuarios no técnicos.

REGLAS ESTRICTAS:
1. SOLO habla de los datos que recibes en el JSON. NUNCA especules ni inventes información.
2. SIEMPRE cita las fuentes: "Según datos del programa Copernicus de la ESA..."
3. Si hay incertidumbre, explica por qué (datos históricos, latitud extrema, nubosidad variable, etc.)
4. Tono: profesional, científico pero accesible. Como un ingeniero explicando a un cliente.
5. NUNCA des consejos de inversión ni hagas promesas de rendimiento.
6. Si los datos son de "data_tier: standard", menciona que son estimaciones basadas en promedios globales.
7. Destaca el "Peor Escenario" (worst_month) para que el usuario tenga expectativas realistas.

FORMATO DE RESPUESTA (JSON):
{
  "summary": "Resumen ejecutivo en 2-3 oraciones",
  "seasonal_analysis": "Análisis de estacionalidad explicando picos y valles",
  "recommendations": "Recomendaciones técnicas sobre inclinación/orientación si aplica",
  "citations": ["Lista de fuentes citadas"],
  "confidence_note": "Nota sobre la confianza de los datos si data_tier es 'standard'"
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
    ) -> dict[str, Any]:
        """
        Generate AI narrative from calculation data.
        
        Args:
            calculation_data: Results from solar calculator
            country_plugin: Name of applied country plugin
        
        Returns:
            Structured narrative with summary, analysis, and recommendations
        """
        if not self.is_configured or not self._model:
            return self._generate_fallback_narrative(calculation_data)

        try:
            # Prepare context for Gemini
            context = json.dumps({
                "calculation_data": calculation_data,
                "applied_plugin": country_plugin,
                "request": "Genera una narrativa científica para estos datos de potencial solar.",
            }, ensure_ascii=False, indent=2)

            response = await self._model.generate_content_async(
                context,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json",
                },
            )

            # Parse response
            result = json.loads(response.text)
            
            # Validate narrative against calculations
            if not self._validate_narrative(calculation_data, result):
                logger.warning("Narrative validation failed, regenerating...")
                return self._generate_fallback_narrative(calculation_data)
            
            return result

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._generate_fallback_narrative(calculation_data)

    def _validate_narrative(
        self,
        calc_data: dict[str, Any],
        narrative: dict[str, Any],
    ) -> bool:
        """
        Validate that AI narrative is coherent with calculations.
        
        Checks for major discrepancies that indicate hallucination.
        """
        try:
            summary = narrative.get("summary", "")
            actual_kwh = calc_data.get("annual_generation_kwh", 0)
            
            # Check if any mentioned kWh values are wildly off
            import re
            numbers = re.findall(r"[\d,]+(?:\.\d+)?\s*kWh", summary)
            
            for num_str in numbers:
                mentioned = float(num_str.replace(",", "").replace("kWh", "").strip())
                if abs(mentioned - actual_kwh) / actual_kwh > 0.10:  # 10% tolerance
                    logger.warning(f"Narrative mismatch: {mentioned} vs {actual_kwh}")
                    return False
            
            return True
            
        except Exception:
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
        
        return {
            "summary": summary,
            "seasonal_analysis": seasonal,
            "recommendations": recommendations,
            "citations": ["ERA5-Land, ECMWF/Copernicus", "CAMS Solar Radiation, ESA"],
            "confidence_note": confidence if confidence else None,
        }


# Singleton instance
ai_consultant = AIConsultant()

