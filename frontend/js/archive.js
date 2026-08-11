import { getArchive } from "./api.js";
import { showToast } from "./feedback.js";

const archiveList = document.getElementById("archive-list");

function formatDate(value) {
    return new Intl.DateTimeFormat(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" })
        .format(new Date(`${value}T12:00:00`));
}

function createDay(day) {
    const panel = document.createElement("article");
    panel.className = "panel archive-day";

    const header = document.createElement("button");
    header.type = "button";
    header.className = "archive-day-header";
    header.setAttribute("aria-expanded", "false");
    header.innerHTML = `
        <span><small>${formatDate(day.date)}</small><strong>${day.totals.calories} kcal</strong></span>
        <span class="archive-macros">
            <span><b>${day.totals.protein}g</b> Protein</span>
            <span><b>${day.totals.carbs}g</b> Carbs</span>
            <span><b>${day.totals.fat}g</b> Fat</span>
        </span>
        <span class="chevron">⌄</span>`;

    const details = document.createElement("div");
    details.className = "archive-details";
    details.hidden = true;
    day.entries.forEach((entry) => {
        const row = document.createElement("div");
        row.className = "archive-entry";
        const name = document.createElement("span");
        const sourceLabel = entry.source === "manual" ? "manual entry" : "mock estimate";
        name.innerHTML = `<strong></strong><small>${entry.quantity}${entry.unit} | ${sourceLabel}</small>`;
        name.querySelector("strong").textContent = entry.food_name;
        const macros = document.createElement("span");
        macros.textContent = `${entry.calories} kcal · P ${entry.protein}g · C ${entry.carbs}g · F ${entry.fat}g`;
        row.append(name, macros);
        details.append(row);
    });

    header.addEventListener("click", () => {
        details.hidden = !details.hidden;
        header.setAttribute("aria-expanded", String(!details.hidden));
        header.querySelector(".chevron").textContent = details.hidden ? "⌄" : "⌃";
    });
    panel.append(header, details);
    return panel;
}

export async function loadArchive() {
    archiveList.innerHTML = "<div class=\"panel empty-state\">Loading archive…</div>";
    try {
        const data = await getArchive();
        archiveList.replaceChildren();
        if (!data.days.length) {
            archiveList.innerHTML = "<div class=\"panel empty-state\"><strong>Your archive is empty.</strong><span>Log a food on Home to begin.</span></div>";
            return;
        }
        data.days.forEach((day) => archiveList.append(createDay(day)));
    } catch (error) {
        showToast(error.message, "error");
    }
}
