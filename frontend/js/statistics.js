import { getPeriodStatistics } from "./api.js";
import { showToast } from "./feedback.js";
import { localToday, formatDate } from "./diary-date.js";
import { readDateInput, setDateInput, validateDateInput } from "./date-input.js";

const rangeButtons = document.querySelectorAll("[data-stat-range]");
const customForm = document.getElementById("custom-date-range-form");
const startInput = document.getElementById("statistics-start-date");
const endInput = document.getElementById("statistics-end-date");
const periodLabel = document.getElementById("statistics-period");
const summary = document.getElementById("statistics-summary");
const detail = document.getElementById("statistics-detail");
let selectedRange = "week";

const macroConfig = [
    ["calories", "Calories", "kcal"],
    ["protein", "Protein", "g"],
    ["carbs", "Carbs", "g"],
    ["fat", "Fat", "g"],
];

function isoDate(value) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function dateDaysAgo(days) {
    const value = new Date();
    value.setHours(12, 0, 0, 0);
    value.setDate(value.getDate() - days);
    return isoDate(value);
}

function selectedDates() {
    if (selectedRange === "month") return { start: dateDaysAgo(29), end: dateDaysAgo(0) };
    if (selectedRange === "custom") {
        return {
            start: readDateInput(startInput),
            end: readDateInput(endInput),
        };
    }
    return { start: dateDaysAgo(6), end: dateDaysAgo(0) };
}

function renderSummary(data) {
    summary.replaceChildren();
    macroConfig.forEach(([key, label, unit]) => {
        const card = document.createElement("article");
        card.className = `macro-card macro-${key} statistics-card`;
        card.innerHTML = `
            <div class="macro-card-top"><span>Average ${label}</span></div>
            <p><strong>${data.daily_averages[key].toLocaleString()}</strong><span> ${unit}</span></p>
            <small>per tracked day</small>`;
        summary.append(card);
    });

    periodLabel.textContent = `${formatDate(data.start_date)} – ${formatDate(data.end_date)}`;
    detail.textContent = data.tracked_days
        ? `${data.entry_count} foods logged across ${data.tracked_days} ${data.tracked_days === 1 ? "day" : "days"}.`
        : "No foods were logged in this period.";
}

function updateRangeControls() {
    rangeButtons.forEach((button) => {
        const isSelected = button.dataset.statRange === selectedRange;
        button.classList.toggle("active", isSelected);
        button.setAttribute("aria-pressed", String(isSelected));
    });
    customForm.hidden = selectedRange !== "custom";
}

export async function loadStatistics() {
    if (selectedRange === "custom" && (!validateDateInput(startInput) || !validateDateInput(endInput))) return;
    const { start, end } = selectedDates();
    if (!start || !end) {
        showToast("Choose a start and end date", "error");
        return;
    }
    if (start > end) {
        showToast("Choose an end date on or after the start date", "error");
        return;
    }

    detail.textContent = "Loading statistics…";
    try {
        renderSummary(await getPeriodStatistics(start, end));
    } catch (error) {
        detail.textContent = "Statistics unavailable.";
        showToast(error.message, "error");
    }
}

export function initStatistics() {
    setDateInput(startInput, dateDaysAgo(6));
    setDateInput(endInput, localToday());
    updateRangeControls();

    rangeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectedRange = button.dataset.statRange;
            updateRangeControls();
            loadStatistics();
        });
    });

    customForm.addEventListener("submit", (event) => {
        event.preventDefault();
        loadStatistics();
    });
}
