/**
 * API Route proxy for estimate endpoint with extended timeout.
 * 
 * Next.js rewrites have a ~30s timeout limit.
 * This route allows us to set custom timeout (60s) for slow PVGIS responses.
 */

import { NextRequest, NextResponse } from "next/server";

function getBackendUrl(): string {
  // In Next.js API routes, read env vars at runtime, not module level
  // Priority: NEXT_PUBLIC_API_URL > BACKEND_URL > localhost (dev only)
  
  // Get URL from environment variables
  let url = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL;
  
  // Remove any whitespace and trailing slashes
  if (url) {
    url = url.trim().replace(/\/+$/, "");
  }
  
  // Validate URL format
  if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
    // Don't allow localhost in production
    if (process.env.NODE_ENV === "production" && url.includes("localhost")) {
      throw new Error("localhost is not allowed in production. Please configure BACKEND_URL in Vercel.");
    }
    return url;
  }
  
  // Only allow localhost in development
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:8000";
  }
  
  // Production without URL configured - this should not happen
  throw new Error("BACKEND_URL or NEXT_PUBLIC_API_URL must be configured in production");
}

export async function POST(request: NextRequest) {
  let backendUrl: string;
  
  try {
    backendUrl = getBackendUrl();
  } catch (error) {
    console.error("❌ Backend URL configuration error:");
    console.error("NEXT_PUBLIC_API_URL:", process.env.NEXT_PUBLIC_API_URL || "NOT SET");
    console.error("BACKEND_URL:", process.env.BACKEND_URL || "NOT SET");
    console.error("NODE_ENV:", process.env.NODE_ENV);
    console.error("All env vars with 'BACKEND' or 'API':", 
      Object.keys(process.env)
        .filter(k => k.includes("BACKEND") || k.includes("API"))
        .map(k => `${k}=${process.env[k]?.substring(0, 20)}...`)
    );
    
    return NextResponse.json(
      { 
        error: "Backend URL not configured",
        message: "Please set BACKEND_URL or NEXT_PUBLIC_API_URL environment variable in Vercel.",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();

    console.log(`[Estimate API] Calling backend at: ${backendUrl}/api/v1/estimate`);

    // Create AbortController for custom timeout (60 seconds)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(`${backendUrl}/api/v1/estimate`, {
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

    console.error("❌ Estimate API error:", error);
    console.error(`Backend URL used: ${backendUrl}`);
    console.error(`Error details:`, error instanceof Error ? error.message : String(error));
    console.error(`Environment check - NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL || "NOT SET"}`);
    console.error(`Environment check - BACKEND_URL: ${process.env.BACKEND_URL || "NOT SET"}`);
    
    return NextResponse.json(
      { 
        error: "Error connecting to backend",
        details: error instanceof Error ? error.message : String(error),
        backend_url: backendUrl,
        hint: "Check that BACKEND_URL is configured in Vercel environment variables"
      },
      { status: 502 }
    );
  }
}

