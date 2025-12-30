"use client";

import { useTranslations } from "next-intl";
import { useTransition, useEffect, useState } from "react";

const locales = [
  { code: "es", flag: "🇪🇸", label: "ES" },
  { code: "en", flag: "🇺🇸", label: "EN" },
] as const;

export function LanguageSelector() {
  const t = useTranslations("languageSelector");
  const [isPending, startTransition] = useTransition();
  const [currentLocale, setCurrentLocale] = useState<string>("es");

  useEffect(() => {
    // Get current locale from cookie
    const match = document.cookie.match(/NEXT_LOCALE=(\w+)/);
    if (match) {
      setCurrentLocale(match[1]);
    }
  }, []);

  const handleChange = (locale: string) => {
    if (locale === currentLocale) return;
    
    startTransition(() => {
      document.cookie = `NEXT_LOCALE=${locale};path=/;max-age=31536000`;
      window.location.reload();
    });
  };

  return (
    <div className="flex items-center gap-1 bg-white/10 dark:bg-slate-800/50 backdrop-blur-sm rounded-full p-1 border border-white/20 dark:border-slate-700">
      {locales.map((locale) => (
        <button
          key={locale.code}
          onClick={() => handleChange(locale.code)}
          disabled={isPending}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all
            ${currentLocale === locale.code 
              ? "bg-white/20 dark:bg-slate-700 text-white shadow-sm" 
              : "text-white/70 hover:text-white hover:bg-white/10"
            }
            ${isPending ? "opacity-50 cursor-wait" : ""}
          `}
          title={t(locale.code)}
        >
          <span className="text-base">{locale.flag}</span>
          <span className="hidden sm:inline text-xs">{locale.label}</span>
        </button>
      ))}
    </div>
  );
}
