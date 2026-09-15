import { getFavorites, logFavorite, removeFavorite } from "./api.js";
import { getDiaryDate, localToday } from "./diary-date.js";
import { readDateInput, setDateInput, validateDateInput } from "./date-input.js";
import { showToast } from "./feedback.js";

const list = document.getElementById("favorites-list");
const count = document.getElementById("favorites-count");
const dateInput = document.getElementById("favorites-date");
let loadVersion = 0;

function createCard(food) {
    const isCount = food.unit === "portion";
    const card = document.createElement("article");
    card.className = "panel favorite-card";
    const title = document.createElement("h2");
    title.textContent = food.food_name;
    const portion = document.createElement("p");
    portion.className = "panel-copy";
    const portionLabel = isCount ? `${food.quantity} ${food.quantity === 1 ? "portion" : "portions"}` : `${food.quantity} ${food.unit}`;
    portion.textContent = `${portionLabel} · ${food.source === "manual" ? "Manual entry" : "AI estimate"}`;
    const macros = document.createElement("p");
    macros.className = "favorite-macros";
    macros.textContent = `${food.calories} kcal · P ${food.protein}g · C ${food.carbs}g · F ${food.fat}g`;
    let weightInput;
    const weightField = document.createElement("div");
    if (food.quantity > 0) {
        weightField.className = "favorite-weight";
        const label = document.createElement("label");
        label.textContent = isCount ? "Quantity to add" : `Weight to add (${food.unit})`;
        weightInput = document.createElement("input");
        weightInput.id = `favorite-weight-${food.favorite_id}`;
        label.htmlFor = weightInput.id;
        weightInput.type = "number";
        weightInput.inputMode = isCount ? "numeric" : "decimal";
        weightInput.min = isCount ? "1" : "0";
        weightInput.max = "5000";
        weightInput.step = isCount ? "1" : "any";
        weightInput.required = true;
        weightInput.value = food.quantity;
        weightInput.setAttribute("aria-label", isCount ? `Quantity to add for ${food.food_name}` : `Weight to add for ${food.food_name} (${food.unit})`);
        macros.setAttribute("aria-live", "polite");
        const updateMacros = () => {
            const quantity = Number(weightInput.value);
            weightInput.setCustomValidity(weightInput.value !== "" && quantity <= 0 ? (isCount ? "Enter at least one portion." : "Enter a weight greater than zero.") : "");
            if (!weightInput.checkValidity()) {
                macros.textContent = isCount ? "Enter a whole number from 1 to 5,000 to preview macros." : "Enter a weight greater than 0 and up to 5,000 g to preview macros.";
                return;
            }
            const scaled = (key) => (food[key] * quantity / food.quantity).toLocaleString(undefined, { maximumFractionDigits: 1 });
            macros.textContent = `${scaled("calories")} kcal · P ${scaled("protein")}g · C ${scaled("carbs")}g · F ${scaled("fat")}g`;
        };
        weightInput.addEventListener("input", updateMacros);
        updateMacros();
        weightField.append(label, weightInput);
    }
    const actions = document.createElement("div");
    actions.className = "favorite-actions";
    const add = document.createElement("button");
    add.type = "button";
    add.className = "primary-button";
    add.textContent = "Add to selected day";
    add.setAttribute("aria-label", `Add ${food.food_name} to selected day`);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "favorite-button";
    remove.textContent = "Remove from favorites";
    remove.setAttribute("aria-label", `Remove ${food.food_name} from Favorites`);
    add.addEventListener("click", async () => {
        if (!validateDateInput(dateInput)) return;
        if (weightInput && !weightInput.reportValidity()) return;
        const quantity = weightInput ? Number(weightInput.value) : undefined;
        add.disabled = true;
        if (weightInput) weightInput.disabled = true;
        add.textContent = "Adding…";
        try {
            const data = await logFavorite(food.favorite_id, readDateInput(dateInput), quantity);
            showToast(data.message);
            document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            if (weightInput) weightInput.disabled = false;
            add.disabled = false;
            add.textContent = "Add to selected day";
        }
    });
    remove.addEventListener("click", async () => {
        remove.disabled = true;
        try {
            const data = await removeFavorite(food.favorite_id);
            await loadFavorites(false);
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
            remove.disabled = false;
        }
    });
    actions.append(add, remove);
    card.append(title, portion);
    if (weightInput) card.append(weightField);
    card.append(macros, actions);
    return card;
}

export async function loadFavorites(resetDate = true) {
    const version = ++loadVersion;
    if (resetDate) setDateInput(dateInput, getDiaryDate());
    count.textContent = "Loading…";
    list.replaceChildren();
    try {
        const data = await getFavorites();
        if (version !== loadVersion) return;
        count.textContent = `${data.favorites.length} ${data.favorites.length === 1 ? "favorite" : "favorites"}`;
        if (!data.favorites.length) {
            const empty = document.createElement("div");
            empty.className = "panel empty-state";
            empty.textContent = "No favorites yet. Choose ☆ Save beside any food in your diary or archive.";
            list.append(empty);
        }
        data.favorites.forEach((food) => list.append(createCard(food)));
    } catch (error) {
        if (version !== loadVersion) return;
        count.textContent = "Unavailable";
        list.textContent = "Could not load favorites. Open Favorites again to retry.";
        showToast(error.message, "error");
    }
}

export function initFavorites() {
    document.getElementById("favorites-today").addEventListener("click", () => {
        setDateInput(dateInput, localToday());
    });
}
