"use client";

interface LocationInsight {
  title: string;
  content: string;
  source: string;
}

interface AIInsightsProps {
  insights?: {
    summary?: string;
    seasonal_analysis?: string;
    location_insights?: LocationInsight[];
    recommendations?: string;
    confidence_note?: string;
    citations?: string[];
  };
  dataTier: string;
  confidenceScore: number;
  appliedPlugin?: string;
  savings?: {
    annual_savings: number;
    currency_symbol: string;
    co2_savings_kg: number;
  };
}

// Icons for different insight types
const insightIcons: Record<string, string> = {
  precipitación: "🌧️",
  lluvia: "🌧️",
  clima: "🌤️",
  climático: "🌤️",
  temperatura: "🌡️",
  sol: "☀️",
  solar: "☀️",
  radiación: "📡",
  latitud: "🌍",
  recurso: "⚡",
  energético: "🔋",
  geográfico: "🗺️",
  default: "📊",
};

function getInsightIcon(title: string): string {
  const lowerTitle = title.toLowerCase();
  for (const [key, icon] of Object.entries(insightIcons)) {
    if (lowerTitle.includes(key)) return icon;
  }
  return insightIcons.default;
}

export function AIInsights({
  insights,
  dataTier,
  confidenceScore,
  appliedPlugin,
  savings,
}: AIInsightsProps) {
  // Generate default insights if AI insights not available
  const displayInsights = insights || {
    summary:
      "Análisis completado. Consulta los gráficos para ver la distribución mensual de generación.",
    seasonal_analysis:
      "La generación solar varía según la estación del año. Los meses de verano presentan mayor radiación.",
    recommendations:
      "Mantén los paneles limpios y revisa periódicamente la orientación para maximizar la captación.",
    location_insights: [],
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          Consultor Solar IA
        </h3>
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-1 text-xs rounded-full ${
              dataTier === "engineering"
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
            }`}
          >
            {dataTier === "engineering" ? "🎯 Precisión Alta" : "📊 Estimación"}
          </span>
          <span className="text-xs text-gray-500">
            Confianza: {(confidenceScore * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6">
        <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
          {displayInsights.summary}
        </p>
      </div>

      {/* Seasonal Analysis */}
      {displayInsights.seasonal_analysis && (
        <div className="mb-6 p-4 bg-sky-50 dark:bg-sky-900/20 rounded-lg">
          <h4 className="font-semibold text-sky-800 dark:text-sky-300 mb-2">
            📅 Análisis Estacional
          </h4>
          <p className="text-gray-700 dark:text-gray-300">
            {displayInsights.seasonal_analysis}
          </p>
        </div>
      )}

      {/* Location Insights - NEW ENRICHED DATA */}
      {displayInsights.location_insights && displayInsights.location_insights.length > 0 && (
        <div className="mb-6 space-y-4">
          <h4 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <span className="text-xl">🌍</span>
            Datos Climáticos y Geográficos de tu Ubicación
          </h4>
          <div className="grid md:grid-cols-2 gap-4">
            {displayInsights.location_insights.map((insight, index) => (
              <div
                key={index}
                className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl flex-shrink-0">
                    {getInsightIcon(insight.title)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h5 className="font-semibold text-indigo-800 dark:text-indigo-300 mb-2">
                      {insight.title}
                    </h5>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                      {insight.content}
                    </p>
                    <p className="mt-2 text-xs text-indigo-600 dark:text-indigo-400 italic">
                      📚 {insight.source}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {displayInsights.recommendations && (
        <div className="mb-6 p-4 bg-solar-50 dark:bg-solar-900/20 rounded-lg">
          <h4 className="font-semibold text-solar-800 dark:text-solar-300 mb-2">
            💡 Recomendaciones
          </h4>
          <p className="text-gray-700 dark:text-gray-300">
            {displayInsights.recommendations}
          </p>
        </div>
      )}

      {/* Savings & CO2 */}
      {savings && (
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <h4 className="font-semibold text-green-800 dark:text-green-300 mb-1">
              💰 Ahorro Estimado
            </h4>
            <p className="text-2xl font-bold text-green-600">
              {savings.currency_symbol}
              {savings.annual_savings.toLocaleString()}
            </p>
            <p className="text-sm text-gray-500">al año</p>
          </div>
          <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
            <h4 className="font-semibold text-emerald-800 dark:text-emerald-300 mb-1">
              🌍 CO₂ Evitado
            </h4>
            <p className="text-2xl font-bold text-emerald-600">
              {savings.co2_savings_kg.toLocaleString()} kg
            </p>
            <p className="text-sm text-gray-500">al año</p>
          </div>
        </div>
      )}

      {/* Applied Plugin */}
      {appliedPlugin && (
        <div className="text-xs text-gray-500 border-t border-gray-200 dark:border-gray-700 pt-4">
          📋 Normativa aplicada: {appliedPlugin}
        </div>
      )}

      {/* Confidence Note */}
      {displayInsights.confidence_note && (
        <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            ⚠️ {displayInsights.confidence_note}
          </p>
        </div>
      )}

      {/* Data Sources */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500">
          {displayInsights.citations && displayInsights.citations.length > 0 ? (
            <>Fuentes: {displayInsights.citations.join(", ")}</>
          ) : (
            <>Fuentes: ERA5-Land (ECMWF), CAMS Solar Radiation (ESA/Copernicus), PVGIS TMY (JRC)</>
          )}
        </p>
      </div>
    </div>
  );
}

