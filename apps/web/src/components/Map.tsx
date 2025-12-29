"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

interface MapProps {
  onLocationSelect: (lat: number, lon: number) => void;
  selectedLocation?: { lat: number; lon: number } | null;
}

export function SolarMap({ onLocationSelect, selectedLocation }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  const markerInstance = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const stableOnLocationSelect = useCallback(onLocationSelect, []);

  useEffect(() => {
    if (!mapContainer.current || mapInstance.current) return;

    let isMounted = true;

    async function initMap() {
      try {
        // Dynamic import to avoid SSR issues
        const maplibregl = (await import("maplibre-gl")).default;

        if (!isMounted || !mapContainer.current) return;

        // Initialize map
        const map = new maplibregl.Map({
          container: mapContainer.current,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: [
                  "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                  "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
                  "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
                ],
                tileSize: 256,
                attribution: "&copy; OpenStreetMap contributors",
              },
            },
            layers: [
              {
                id: "osm",
                type: "raster",
                source: "osm",
                minzoom: 0,
                maxzoom: 19,
              },
            ],
          },
          center: [0, 20],
          zoom: 2,
        });

        mapInstance.current = map;

        // Add navigation controls
        map.addControl(new maplibregl.NavigationControl(), "top-right");

        // Handle click events
        map.on("click", (e: any) => {
          const { lat, lng } = e.lngLat;
          stableOnLocationSelect(lat, lng);
        });

        map.on("load", () => {
          if (isMounted) {
            setIsLoading(false);
          }
        });

        // Try to get user's location
        if (typeof navigator !== "undefined" && navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (position) => {
              const { latitude, longitude } = position.coords;
              map.flyTo({
                center: [longitude, latitude],
                zoom: 10,
              });
            },
            () => {
              // Location denied, stay at default
            }
          );
        }
      } catch (err) {
        console.error("Error initializing map:", err);
        if (isMounted) {
          setError("No se pudo cargar el mapa. Por favor ingresa las coordenadas manualmente.");
          setIsLoading(false);
        }
      }
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [stableOnLocationSelect]);

  // Update marker when location changes
  useEffect(() => {
    if (!mapInstance.current || !selectedLocation) return;

    async function updateMarker() {
      try {
        const maplibregl = (await import("maplibre-gl")).default;

        // Remove existing marker
        if (markerInstance.current) {
          markerInstance.current.remove();
        }

        // Create marker element
        const el = document.createElement("div");
        el.className = "solar-marker";
        el.style.cssText = `
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        `;
        el.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          </svg>
        `;

        markerInstance.current = new maplibregl.Marker({ element: el })
          .setLngLat([selectedLocation.lon, selectedLocation.lat])
          .addTo(mapInstance.current);

        // Fly to location
        mapInstance.current.flyTo({
          center: [selectedLocation.lon, selectedLocation.lat],
          zoom: 12,
        });
      } catch (err) {
        console.error("Error updating marker:", err);
      }
    }

    updateMarker();
  }, [selectedLocation]);

  if (error) {
    return (
      <div className="w-full h-[400px] bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-xl flex items-center justify-center">
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-2">{error}</p>
          <p className="text-sm text-gray-500">Usa los campos de coordenadas debajo del formulario.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={mapContainer}
        className="w-full h-[400px] rounded-xl overflow-hidden shadow-lg ring-1 ring-black/5"
      />
      {isLoading && (
        <div className="absolute inset-0 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-gray-800 dark:to-gray-900 rounded-xl flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Cargando mapa...</p>
          </div>
        </div>
      )}
      {!isLoading && (
        <div className="absolute bottom-4 left-4 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm px-4 py-2.5 rounded-lg text-sm shadow-lg">
          <span className="text-gray-700 dark:text-gray-300 font-medium">
            ☀️ Haz clic para seleccionar ubicación
          </span>
        </div>
      )}
    </div>
  );
}
