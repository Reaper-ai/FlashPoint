import { updateClock } from './js/utils.js?v=3';
import { initFeed } from './js/feed.js?v=3';
import { initMap } from './js/map.js?v=3';
import { initChat } from './js/chat.js?v=3';
import { initCommodities } from './js/commodities.js?v=3';
import { initConflicts } from './js/conflicts.js?v=3';
import { initReports } from './js/reports.js?v=3';
import { initTracking } from './js/tracking.js?v=3';
import { initTestData } from './js/test-data.js?v=3';
import './js/debug.js?v=3'; // Load debug commands

function init() {
    console.log("🚀 Starting FlashPoint initialization...");

    updateClock();
    setInterval(updateClock, 1000);

    // Initialize map first
    console.log("🗺️ Initializing map...");
    const mapReady = initMap();

    console.log("🗺️ Map ready:", mapReady);

    if (mapReady) {
        // Wait a bit for map to fully initialize, then load data
        setTimeout(() => {
            console.log("📡 Loading data modules...");
            initFeed();
            initConflicts();
            initTracking();  // Load flights & ships

            // Add test data for immediate visualization
            initTestData();
        }, 1000);
    } else {
        console.error("❌ Map initialization failed - skipping data loading");
    }

    // Initialize other modules
    initChat();
    initCommodities();
    initReports();

    console.log("✅ FlashPoint operational");
    console.log("🔧 Debug commands available: FlashPointDebug.checkMap()");
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
