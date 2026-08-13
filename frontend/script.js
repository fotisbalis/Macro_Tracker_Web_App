import { loadArchive } from "./js/archive.js";
import { getHealth } from "./js/api.js";
import { showToast } from "./js/feedback.js";
import { initHome, loadToday } from "./js/home.js";
import { initNavigation } from "./js/navigation.js";
import { initTheme } from "./js/theme.js";
import { initUser, loadUser } from "./js/user.js";

const providerLabel = document.getElementById("ai-provider-label");

async function loadAIStatus() {
    try {
        const health = await getHealth();
        providerLabel.textContent = health.ai_provider === "qwen"
            ? "Qwen AI active"
            : "Mock AI active";
    } catch (_error) {
        providerLabel.textContent = "AI status unavailable";
    }
}

initTheme();
initHome();
initUser();
initNavigation({
    onNavigate(pageId) {
        if (pageId === "home") loadToday().catch(() => {});
        if (pageId === "archive") loadArchive();
        if (pageId === "user") loadUser().catch((error) => showToast(error.message, "error"));
    },
});

document.addEventListener("macrotrackerdatachange", () => loadToday().catch(() => {}));

try {
    await loadAIStatus();
    await loadUser();
    await loadToday();
    if (window.location.hash === "#archive") await loadArchive();
} catch (error) {
    showToast(error.message, "error");
}
