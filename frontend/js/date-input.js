import { formatDate, localToday, parseDate } from "./diary-date.js";

const calendars = new WeakMap();

export const readDateInput = (input) => parseDate(input.value);

function updateValidity(input) {
    const value = readDateInput(input);
    input.setCustomValidity(!value ? "Enter a valid date as DD/MM/YYYY." : value > localToday() ? "Choose today or a previous date." : "");
    return value;
}

export function setDateInput(input, value) {
    input.value = formatDate(value);
    updateValidity(input);
    const calendar = calendars.get(input);
    if (calendar) {
        calendar.max = localToday();
        calendar.value = value || "";
    }
}

export function validateDateInput(input) {
    updateValidity(input);
    return input.reportValidity();
}

export function initDateInputs() {
    document.querySelectorAll('input[type="date"]').forEach((input) => {
        const initial = input.value;
        const label = input.labels?.[0]?.textContent.trim() || "date";
        const wrapper = document.createElement("div");
        wrapper.className = "date-picker";
        input.before(wrapper);
        wrapper.append(input);
        input.type = "text";
        input.placeholder = "DD/MM/YYYY";
        input.maxLength = 10;
        input.autocomplete = "off";
        input.setAttribute("aria-label", label);
        input.setAttribute("aria-description", "Date in DD/MM/YYYY format");

        const calendar = document.createElement("input");
        calendar.type = "date";
        calendar.className = "date-picker-native";
        calendar.tabIndex = -1;
        calendar.setAttribute("aria-hidden", "true");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "date-picker-button";
        button.setAttribute("aria-label", `Open calendar for ${label}`);
        button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 11h18"/></svg>';
        wrapper.append(calendar, button);
        calendars.set(input, calendar);
        const syncDisabled = () => {
            calendar.disabled = input.disabled;
            button.disabled = input.disabled;
        };
        new MutationObserver(syncDisabled).observe(input, { attributes: true, attributeFilter: ["disabled"] });
        syncDisabled();
        input.addEventListener("input", () => {
            const value = updateValidity(input);
            calendar.value = value || "";
        });
        button.addEventListener("click", () => {
            calendar.max = localToday();
            calendar.value = readDateInput(input) || localToday();
            if (calendar.showPicker) calendar.showPicker();
            else calendar.click();
        });
        calendar.addEventListener("change", () => {
            setDateInput(input, calendar.value);
            input.dispatchEvent(new Event("change", { bubbles: true }));
            input.focus();
        });
        setDateInput(input, initial);
    });
}
