"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";

interface RoofPresetsProps {
  onSelect: (tilt: number, name: string) => void;
  selectedTilt?: number;
}

export function RoofPresets({ onSelect, selectedTilt }: RoofPresetsProps) {
  const t = useTranslations("roofPresets");

  const ROOF_PRESETS = [
    {
      id: "flat",
      name: t("flat.name"),
      tilt: 10,
      icon: "🏢",
      description: t("flat.description"),
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
      name: t("moderate.name"),
      tilt: 30,
      icon: "🏠",
      description: t("moderate.description"),
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
      name: t("steep.name"),
      tilt: 45,
      icon: "⛰️",
      description: t("steep.description"),
      illustration: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polygon points="50,5 15,50 85,50" fill="currentColor" className="text-slate-300 dark:text-slate-600" />
          <line x1="50" y1="5" x2="85" y2="50" stroke="currentColor" strokeWidth="3" className="text-amber-500" />
          <circle cx="88" cy="15" r="8" fill="currentColor" className="text-amber-400" />
          <path d="M88 5 L88 25 M78 15 L98 15" stroke="currentColor" strokeWidth="1.5" className="text-amber-300" />
        </svg>
      ),
    },
  ];

  const getSelectedPreset = () => {
    if (selectedTilt === undefined) return null;
    // Match preset by tilt ranges
    if (selectedTilt <= 15) return "flat";
    if (selectedTilt <= 37) return "moderate";
    if (selectedTilt <= 55) return "steep";
    return "moderate"; // Default
  };

  const selected = getSelectedPreset();

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        {t("title")}
      </label>
      <div className="grid grid-cols-3 gap-3">
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
