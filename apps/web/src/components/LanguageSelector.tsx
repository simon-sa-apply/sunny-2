"use client";

import { useTranslations } from "next-intl";
import { useTransition } from "react";

const locales = [
  { code: "es", flag: "🇪🇸" },
  { code: "en", flag: "🇺🇸" },
] as const;

export function LanguageSelector() {
  const t = useTranslations("languageSelector");
  const [isPending, startTransition] = useTransition();

  const handleChange = (locale: string) => {
    startTransition(() => {
      // Set cookie and reload to apply new locale
      document.cookie = `NEXT_LOCALE=${locale};path=/;max-age=31536000`;
      window.location.reload();
    });
  };

  return (
    <div className="flex items-center gap-1">
      {locales.map((locale) => (
        <button
          key={locale.code}
          onClick={() => handleChange(locale.code)}
          disabled={isPending}
          className={`
            px-2 py-1 rounded-lg text-sm font-medium transition-all
            ${isPending ? "opacity-50 cursor-wait" : "hover:bg-white/10"}
          `}
          title={t(locale.code)}
        >
          <span className="text-lg">{locale.flag}</span>
        </button>
      ))}
    </div>
  );
}

