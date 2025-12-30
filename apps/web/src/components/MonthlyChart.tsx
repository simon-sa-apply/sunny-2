"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useTranslations } from "next-intl";

interface MonthlyChartProps {
  data: Record<string, number>;
  animate?: boolean;
}

export function MonthlyChart({ data, animate = true }: MonthlyChartProps) {
  const t = useTranslations("monthlyChart");

  const chartData = Object.entries(data).map(([month, kwh]) => ({
    month,
    kwh: Math.round(kwh),
    isPeak: kwh === Math.max(...Object.values(data)),
    isWorst: kwh === Math.min(...Object.values(data)),
  }));

  const maxKwh = Math.max(...Object.values(data));
  const minKwh = Math.min(...Object.values(data));
  const avgKwh = Object.values(data).reduce((a, b) => a + b, 0) / 12;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl md:rounded-2xl p-4 md:p-6 shadow-lg h-full flex flex-col">
      <h3 className="text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-3 md:mb-4">
        {t("title")}
      </h3>

      <div className="flex-1 min-h-[220px] md:min-h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorKwh" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: "#e5e7eb" }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}`}
            domain={[0, "dataMax + 50"]}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {data.month}
                    </p>
                    <p className="text-solar-600 font-mono">
                      {data.kwh.toLocaleString()} kWh
                    </p>
                    {data.isPeak && (
                      <span className="text-xs text-green-600">
                        🔥 {t("peak")}
                      </span>
                    )}
                    {data.isWorst && (
                      <span className="text-xs text-blue-600">
                        ❄️ {t("worst")}
                      </span>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine
            y={avgKwh}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{ value: t("average"), position: "right", fontSize: 10 }}
          />
          <Area
            type="monotone"
            dataKey="kwh"
            stroke="#f59e0b"
            strokeWidth={2}
            fill="url(#colorKwh)"
            animationDuration={animate ? 1000 : 0}
          />
        </AreaChart>
      </ResponsiveContainer>
      </div>

      <div className="flex justify-between mt-3 md:mt-4 text-xs md:text-sm">
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">{t("min")}</p>
          <p className="font-mono font-semibold text-blue-600">
            {minKwh.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">{t("average")}</p>
          <p className="font-mono font-semibold text-gray-600 dark:text-gray-300">
            {Math.round(avgKwh).toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">{t("max")}</p>
          <p className="font-mono font-semibold text-green-600">
            {maxKwh.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
