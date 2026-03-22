/**
 * tracking.js - Flight and Ship tracking integration with better timing
 */

import { API_BASE } from './utils.js';

let flightMarkers = [];
let shipMarkers = [];
let lastPositions = new Map(); // Track previous positions for movement calculation

/**
 * Fetch and render flight tracking data
 */
async function fetchFlights() {
    try {
        console.log("✈️ Fetching flights...");
        const resp = await fetch(`${API_BASE}/api/tracking/flights?limit=50`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const data = await resp.json();

        if (data.success && data.flights) {
            console.log(`✈️ Received ${data.flights.length} flights`);
            waitForMapAndRenderFlights(data.flights);
        }

    } catch (err) {
        console.error("Failed to fetch flights:", err);
    }
}

/**
 * Fetch and render ship tracking data
 */
async function fetchShips() {
    try {
        console.log("🚢 Fetching ships...");
        const resp = await fetch(`${API_BASE}/api/tracking/ships?limit=50`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const data = await resp.json();

        if (data.success && data.ships) {
            console.log(`🚢 Received ${data.ships.length} ships`);
            waitForMapAndRenderShips(data.ships);
        }

    } catch (err) {
        console.error("Failed to fetch ships:", err);
    }
}

/**
 * Wait for map and render flights
 */
function waitForMapAndRenderFlights(flights) {
    const maxAttempts = 10;
    let attempts = 0;

    function tryRender() {
        attempts++;
        const { map, militaryAircraftLayer, civilianAircraftLayer } = window.FlashPointMap || {};

        if (map && militaryAircraftLayer && civilianAircraftLayer) {
            console.log("✈️ Map and aircraft layers ready, rendering flights...");
            renderFlightMarkers(flights);
            return;
        }

        if (attempts < maxAttempts) {
            console.log(`✈️ Aircraft layers not ready, attempt ${attempts}/${maxAttempts}`);
            setTimeout(tryRender, 500);
        } else {
            console.error("❌ Failed to render flights - aircraft layers not ready");
        }
    }

    tryRender();
}

/**
 * Wait for map and render ships
 */
function waitForMapAndRenderShips(ships) {
    const maxAttempts = 10;
    let attempts = 0;

    function tryRender() {
        attempts++;
        const { map, oilTankerLayer } = window.FlashPointMap || {};

        if (map && oilTankerLayer) {
            console.log("🚢 Map and tanker layer ready, rendering ships...");
            renderShipMarkers(ships);
            return;
        }

        if (attempts < maxAttempts) {
            console.log(`🚢 Tanker layer not ready, attempt ${attempts}/${maxAttempts}`);
            setTimeout(tryRender, 500);
        } else {
            console.error("❌ Failed to render ships - tanker layer not ready");
        }
    }

    tryRender();
}

/**
 * Render flight markers with filtering and dynamic movement
 */
function renderFlightMarkers(flights) {
    const { map, militaryAircraftLayer, civilianAircraftLayer } = window.FlashPointMap || {};
    if (!map || !militaryAircraftLayer || !civilianAircraftLayer) {
        console.error("❌ No map layers available for flight rendering");
        return;
    }

    console.log(`✈️ Rendering ${flights.length} flight markers...`);

    // Clear old flight markers
    flightMarkers.forEach(marker => {
        if (militaryAircraftLayer.hasLayer(marker) || civilianAircraftLayer.hasLayer(marker)) {
            militaryAircraftLayer.removeLayer(marker);
            civilianAircraftLayer.removeLayer(marker);
        }
    });
    flightMarkers = [];

    // Filter: Only show military and civilian aircraft (exclude cargo, private, etc.)
    const filteredFlights = flights.filter(flight => {
        if (!flight.lat || !flight.lon) return false;

        // Only show aircraft that are definitely military or civilian
        const callsign = (flight.callsign || '').toUpperCase();
        const icao = (flight.icao24 || '').toUpperCase();

        // Military aircraft indicators
        const isMilitary = flight.military === true ||
                          callsign.includes('AF') || // Air Force
                          callsign.includes('ARMY') ||
                          callsign.includes('NAVY') ||
                          callsign.match(/^[A-Z]{1,3}\d{2,4}$/) || // Military pattern like AF1, ARMY01
                          flight.squawk === '7700'; // Emergency military

        // Civilian aircraft indicators
        const isCivilian = flight.military === false ||
                          callsign.match(/^[A-Z]{2,3}\d{1,4}[A-Z]?$/) || // Airline format like UAL123, BA456A
                          flight.altitude > 20000; // High altitude civilian

        return isMilitary || isCivilian;
    });

    console.log(`✈️ Filtered to ${filteredFlights.length} military/civilian aircraft`);

    let militaryRendered = 0, civilianRendered = 0;

    filteredFlights.forEach(flight => {
        try {
            const isMilitary = flight.military === true ||
                             (flight.callsign || '').toUpperCase().includes('AF') ||
                             (flight.callsign || '').toUpperCase().includes('ARMY') ||
                             (flight.callsign || '').toUpperCase().includes('NAVY');

            const color = isMilitary ? "#ff3333" : "#0099ff";
            const icon = isMilitary ? "🎯" : "✈️";
            const layer = isMilitary ? militaryAircraftLayer : civilianAircraftLayer;

            // Debug: Check if layer is available
            if (!layer) {
                console.error(`❌ Layer not available for ${isMilitary ? 'military' : 'civilian'} aircraft`);
                return;
            }

            // Debug: Log first few aircraft
            if (filteredFlights.indexOf(flight) < 3) {
                console.log(`🔍 Aircraft sample:`, {
                    callsign: flight.callsign,
                    icao24: flight.icao24,
                    military: flight.military,
                    isMilitary: isMilitary,
                    lat: flight.lat,
                    lon: flight.lon,
                    layerType: isMilitary ? 'military' : 'civilian'
                });
            }

            // Calculate movement vector if we have previous position
            const flightId = flight.icao24 || flight.callsign;
            const currentPos = [flight.lat, flight.lon];
            const lastPos = lastPositions.get(flightId);
            let movementArrow = '';

            if (lastPos) {
                const deltaLat = flight.lat - lastPos[0];
                const deltaLon = flight.lon - lastPos[1];
                const distance = Math.sqrt(deltaLat * deltaLat + deltaLon * deltaLon);

                if (distance > 0.01) { // Significant movement
                    const heading = Math.atan2(deltaLon, deltaLat) * 180 / Math.PI;
                    movementArrow = getArrowForHeading(heading);
                }
            }

            // Store current position for next update
            lastPositions.set(flightId, currentPos);

            const marker = L.circleMarker(currentPos, {
                color: color,
                fillColor: color,
                fillOpacity: 0.8,
                radius: isMilitary ? 10 : 6,
                weight: 3
            });

            marker.bindPopup(`
                <div style="font-family: monospace; font-size: 12px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">
                        ${icon} ${flight.callsign || flight.icao24} ${movementArrow}
                    </div>
                    <div style="color: ${color}; font-size: 11px;">
                        ${isMilitary ? '🎯 MILITARY' : '✈️ CIVILIAN'}<br>
                        Alt: ${flight.altitude || 'N/A'}ft<br>
                        Speed: ${flight.velocity || 'N/A'} m/s<br>
                        ${flight.emergency ? '<span style="color: #ff0000;">⚠️ EMERGENCY</span>' : ''}
                        ${movementArrow ? `<br>Moving: ${movementArrow}` : ''}
                    </div>
                </div>
            `);

            marker.addTo(layer);
            flightMarkers.push(marker);

            if (isMilitary) militaryRendered++;
            else civilianRendered++;

            // Debug first few additions
            if (filteredFlights.indexOf(flight) < 3) {
                console.log(`✅ Added ${isMilitary ? 'military' : 'civilian'} marker for ${flight.callsign || flight.icao24}`);
            }

        } catch (error) {
            console.error("❌ Failed to render flight marker:", error, flight);
        }
    });

    console.log(`✅ Rendered ${militaryRendered} military + ${civilianRendered} civilian aircraft`);
}

/**
 * Get arrow symbol for movement direction
 */
function getArrowForHeading(heading) {
    const directions = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖'];
    const index = Math.round(((heading + 360) % 360) / 45) % 8;
    return directions[index];
}

/**
 * Render ship markers - ONLY oil tankers with dynamic movement
 */
function renderShipMarkers(ships) {
    const { map, oilTankerLayer } = window.FlashPointMap || {};
    if (!map || !oilTankerLayer) {
        console.error("❌ No map or oil tanker layer available for ship rendering");
        return;
    }

    console.log(`🚢 Rendering ${ships.length} ship markers...`);

    // Clear old ship markers
    shipMarkers.forEach(marker => {
        if (oilTankerLayer.hasLayer(marker)) {
            oilTankerLayer.removeLayer(marker);
        }
    });
    shipMarkers = [];

    // Filter: ONLY show oil tankers
    const oilTankers = ships.filter(ship => {
        if (!ship.lat || !ship.lon) return false;

        // Debug: Log first few ships to see data structure
        if (ships.indexOf(ship) < 3) {
            console.log("🔍 Ship data sample:", {
                name: ship.name,
                is_tanker: ship.is_tanker,
                vessel_type: ship.vessel_type,
                ship_type: ship.ship_type,
                mmsi: ship.mmsi
            });
        }

        // Multiple ways to detect oil tankers - made less strict
        const isTanker = ship.is_tanker === true ||
                        ship.is_tanker === 'true' ||
                        (ship.vessel_type && ship.vessel_type.toLowerCase().includes('tanker')) ||
                        (ship.name && ship.name.toLowerCase().includes('tanker')) ||
                        (ship.name && ship.name.toLowerCase().includes('crude')) ||
                        (ship.name && ship.name.toLowerCase().includes('oil')) ||
                        ship.ship_type === 80 || // IMO tanker code
                        ship.ship_type === 81 || // Chemical tanker
                        ship.ship_type === 82 ||   // LNG tanker
                        // Add more lenient detection
                        (ship.flag && ship.flag.toLowerCase() === 'liberia') || // Common tanker flag
                        (ship.speed !== undefined && ship.speed < 8); // Slow ships often tankers

        return isTanker;
    });

    console.log(`🛢️ Filtered to ${oilTankers.length} oil tankers out of ${ships.length} ships`);

    let rendered = 0;
    oilTankers.forEach(ship => {
        try {
            // Calculate movement vector if we have previous position
            const shipId = ship.mmsi || ship.name;
            const currentPos = [ship.lat, ship.lon];
            const lastPos = lastPositions.get(shipId);
            let movementArrow = '';

            if (lastPos) {
                const deltaLat = ship.lat - lastPos[0];
                const deltaLon = ship.lon - lastPos[1];
                const distance = Math.sqrt(deltaLat * deltaLat + deltaLon * deltaLon);

                if (distance > 0.005) { // Significant movement for ships (slower than aircraft)
                    const heading = Math.atan2(deltaLon, deltaLat) * 180 / Math.PI;
                    movementArrow = getArrowForHeading(heading);
                }
            }

            // Store current position for next update
            lastPositions.set(shipId, currentPos);

            // Determine tanker type and color
            let tankerType = 'OIL TANKER';
            let color = '#ff8800';

            if ((ship.name || '').toLowerCase().includes('crude')) {
                tankerType = 'CRUDE TANKER';
                color = '#cc4400';
            } else if ((ship.name || '').toLowerCase().includes('lng') || ship.ship_type === 82) {
                tankerType = 'LNG TANKER';
                color = '#00cc88';
            } else if (ship.ship_type === 81) {
                tankerType = 'CHEMICAL TANKER';
                color = '#cc0088';
            }

            const marker = L.circleMarker(currentPos, {
                color: color,
                fillColor: color,
                fillOpacity: 0.8,
                radius: 9,
                weight: 3
            });

            marker.bindPopup(`
                <div style="font-family: monospace; font-size: 12px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">
                        🛢️ ${ship.name || ship.mmsi} ${movementArrow}
                    </div>
                    <div style="color: ${color}; font-size: 11px;">
                        ${tankerType}<br>
                        Speed: ${ship.speed || 'N/A'} knots<br>
                        Course: ${ship.course || 'N/A'}°<br>
                        Flag: ${ship.flag || 'N/A'}<br>
                        ${movementArrow ? `Moving: ${movementArrow}` : 'Stationary'}
                    </div>
                </div>
            `);

            marker.addTo(oilTankerLayer);
            shipMarkers.push(marker);
            rendered++;

        } catch (error) {
            console.error("❌ Failed to render tanker marker:", error, ship);
        }
    });

    console.log(`✅ Rendered ${rendered} oil tanker markers`);
}

/**
 * Initialize tracking module with dynamic updates
 */
export function initTracking() {
    console.log("📡 Initializing enhanced flight & ship tracking...");

    // Wait longer for map layers to be ready
    setTimeout(() => {
        fetchFlights();
        fetchShips();
    }, 2000);

    // More frequent updates for dynamic tracking
    // Aircraft: every 30 seconds (they move fast)
    setInterval(fetchFlights, 30 * 1000);

    // Ships: every 2 minutes (they move slower)
    setInterval(fetchShips, 2 * 60 * 1000);

    console.log("✅ Dynamic tracking initialized:");
    console.log("  - Aircraft: 30s updates");
    console.log("  - Ships: 2min updates");
    console.log("  - Movement vectors enabled");
}

/**
 * Manual refresh functions for UI controls
 */
export function refreshFlights() {
    console.log("🔄 Manual flight refresh...");
    fetchFlights();
}

export function refreshShips() {
    console.log("🔄 Manual ship refresh...");
    fetchShips();
}

/**
 * Clear position history (useful for debugging)
 */
export function clearTrackingHistory() {
    lastPositions.clear();
    console.log("🗑️ Cleared movement tracking history");
}

/**
 * Get tracking statistics
 */
export function getTrackingStats() {
    const stats = window.FlashPointMap ? {
        militaryAircraft: window.FlashPointMap.militaryAircraftLayer ?
                         window.FlashPointMap.militaryAircraftLayer.getLayers().length : 0,
        civilianAircraft: window.FlashPointMap.civilianAircraftLayer ?
                         window.FlashPointMap.civilianAircraftLayer.getLayers().length : 0,
        oilTankers: window.FlashPointMap.oilTankerLayer ?
                   window.FlashPointMap.oilTankerLayer.getLayers().length : 0,
        trackedPositions: lastPositions.size
    } : {};

    console.log("📊 Tracking Stats:", stats);
    return stats;
}