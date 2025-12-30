"use client";

import { useTranslations } from "next-intl";

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
  temperature: "🌡️",
  temperatura: "🌡️",
  sol: "☀️",
  sun: "☀️",
  solar: "☀️",
  radiación: "📡",
  radiation: "📡",
  latitud: "🌍",
  latitude: "🌍",
  recurso: "⚡",
  resource: "⚡",
  energético: "🔋",
  energy: "🔋",
  geográfico: "🗺️",
  geographic: "🗺️",
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
  const t = useTranslations("aiInsights");

  // Generate default insights if AI insights not available
  const displayInsights = insights || {
    summary: "",
    seasonal_analysis: "",
    recommendations: "",
    location_insights: [],
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl md:rounded-2xl p-4 md:p-6 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <h3 className="text-base md:text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-xl md:text-2xl">🤖</span>
          {t("title")}
        </h3>
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-1 text-[10px] md:text-xs rounded-full ${
              dataTier === "engineering"
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
            }`}
          >
            {dataTier === "engineering" ? `🎯 ${t("dataTier.engineering")}` : `📊 ${t("dataTier.standard")}`}
          </span>
          <span className="text-[10px] md:text-xs text-gray-500">
            {(confidenceScore * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Summary */}
      {displayInsights.summary && (
        <div className="mb-4 md:mb-6">
          <p className="text-gray-700 dark:text-gray-300 text-sm md:text-base leading-relaxed">
            {displayInsights.summary}
          </p>
        </div>
      )}

      {/* Seasonal Analysis */}
      {displayInsights.seasonal_analysis && (
        <div className="mb-4 md:mb-6 p-3 md:p-4 bg-sky-50 dark:bg-sky-900/20 rounded-lg">
          <h4 className="font-semibold text-sky-800 dark:text-sky-300 mb-1 md:mb-2 text-sm md:text-base">
            📅 {t("seasonal")}
          </h4>
          <p className="text-gray-700 dark:text-gray-300 text-xs md:text-sm">
            {displayInsights.seasonal_analysis}
          </p>
        </div>
      )}

      {/* Location Insights - ENRICHED DATA */}
      {displayInsights.location_insights && displayInsights.location_insights.length > 0 && (
        <div className="mb-4 md:mb-6 space-y-3 md:space-y-4">
          <h4 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 text-sm md:text-base">
            <span className="text-lg md:text-xl">🌍</span>
            {t("locationData")}
          </h4>
          <div className="grid md:grid-cols-2 gap-3 md:gap-4">
            {displayInsights.location_insights.map((insight, index) => (
              <div
                key={index}
                className="p-3 md:p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg md:rounded-xl border border-indigo-100 dark:border-indigo-800"
              >
                <div className="flex items-start gap-2 md:gap-3">
                  <span className="text-xl md:text-2xl flex-shrink-0">
                    {getInsightIcon(insight.title)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h5 className="font-semibold text-indigo-800 dark:text-indigo-300 mb-1 md:mb-2 text-sm md:text-base">
                      {insight.title}
                    </h5>
                    <p className="text-gray-700 dark:text-gray-300 text-xs md:text-sm leading-relaxed">
                      {insight.content}
                    </p>
                    <p className="mt-1.5 md:mt-2 text-[10px] md:text-xs text-indigo-600 dark:text-indigo-400 italic">
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
        <div className="mb-4 md:mb-6 p-3 md:p-4 bg-solar-50 dark:bg-solar-900/20 rounded-lg">
          <h4 className="font-semibold text-solar-800 dark:text-solar-300 mb-1 md:mb-2 text-sm md:text-base">
            💡 {t("recommendations")}
          </h4>
          <p className="text-gray-700 dark:text-gray-300 text-xs md:text-sm">
            {displayInsights.recommendations}
          </p>
        </div>
      )}

      {/* Savings & CO2 */}
      {savings && (
        <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6">
          <div className="p-3 md:p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <h4 className="font-semibold text-green-800 dark:text-green-300 mb-1 text-xs md:text-sm">
              💰 {t("savings")}
            </h4>
            <p className="text-lg md:text-2xl font-bold text-green-600">
              {savings.currency_symbol}
              {savings.annual_savings.toLocaleString()}
              <span className="text-xs md:text-lg font-normal ml-1">USD</span>
            </p>
            <p className="text-[10px] md:text-sm text-gray-500">{t("perYear")}</p>
          </div>
          <div className="p-3 md:p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
            <h4 className="font-semibold text-emerald-800 dark:text-emerald-300 mb-1 text-xs md:text-sm">
              🌍 CO₂
            </h4>
            <p className="text-lg md:text-2xl font-bold text-emerald-600">
              {savings.co2_savings_kg.toLocaleString()} kg
            </p>
            <p className="text-[10px] md:text-sm text-gray-500">{t("co2")}</p>
          </div>
        </div>
      )}

      {/* Applied Plugin */}
      {appliedPlugin && (
        <div className="text-[10px] md:text-xs text-gray-500 border-t border-gray-200 dark:border-gray-700 pt-3 md:pt-4">
          📋 {appliedPlugin}
        </div>
      )}

      {/* Confidence Note */}
      {displayInsights.confidence_note && (
        <div className="mt-3 md:mt-4 p-2 md:p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <p className="text-xs md:text-sm text-yellow-700 dark:text-yellow-300">
            ⚠️ {displayInsights.confidence_note}
          </p>
        </div>
      )}

      {/* Data Sources */}
      <div className="mt-3 md:mt-4 pt-3 md:pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-[10px] md:text-xs text-gray-500">
          {displayInsights.citations && displayInsights.citations.length > 0 ? (
            <>{displayInsights.citations.join(", ")}</>
          ) : (
            <>ERA5-Land, CAMS Solar, PVGIS</>
          )}
        </p>
      </div>
    </div>
  );
}
