import { getUserStatistics, updateTargets } from "./api.js";
import { showToast } from "./feedback.js";
import { setCurrentProfile } from "./profile.js";

function fillTargets(targets) {
    document.getElementById("target-calories").value = targets.calories;
    document.getElementById("target-protein").value = targets.protein;
    document.getElementById("target-carbs").value = targets.carbs;
    document.getElementById("target-fat").value = targets.fat;
}

async function renderStatistics() {
    const data = await getUserStatistics();
    const container = document.getElementById("profile-stats");
    container.innerHTML = `
        <span><strong>${data.day_count}</strong><small>days tracked</small></span>
        <span><strong>${data.entry_count}</strong><small>foods logged</small></span>
        <span><strong>${data.average_daily_calories}</strong><small>avg kcal/day</small></span>`;
}

export async function renderUser(user) {
    setCurrentProfile(user);
    document.getElementById("user-type-badge").textContent = "Local user";
    document.getElementById("profile-name").textContent = user.user_name;
    fillTargets(user.targets);
    try {
        await renderStatistics();
    } catch (_error) {
        document.getElementById("profile-stats").textContent = "Statistics unavailable.";
    }
}

export function initUser() {
    document.getElementById("switch-profile-button").addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("macrotrackerswitchprofile"));
    });

    document.getElementById("targets-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = event.currentTarget.querySelector("button[type=submit]");
        button.disabled = true;
        try {
            const data = await updateTargets({
                calorie_target: Number(document.getElementById("target-calories").value),
                protein_target: Number(document.getElementById("target-protein").value),
                carbs_target: Number(document.getElementById("target-carbs").value),
                fat_target: Number(document.getElementById("target-fat").value),
            });
            showToast(data.message);
            document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            button.disabled = false;
        }
    });
}
