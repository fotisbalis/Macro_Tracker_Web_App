import { createProfile, deselectProfile, getProfiles, selectProfile } from "./api.js";
import { showToast } from "./feedback.js";
import { setCurrentProfile } from "./profile.js";

const gate = document.getElementById("profile-gate");
const navbar = document.getElementById("app-navbar");
const appShell = document.getElementById("app-shell");
const profileList = document.getElementById("profile-list");
const profileCount = document.getElementById("profile-count");
const createForm = document.getElementById("create-profile-form");
const nameInput = document.getElementById("new-profile-name");
let onProfileSelected = null;

function profileCard(user) {
    const button = document.createElement("button");
    button.className = "profile-choice";
    button.type = "button";
    button.dataset.profileId = user.user_id;
    button.setAttribute("aria-label", `Continue as ${user.user_name}`);

    const initial = document.createElement("span");
    initial.className = "profile-choice-initial";
    initial.textContent = user.user_name.charAt(0).toUpperCase();

    const identity = document.createElement("span");
    identity.className = "profile-choice-identity";
    const name = document.createElement("strong");
    name.textContent = user.user_name;
    const detail = document.createElement("small");
    detail.textContent = "Open local profile";
    identity.append(name, detail);

    const arrow = document.createElement("span");
    arrow.className = "profile-choice-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "→";
    button.append(initial, identity, arrow);
    return button;
}

async function renderProfiles() {
    profileList.innerHTML = "<p class=\"empty-state\">Loading local profiles…</p>";
    const data = await getProfiles();
    profileList.replaceChildren();
    profileCount.textContent = `${data.users.length} ${data.users.length === 1 ? "user" : "users"}`;

    if (!data.users.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state profile-list-empty";
        empty.innerHTML = "<strong>No users yet.</strong><span>Create the first local profile to begin.</span>";
        profileList.append(empty);
        nameInput.focus();
        return;
    }
    data.users.forEach((user) => profileList.append(profileCard(user)));
}

async function enterApplication(user) {
    setCurrentProfile(user);
    gate.hidden = true;
    navbar.hidden = false;
    appShell.hidden = false;
    await onProfileSelected?.(user);
}

export async function showProfileGate({ clearSelection = false } = {}) {
    if (clearSelection) await deselectProfile();
    setCurrentProfile(null);
    navbar.hidden = true;
    appShell.hidden = true;
    gate.hidden = false;
    await renderProfiles();
}

export function initProfileGate({ onSelected }) {
    onProfileSelected = onSelected;

    profileList.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-profile-id]");
        if (!button) return;
        button.disabled = true;
        try {
            const data = await selectProfile(Number(button.dataset.profileId));
            await enterApplication(data.user);
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
            button.disabled = false;
        }
    });

    createForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = createForm.querySelector("button[type=submit]");
        button.disabled = true;
        try {
            const data = await createProfile(nameInput.value);
            createForm.reset();
            await enterApplication(data.user);
            showToast(data.message);
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            button.disabled = false;
        }
    });
}

export async function startProfileGate() {
    await showProfileGate({ clearSelection: true });
}
