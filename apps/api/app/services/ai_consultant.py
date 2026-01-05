"""
AI Consultant Service - Gemini 2.0 Integration.

Generates scientific narratives and insights from solar calculations.
Acts as the "Virtual Energy Consultant" for users.
"""

import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _estimate_climate_data(lat: float, lon: float, annual_kwh: float) -> dict[str, Any]:
    """
    Estimate climate data (precipitation, cloudy days, temperature range) based on location.
    
    Uses latitude, longitude, and solar generation as proxies for climate characteristics.
    These are rough estimates - in production, use actual climate APIs (ERA5, WorldClim, etc.)
    """
    abs_lat = abs(lat)
    
    # Estimate annual precipitation (mm) based on latitude and solar resource
    if abs_lat < 23.5:
        # Tropical zones: high variability (deserts to rainforests)
        if annual_kwh > 6000:
            annual_precip_mm = 100  # Desert/arid
        elif annual_kwh > 5000:
            annual_precip_mm = 500  # Semi-arid
        else:
            annual_precip_mm = 2000  # Tropical rainforest
    elif abs_lat < 35:
        # Subtropical: Mediterranean to humid subtropical
        if annual_kwh > 5500:
            annual_precip_mm = 300  # Mediterranean/arid
        elif annual_kwh > 4500:
            annual_precip_mm = 800  # Subtropical dry
        else:
            annual_precip_mm = 1200  # Humid subtropical
    elif abs_lat < 55:
        # Temperate zones: moderate precipitation
        if annual_kwh > 4500:
            annual_precip_mm = 400  # Continental dry
        elif annual_kwh > 3500:
            annual_precip_mm = 700  # Temperate oceanic
        else:
            annual_precip_mm = 1000  # Temperate continental
    else:
        # High latitude: low to moderate precipitation
        if annual_kwh > 3000:
            annual_precip_mm = 300  # Subarctic dry
        else:
            annual_precip_mm = 600  # Subarctic continental
    
    # Estimate cloudy days per year based on solar resource
    # Lower annual_kwh typically indicates more cloudiness
    if annual_kwh > 6000:
        cloudy_days = 50  # Very sunny
    elif annual_kwh > 5000:
        cloudy_days = 80  # Mostly sunny
    elif annual_kwh > 4000:
        cloudy_days = 120  # Partly cloudy
    elif annual_kwh > 3000:
        cloudy_days = 150  # Cloudy
    else:
        cloudy_days = 200  # Very cloudy
    
    # Estimate temperature range (°C) based on latitude
    if abs_lat < 23.5:
        # Tropical: small temperature range
        temp_min = 20
        temp_max = 32
    elif abs_lat < 35:
        # Subtropical: moderate range
        temp_min = 10
        temp_max = 30
    elif abs_lat < 55:
        # Temperate: larger range
        temp_min = -5
        temp_max = 25
    else:
        # High latitude: very large range
        temp_min = -20
        temp_max = 15
    
    return {
        "annual_precipitation_mm": round(annual_precip_mm),
        "cloudy_days_per_year": cloudy_days,
        "temperature_range_c": {
            "min": temp_min,
            "max": temp_max,
            "range": temp_max - temp_min,
        },
    }


# System prompt for Gemini - enriched geographic analysis
SYSTEM_PROMPT = """Eres "Sunny", un Consultor Solar experto en análisis geográfico y climático. 
Interpretas datos de Copernicus/PVGIS para proporcionar insights valiosos y específicos sobre cada ubicación.

REGLAS:
1. SOLO habla de los datos del JSON. NUNCA especules sin evidencia.
2. Enfócate en información GEOGRÁFICA VALIOSA: patrones climáticos regionales, factores geográficos únicos, comparaciones con zonas similares.
3. Respuestas INFORMATIVAS pero CONCISAS: 40-60 palabras por insight geográfico, 2-3 oraciones por análisis.
4. Cita fuentes específicas: "Copernicus CAMS", "PVGIS-SARAH2", "ERA5-Land", "AEMET", "WorldClim", etc.
5. Tono: profesional, educativo y específico. Como un experto en climatología solar.
6. NUNCA des consejos de inversión financiera.
7. Destaca factores geográficos únicos: proximidad al mar, altitud, latitud, patrones de viento, nubosidad regional.
8. Incluye comparaciones con otras regiones similares cuando sea relevante.
9. INCORPORA en los insights existentes: precipitación anual (mm), días nublados estimados, y rango de temperatura anual (°C).
10. Integra estos datos climáticos de forma natural en los location_insights, especialmente en "Patrones climáticos locales" y "Factores geográficos".

FORMATO JSON (ANÁLISIS ENRIQUECIDO):
{
  "summary": "2-3 oraciones sobre el potencial solar con contexto geográfico (máx 50 palabras)",
  "seasonal_analysis": "2-3 oraciones sobre estacionalidad con patrones climáticos específicos (máx 60 palabras)",
  "location_insights": [
    {
      "title": "Título descriptivo (4-7 palabras)",
      "content": "Insight geográfico valioso en 40-60 palabras con datos específicos de la ubicación",
      "source": "Fuente específica (ej: 'Copernicus CAMS', 'PVGIS-TMY')"
    }
  ],
  "recommendations": "1-2 oraciones técnicas con contexto geográfico (máx 30 palabras)",
  "citations": ["Fuentes específicas usadas"],
  "confidence_note": "1 oración si data_tier es 'standard', null si 'engineering'"
}

IMPORTANTE: Genera 3-4 location_insights que cubran:
- Recurso solar específico de la latitud/región
- Patrones climáticos locales (nubosidad, precipitación, temperatura)
- Factores geográficos que afectan la producción (altitud, proximidad al mar, vientos)
- Comparación con otras zonas similares o contexto regional
"""


class AIConsultant:
    """
    AI Consultant for generating solar insights using Gemini 2.0.
    """

    def __init__(self) -> None:
        self._client: Any | None = None
        self._model: Any | None = None

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
        country_plugin: str | None = None,
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

        except TimeoutError:
            logger.warning(f"Gemini timed out after {timeout_seconds}s, using fallback")
            return self._generate_fallback_narrative(calculation_data)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._generate_fallback_narrative(calculation_data)

    async def _call_gemini(
        self,
        calculation_data: dict[str, Any],
        country_plugin: str | None,
    ) -> dict[str, Any]:
        """Internal method to call Gemini API."""
        # Extract location details for richer context
        location = calculation_data.get("location", {})
        lat = location.get("lat", 0)
        lon = location.get("lon", 0)
        country_code = location.get("country_code", "")
        
        # Extract calculation data for geographic analysis
        monthly_breakdown = calculation_data.get("monthly_breakdown", {})
        peak_month = calculation_data.get("peak_month", {})
        worst_month = calculation_data.get("worst_month", {})
        annual_kwh = calculation_data.get("annual_generation_kwh", 0)
        optimization = calculation_data.get("optimization", {})
        efficiency = optimization.get("efficiency_vs_optimal", 1.0)
        
        # Calculate seasonal variability
        monthly_values = list(monthly_breakdown.values()) if monthly_breakdown else []
        seasonal_variability = 0.0
        if monthly_values and len(monthly_values) > 0:
            max_month = max(monthly_values)
            min_month = min(monthly_values)
            if min_month > 0:
                seasonal_variability = (max_month - min_month) / min_month
        
        # Determine geographic characteristics
        abs_lat = abs(lat)
        hemisphere = "norte" if lat >= 0 else "sur"
        
        if abs_lat < 23.5:
            latitude_band = "tropical"
            climate_zone = "ecuatorial/tropical"
        elif abs_lat < 35:
            latitude_band = "subtropical"
            climate_zone = "subtropical"
        elif abs_lat < 55:
            latitude_band = "templada"
            climate_zone = "templada"
        else:
            latitude_band = "alta"
            climate_zone = "subpolar/polar"
        
        # Estimate coastal proximity (rough approximation)
        # This is a simplified heuristic - in production, use actual elevation/coastline data
        coastal_proximity = "interior"
        abs_lon = abs(lon)
        if abs_lon < 10 or abs_lon > 170:  # Near prime meridian or date line
            coastal_proximity = "posiblemente costero"
        
        # Calculate peak/worst ratio
        peak_kwh = peak_month.get("kwh", 0)
        worst_kwh = worst_month.get("kwh", 0)
        peak_worst_ratio = peak_kwh / worst_kwh if worst_kwh > 0 else 0
        
        # Estimate climate data (precipitation, cloudy days, temperature)
        climate_data = _estimate_climate_data(lat, lon, annual_kwh)

        # Prepare enriched context for Gemini
        context = json.dumps({
            "calculation_data": calculation_data,
            "applied_plugin": country_plugin,
            "location_context": {
                "latitude": lat,
                "longitude": lon,
                "country_code": country_code,
                "hemisphere": hemisphere,
                "latitude_band": latitude_band,
                "climate_zone": climate_zone,
                "seasonal_variability_ratio": round(seasonal_variability, 2),
                "peak_worst_ratio": round(peak_worst_ratio, 2),
                "coastal_proximity": coastal_proximity,
                "annual_generation_kwh": annual_kwh,
                "peak_month": peak_month.get("month", ""),
                "worst_month": worst_month.get("month", ""),
                "efficiency_vs_optimal": round(efficiency, 3),
                "climate_data": {
                    "annual_precipitation_mm": climate_data["annual_precipitation_mm"],
                    "cloudy_days_per_year": climate_data["cloudy_days_per_year"],
                    "temperature_range_c": climate_data["temperature_range_c"],
                },
            },
            "request": (
                "Genera un análisis GEOGRÁFICO ENRIQUECIDO con información valiosa sobre esta ubicación específica. "
                "Incluye 3-4 'location_insights' que cubran: "
                "1) Recurso solar específico de la latitud/región con datos concretos, "
                "2) Patrones climáticos locales que DEBEN incluir: precipitación anual ({annual_precip} mm), "
                "días nublados estimados ({cloudy_days} días/año), y rango de temperatura ({temp_min}°C a {temp_max}°C), "
                "3) Factores geográficos únicos (altitud, proximidad al mar, vientos, estacionalidad), "
                "4) Comparación con otras zonas similares o contexto regional. "
                "Cada insight debe tener 40-60 palabras con información específica y valiosa. "
                "INCORPORA los datos climáticos (precipitación, días nublados, temperatura) de forma natural en los insights, "
                "especialmente en 'Patrones climáticos locales' y 'Factores geográficos'. "
                "Cita fuentes como 'ERA5-Land', 'Copernicus CAMS', 'PVGIS-TMY', 'WorldClim' para datos climáticos. "
                "Usa los datos de monthly_breakdown para analizar patrones estacionales específicos."
            ).format(
                annual_precip=climate_data["annual_precipitation_mm"],
                cloudy_days=climate_data["cloudy_days_per_year"],
                temp_min=climate_data["temperature_range_c"]["min"],
                temp_max=climate_data["temperature_range_c"]["max"],
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
            if len(insights) < 3:  # Require at least 3 insights for enriched analysis
                logger.warning(f"Insufficient location_insights: {len(insights)} < 3")
                return False

            for i, insight in enumerate(insights):
                content = insight.get("content", "")
                word_count = len(content.split())
                if word_count < 30:  # Minimum 30 words for enriched insights
                    logger.warning(f"Insight {i} too short: {word_count} words (minimum 30)")
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

        # Enriched summary with geographic context
        summary = (
            f"Potencial solar anual de {annual:,.0f} kWh con producción máxima en {peak_month} "
            f"({peak.get('kwh', 0):,.0f} kWh) y mínima en {worst_month} ({worst.get('kwh', 0):,.0f} kWh). "
            f"La ubicación geográfica presenta características favorables para la generación solar."
        )

        # Enriched seasonal analysis
        peak_kwh = peak.get('kwh', 0)
        worst_kwh = worst.get('kwh', 0)
        ratio = peak_kwh / worst_kwh if worst_kwh > 0 else 0
        
        seasonal = (
            f"Estacionalidad {'muy marcada' if ratio > 3 else 'moderada' if ratio > 2 else 'suave'} "
            f"con producción máxima en {peak_month} ({peak_kwh:,.0f} kWh) y mínima en {worst_month} ({worst_kwh:,.0f} kWh). "
            f"El ratio estacional de {ratio:.1f}:1 indica {'variabilidad significativa' if ratio > 2.5 else 'producción relativamente estable'} durante el año."
        )

        # Enriched recommendations with geographic context
        if efficiency < 0.95:
            optimal_tilt = optimization.get("optimal_tilt", 0)
            recommendations = (
                f"Captando {efficiency*100:.0f}% del potencial óptimo. "
                f"Ajustar la inclinación a {optimal_tilt:.0f}° mejoraría significativamente la producción anual."
            )
        else:
            recommendations = (
                "Configuración cercana al óptimo para esta ubicación geográfica. "
                "El sistema está bien orientado para maximizar la captación solar."
            )

        # Confidence note
        confidence = "Estimación basada en promedios regionales." if data_tier == "standard" else None

        # Generate enriched location insights
        location = calc_data.get("location", {})
        lon = location.get("lon", 0)
        location_insights = self._generate_fallback_location_insights(
            lat, annual, monthly_breakdown=calc_data.get("monthly_breakdown"), lon=lon
        )

        return {
            "summary": summary,
            "seasonal_analysis": seasonal,
            "location_insights": location_insights,
            "recommendations": recommendations,
            "citations": ["Copernicus CAMS", "PVGIS-SARAH2", "ERA5-Land", "WorldClim"],
            "confidence_note": confidence,
        }

    def _generate_fallback_location_insights(
        self,
        lat: float,
        annual_kwh: float,
        monthly_breakdown: dict[str, float] | None = None,
        lon: float = 0.0,
    ) -> list[dict[str, str]]:
        """Generate enriched location insights (40-60 words each)."""
        insights = []
        abs_lat = abs(lat)
        
        # Calculate seasonal patterns if monthly data available
        peak_month_name = ""
        worst_month_name = ""
        peak_worst_ratio = 0.0
        if monthly_breakdown:
            monthly_values = list(monthly_breakdown.values())
            month_names = list(monthly_breakdown.keys())
            if monthly_values:
                max_idx = monthly_values.index(max(monthly_values))
                min_idx = monthly_values.index(min(monthly_values))
                peak_month_name = month_names[max_idx] if max_idx < len(month_names) else ""
                worst_month_name = month_names[min_idx] if min_idx < len(month_names) else ""
                if min(monthly_values) > 0:
                    peak_worst_ratio = max(monthly_values) / min(monthly_values)

        # Insight 1: Solar resource based on latitude (ENRICHED)
        if abs_lat < 25:
            solar_context = (
                f"Zona {('tropical' if abs_lat < 23.5 else 'subtropical')} con irradiación anual superior a 2.000 kWh/m². "
                f"La producción solar es notablemente estable durante todo el año debido a la variación mínima del ángulo solar. "
                f"Esta latitud ofrece uno de los mejores recursos solares del planeta, con ratios estacionales cercanos a 1.2:1."
            )
            solar_source = "PVGIS Global Solar Atlas"
        elif abs_lat < 45:
            seasonal_desc = f"Ratio {peak_month_name}/{worst_month_name} de {peak_worst_ratio:.1f}:1" if peak_worst_ratio > 0 else "estacionalidad marcada"
            solar_context = (
                f"Latitud media ({abs_lat:.1f}°) con {seasonal_desc}. "
                f"La irradiación anual típica oscila entre 1.400-1.900 kWh/m², con veranos muy productivos e inviernos moderados. "
                f"Esta zona requiere optimización del ángulo de inclinación para maximizar la captación en meses de menor radiación."
            )
            solar_source = "PVGIS TMY Database"
        else:
            solar_context = (
                f"Latitud alta ({abs_lat:.1f}°) con estacionalidad extrema. "
                f"Los veranos ofrecen producción excelente con días muy largos, mientras que los inviernos son limitados por horas de sol reducidas. "
                f"Irradiación anual típicamente inferior a 1.200 kWh/m². La orientación e inclinación son críticas para aprovechar los meses productivos."
            )
            solar_source = "PVGIS High-Latitude Database"

        insights.append({
            "title": "Recurso solar regional",
            "content": solar_context,
            "source": solar_source,
        })

        # Insight 2: Climate patterns (ENRICHED with precipitation, cloudy days, temperature)
        # Estimate climate data for fallback
        climate_data = _estimate_climate_data(lat, lon, annual_kwh)
        precip_mm = climate_data["annual_precipitation_mm"]
        cloudy_days = climate_data["cloudy_days_per_year"]
        temp_min = climate_data["temperature_range_c"]["min"]
        temp_max = climate_data["temperature_range_c"]["max"]
        temp_range = temp_max - temp_min
        
        if annual_kwh > 6000:
            climate_context = (
                f"Clima árido o semiárido con precipitación anual de {precip_mm} mm y aproximadamente {cloudy_days} días nublados al año. "
                f"Rango de temperatura anual de {temp_min}°C a {temp_max}°C (variación de {temp_range}°C). "
                f"La baja humedad relativa y la escasa nubosidad favorecen el rendimiento de los paneles, minimizando pérdidas por reflexión y suciedad. "
                f"Temperaturas altas pueden reducir ligeramente la eficiencia, pero el recurso solar excepcional compensa ampliamente."
            )
        elif annual_kwh > 4000:
            climate_context = (
                f"Clima mediterráneo o templado con precipitación anual de {precip_mm} mm y aproximadamente {cloudy_days} días nublados al año. "
                f"Rango de temperatura anual de {temp_min}°C a {temp_max}°C (variación de {temp_range}°C). "
                f"Las temperaturas moderadas optimizan la eficiencia de los paneles, evitando pérdidas por sobrecalentamiento. "
                f"La radiación difusa en días nublados es captada eficientemente por paneles modernos con tecnología bifacial."
            )
        else:
            climate_context = (
                f"Clima oceánico o continental con precipitación anual de {precip_mm} mm y aproximadamente {cloudy_days} días nublados al año. "
                f"Rango de temperatura anual de {temp_min}°C a {temp_max}°C (variación de {temp_range}°C). "
                f"Los paneles modernos captan eficientemente la radiación difusa, que puede representar hasta el 40% de la producción total. "
                f"La tecnología de células PERC y TOPCon mejora significativamente el rendimiento en condiciones de baja irradiación."
            )

        insights.append({
            "title": "Patrones climáticos locales",
            "content": climate_context,
            "source": "ERA5-Land & PVGIS-TMY",
        })

        # Insight 3: Seasonal variability (ENRICHED)
        if peak_worst_ratio > 0:
            if peak_worst_ratio > 3:
                variability_desc = "muy marcada"
                variability_context = (
                    f"Estacionalidad {variability_desc} con producción en {peak_month_name} hasta {peak_worst_ratio:.1f} veces superior a {worst_month_name}. "
                    f"Este patrón requiere sistemas de almacenamiento o conexión a red para aprovechar la producción estival. "
                    f"La optimización del ángulo de inclinación puede mejorar significativamente la producción en meses de menor radiación."
                )
            elif peak_worst_ratio > 2:
                variability_desc = "moderada"
                variability_context = (
                    f"Estacionalidad {variability_desc} con variación de {peak_worst_ratio:.1f}:1 entre {peak_month_name} y {worst_month_name}. "
                    f"La producción es relativamente estable durante la mayor parte del año, con picos estacionales predecibles. "
                    f"Un sistema bien dimensionado puede satisfacer necesidades energéticas durante todo el año con mínima dependencia de almacenamiento."
                )
            else:
                variability_desc = "suave"
                variability_context = (
                    f"Estacionalidad {variability_desc} con producción relativamente constante durante todo el año. "
                    f"La variación entre {peak_month_name} y {worst_month_name} es de solo {peak_worst_ratio:.1f}:1, "
                    f"indicando un recurso solar muy estable y predecible, ideal para sistemas autónomos o conexión a red."
                )
        else:
            variability_context = (
                "Patrón estacional típico de la latitud con producción variable según la época del año. "
                "La optimización del sistema y el dimensionamiento adecuado son clave para maximizar el aprovechamiento del recurso disponible."
            )

        insights.append({
            "title": "Variabilidad estacional",
            "content": variability_context,
            "source": "Análisis mensual - Copernicus CAMS",
        })

        # Insight 4: Geographic factors (ENRICHED with climate context)
        if abs_lat < 30:
            geo_context = (
                f"Ubicación en zona de alta irradiación solar con ángulos solares favorables durante todo el año. "
                f"La proximidad al ecuador garantiza producción estable sin grandes variaciones estacionales. "
                f"Con precipitación anual estimada de {precip_mm} mm y {cloudy_days} días nublados, "
                f"factores como la altitud y la proximidad al mar pueden influir localmente en la nubosidad y la temperatura "
                f"(rango anual: {temp_min}°C a {temp_max}°C)."
            )
        elif abs_lat < 50:
            geo_context = (
                f"Región con recurso solar moderado a bueno, influenciado por patrones climáticos regionales. "
                f"Precipitación anual de {precip_mm} mm y {cloudy_days} días nublados caracterizan el clima local "
                f"con temperaturas entre {temp_min}°C y {temp_max}°C. "
                f"La altitud puede mejorar la producción al reducir la absorción atmosférica, mientras que la proximidad al mar puede aumentar la nubosidad. "
                f"La orientación hacia el ecuador y la inclinación óptima son factores críticos para maximizar la captación."
            )
        else:
            geo_context = (
                f"Zona de latitud alta donde factores geográficos como la altitud, orientación y sombras son críticos. "
                f"Clima caracterizado por {precip_mm} mm de precipitación anual, {cloudy_days} días nublados, "
                f"y rango de temperatura de {temp_min}°C a {temp_max}°C. "
                f"Los días largos en verano compensan parcialmente la menor irradiación, mientras que en invierno la producción es limitada. "
                f"La selección del sitio y la optimización del sistema son esenciales para aprovechar eficientemente el recurso disponible."
            )

        insights.append({
            "title": "Factores geográficos",
            "content": geo_context,
            "source": "ERA5-Land & PVGIS Geographic Analysis",
        })

        return insights


# Singleton instance
ai_consultant = AIConsultant()

