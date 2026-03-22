/**
 * reports.js - SITREP generation module
 */

import { API_BASE, ENDPOINTS, showNotification } from './utils.js';

let latestReport = null;

/**
 * Generate report (text)
 */
async function generateReport() {
    const btn = document.getElementById("generate-report-btn");
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = "⏳ Generating...";
    showNotification("Generating SITREP...", "info");

    try {
        const resp = await fetch(`${API_BASE}${ENDPOINTS.report}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const data = await resp.json();
        latestReport = data.report;

        // Show report section and populate preview
        const reportSection = document.getElementById("report-section");
        const reportPreview = document.getElementById("report-preview");

        if (reportSection) reportSection.classList.remove("hidden");
        if (reportPreview) reportPreview.value = latestReport;

        showNotification("SITREP generated successfully", "success");
        console.log("✅ Report generated");

    } catch (err) {
        console.error("Report generation failed:", err);
        showNotification(`Failed to generate report: ${err.message}`, "error");

    } finally {
        btn.disabled = false;
        btn.textContent = "GENERATE REPORT";
    }
}

/**
 * Download report as PDF
 */
async function downloadPDF() {
    const btn = document.getElementById("download-pdf-btn");
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = "⏳ Generating PDF...";
    showNotification("Generating PDF...", "info");

    try {
        const resp = await fetch(`${API_BASE}${ENDPOINTS.report_pdf}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement("a");
        a.href = url;
        a.download = `SITREP_${new Date().toISOString().split('T')[0]}.pdf`;
        a.click();
        
        URL.revokeObjectURL(url);
        showNotification("PDF downloaded", "success");
        console.log("✅ PDF downloaded");

    } catch (err) {
        console.error("PDF generation failed:", err);
        showNotification(`Failed to generate PDF: ${err.message}`, "error");

    } finally {
        btn.disabled = false;
        btn.textContent = "⬇ DOWNLOAD PDF";
    }
}

/**
 * Initialize reports module
 */
export function initReports() {
    const reportBtn = document.getElementById("generate-report-btn");
    const pdfBtn = document.getElementById("download-pdf-btn");

    if (reportBtn) {
        reportBtn.addEventListener("click", generateReport);
    }

    if (pdfBtn) {
        pdfBtn.addEventListener("click", downloadPDF);
    }

    console.log("📊 Reports module initialized");
}

/**
 * Get latest report
 */
export function getLatestReport() {
    return latestReport;
}
