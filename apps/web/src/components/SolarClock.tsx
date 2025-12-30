"use client";

import { useState, useEffect, useMemo } from "react";
import { useTranslations } from "next-intl";

interface SolarClockProps {
  interpolationModel: {
    tilts: number[];
    orientations: number[];
    annual_values: number[][];
    optimal_tilt: number;
    optimal_orientation: number;
    optimal_annual_kwh: number;
  } | null;
  onUpdate: (result: InterpolationResult) => void;
  initialTilt?: number;
  initialOrientation?: number;
}

interface InterpolationResult {
  annual_kwh: number;
  efficiency: number;
  tilt: number;
  orientation: number;
}

const ORIENTATION_LABELS: Record<number, string> = {
  0: "N",
  45: "NE",
  90: "E",
  135: "SE",
  180: "S",
  225: "SW",
  270: "W",
  315: "NW",
};

export function SolarClock({
  interpolationModel,
  onUpdate,
  initialTilt = 30,
  initialOrientation = 180,
}: SolarClockProps) {
  const t = useTranslations("solarClock");
  const [tilt, setTilt] = useState(initialTilt);
  const [orientation, setOrientation] = useState(initialOrientation);

  // Interpolate value from model
  const result = useMemo(() => {
    if (!interpolationModel) {
      return { annual_kwh: 0, efficiency: 1, tilt, orientation };
    }

    const { tilts, orientations, annual_values, optimal_annual_kwh } =
      interpolationModel;

    // Find nearest indices
    const tiltIdx = tilts.findIndex((t) => t >= tilt) || tilts.length - 1;
    const orientIdx =
      orientations.findIndex((o) => o >= orientation) || orientations.length - 1;

    // Simple nearest-neighbor interpolation for demo
    const t0 = Math.max(0, tiltIdx - 1);
    const o0 = Math.max(0, orientIdx - 1);

    const annual_kwh = annual_values[t0]?.[o0] ?? 0;
    const efficiency = optimal_annual_kwh > 0 ? annual_kwh / optimal_annual_kwh : 1;

    return { annual_kwh, efficiency, tilt, orientation };
  }, [interpolationModel, tilt, orientation]);

  // Notify parent of changes
  useEffect(() => {
    onUpdate(result);
  }, [result, onUpdate]);

  const efficiencyColor =
    result.efficiency > 0.9
      ? "text-green-600"
      : result.efficiency > 0.7
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl md:rounded-2xl p-4 md:p-6 shadow-lg h-full flex flex-col w-full">
      <h3 className="text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-4 md:mb-6">
        ☀️ {t("title")}
      </h3>

      {/* Annual KWH Display */}
      <div className="text-center mb-4 md:mb-6">
        <span className="text-2xl md:text-4xl font-bold text-gray-900 dark:text-white">
          {result.annual_kwh.toLocaleString()}
        </span>
        <span className="text-sm md:text-lg text-gray-500 ml-1 md:ml-2">kWh/year</span>
        <div className={`text-xs md:text-sm mt-1 ${efficiencyColor}`}>
          {(result.efficiency * 100).toFixed(0)}% {t("efficiency")}
        </div>
      </div>

      {/* Tilt Slider */}
      <div className="mb-4 md:mb-6">
        <label className="flex items-center justify-between text-xs md:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          <span>{t("tilt")}</span>
          <span className="font-mono text-solar-600">{tilt}°</span>
        </label>
        <input
          type="range"
          min={0}
          max={90}
          step={5}
          value={tilt}
          onChange={(e) => setTilt(Number(e.target.value))}
          className="w-full h-2 md:h-3 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-solar-500"
        />
        <div className="flex justify-between text-[10px] md:text-xs text-gray-500 mt-1">
          <span>0°</span>
          <span>90°</span>
        </div>
      </div>

      {/* Orientation Compass */}
      <div>
        <label className="block text-xs md:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 md:mb-3">
          {t("orientation")}
        </label>
        <div className="grid grid-cols-4 gap-1.5 md:gap-2">
          {Object.entries(ORIENTATION_LABELS).map(([deg, label]) => (
            <button
              key={deg}
              onClick={() => setOrientation(Number(deg))}
              className={`p-2 md:p-3 rounded-lg border text-xs md:text-sm font-medium transition-all
                ${
                  orientation === Number(deg)
                    ? "bg-solar-500 text-white border-solar-500 scale-105"
                    : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-solar-300"
                }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Optimal indicator */}
      {interpolationModel && (
        <div className="mt-3 md:mt-4 p-2 md:p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p className="text-xs md:text-sm text-green-700 dark:text-green-400">
            💡 {interpolationModel.optimal_tilt}° / {ORIENTATION_LABELS[interpolationModel.optimal_orientation] || "N"}
          </p>
        </div>
      )}
    </div>
  );
}
