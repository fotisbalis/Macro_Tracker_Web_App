import { getSession, getUserStatistics, login, logout, signup, updateTargets } from "./api.js";
import { showToast } from "./feedback.js";
import { setCurrentSession } from "./session.js";

const guestPanel = document.getElementById("guest-account-panel");
const signedPanel = document.getElementById("signed-account-panel");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

function fillTargets(targets) {
    document.getElementById("target-calories").value = targets.calories;
    document.getElementById("target-protein").value = targets.protein;
    document.getElementById("target-carbs").value = targets.carbs;
    document.getElementById("target-fat").value = targets.fat;
}

function showTab(name) {
    const isLogin = name === "login";
    loginForm.hidden = !isLogin;
    signupForm.hidden = isLogin;
    document.getElementById("show-login").classList.toggle("active", isLogin);
    document.getElementById("show-signup").classList.toggle("active", !isLogin);
    document.getElementById("show-login").setAttribute("aria-selected", String(isLogin));
    document.getElementById("show-signup").setAttribute("aria-selected", String(!isLogin));
}

async function renderStatistics() {
    const data = await getUserStatistics();
    const container = document.getElementById("profile-stats");
    container.innerHTML = `
        <span><strong>${data.day_count}</strong><small>days tracked</small></span>
        <span><strong>${data.entry_count}</strong><small>foods logged</small></span>
        <span><strong>${data.average_daily_calories}</strong><small>avg kcal/day</small></span>`;
}

export async function renderUser(payload) {
    setCurrentSession(payload);
    const isGuest = payload.user.user_type === "guest";
    document.getElementById("user-type-badge").textContent = isGuest ? "Guest session" : "Signed account";
    guestPanel.hidden = !isGuest;
    signedPanel.hidden = isGuest;
    fillTargets(payload.user.targets);

    if (!isGuest) {
        document.getElementById("profile-name").textContent = payload.user.user_name;
        document.getElementById("profile-email").textContent = payload.user.email;
        try {
            await renderStatistics();
        } catch (_error) {
            document.getElementById("profile-stats").textContent = "Statistics unavailable.";
        }
    }
}

export async function loadUser() {
    const payload = await getSession();
    await renderUser(payload);
    return payload;
}

async function runAuth(action, form, payload) {
    const button = form.querySelector("button[type=submit], #logout-button");
    button.disabled = true;
    try {
        const data = await action(payload);
        form.reset();
        await renderUser(data);
        showToast(data.user.user_type === "guest" ? "Logged out" : `Welcome, ${data.user.user_name}`);
        document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        button.disabled = false;
    }
}

export function initUser() {
    document.getElementById("show-login").addEventListener("click", () => showTab("login"));
    document.getElementById("show-signup").addEventListener("click", () => showTab("signup"));

    loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        runAuth(login, loginForm, {
            email: document.getElementById("login-email").value,
            password: document.getElementById("login-password").value,
        });
    });

    signupForm.addEventListener("submit", (event) => {
        event.preventDefault();
        runAuth(signup, signupForm, {
            user_name: document.getElementById("signup-name").value,
            email: document.getElementById("signup-email").value,
            password: document.getElementById("signup-password").value,
        });
    });

    document.getElementById("logout-button").addEventListener("click", () => runAuth(logout, signedPanel, undefined));

    document.getElementById("targets-form").addEventListener("submit", async (event) => {
        event.preventDefault();
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
        }
    });
}
