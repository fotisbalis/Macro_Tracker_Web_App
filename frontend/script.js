import { loadArchive } from "./js/archive.js";
import { initAISettings, loadAIStatus } from "./js/ai-settings.js";
import { showToast } from "./js/feedback.js";
import { initHome, loadToday } from "./js/home.js";
import { initNavigation, showPage } from "./js/navigation.js";
import { initProfileGate, showProfileGate, startProfileGate } from "./js/profile-gate.js";
import { initStatistics, loadStatistics } from "./js/statistics.js";
import { initTheme } from "./js/theme.js";
import { initUser, renderUser } from "./js/user.js";

initTheme();
initAISettings();
initHome();
initUser();
initStatistics();
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
        if (pageId === "statistics") loadStatistics();
    },
});

document.addEventListener("macrotrackerdatachange", () => loadToday().catch(() => {}));
document.addEventListener("macrotrackerswitchprofile", () => {
    showProfileGate({ clearSelection: true }).catch((error) => showToast(error.message, "error"));
});

try {
    await loadAIStatus().catch(() => {});
    await startProfileGate();
} catch (error) {
    showToast(error.message, "error");
}
