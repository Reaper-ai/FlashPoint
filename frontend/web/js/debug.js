/**
 * debug.js - Browser console debugging commands
 */

// Make debugging functions globally available
window.FlashPointDebug = {

    // Check map status
    checkMap() {
        console.log("🔍 MAP DEBUG INFO:");
        console.log("- Map object:", window.FlashPointMap?.map);
        console.log("- Main marker layer:", window.FlashPointMap?.markerLayer);
        console.log("- Military aircraft layer:", window.FlashPointMap?.militaryAircraftLayer);
        console.log("- Civilian aircraft layer:", window.FlashPointMap?.civilianAircraftLayer);
        console.log("- Oil tanker layer:", window.FlashPointMap?.oilTankerLayer);
        console.log("- Conflict layer:", window.FlashPointMap?.conflictLayer);
        console.log("- Hotspot layer:", window.FlashPointMap?.hotspotLayer);
        console.log("- Container element:", document.getElementById("map"));

        const container = document.getElementById("map");
        if (container) {
            console.log("- Container dimensions:", {
                width: container.offsetWidth,
                height: container.offsetHeight,
                display: getComputedStyle(container).display,
                visibility: getComputedStyle(container).visibility
            });
        }

        // Layer statistics
        if (window.FlashPointMap) {
            const layers = window.FlashPointMap;
            console.log("- Layer counts:", {
                military: layers.militaryAircraftLayer?.getLayers().length || 0,
                civilian: layers.civilianAircraftLayer?.getLayers().length || 0,
                tankers: layers.oilTankerLayer?.getLayers().length || 0,
                conflicts: layers.conflictLayer?.getLayers().length || 0,
                hotspots: layers.hotspotLayer?.getLayers().length || 0
            });
        }
    },

    // Add test marker manually
    addTestMarker() {
        if (window.FlashPointMap?.addTestMarker) {
            return window.FlashPointMap.addTestMarker();
        } else {
            console.error("❌ Test marker function not available");
        }
    },

    // Test military aircraft marker
    addTestMilitary() {
        const { militaryAircraftLayer } = window.FlashPointMap || {};
        if (!militaryAircraftLayer) {
            console.error("❌ Military layer not available");
            return;
        }

        const marker = L.circleMarker([39.0, -77.0], {
            color: '#ff3333',
            fillColor: '#ff3333',
            fillOpacity: 0.8,
            radius: 10,
            weight: 3
        });
        marker.bindPopup("🎯 TEST MILITARY<br>Washington DC Area");
        marker.addTo(militaryAircraftLayer);
        console.log("✅ Added test military aircraft marker");
        return marker;
    },

    // Test civilian aircraft marker
    addTestCivilian() {
        const { civilianAircraftLayer } = window.FlashPointMap || {};
        if (!civilianAircraftLayer) {
            console.error("❌ Civilian layer not available");
            return;
        }

        const marker = L.circleMarker([40.7, -74.0], {
            color: '#0099ff',
            fillColor: '#0099ff',
            fillOpacity: 0.8,
            radius: 6,
            weight: 3
        });
        marker.bindPopup("✈️ TEST CIVILIAN<br>New York Area");
        marker.addTo(civilianAircraftLayer);
        console.log("✅ Added test civilian aircraft marker");
        return marker;
    },

    // Test oil tanker marker
    addTestTanker() {
        const { oilTankerLayer } = window.FlashPointMap || {};
        if (!oilTankerLayer) {
            console.error("❌ Oil tanker layer not available");
            return;
        }

        const marker = L.circleMarker([29.7, -95.3], {
            color: '#ff8800',
            fillColor: '#ff8800',
            fillOpacity: 0.8,
            radius: 9,
            weight: 3
        });
        marker.bindPopup("🛢️ TEST TANKER<br>Houston Area");
        marker.addTo(oilTankerLayer);
        console.log("✅ Added test oil tanker marker");
        return marker;
    },

    // Add marker at specific location
    addMarker(lat, lon, color = '#ff0000', label = 'Debug Marker') {
        const { map, markerLayer } = window.FlashPointMap || {};

        if (!map || !markerLayer) {
            console.error("❌ Map not available");
            return null;
        }

        const marker = L.circle([lat, lon], {
            color: color,
            fillColor: color,
            fillOpacity: 0.7,
            radius: 100000,
            weight: 3
        });

        marker.bindPopup(`${label}<br>Lat: ${lat}<br>Lon: ${lon}`);
        marker.addTo(markerLayer);

        console.log(`✅ Added marker at [${lat}, ${lon}]`);
        return marker;
    },

    // Clear all markers
    clearAllMarkers() {
        const layers = window.FlashPointMap || {};
        let totalCleared = 0;

        ['markerLayer', 'militaryAircraftLayer', 'civilianAircraftLayer',
         'oilTankerLayer', 'conflictLayer', 'hotspotLayer'].forEach(layerName => {
            const layer = layers[layerName];
            if (layer) {
                const count = layer.getLayers().length;
                layer.clearLayers();
                totalCleared += count;
                console.log(`🗑️ Cleared ${count} markers from ${layerName}`);
            }
        });

        console.log(`🗑️ Total cleared: ${totalCleared} markers`);
    },

    // Clear specific layer
    clearLayer(layerType) {
        const layers = window.FlashPointMap || {};
        const layerMap = {
            'military': 'militaryAircraftLayer',
            'civilian': 'civilianAircraftLayer',
            'tankers': 'oilTankerLayer',
            'conflicts': 'conflictLayer',
            'hotspots': 'hotspotLayer'
        };

        const layerName = layerMap[layerType];
        if (!layerName || !layers[layerName]) {
            console.error(`❌ Layer '${layerType}' not found`);
            return;
        }

        const count = layers[layerName].getLayers().length;
        layers[layerName].clearLayers();
        console.log(`🗑️ Cleared ${count} markers from ${layerType} layer`);
    },

    // Test tracking refresh
    refreshTracking() {
        import('./tracking.js').then(module => {
            console.log("🔄 Refreshing tracking data...");
            module.refreshFlights();
            setTimeout(() => module.refreshShips(), 1000);
        }).catch(err => {
            console.error("❌ Failed to refresh tracking:", err);
        });
    },

    // Test Leaflet basics
    testLeaflet() {
        console.log("🔍 LEAFLET TEST:");
        console.log("- Leaflet loaded:", typeof L !== 'undefined');
        console.log("- Leaflet version:", L?.version);

        if (typeof L !== 'undefined') {
            console.log("✅ Leaflet is available");

            // Test creating a simple marker
            try {
                const testCircle = L.circle([0, 0], { radius: 1000 });
                console.log("✅ Can create Leaflet circle:", testCircle);
            } catch (e) {
                console.error("❌ Failed to create Leaflet circle:", e);
            }
        } else {
            console.error("❌ Leaflet not loaded!");
        }
    },

    // Force map resize (sometimes fixes display issues)
    resizeMap() {
        const { map } = window.FlashPointMap || {};
        if (map) {
            map.invalidateSize();
            console.log("🔄 Map resized");
        }
    }
};

// Show debug help
console.log(`
🔧 FlashPoint Debug Commands:
- FlashPointDebug.checkMap()     - Check map status and layer counts
- FlashPointDebug.addTestMarker() - Add basic test marker
- FlashPointDebug.addTestMilitary() - Add test military aircraft
- FlashPointDebug.addTestCivilian() - Add test civilian aircraft
- FlashPointDebug.addTestTanker() - Add test oil tanker
- FlashPointDebug.addMarker(lat, lon, color, label) - Add custom marker
- FlashPointDebug.clearAllMarkers() - Clear all markers from all layers
- FlashPointDebug.clearLayer(type) - Clear specific layer (military/civilian/tankers/conflicts/hotspots)
- FlashPointDebug.refreshTracking() - Refresh flight and ship data
- FlashPointDebug.testLeaflet()  - Test Leaflet library
- FlashPointDebug.resizeMap()    - Force map resize
`);

export default window.FlashPointDebug;