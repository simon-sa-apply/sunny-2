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

interface MonthlyChartProps {
  data: Record<string, number>;
  animate?: boolean;
}

export function MonthlyChart({ data, animate = true }: MonthlyChartProps) {
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
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Generación Mensual Estimada
      </h3>

      <ResponsiveContainer width="100%" height={300}>
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
                        🔥 Mejor mes
                      </span>
                    )}
                    {data.isWorst && (
                      <span className="text-xs text-blue-600">
                        ❄️ Mes mínimo
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
            label={{ value: "Promedio", position: "right", fontSize: 10 }}
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

      <div className="flex justify-between mt-4 text-sm">
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">Mínimo</p>
          <p className="font-mono font-semibold text-blue-600">
            {minKwh.toLocaleString()} kWh
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">Promedio</p>
          <p className="font-mono font-semibold text-gray-600 dark:text-gray-300">
            {Math.round(avgKwh).toLocaleString()} kWh
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">Máximo</p>
          <p className="font-mono font-semibold text-green-600">
            {maxKwh.toLocaleString()} kWh
          </p>
        </div>
      </div>
    </div>
  );
}

