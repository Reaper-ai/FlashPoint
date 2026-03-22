/**
 * conflicts.js - Global conflict tracker integration with better timing
 */

import { API_BASE, ENDPOINTS } from './utils.js';
import { renderConflictMarkers } from './map.js';

/**
 * Fetch and render conflicts with retry logic
 */
async function fetchConflicts() {
    try {
        console.log("🔴 Fetching conflicts...");
        const resp = await fetch(`${API_BASE}${ENDPOINTS.conflicts}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const data = await resp.json();

        if (data.success && data.conflicts) {
            console.log(`🔴 Received ${data.conflicts.length} conflicts`);

            // Wait for map to be ready, then render
            waitForMapAndRender(data.conflicts);
        } else {
            console.log("⚠️ No conflicts in response");
        }

    } catch (err) {
        console.error("Failed to fetch conflicts:", err);
    }
}

/**
 * Wait for map to be ready, then render conflicts
 */
function waitForMapAndRender(conflicts) {
    const maxAttempts = 10;
    let attempts = 0;

    function tryRender() {
        attempts++;

        // Check if map globals and conflict layer are available
        const { map, conflictLayer } = window.FlashPointMap || {};

        if (map && conflictLayer) {
            console.log("🔴 Map and conflict layer ready, rendering conflicts...");
            renderConflictMarkers(conflicts);
            return;
        }

        if (attempts < maxAttempts) {
            console.log(`🔴 Map not ready, attempt ${attempts}/${maxAttempts}, retrying...`);
            setTimeout(tryRender, 500);
        } else {
            console.error("❌ Failed to render conflicts - map not ready after all attempts");
        }
    }

    tryRender();
}

/**
 * Initialize conflicts module
 */
export function initConflicts() {
    console.log("⚔️ Initializing conflicts tracker...");

    // Wait a bit longer for map initialization
    setTimeout(() => {
        fetchConflicts();
    }, 1500);

    // Refresh every 12 hours
    setInterval(fetchConflicts, 12 * 60 * 60 * 1000);

    console.log("⚔️ Conflicts tracker initialized");
}
