/**
 * API Route proxy for estimate endpoint with extended timeout.
 * 
 * Next.js rewrites have a ~30s timeout limit.
 * This route allows us to set custom timeout (60s) for slow PVGIS responses.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

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
    return NextResponse.json(
      { error: "Error connecting to backend" },
      { status: 502 }
    );
  }
}

