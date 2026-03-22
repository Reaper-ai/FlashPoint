/**
 * map.js - Ultra-simplified map with debugging
 */

import { escapeHTML } from './utils.js';

export let map, markerLayer;
const locationData = new Map();
const markerCache = new Map();
let updateQueue = [];
let isProcessing = false;

// Separate layers for different marker types
let militaryAircraftLayer, civilianAircraftLayer, oilTankerLayer, conflictLayer, hotspotLayer;
let layerControl;

// Make map and layers globally accessible for debugging
window.FlashPointMap = {
    map: null,
    markerLayer: null,
    militaryAircraftLayer: null,
    civilianAircraftLayer: null,
    oilTankerLayer: null,
    conflictLayer: null,
    hotspotLayer: null,
    addTestMarker: null
};

const HOTSPOT_COLORS = {
    1: "#10b981",   // Green
    5: "#f59e0b",   // Amber
    10: "#ef4444",  // Red
    20: "#dc2626"   // Dark Red
};

/**
 * Initialize map with maximum debugging
 */
export function initMap() {
    const container = document.getElementById("map");
    if (!container) {
        console.error("❌ Map container '#map' not found");
        return false;
    }

    console.log("🗺️ Map container found:", container);
    console.log("🗺️ Container dimensions:", {
        width: container.offsetWidth,
        height: container.offsetHeight
    });

    try {
        // Clear existing map
        if (map) {
            console.log("🗑️ Removing existing map");
            map.remove();
        }

        // Create map
        console.log("🗺️ Creating Leaflet map...");
        map = L.map("map", {
            center: [40, -95], // Center on USA
            zoom: 4,
            zoomControl: true,
            scrollWheelZoom: true,
            preferCanvas: true,
            renderer: L.canvas({ padding: 0.5 })
        });

        // Add tile layer
        console.log("🗺️ Adding OSM tiles...");
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; OpenStreetMap',
            subdomains: ['a', 'b', 'c'],
            maxZoom: 18
        }).addTo(map);

        // Create marker layer (main container)
        console.log("🗺️ Creating marker layer...");
        markerLayer = L.layerGroup().addTo(map);

        // Create separate layers for different marker types
        militaryAircraftLayer = L.layerGroup().addTo(map);
        civilianAircraftLayer = L.layerGroup().addTo(map);
        oilTankerLayer = L.layerGroup().addTo(map);
        conflictLayer = L.layerGroup().addTo(map);
        hotspotLayer = L.layerGroup().addTo(map);

        // Create layer control
        const overlayMaps = {
            "🎯 Military Aircraft": militaryAircraftLayer,
            "✈️ Civilian Aircraft": civilianAircraftLayer,
            "🛢️ Oil Tankers": oilTankerLayer,
            "⚔️ Conflicts": conflictLayer,
            "📍 Geo Hotspots": hotspotLayer
        };

        layerControl = L.control.layers(null, overlayMaps, {
            collapsed: false,
            position: 'topright'
        }).addTo(map);

        // Make all layers globally accessible
        window.FlashPointMap.map = map;
        window.FlashPointMap.markerLayer = markerLayer;
        window.FlashPointMap.militaryAircraftLayer = militaryAircraftLayer;
        window.FlashPointMap.civilianAircraftLayer = civilianAircraftLayer;
        window.FlashPointMap.oilTankerLayer = oilTankerLayer;
        window.FlashPointMap.conflictLayer = conflictLayer;
        window.FlashPointMap.hotspotLayer = hotspotLayer;

        // Add test marker function to global scope
        window.FlashPointMap.addTestMarker = function() {
            console.log("🧪 Adding manual test marker...");
            const testMarker = L.circle([40.7128, -74.0060], {
                color: '#ff0000',
                fillColor: '#ff0000',
                fillOpacity: 0.6,
                radius: 100000,
                weight: 3
            });

            testMarker.bindPopup("🧪 Manual Test Marker<br>New York City");
            testMarker.addTo(markerLayer);

            console.log("✅ Manual test marker added");
            return testMarker;
        };

        // Immediately add a test marker
        console.log("🧪 Adding immediate test marker...");
        setTimeout(() => {
            const immediateTest = L.circle([51.5074, -0.1278], {
                color: '#00ff00',
                fillColor: '#00ff00',
                fillOpacity: 0.8,
                radius: 50000,
                weight: 4
            });

            immediateTest.bindPopup("✅ IMMEDIATE TEST MARKER<br>London, UK<br>If you see this, map rendering works!");
            immediateTest.addTo(markerLayer);

            console.log("✅ Immediate test marker added to London");
            console.log("🗺️ Marker layer has", markerLayer.getLayers().length, "markers");
        }, 500);

        // Log successful initialization
        console.log("✅ Map initialized successfully");
        console.log("🗺️ Map object:", map);
        console.log("🗺️ Marker layer object:", markerLayer);

        return true;

    } catch (error) {
        console.error("❌ Map initialization failed:", error);
        return false;
    }
}

/**
 * Simplified marker update - uses hotspot layer
 */
export function updateMapHotspot(item) {
    if (!item?.lat || !item?.lon) {
        console.log("⚠️ Missing coordinates:", item);
        return;
    }

    if (!map || !hotspotLayer) {
        console.log("⚠️ Map or hotspot layer not initialized");
        return;
    }

    console.log("📍 Adding hotspot marker:", {
        lat: item.lat,
        lon: item.lon,
        place: item.place
    });

    try {
        const circle = L.circle([item.lat, item.lon], {
            color: '#0066ff',
            fillColor: '#0066ff',
            fillOpacity: 0.6,
            radius: 75000,
            weight: 2
        });

        circle.bindPopup(`
            <strong>${escapeHTML(item.place || 'Unknown')}</strong><br>
            <small>${escapeHTML((item.text || '').substring(0, 100))}...</small>
        `);

        circle.addTo(hotspotLayer);

        console.log("✅ Hotspot marker added successfully");
        console.log("🗺️ Total hotspot markers:", hotspotLayer.getLayers().length);

    } catch (error) {
        console.error("❌ Failed to add hotspot marker:", error);
    }
}

/**
 * Simplified conflict markers - uses conflict layer
 */
export async function renderConflictMarkers(conflicts) {
    if (!conflicts?.length) {
        console.log("⚠️ No conflicts to render");
        return;
    }

    if (!map || !conflictLayer) {
        console.log("⚠️ Map or conflict layer not initialized for conflicts");
        return;
    }

    console.log("🔴 Rendering conflict markers:", conflicts.length);

    // Clear existing conflict markers
    conflictLayer.clearLayers();

    conflicts.forEach((conflict, index) => {
        if (!conflict.lat || !conflict.lon) {
            console.log("⚠️ Conflict missing coordinates:", conflict);
            return;
        }

        try {
            const colors = {
                critical: "#dc2626",
                high: "#ea580c",
                medium: "#f59e0b",
                low: "#16a34a"
            };

            const color = colors[conflict.severity?.toLowerCase()] || "#6b7280";

            const marker = L.circleMarker([conflict.lat, conflict.lon], {
                color: color,
                fillColor: color,
                fillOpacity: 0.8,
                radius: 8,
                weight: 2
            });

            marker.bindPopup(`
                <strong style="color: ${color}">${escapeHTML(conflict.name)}</strong><br>
                Status: ${escapeHTML(conflict.status || 'Active')}<br>
                Severity: ${escapeHTML(conflict.severity || 'Unknown')}
            `);

            marker.addTo(conflictLayer);
            console.log(`✅ Added conflict marker ${index + 1}:`, conflict.name);

        } catch (error) {
            console.error("❌ Failed to add conflict marker:", error, conflict);
        }
    });

    console.log("✅ Conflict markers rendering complete");
    console.log("🗺️ Total conflict markers:", conflictLayer.getLayers().length);
}

/**
 * Clear all markers from all layers
 */
export function clearMap() {
    let totalCleared = 0;

    if (markerLayer) {
        totalCleared += markerLayer.getLayers().length;
        markerLayer.clearLayers();
    }
    if (militaryAircraftLayer) {
        totalCleared += militaryAircraftLayer.getLayers().length;
        militaryAircraftLayer.clearLayers();
    }
    if (civilianAircraftLayer) {
        totalCleared += civilianAircraftLayer.getLayers().length;
        civilianAircraftLayer.clearLayers();
    }
    if (oilTankerLayer) {
        totalCleared += oilTankerLayer.getLayers().length;
        oilTankerLayer.clearLayers();
    }
    if (conflictLayer) {
        totalCleared += conflictLayer.getLayers().length;
        conflictLayer.clearLayers();
    }
    if (hotspotLayer) {
        totalCleared += hotspotLayer.getLayers().length;
        hotspotLayer.clearLayers();
    }

    console.log(`🗑️ Cleared ${totalCleared} markers from all layers`);
    locationData.clear();
    markerCache.clear();
    updateQueue = [];
}

/**
 * Get map statistics for all layers
 */
export function getMapStats() {
    return {
        hasMap: !!map,
        hasMarkerLayer: !!markerLayer,
        markerCount: markerLayer ? markerLayer.getLayers().length : 0,
        militaryAircraft: militaryAircraftLayer ? militaryAircraftLayer.getLayers().length : 0,
        civilianAircraft: civilianAircraftLayer ? civilianAircraftLayer.getLayers().length : 0,
        oilTankers: oilTankerLayer ? oilTankerLayer.getLayers().length : 0,
        conflicts: conflictLayer ? conflictLayer.getLayers().length : 0,
        hotspots: hotspotLayer ? hotspotLayer.getLayers().length : 0,
        queueSize: updateQueue.length
    };
}