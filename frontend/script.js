import { loadArchive } from "./js/archive.js";
import { showToast } from "./js/feedback.js";
import { initHome, loadToday } from "./js/home.js";
import { initNavigation } from "./js/navigation.js";
import { initTheme } from "./js/theme.js";
import { initUser, loadUser } from "./js/user.js";

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
    await loadUser();
    await loadToday();
    if (window.location.hash === "#archive") await loadArchive();
} catch (error) {
    showToast(error.message, "error");
}

