import { loadArchive } from "./js/archive.js";
import { getHealth } from "./js/api.js";
import { showToast } from "./js/feedback.js";
import { initHome, loadToday } from "./js/home.js";
import { initNavigation, showPage } from "./js/navigation.js";
import { initProfileGate, showProfileGate, startProfileGate } from "./js/profile-gate.js";
import { initTheme } from "./js/theme.js";
import { initUser, renderUser } from "./js/user.js";

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
initProfileGate({
    async onSelected(user) {
        await renderUser(user);
        window.location.hash = "#home";
        showPage("home");
        await loadToday();
    },
});
initNavigation({
    onNavigate(pageId) {
        if (pageId === "home") loadToday().catch(() => {});
        if (pageId === "archive") loadArchive();
    },
});

document.addEventListener("macrotrackerdatachange", () => loadToday().catch(() => {}));
document.addEventListener("macrotrackerswitchprofile", () => {
    showProfileGate({ clearSelection: true }).catch((error) => showToast(error.message, "error"));
});

try {
    await loadAIStatus();
    await startProfileGate();
} catch (error) {
    showToast(error.message, "error");
}
