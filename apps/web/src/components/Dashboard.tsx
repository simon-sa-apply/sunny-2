"use client";

import { useState, useCallback } from "react";
import { SolarMap } from "./Map";
import { ParameterForm } from "./ParameterForm";
import { MonthlyChart } from "./MonthlyChart";
import { SolarClock } from "./SolarClock";
import { AIInsights } from "./AIInsights";
import { ProgressBar } from "./ProgressBar";

interface EstimateResult {
  annual_generation_kwh: number;
  monthly_breakdown: Record<string, number>;
  peak_month: { month: string; kwh: number };
  worst_month: { month: string; kwh: number };
  optimization: {
    current_tilt: number;
    current_orientation: number;
    optimal_tilt: number;
    optimal_orientation: number;
    efficiency_vs_optimal: number;
    optimal_annual_kwh: number;
  };
  savings?: {
    annual_savings: number;
    currency_symbol: string;
    co2_savings_kg: number;
  };
  ai_insights?: {
    summary: string;
    seasonal_analysis: string;
    recommendations: string;
  };
  data_tier: string;
  confidence_score: number;
  applied_plugin?: string;
}

export function Dashboard() {
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, message: "" });
  const [result, setResult] = useState<EstimateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleLocationSelect = useCallback((lat: number, lon: number) => {
    setLocation({ lat, lon });
    setResult(null);
    setError(null);
  }, []);

  const handleSubmit = async (data: {
    area_m2: number;
    tilt?: number;
    orientation?: string;
  }) => {
    if (!location) return;

    setIsLoading(true);
    setError(null);
    setProgress({ percent: 0, message: "Conectando..." });

    try {
      // Simulate progress updates
      setProgress({ percent: 20, message: "Conectando con satélite..." });
      await new Promise((r) => setTimeout(r, 500));

      setProgress({ percent: 40, message: "Descargando datos de radiación..." });

      const response = await fetch("/api/v1/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: location.lat,
          lon: location.lon,
          area_m2: data.area_m2,
          tilt: data.tilt,
          orientation: data.orientation === "auto" ? undefined : data.orientation,
        }),
      });

      setProgress({ percent: 80, message: "Generando análisis..." });

      if (!response.ok) {
        throw new Error("Error al calcular estimación");
      }

      const result = await response.json();
      setProgress({ percent: 100, message: "¡Completado!" });
      setResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSolarClockUpdate = useCallback(
    (clockResult: { annual_kwh: number }) => {
      // Update the chart if we have a result
      if (result) {
        // In a real app, we'd update the monthly breakdown too
        console.log("Solar clock update:", clockResult);
      }
    },
    [result]
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-solar-50 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            sunny<span className="text-solar-500">-2</span>
          </h1>
          <span className="text-sm text-gray-500">
            Diagnóstico Solar de Alta Precisión
          </span>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Input Section */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              1. Selecciona tu ubicación
            </h2>
            <SolarMap
              onLocationSelect={handleLocationSelect}
              selectedLocation={location}
            />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              2. Configura tus paneles
            </h2>
            <ParameterForm
              onSubmit={handleSubmit}
              isLoading={isLoading}
              location={location}
            />
          </div>
        </div>

        {/* Progress Bar */}
        {isLoading && (
          <ProgressBar percent={progress.percent} message={progress.message} />
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-8">
            <p className="text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Results Dashboard */}
        {result && (
          <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Generación Anual
                </p>
                <p className="text-3xl font-bold text-solar-600">
                  {result.annual_generation_kwh.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">kWh/año</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Mejor Mes
                </p>
                <p className="text-3xl font-bold text-green-600">
                  {result.peak_month.month}
                </p>
                <p className="text-sm text-gray-500">
                  {result.peak_month.kwh.toLocaleString()} kWh
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Peor Escenario
                </p>
                <p className="text-3xl font-bold text-blue-600">
                  {result.worst_month.month}
                </p>
                <p className="text-sm text-gray-500">
                  {result.worst_month.kwh.toLocaleString()} kWh
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Eficiencia
                </p>
                <p className="text-3xl font-bold text-purple-600">
                  {(result.optimization.efficiency_vs_optimal * 100).toFixed(0)}%
                </p>
                <p className="text-sm text-gray-500">del óptimo</p>
              </div>
            </div>

            {/* Charts and Clock */}
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <MonthlyChart data={result.monthly_breakdown} />
              </div>
              <div>
                <SolarClock
                  interpolationModel={{
                    tilts: Array.from({ length: 19 }, (_, i) => i * 5),
                    orientations: Array.from({ length: 24 }, (_, i) => i * 15),
                    annual_values: Array(19).fill(
                      Array(24).fill(result.annual_generation_kwh)
                    ),
                    optimal_tilt: result.optimization.optimal_tilt,
                    optimal_orientation: result.optimization.optimal_orientation,
                    optimal_annual_kwh: result.optimization.optimal_annual_kwh,
                  }}
                  onUpdate={handleSolarClockUpdate}
                  initialTilt={result.optimization.current_tilt}
                  initialOrientation={result.optimization.current_orientation}
                />
              </div>
            </div>

            {/* AI Insights */}
            <AIInsights
              insights={result.ai_insights}
              dataTier={result.data_tier}
              confidenceScore={result.confidence_score}
              appliedPlugin={result.applied_plugin}
              savings={result.savings}
            />
          </div>
        )}
      </main>

      <footer className="border-t border-gray-200 dark:border-gray-700 mt-16">
        <div className="container mx-auto px-4 py-8 text-center text-gray-500">
          <p>
            Powered by{" "}
            <span className="font-semibold text-sky-600">Copernicus CDSE</span> &{" "}
            <span className="font-semibold text-purple-600">Gemini 2.0</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

