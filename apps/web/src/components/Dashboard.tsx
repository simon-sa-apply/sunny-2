"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { Hero } from "./Hero";
import { LocationSearch } from "./LocationSearch";
import { SolarMap } from "./Map";
import { ParameterForm } from "./ParameterForm";
import { MonthlyChart } from "./MonthlyChart";
import { SolarClock } from "./SolarClock";
import { AIInsights } from "./AIInsights";
import { ProgressBar } from "./ProgressBar";
import { ImpactCard } from "./ImpactCard";
import { RoofPresets } from "./RoofPresets";
import { LanguageSelector } from "./LanguageSelector";

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
    location_insights?: Array<{
      title: string;
      content: string;
      source: string;
    }>;
    recommendations: string;
    confidence_note?: string;
    citations?: string[];
  };
  data_tier: string;
  confidence_score: number;
  applied_plugin?: string;
}

export function Dashboard() {
  const tResults = useTranslations("results");
  const tProgress = useTranslations("progress");
  const tErrors = useTranslations("errors");
  const tFooter = useTranslations("footer");
  const tForm = useTranslations("parameterForm");
  const tLocation = useTranslations("locationSearch");

  const [showCalculator, setShowCalculator] = useState(false);
  const [location, setLocation] = useState<{
    lat: number;
    lon: number;
    name?: string;
  } | null>(null);
  const [selectedTilt, setSelectedTilt] = useState<number>(30);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, message: "" });
  const [result, setResult] = useState<EstimateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const calculatorRef = useRef<HTMLDivElement>(null);

  const handleGetStarted = useCallback(() => {
    setShowCalculator(true);
    setTimeout(() => {
      calculatorRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  const handleLocationSelect = useCallback(
    (lat: number, lon: number, name?: string) => {
      setLocation({ lat, lon, name });
      setResult(null);
      setError(null);
    },
    []
  );

  const handleRoofPresetSelect = useCallback((tilt: number) => {
    if (tilt === -1) {
      return;
    }
    setSelectedTilt(tilt);
  }, []);

  const handleSubmit = async (data: {
    area_m2: number;
    tilt?: number;
    orientation?: string;
  }) => {
    if (!location) return;

    setIsLoading(true);
    setError(null);
    setProgress({ percent: 0, message: tProgress("connecting") });

    const requestBody = {
      lat: location.lat,
      lon: location.lon,
      area_m2: data.area_m2,
      tilt: data.tilt ?? selectedTilt,
      orientation: data.orientation === "auto" ? undefined : data.orientation,
    };

    try {
      setProgress({ percent: 20, message: `🛰️ ${tProgress("satellite")}` });

      const fastResponse = await fetch("/api/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...requestBody, include_ai_insights: false }),
      });

      setProgress({ percent: 70, message: `🧮 ${tProgress("calculating")}` });

      if (!fastResponse.ok) {
        throw new Error(tErrors("calculation"));
      }

      const fastResult = await fastResponse.json();
      setProgress({ percent: 85, message: `✨ ${tProgress("complete")}` });
      setResult(fastResult);

      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 300);

      setIsLoading(false);

      setProgress({ percent: 90, message: "🤖 AI analysis..." });
      
      fetch("/api/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...requestBody, include_ai_insights: true }),
      })
        .then((res) => res.json())
        .then((fullResult) => {
          if (fullResult.ai_insights) {
            setResult((prev) =>
              prev ? { ...prev, ai_insights: fullResult.ai_insights } : prev
            );
            setProgress({ percent: 100, message: `✨ ${tProgress("complete")}` });
          }
        })
        .catch((err) => {
          console.warn("Failed to load AI insights:", err);
        });

    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setIsLoading(false);
    }
  };

  const handleSolarClockUpdate = useCallback(
    (clockResult: { annual_kwh: number }) => {
      if (result) {
        console.log("Solar clock update:", clockResult);
      }
    },
    [result]
  );

  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      {/* Hero Section */}
      <AnimatePresence>
        {!showCalculator && <Hero onGetStarted={handleGetStarted} />}
      </AnimatePresence>

      {/* Calculator Section */}
      <AnimatePresence>
        {showCalculator && (
          <motion.div
            ref={calculatorRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {/* Header */}
            <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
              <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <button
                  onClick={() => setShowCalculator(false)}
                  className="flex items-center gap-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  sunny<span className="text-amber-500">-2</span>
                </h1>
                <LanguageSelector />
              </div>
            </header>

            <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
              {/* Step 1: Location Search */}
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl mx-auto mb-8 md:mb-12"
              >
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    {tLocation("title")}
                  </h2>
                </div>

                <LocationSearch onLocationSelect={handleLocationSelect} />

                {/* Map */}
                <div className="mt-6">
                  <SolarMap
                    onLocationSelect={handleLocationSelect}
                    selectedLocation={location}
                  />
                </div>

                {/* Location confirmation */}
                <AnimatePresence>
                  {location && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl flex items-center gap-3"
                    >
                      <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center text-white">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <div className="font-medium text-emerald-900 dark:text-emerald-100">
                          {location.name || tLocation("selected")}
                        </div>
                        <div className="text-sm text-emerald-700 dark:text-emerald-300">
                          {location.lat.toFixed(4)}°, {location.lon.toFixed(4)}°
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.section>

              {/* Step 2: Panel Configuration */}
              <AnimatePresence>
                {location && (
                  <motion.section
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="w-full"
                  >
                    <div className="bg-white dark:bg-slate-800 rounded-2xl md:rounded-3xl shadow-xl p-4 sm:p-6 lg:p-8 border border-slate-200 dark:border-slate-700">
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-3">
                        <span className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600">
                          ☀️
                        </span>
                        {tForm("title")}
                      </h2>

                      {/* Roof Presets */}
                      <div className="mb-8">
                        <RoofPresets
                          onSelect={handleRoofPresetSelect}
                          selectedTilt={selectedTilt}
                        />
                      </div>

                      {/* Parameter Form */}
                      <ParameterForm
                        onSubmit={handleSubmit}
                        isLoading={isLoading}
                        location={location}
                        initialTilt={selectedTilt}
                      />
                    </div>
                  </motion.section>
                )}
              </AnimatePresence>

              {/* Progress Bar */}
              <AnimatePresence>
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="max-w-2xl mx-auto mt-6 md:mt-8"
                  >
                    <ProgressBar percent={progress.percent} message={progress.message} />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="max-w-2xl mx-auto mt-6 md:mt-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4 sm:p-6"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-800 flex items-center justify-center text-red-600 dark:text-red-300">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-medium text-red-900 dark:text-red-100">{tErrors("title")}</h3>
                        <p className="text-red-700 dark:text-red-300">{error}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results Dashboard */}
              <AnimatePresence>
                {result && (
                  <motion.div
                    id="results"
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-10 md:mt-16 space-y-6 md:space-y-8"
                  >
                    {/* Main Result Header */}
                    <div className="text-center px-4">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", delay: 0.2 }}
                        className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-white text-4xl mb-4 shadow-xl shadow-amber-500/30"
                      >
                        ☀️
                      </motion.div>
                      <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
                        {result.annual_generation_kwh.toLocaleString()}
                        <span className="text-2xl font-normal text-slate-500 ml-2">
                          {tResults("title")}
                        </span>
                      </h2>
                      <p className="text-slate-600 dark:text-slate-400">
                        {tResults("subtitle")}
                      </p>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl md:rounded-2xl p-4 md:p-6 text-white"
                      >
                        <div className="text-sm opacity-80">{tResults("cards.annual")}</div>
                        <div className="text-3xl font-bold mt-1">
                          {result.annual_generation_kwh.toLocaleString()}
                        </div>
                        <div className="text-sm opacity-80">{tResults("title")}</div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="bg-white dark:bg-slate-800 rounded-xl md:rounded-2xl p-4 md:p-6 border border-slate-200 dark:border-slate-700"
                      >
                        <div className="text-xs md:text-sm text-slate-500">{tResults("cards.peak")}</div>
                        <div className="text-2xl md:text-3xl font-bold text-emerald-600 mt-1">
                          {result.peak_month.month}
                        </div>
                        <div className="text-sm text-slate-500">
                          {result.peak_month.kwh.toLocaleString()} kWh
                        </div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white dark:bg-slate-800 rounded-xl md:rounded-2xl p-4 md:p-6 border border-slate-200 dark:border-slate-700"
                      >
                        <div className="text-xs md:text-sm text-slate-500">{tResults("cards.worst")}</div>
                        <div className="text-2xl md:text-3xl font-bold text-blue-600 mt-1">
                          {result.worst_month.month}
                        </div>
                        <div className="text-sm text-slate-500">
                          {result.worst_month.kwh.toLocaleString()} kWh
                        </div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="bg-white dark:bg-slate-800 rounded-xl md:rounded-2xl p-4 md:p-6 border border-slate-200 dark:border-slate-700"
                      >
                        <div className="text-xs md:text-sm text-slate-500">{tResults("cards.efficiency")}</div>
                        <div className="text-2xl md:text-3xl font-bold text-purple-600 mt-1">
                          {(result.optimization.efficiency_vs_optimal * 100).toFixed(0)}%
                        </div>
                        <div className="text-sm text-slate-500">{tResults("cards.ofOptimal")}</div>
                      </motion.div>
                    </div>

                    {/* Charts Row: Monthly Chart (2/3) + Solar Clock (1/3) */}
                    <div className="grid lg:grid-cols-3 gap-4 md:gap-6">
                      <div className="lg:col-span-2 h-full">
                        <MonthlyChart data={result.monthly_breakdown} />
                      </div>
                      <div className="h-full flex">
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

                    {/* Impact Card - Full Width */}
                    {result.savings && (
                      <div>
                        <ImpactCard
                          annualKwh={result.annual_generation_kwh}
                          co2SavedKg={result.savings.co2_savings_kg}
                          currencySymbol={result.savings.currency_symbol}
                          annualSavings={result.savings.annual_savings}
                        />
                      </div>
                    )}

                    {/* AI Insights - Full Width */}
                    <div>
                      <AIInsights
                        insights={result.ai_insights}
                        dataTier={result.data_tier}
                        confidenceScore={result.confidence_score}
                        appliedPlugin={result.applied_plugin}
                        savings={result.savings}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </main>

            {/* Footer */}
            <footer className="border-t border-slate-200 dark:border-slate-700 mt-16">
              <div className="container mx-auto px-4 py-8 text-center text-slate-500">
                <p>
                  {tFooter("dataFrom")}{" "}
                  <span className="font-semibold text-sky-600">Copernicus CDSE (ESA)</span>{" "}
                  {tFooter("and")}{" "}
                  <span className="font-semibold text-purple-600">Gemini 2.0</span>
                </p>
              </div>
            </footer>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
