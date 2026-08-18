import { getPeriodStatistics } from "./api.js";
import { showToast } from "./feedback.js";

const rangeButtons = document.querySelectorAll("[data-stat-range]");
const customForm = document.getElementById("custom-date-range-form");
const startInputs = [
    document.getElementById("statistics-start-day"),
    document.getElementById("statistics-start-month"),
    document.getElementById("statistics-start-year"),
];
const endInputs = [
    document.getElementById("statistics-end-day"),
    document.getElementById("statistics-end-month"),
    document.getElementById("statistics-end-year"),
];
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

function europeanDateParts(isoValue) {
    const [year, month, day] = isoValue.split("-");
    return [day, month, year];
}

function parseEuropeanDate(parts) {
    const [day, month, year] = parts.map((input) => input.value.trim());
    if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) return null;
    const paddedDay = day.padStart(2, "0");
    const paddedMonth = month.padStart(2, "0");
    const parsed = new Date(Number(year), Number(paddedMonth) - 1, Number(paddedDay), 12);
    if (
        parsed.getFullYear() !== Number(year)
        || parsed.getMonth() !== Number(paddedMonth) - 1
        || parsed.getDate() !== Number(paddedDay)
    ) return null;
    return `${parsed.getFullYear()}-${paddedMonth}-${paddedDay}`;
}

function selectedDates() {
    if (selectedRange === "month") return { start: dateDaysAgo(29), end: dateDaysAgo(0) };
    if (selectedRange === "custom") {
        return {
            start: parseEuropeanDate(startInputs),
            end: parseEuropeanDate(endInputs),
        };
    }
    return { start: dateDaysAgo(6), end: dateDaysAgo(0) };
}

function formatDate(value) {
    return europeanDateParts(value).join("/");
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
    const { start, end } = selectedDates();
    if (!start || !end) {
        showToast("Use the date format DD/MM/YYYY", "error");
        return;
    }
    if (start > end) {
        showToast("Choose an end date after the start date", "error");
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
    europeanDateParts(dateDaysAgo(6)).forEach((value, index) => { startInputs[index].value = value; });
    europeanDateParts(dateDaysAgo(0)).forEach((value, index) => { endInputs[index].value = value; });
    updateRangeControls();

    [startInputs, endInputs].forEach((inputs) => {
        inputs.forEach((input, index) => {
            input.addEventListener("input", () => {
                const maximumLength = index === 2 ? 4 : 2;
                input.value = input.value.replace(/\D/g, "").slice(0, maximumLength);
                if (input.value.length === maximumLength) inputs[index + 1]?.focus();
            });
            input.addEventListener("keydown", (event) => {
                if (event.key === "Backspace" && !input.value) inputs[index - 1]?.focus();
            });
            if (index < 2) {
                input.addEventListener("blur", () => {
                    if (/^\d$/.test(input.value)) input.value = input.value.padStart(2, "0");
                });
            }
        });
    });

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
