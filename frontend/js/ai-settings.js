import { getAIStatus, removeOpenAIKey, saveOpenAIKey } from "./api.js";
import { showToast } from "./feedback.js";

const settingsButton = document.getElementById("ai-settings-button");
const providerLabel = document.getElementById("ai-provider-label");
const dialog = document.getElementById("ai-settings-dialog");
const form = document.getElementById("ai-settings-form");
const apiKeyInput = document.getElementById("openai-api-key");
const visibilityButton = document.getElementById("api-key-visibility");
const saveButton = document.getElementById("save-api-key");
const removeButton = document.getElementById("remove-api-key");
const closeButtons = [
    document.getElementById("ai-settings-close"),
    document.getElementById("cancel-ai-settings"),
];

let aiActive = false;

function renderStatus(status) {
    aiActive = Boolean(status.active);
    settingsButton.classList.toggle("active", aiActive);
    settingsButton.classList.toggle("inactive", !aiActive);
    removeButton.hidden = !aiActive;
    saveButton.textContent = aiActive ? "Update key" : "Save key";

    if (!status.storage_available) {
        providerLabel.textContent = "AI setup unavailable";
        settingsButton.disabled = true;
        return;
    }

    settingsButton.disabled = false;
    providerLabel.textContent = aiActive ? "OpenAI active" : "Set up AI";
}

export async function loadAIStatus() {
    try {
        const status = await getAIStatus();
        renderStatus(status);
        return status;
    } catch (_error) {
        providerLabel.textContent = "AI status unavailable";
        settingsButton.classList.remove("active", "inactive");
        throw _error;
    }
}

export function openAISettings() {
    if (settingsButton.disabled) return;
    apiKeyInput.value = "";
    apiKeyInput.type = "password";
    visibilityButton.textContent = "Show";
    visibilityButton.setAttribute("aria-label", "Show API key");
    dialog.showModal();
    window.setTimeout(() => apiKeyInput.focus(), 0);
}

function closeAISettings() {
    dialog.close();
    apiKeyInput.value = "";
}

export function initAISettings() {
    settingsButton.addEventListener("click", openAISettings);
    closeButtons.forEach((button) => button.addEventListener("click", closeAISettings));

    visibilityButton.addEventListener("click", () => {
        const reveal = apiKeyInput.type === "password";
        apiKeyInput.type = reveal ? "text" : "password";
        visibilityButton.textContent = reveal ? "Hide" : "Show";
        visibilityButton.setAttribute("aria-label", `${reveal ? "Hide" : "Show"} API key`);
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) closeAISettings();
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        saveButton.disabled = true;
        saveButton.textContent = "Saving...";
        try {
            const data = await saveOpenAIKey(apiKeyInput.value);
            await loadAIStatus();
            closeAISettings();
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = aiActive ? "Update key" : "Save key";
        }
    });

    removeButton.addEventListener("click", async () => {
        removeButton.disabled = true;
        try {
            const data = await removeOpenAIKey();
            await loadAIStatus();
            closeAISettings();
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            removeButton.disabled = false;
        }
    });

    document.addEventListener("macrotrackeropenaisettings", openAISettings);
}
