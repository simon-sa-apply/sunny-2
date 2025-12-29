"use client";

interface ProgressBarProps {
  percent: number;
  message: string;
}

export function ProgressBar({ percent, message }: ProgressBarProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg mb-8">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {message}
        </span>
        <span className="text-sm font-mono text-solar-600">{percent}%</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-solar-400 to-solar-600 h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>🛰️ Satélite</span>
        <span>📊 Cálculo</span>
        <span>🤖 IA</span>
        <span>✅ Listo</span>
      </div>
    </div>
  );
}

