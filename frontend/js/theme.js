import { THEME_KEY } from "./config.js";

export function initTheme() {
    const button = document.getElementById("theme-toggle");

    function updateButton() {
        const isDark = document.documentElement.dataset.theme === "dark";
        button.setAttribute("aria-checked", String(isDark));
        button.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
    }

    updateButton();
    button.addEventListener("click", () => {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = next;
        localStorage.setItem(THEME_KEY, next);
        updateButton();
    });
}

