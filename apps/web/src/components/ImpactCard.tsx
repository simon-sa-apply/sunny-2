"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";

interface ImpactCardProps {
  annualKwh: number;
  co2SavedKg?: number;
  currencySymbol?: string;
  annualSavings?: number;
}

export function ImpactCard({
  annualKwh,
  co2SavedKg,
  currencySymbol = "$",
  annualSavings,
}: ImpactCardProps) {
  const t = useTranslations("impact");

  // Impact equivalences for storytelling
  const equivalences = [
    {
      icon: "🚗",
      value: Math.round(annualKwh / 15),
      label: t("equivalences.cars"),
    },
    {
      icon: "🌳",
      value: Math.round(annualKwh * 0.4 / 20),
      label: t("equivalences.trees"),
    },
    {
      icon: "📱",
      value: Math.round(annualKwh * 1000 / 10),
      label: t("equivalences.phones"),
    },
    {
      icon: "🎬",
      value: Math.round(annualKwh / 0.15), // TV grande ~150W = 0.15 kWh/hora
      label: t("equivalences.netflix"),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl md:rounded-3xl p-4 md:p-6 text-white overflow-hidden relative"
    >
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          <pattern id="dots" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="currentColor" />
          </pattern>
          <rect x="0" y="0" width="100" height="100" fill="url(#dots)" />
        </svg>
      </div>

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4 md:mb-6">
          <span className="text-xl md:text-2xl">🌍</span>
          <h3 className="font-semibold text-base md:text-lg">{t("title")}</h3>
        </div>

        {/* Main stats */}
        <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6">
          {co2SavedKg && (
            <div className="bg-white/20 backdrop-blur rounded-xl md:rounded-2xl p-3 md:p-4">
              <div className="text-xl md:text-3xl font-bold">
                {co2SavedKg.toLocaleString()}
                <span className="text-sm md:text-lg font-normal ml-1">kg</span>
              </div>
              <div className="text-xs md:text-sm text-white/80">{t("co2")}</div>
            </div>
          )}
          {annualSavings && (
            <div className="bg-white/20 backdrop-blur rounded-xl md:rounded-2xl p-3 md:p-4">
              <div className="text-xl md:text-3xl font-bold">
                {currencySymbol}
                {annualSavings.toLocaleString()}
                <span className="text-sm md:text-lg font-normal ml-1">USD</span>
              </div>
              <div className="text-xs md:text-sm text-white/80">{t("savings")}</div>
            </div>
          )}
        </div>

        {/* Equivalences */}
        <div className="space-y-2 md:space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {equivalences.map((eq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-2 bg-white/10 rounded-lg md:rounded-xl px-2 md:px-3 py-1.5 md:py-2"
              >
                <span className="text-lg md:text-xl">{eq.icon}</span>
                <div>
                  <div className="font-semibold text-xs md:text-sm">
                    {eq.value.toLocaleString()}
                  </div>
                  <div className="text-[10px] md:text-xs text-white/60 line-clamp-1">{eq.label}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 10 year projection */}
        <div className="mt-4 md:mt-6 pt-3 md:pt-4 border-t border-white/20">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs md:text-sm text-white/80">{t("timeline.title")}</div>
              <div className="text-lg md:text-2xl font-bold">
                {(annualKwh * 10).toLocaleString()} kWh
              </div>
            </div>
            {annualSavings && (
              <div className="text-right">
                <div className="text-xs md:text-sm text-white/80">{t("timeline.savings")}</div>
                <div className="text-lg md:text-2xl font-bold">
                  {currencySymbol}
                  {(annualSavings * 10).toLocaleString()}
                  <span className="text-xs md:text-base font-normal ml-1">USD</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
