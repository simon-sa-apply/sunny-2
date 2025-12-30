"use client";

import { motion } from "framer-motion";

interface RoofPresetsProps {
  onSelect: (tilt: number, name: string) => void;
  selectedTilt?: number;
}

const ROOF_PRESETS = [
  {
    id: "flat",
    name: "Techo plano",
    tilt: 10,
    icon: "🏢",
    description: "Edificios, terrazas",
    illustration: (
      <svg viewBox="0 0 100 60" className="w-full h-full">
        <rect x="10" y="30" width="80" height="25" fill="currentColor" className="text-slate-300 dark:text-slate-600" />
        <line x1="10" y1="30" x2="90" y2="28" stroke="currentColor" strokeWidth="3" className="text-amber-500" />
        <circle cx="85" cy="15" r="8" fill="currentColor" className="text-amber-400" />
        <path d="M85 5 L85 25 M75 15 L95 15 M78 8 L92 22 M78 22 L92 8" stroke="currentColor" strokeWidth="1.5" className="text-amber-300" />
      </svg>
    ),
  },
  {
    id: "moderate",
    name: "Inclinación típica",
    tilt: 30,
    icon: "🏠",
    description: "Casas estándar",
    illustration: (
      <svg viewBox="0 0 100 60" className="w-full h-full">
        <polygon points="50,10 10,40 90,40" fill="currentColor" className="text-slate-300 dark:text-slate-600" />
        <rect x="20" y="40" width="60" height="15" fill="currentColor" className="text-slate-300 dark:text-slate-600" />
        <line x1="50" y1="10" x2="90" y2="40" stroke="currentColor" strokeWidth="3" className="text-amber-500" />
        <circle cx="85" cy="12" r="8" fill="currentColor" className="text-amber-400" />
        <path d="M85 2 L85 22 M75 12 L95 12" stroke="currentColor" strokeWidth="1.5" className="text-amber-300" />
      </svg>
    ),
  },
  {
    id: "steep",
    name: "Muy inclinado",
    tilt: 45,
    icon: "⛰️",
    description: "Climas nevados",
    illustration: (
      <svg viewBox="0 0 100 60" className="w-full h-full">
        <polygon points="50,5 15,50 85,50" fill="currentColor" className="text-slate-300 dark:text-slate-600" />
        <line x1="50" y1="5" x2="85" y2="50" stroke="currentColor" strokeWidth="3" className="text-amber-500" />
        <circle cx="88" cy="15" r="8" fill="currentColor" className="text-amber-400" />
        <path d="M88 5 L88 25 M78 15 L98 15" stroke="currentColor" strokeWidth="1.5" className="text-amber-300" />
      </svg>
    ),
  },
  {
    id: "custom",
    name: "Personalizado",
    tilt: -1, // Special value for custom
    icon: "⚙️",
    description: "Ajuste manual",
    illustration: (
      <svg viewBox="0 0 100 60" className="w-full h-full">
        <circle cx="50" cy="30" r="20" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-300 dark:text-slate-600" strokeDasharray="5,3" />
        <path d="M50 15 L55 25 L45 25 Z" fill="currentColor" className="text-amber-500" />
        <path d="M50 45 L55 35 L45 35 Z" fill="currentColor" className="text-amber-500" />
        <path d="M35 30 L45 35 L45 25 Z" fill="currentColor" className="text-amber-500" />
        <path d="M65 30 L55 35 L55 25 Z" fill="currentColor" className="text-amber-500" />
      </svg>
    ),
  },
];

export function RoofPresets({ onSelect, selectedTilt }: RoofPresetsProps) {
  const getSelectedPreset = () => {
    if (selectedTilt === undefined) return null;
    const preset = ROOF_PRESETS.find(
      (p) => p.tilt === selectedTilt || (p.tilt === 10 && selectedTilt < 15) || (p.tilt === 30 && selectedTilt >= 15 && selectedTilt < 40)
    );
    return preset?.id || "custom";
  };

  const selected = getSelectedPreset();

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        Tipo de techo
      </label>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {ROOF_PRESETS.map((preset, index) => (
          <motion.button
            key={preset.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => onSelect(preset.tilt, preset.name)}
            className={`relative p-4 rounded-2xl border-2 text-left transition-all hover:scale-[1.02] ${
              selected === preset.id
                ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-lg shadow-amber-500/20"
                : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600"
            }`}
          >
            {/* Selection indicator */}
            {selected === preset.id && (
              <motion.div
                layoutId="selectedRoof"
                className="absolute top-2 right-2 w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center"
              >
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </motion.div>
            )}

            {/* Illustration */}
            <div className="h-16 mb-3 text-slate-400">
              {preset.illustration}
            </div>

            {/* Text */}
            <div className="font-medium text-slate-900 dark:text-white text-sm">
              {preset.name}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {preset.tilt > 0 ? `~${preset.tilt}°` : preset.description}
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

