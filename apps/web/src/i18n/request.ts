import { getRequestConfig } from "next-intl/server";
import { cookies, headers } from "next/headers";

export const locales = ["es", "en"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "es";

export default getRequestConfig(async () => {
  // Try to get locale from cookie first, then Accept-Language header
  const cookieStore = await cookies();
  const headersList = await headers();
  
  let locale: Locale = defaultLocale;
  
  // Check cookie
  const cookieLocale = cookieStore.get("NEXT_LOCALE")?.value;
  if (cookieLocale && locales.includes(cookieLocale as Locale)) {
    locale = cookieLocale as Locale;
  } else {
    // Check Accept-Language header
    const acceptLanguage = headersList.get("Accept-Language");
    if (acceptLanguage) {
      const preferred = acceptLanguage.split(",")[0].split("-")[0];
      if (locales.includes(preferred as Locale)) {
        locale = preferred as Locale;
      }
    }
  }

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});

