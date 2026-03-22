/**
 * feed.js - Optimized real-time event feed via SSE
 */

import { API_BASE, ENDPOINTS, biasClass, escapeHTML } from './utils.js';
import { updateMapHotspot } from './map.js';

let feedItems = [];
let eventSource = null;
const pendingCards = [];
let renderScheduled = false;

/**
 * Build a feed card DOM element
 */
function buildFeedCard(item, isNew = false) {
    const bias = item.bias || "Neutral";
    const src = item.source || "UNKNOWN";
    const text = item.text || "";
    const place = item.place ? ` • ${item.place}` : "";
    const cls = `cyber-card ${biasClass(bias)}${isNew ? " feed-card--new" : ""}`.trim();

    const card = document.createElement("div");
    card.className = cls;
    card.innerHTML = `
        <div class="feed-source">${escapeHTML(src)} &bull; <span class="bias-tag">${escapeHTML(bias)}</span>${escapeHTML(place)}</div>
        <div class="feed-text">${escapeHTML(text)}</div>
    `;
    return card;
}

/**
 * Batch render pending cards using requestAnimationFrame
 */
function scheduleBatchRender() {
    if (renderScheduled || pendingCards.length === 0) return;

    renderScheduled = true;
    requestAnimationFrame(() => {
        renderPendingCards();
        renderScheduled = false;
    });
}

/**
 * Render all pending cards in one batch
 */
function renderPendingCards() {
    if (pendingCards.length === 0) return;

    const container = document.getElementById("feed-container");
    if (!container) return;

    const fragment = document.createDocumentFragment();
    const batch = pendingCards.splice(0, 10); // Process max 10 at a time

    batch.forEach(item => {
        const card = buildFeedCard(item, true);
        fragment.appendChild(card);
        feedItems.unshift(item);

        // Update map with retry logic
        if (item.lat && item.lon) {
            waitForMapAndRenderHotspot(item);
        }
    });

    // Add all cards at once
    if (container.firstChild) {
        container.insertBefore(fragment, container.firstChild);
    } else {
        container.appendChild(fragment);
    }

    // Limit displayed cards to 100
    const cards = container.querySelectorAll(".cyber-card");
    if (cards.length > 100) {
        for (let i = 100; i < cards.length; i++) {
            cards[i].remove();
        }
    }

    // If more pending, schedule next batch
    if (pendingCards.length > 0) {
        scheduleBatchRender();
    }
}

/**
 * Queue new event card for batch rendering
 */
function queueFeedCard(item) {
    pendingCards.push(item);
    scheduleBatchRender();
}

/**
 * Wait for map and render hotspot with retry logic
 */
function waitForMapAndRenderHotspot(item) {
    const maxAttempts = 10;
    let attempts = 0;

    function tryRender() {
        attempts++;
        const { map, hotspotLayer } = window.FlashPointMap || {};

        if (map && hotspotLayer) {
            console.log("📍 Map and hotspot layer ready, rendering hotspot marker...");
            updateMapHotspot(item);
            return;
        }

        if (attempts < maxAttempts) {
            console.log(`📍 Map/hotspot layer not ready, attempt ${attempts}/${maxAttempts}`);
            setTimeout(tryRender, 500);
        } else {
            console.error("❌ Failed to render hotspot - map/hotspot layer not ready");
        }
    }

    tryRender();
}

/**
 * Load initial events from PostgreSQL
 */
async function loadInitialEvents() {
    try {
        const resp = await fetch(`${API_BASE}${ENDPOINTS.events_recent}?limit=50`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || "Failed to load events");

        const container = document.getElementById("feed-container");
        if (!container) return;

        container.innerHTML = ""; // Clear placeholder

        // Render in reverse (oldest first, newest at top)
        data.events.reverse().forEach(event => {
            const card = buildFeedCard(event);
            container.appendChild(card);
            feedItems.push(event);

            // Update map hotspot for initial events with retry logic
            if (event.lat && event.lon) {
                waitForMapAndRenderHotspot(event);
            }
        });

        console.log(`✅ Loaded ${data.count} initial events`);
        
    } catch (err) {
        console.error("Failed to load initial events:", err);
        document.getElementById("feed-container").innerHTML = `
            <div class="cyber-card alert-card">
                <strong>⚠️ Feed Offline</strong><br>
                Unable to load events: ${err.message}
            </div>
        `;
    }
}

/**
 * Initialize SSE connection for real-time updates
 */
function connectSSE() {
    if (eventSource) {
        eventSource.close();
    }

    const url = `${API_BASE}${ENDPOINTS.events_stream}`;
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
        console.log("✅ SSE connected");
    };

    eventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);

            // Ignore duplicates
            if (feedItems.some(item => item.id === data.id)) {
                return;
            }

            // Queue for batch rendering
            queueFeedCard(data);

        } catch (err) {
            console.error("SSE parse error:", err);
        }
    };

    eventSource.onerror = (err) => {
        console.error("❌ SSE error:", err);
        eventSource.close();
        
        // Reconnect after 5 seconds
        setTimeout(() => {
            console.log("🔄 Reconnecting SSE...");
            connectSSE();
        }, 5000);
    };
}

/**
 * Initialize feed module
 */
export function initFeed() {
    console.log("📡 Initializing feed...");
    loadInitialEvents().then(() => {
        connectSSE();
    });
}

/**
 * Get current feed items
 */
export function getFeedItems() {
    return feedItems;
}

/**
 * Cleanup
 */
export function disconnectFeed() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}
