import { addManualFood, analyzeFood, deleteFood, getToday } from "./api.js";
import { showToast } from "./feedback.js";

const macroSummary = document.getElementById("macro-summary");
const entriesContainer = document.getElementById("today-entries");
const entryCount = document.getElementById("entry-count");
const todayLabel = document.getElementById("today-label");
const form = document.getElementById("food-form");
const analyzeButton = document.getElementById("analyze-button");
const latestResult = document.getElementById("latest-result");
const foodNameInput = document.getElementById("food-name");
const quantityInput = document.getElementById("food-quantity");
const manualToggle = document.getElementById("manual-entry-toggle");
const manualPanel = document.getElementById("manual-macro-panel");
const manualInputs = [
    document.getElementById("manual-calories"),
    document.getElementById("manual-protein"),
    document.getElementById("manual-carbs"),
    document.getElementById("manual-fat"),
];
let manualMode = false;

const macroConfig = [
    ["calories", "Calories", "kcal"],
    ["protein", "Protein", "g"],
    ["carbs", "Carbs", "g"],
    ["fat", "Fat", "g"],
];

function formatDate(value) {
    return new Intl.DateTimeFormat(undefined, { weekday: "long", day: "numeric", month: "long" })
        .format(new Date(`${value}T12:00:00`));
}

function renderSummary(totals, targets) {
    macroSummary.replaceChildren();
    macroConfig.forEach(([key, label, unit]) => {
        const value = totals[key] || 0;
        const target = targets[key] || 0;
        const percent = target ? Math.min((value / target) * 100, 100) : 0;
        const card = document.createElement("article");
        card.className = `macro-card macro-${key}`;
        card.innerHTML = `
            <div class="macro-card-top"><span>${label}</span><span>${Math.round(percent)}%</span></div>
            <p><strong>${value.toLocaleString()}</strong><span> / ${target.toLocaleString()} ${unit}</span></p>
            <div class="progress-track"><span style="width:${percent}%"></span></div>`;
        macroSummary.append(card);
    });
}

function metric(label, value, unit) {
    const item = document.createElement("span");
    item.innerHTML = `<strong>${value}</strong> ${unit}<small>${label}</small>`;
    return item;
}

function createEntryCard(entry) {
    const card = document.createElement("article");
    card.className = "food-entry";

    const identity = document.createElement("div");
    identity.className = "food-identity";
    const initial = document.createElement("span");
    initial.className = "food-initial";
    initial.textContent = entry.food_name.charAt(0).toUpperCase();
    const text = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = entry.food_name;
    title.title = entry.food_name;
    const subtitle = document.createElement("p");
    const sourceLabel = entry.source === "manual" ? "manual entry" : "mock estimate";
    subtitle.textContent = `${entry.quantity} ${entry.unit} | ${sourceLabel}`;
    text.append(title, subtitle);
    identity.append(initial, text);

    const metrics = document.createElement("div");
    metrics.className = "entry-metrics";
    metrics.append(
        metric("kcal", entry.calories, ""),
        metric("protein", entry.protein, "g"),
        metric("carbs", entry.carbs, "g"),
        metric("fat", entry.fat, "g"),
    );

    const remove = document.createElement("button");
    remove.className = "remove-button";
    remove.type = "button";
    remove.dataset.entryId = entry.entry_id;
    remove.setAttribute("aria-label", `Remove ${entry.food_name}`);
    remove.textContent = "×";
    card.append(identity, metrics, remove);
    return card;
}

function renderEntries(entries) {
    entriesContainer.replaceChildren();
    entryCount.textContent = `${entries.length} ${entries.length === 1 ? "entry" : "entries"}`;
    if (!entries.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state entry-empty";
        empty.innerHTML = "<strong>No foods logged yet.</strong><span>Your first entry will appear here.</span>";
        entriesContainer.append(empty);
        return;
    }
    entries.forEach((entry) => entriesContainer.append(createEntryCard(entry)));
}

export async function loadToday() {
    try {
        const data = await getToday();
        todayLabel.textContent = formatDate(data.date);
        renderSummary(data.totals, data.targets);
        renderEntries(data.entries);
        return data;
    } catch (error) {
        entriesContainer.innerHTML = `<p class="empty-state">${error.message}</p>`;
        throw error;
    }
}

function showLatest(entry) {
    latestResult.hidden = false;
    latestResult.innerHTML = `
        <span class="result-check">✓</span>
        <div><strong>${entry.calories} kcal added</strong><p>${entry.protein}g protein · ${entry.carbs}g carbs · ${entry.fat}g fat</p></div>`;
}

function setManualMode(enabled) {
    manualMode = enabled;
    manualPanel.hidden = !enabled;
    manualToggle.setAttribute("aria-expanded", String(enabled));
    manualToggle.querySelector(".manual-toggle-icon").textContent = enabled ? "−" : "+";
    foodNameInput.required = !enabled;
    quantityInput.required = !enabled;
    quantityInput.min = enabled ? "0" : "1";
    manualInputs.forEach((input) => {
        input.disabled = !enabled;
        input.required = enabled;
    });
    analyzeButton.querySelector("span").textContent = enabled ? "Add manual meal" : "Calculate and add";
}

export function initHome() {
    manualToggle.addEventListener("click", () => setManualMode(!manualMode));

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        analyzeButton.disabled = true;
        analyzeButton.querySelector("span").textContent = manualMode ? "Adding meal..." : "Calculating...";
        try {
            const data = manualMode
                ? await addManualFood({
                    food_name: foodNameInput.value.trim() || null,
                    quantity: quantityInput.value === "" ? 0 : Number(quantityInput.value),
                    calories: Number(manualInputs[0].value),
                    protein: Number(manualInputs[1].value),
                    carbs: Number(manualInputs[2].value),
                    fat: Number(manualInputs[3].value),
                })
                : await analyzeFood({
                    food_name: foodNameInput.value,
                    quantity: Number(quantityInput.value),
                });
            showLatest(data.entry);
            form.reset();
            setManualMode(false);
            await loadToday();
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            analyzeButton.disabled = false;
            analyzeButton.querySelector("span").textContent = manualMode ? "Add manual meal" : "Calculate and add";
        }
    });

    entriesContainer.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-entry-id]");
        if (!button) return;
        button.disabled = true;
        try {
            await deleteFood(button.dataset.entryId);
            await loadToday();
            showToast("Food removed");
        } catch (error) {
            showToast(error.message, "error");
            button.disabled = false;
        }
    });
}
