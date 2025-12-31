/**
 * API Route proxy for estimate endpoint with extended timeout.
 * 
 * Next.js rewrites have a ~30s timeout limit.
 * This route allows us to set custom timeout (60s) for slow PVGIS responses.
 */

import { NextRequest, NextResponse } from "next/server";

// Use NEXT_PUBLIC_API_URL from vercel.json or BACKEND_URL, fallback to localhost for dev
const BACKEND_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  process.env.BACKEND_URL || 
  (process.env.NODE_ENV === "development" ? "http://localhost:8000" : null);

export async function POST(request: NextRequest) {
  // Validate backend URL is configured in production
  if (!BACKEND_URL) {
    console.error("BACKEND_URL or NEXT_PUBLIC_API_URL environment variable is not set!");
    console.error("Available env vars:", Object.keys(process.env).filter(k => k.includes("BACKEND") || k.includes("API")));
    return NextResponse.json(
      { 
        error: "Backend URL not configured. Please set BACKEND_URL or NEXT_PUBLIC_API_URL environment variable.",
        details: "This is a configuration error. Contact the administrator."
      },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();

    console.log(`[Estimate API] Calling backend at: ${BACKEND_URL}/api/v1/estimate`);

    // Create AbortController for custom timeout (60 seconds)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(`${BACKEND_URL}/api/v1/estimate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: errorText || "Error from backend" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      return NextResponse.json(
        { error: "Request timeout - El servidor tardó más de 60 segundos" },
        { status: 504 }
      );
    }

    console.error("Estimate API error:", error);
    console.error(`Backend URL used: ${BACKEND_URL}`);
    console.error(`Error details:`, error instanceof Error ? error.message : String(error));
    
    return NextResponse.json(
      { 
        error: "Error connecting to backend",
        details: error instanceof Error ? error.message : String(error),
        backend_url: BACKEND_URL
      },
      { status: 502 }
    );
  }
}

