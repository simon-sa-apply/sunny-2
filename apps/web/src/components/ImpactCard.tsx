"use client";

import { motion } from "framer-motion";

interface ImpactCardProps {
  annualKwh: number;
  co2SavedKg?: number;
  currencySymbol?: string;
  annualSavings?: number;
}

// Impact equivalences for storytelling
const getEquivalences = (kwh: number) => {
  return [
    {
      icon: "🚗",
      value: Math.round(kwh / 15),
      unit: "cargas",
      label: "de auto eléctrico",
      description: "Cargas completas de un Tesla Model 3",
    },
    {
      icon: "📱",
      value: Math.round(kwh * 1000 / 10),
      unit: "",
      label: "celulares cargados",
      description: "Cada carga consume ~10 Wh",
    },
    {
      icon: "🌳",
      value: Math.round(kwh * 0.4 / 20),
      unit: "",
      label: "árboles equivalentes",
      description: "Absorción de CO₂ anual",
    },
    {
      icon: "💡",
      value: Math.round(kwh / 10 / 365),
      unit: "h/día",
      label: "de iluminación LED",
      description: "Con bombillas de 10W",
    },
  ];
};

export function ImpactCard({
  annualKwh,
  co2SavedKg,
  currencySymbol = "$",
  annualSavings,
}: ImpactCardProps) {
  const equivalences = getEquivalences(annualKwh);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl p-6 text-white overflow-hidden relative"
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
        <div className="flex items-center gap-2 mb-6">
          <span className="text-2xl">🌍</span>
          <h3 className="font-semibold text-lg">Tu impacto ambiental</h3>
        </div>

        {/* Main stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {co2SavedKg && (
            <div className="bg-white/20 backdrop-blur rounded-2xl p-4">
              <div className="text-3xl font-bold">
                {co2SavedKg.toLocaleString()}
                <span className="text-lg font-normal ml-1">kg</span>
              </div>
              <div className="text-sm text-white/80">CO₂ evitado/año</div>
            </div>
          )}
          {annualSavings && (
            <div className="bg-white/20 backdrop-blur rounded-2xl p-4">
              <div className="text-3xl font-bold">
                {currencySymbol}
                {annualSavings.toLocaleString()}
              </div>
              <div className="text-sm text-white/80">Ahorro/año</div>
            </div>
          )}
        </div>

        {/* Equivalences */}
        <div className="space-y-3">
          <div className="text-sm font-medium text-white/80 mb-2">
            Esto equivale a:
          </div>
          <div className="grid grid-cols-2 gap-2">
            {equivalences.map((eq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-2 bg-white/10 rounded-xl px-3 py-2"
              >
                <span className="text-xl">{eq.icon}</span>
                <div>
                  <div className="font-semibold text-sm">
                    {eq.value.toLocaleString()}{" "}
                    <span className="font-normal text-white/70">{eq.unit}</span>
                  </div>
                  <div className="text-xs text-white/60">{eq.label}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 10 year projection */}
        <div className="mt-6 pt-4 border-t border-white/20">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-white/80">En 10 años generarás</div>
              <div className="text-2xl font-bold">
                {(annualKwh * 10).toLocaleString()} kWh
              </div>
            </div>
            {annualSavings && (
              <div className="text-right">
                <div className="text-sm text-white/80">Ahorrarás</div>
                <div className="text-2xl font-bold">
                  {currencySymbol}
                  {(annualSavings * 10).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

