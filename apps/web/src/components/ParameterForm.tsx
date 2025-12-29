"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

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
}

const ORIENTATIONS = [
  { value: "auto", label: "Óptimo Automático", icon: "✨" },
  { value: "N", label: "Norte", icon: "⬆️" },
  { value: "NE", label: "Noreste", icon: "↗️" },
  { value: "E", label: "Este", icon: "➡️" },
  { value: "SE", label: "Sureste", icon: "↘️" },
  { value: "S", label: "Sur", icon: "⬇️" },
  { value: "SW", label: "Suroeste", icon: "↙️" },
  { value: "W", label: "Oeste", icon: "⬅️" },
  { value: "NW", label: "Noroeste", icon: "↖️" },
] as const;

export function ParameterForm({
  onSubmit,
  isLoading,
  location,
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
      tilt: 30,
      orientation: "auto",
    },
    mode: "onChange",
  });

  const currentTilt = watch("tilt");
  const currentOrientation = watch("orientation");

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg space-y-6"
    >
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
        Parámetros del Panel
      </h3>

      {/* Area */}
      <div>
        <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          <span>Superficie cubierta</span>
          <span
            className="text-xs text-gray-500 cursor-help"
            title="Área total de paneles solares en metros cuadrados"
          >
            ℹ️
          </span>
        </label>
        <div className="relative">
          <input
            type="number"
            {...register("area_m2", { valueAsNumber: true })}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-solar-500 focus:border-transparent"
            placeholder="15"
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">
            m²
          </span>
        </div>
        {errors.area_m2 && (
          <p className="text-red-500 text-sm mt-1">{errors.area_m2.message}</p>
        )}
      </div>

      {/* Tilt */}
      <div>
        <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          <span>Inclinación</span>
          <span className="text-solar-600 font-mono">{currentTilt}°</span>
        </label>
        <input
          type="range"
          {...register("tilt", { valueAsNumber: true })}
          min="0"
          max="90"
          step="5"
          className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer
                   accent-solar-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0° (Horizontal)</span>
          <span>90° (Vertical)</span>
        </div>
      </div>

      {/* Orientation */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Orientación
        </label>
        <div className="grid grid-cols-3 gap-2">
          {ORIENTATIONS.map((orient) => (
            <button
              key={orient.value}
              type="button"
              onClick={() =>
                setValue("orientation", orient.value, { shouldValidate: true })
              }
              className={`p-2 rounded-lg border text-sm font-medium transition-all
                ${
                  currentOrientation === orient.value
                    ? "bg-solar-500 text-white border-solar-500"
                    : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-solar-300"
                }`}
            >
              <span className="mr-1">{orient.icon}</span>
              {orient.label}
            </button>
          ))}
        </div>
      </div>

      {/* Location Display */}
      {location && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p className="text-sm text-green-700 dark:text-green-400">
            📍 Ubicación: {location.lat.toFixed(4)}°,{" "}
            {location.lon.toFixed(4)}°
          </p>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!location || !isValid || isLoading}
        className={`w-full py-4 rounded-xl font-semibold text-white transition-all
          ${
            !location || !isValid || isLoading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-solar-500 hover:bg-solar-600 shadow-lg shadow-solar-500/30 hover:scale-[1.02]"
          }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
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
          </span>
        ) : (
          "Calcular Potencial Solar"
        )}
      </button>
    </form>
  );
}

