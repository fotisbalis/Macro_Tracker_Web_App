import { saveFavorite } from "./api.js";
import { showToast } from "./feedback.js";

export function createFavoriteButton(entry) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "favorite-button";
    button.textContent = "☆ Save";
    button.setAttribute("aria-label", `Save ${entry.food_name} to Favorites`);
    button.addEventListener("click", async () => {
        button.disabled = true;
        try {
            const data = await saveFavorite(entry.entry_id);
            button.textContent = "★ Saved";
            button.setAttribute("aria-label", `${entry.food_name} saved to Favorites`);
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
            button.disabled = false;
        }
    });
    return button;
}
