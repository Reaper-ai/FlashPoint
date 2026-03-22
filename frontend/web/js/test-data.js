/**
 * test-data.js - Simple test markers for debugging
 */

/**
 * Add simple test markers directly
 */
export function initTestData() {
    console.log("🧪 Test data initializing...");

    setTimeout(() => {
        // Access global map objects
        const { map, markerLayer } = window.FlashPointMap || {};

        if (!map || !markerLayer) {
            console.error("❌ Test data: Map not available globally");
            console.log("Available:", window.FlashPointMap);
            return;
        }

        console.log("🧪 Adding test markers...");

        // Test marker 1: Paris (Green)
        const parisMarker = L.circle([48.8566, 2.3522], {
            color: '#00ff00',
            fillColor: '#00ff00',
            fillOpacity: 0.7,
            radius: 80000,
            weight: 3
        });
        parisMarker.bindPopup("🧪 TEST: Paris, France<br>Green Circle");
        parisMarker.addTo(markerLayer);

        // Test marker 2: Tokyo (Red)
        const tokyoMarker = L.circle([35.6762, 139.6503], {
            color: '#ff0000',
            fillColor: '#ff0000',
            fillOpacity: 0.7,
            radius: 80000,
            weight: 3
        });
        tokyoMarker.bindPopup("🧪 TEST: Tokyo, Japan<br>Red Circle");
        tokyoMarker.addTo(markerLayer);

        // Test marker 3: New York (Blue)
        const nyMarker = L.circle([40.7128, -74.0060], {
            color: '#0000ff',
            fillColor: '#0000ff',
            fillOpacity: 0.7,
            radius: 80000,
            weight: 3
        });
        nyMarker.bindPopup("🧪 TEST: New York, USA<br>Blue Circle");
        nyMarker.addTo(markerLayer);

        // Test conflict marker: Los Angeles (Purple)
        const laConflict = L.circleMarker([34.0522, -118.2437], {
            color: '#800080',
            fillColor: '#800080',
            fillOpacity: 0.8,
            radius: 10,
            weight: 3
        });
        laConflict.bindPopup("⚔️ TEST CONFLICT<br>Los Angeles<br>Critical Status");
        laConflict.addTo(markerLayer);

        console.log("✅ Added 4 test markers");
        console.log("🗺️ Total markers:", markerLayer.getLayers().length);

        // Center map on USA to see markers
        map.setView([39.8283, -98.5795], 4);

        console.log("✅ Test data complete - check map for colored circles!");

    }, 2000); // Wait 2 seconds for map to be ready
}