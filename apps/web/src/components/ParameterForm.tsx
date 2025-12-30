"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect } from "react";
import { motion } from "framer-motion";

const schema = z.object({
  area_m2: z.number().min(1, "Mínimo 1 m²").max(10000, "Máximo 10,000 m²"),
  tilt: z.number().min(0).max(90).optional(),
  orientation: z
    .enum(["N", "S", "E", "W", "NE", "NW", "SE", "SW", "auto"])
    .optional(),
});

type FormData = z.infer<typeof schema>;

interface ParameterFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
  location: { lat: number; lon: number } | null;
  initialTilt?: number;
}

const ORIENTATIONS = [
  { value: "auto", label: "Óptimo Auto", icon: "✨", description: "Calculamos el mejor" },
  { value: "N", label: "Norte", icon: "⬆️" },
  { value: "NE", label: "Noreste", icon: "↗️" },
  { value: "E", label: "Este", icon: "➡️" },
  { value: "SE", label: "Sureste", icon: "↘️" },
  { value: "S", label: "Sur", icon: "⬇️" },
  { value: "SW", label: "Suroeste", icon: "↙️" },
  { value: "W", label: "Oeste", icon: "⬅️" },
  { value: "NW", label: "Noroeste", icon: "↖️" },
] as const;

// Common panel sizes for quick selection
const AREA_PRESETS = [
  { value: 10, label: "Pequeño", description: "~6 paneles" },
  { value: 20, label: "Mediano", description: "~12 paneles" },
  { value: 40, label: "Grande", description: "~24 paneles" },
];

export function ParameterForm({
  onSubmit,
  isLoading,
  location,
  initialTilt = 30,
}: ParameterFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      area_m2: 15,
      tilt: initialTilt,
      orientation: "auto",
    },
    mode: "onChange",
  });

  const currentTilt = watch("tilt");
  const currentOrientation = watch("orientation");
  const currentArea = watch("area_m2");

  // Update tilt when initialTilt changes (from roof presets)
  useEffect(() => {
    setValue("tilt", initialTilt);
  }, [initialTilt, setValue]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Area Selection */}
      <div>
        <label className="flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          <span className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 text-sm">
              📐
            </span>
            Superficie de paneles
          </span>
          <span className="text-amber-600 font-mono">{currentArea} m²</span>
        </label>

        {/* Quick presets */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {AREA_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => setValue("area_m2", preset.value, { shouldValidate: true })}
              className={`p-3 rounded-xl border-2 text-center transition-all ${
                currentArea === preset.value
                  ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20"
                  : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
              }`}
            >
              <div className="font-semibold text-slate-900 dark:text-white">
                {preset.value} m²
              </div>
              <div className="text-xs text-slate-500">{preset.description}</div>
            </button>
          ))}
        </div>

        {/* Custom input */}
        <div className="relative">
          <input
            type="number"
            {...register("area_m2", { valueAsNumber: true })}
            className="w-full px-4 py-3 border-2 border-slate-200 dark:border-slate-700 rounded-xl 
                     bg-white dark:bg-slate-900 text-slate-900 dark:text-white
                     focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all"
            placeholder="Ingresa un valor personalizado"
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-medium">
            m²
          </span>
        </div>
        {errors.area_m2 && (
          <p className="text-red-500 text-sm mt-2">{errors.area_m2.message}</p>
        )}
      </div>

      {/* Tilt Slider */}
      <div>
        <label className="flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          <span className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-sky-100 dark:bg-sky-900/30 flex items-center justify-center text-sky-600 text-sm">
              📐
            </span>
            Inclinación del techo
          </span>
          <span className="text-sky-600 font-mono">{currentTilt}°</span>
        </label>

        <div className="relative">
          <input
            type="range"
            {...register("tilt", { valueAsNumber: true })}
            min="0"
            max="90"
            step="5"
            className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full appearance-none cursor-pointer
                     accent-sky-500"
          />
          {/* Markers */}
          <div className="flex justify-between text-xs text-slate-400 mt-2 px-1">
            <span>0° Plano</span>
            <span>30° Típico</span>
            <span>90° Vertical</span>
          </div>
        </div>
      </div>

      {/* Orientation */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          <span className="w-6 h-6 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 text-sm">
            🧭
          </span>
          Orientación de los paneles
        </label>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
          {ORIENTATIONS.map((orient) => (
            <motion.button
              key={orient.value}
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() =>
                setValue("orientation", orient.value, { shouldValidate: true })
              }
              className={`p-3 rounded-xl border-2 text-center transition-all ${
                currentOrientation === orient.value
                  ? "border-purple-500 bg-purple-50 dark:bg-purple-900/20 shadow-lg shadow-purple-500/10"
                  : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
              }`}
            >
              <div className="text-xl mb-1">{orient.icon}</div>
              <div className="font-medium text-sm text-slate-900 dark:text-white">
                {orient.label}
              </div>
              {orient.description && (
                <div className="text-xs text-slate-500">{orient.description}</div>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <motion.button
        type="submit"
        disabled={!location || !isValid || isLoading}
        whileHover={location && isValid && !isLoading ? { scale: 1.02 } : {}}
        whileTap={location && isValid && !isLoading ? { scale: 0.98 } : {}}
        className={`w-full py-4 rounded-2xl font-semibold text-lg transition-all flex items-center justify-center gap-3
          ${
            !location || !isValid || isLoading
              ? "bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed"
              : "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-xl shadow-amber-500/30 hover:shadow-amber-500/50"
          }`}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Calculando...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Calcular Potencial Solar
          </>
        )}
      </motion.button>

      {!location && (
        <p className="text-center text-slate-500 text-sm">
          👆 Primero selecciona una ubicación en el mapa
        </p>
      )}
    </form>
  );
}
