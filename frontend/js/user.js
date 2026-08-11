import {
    changePassword,
    getSession,
    getUserStatistics,
    login,
    logout,
    requestPasswordReset,
    signup,
    updateTargets,
    verifyPasswordReset,
    verifySignup,
} from "./api.js";
import { showToast } from "./feedback.js";
import { setCurrentSession } from "./session.js";

const guestPanel = document.getElementById("guest-account-panel");
const signedPanel = document.getElementById("signed-account-panel");
const authTabs = document.getElementById("auth-tabs");
const forms = {
    login: document.getElementById("login-form"),
    signup: document.getElementById("signup-form"),
    signupVerification: document.getElementById("signup-verification-form"),
    forgotPassword: document.getElementById("forgot-password-form"),
    passwordVerification: document.getElementById("password-verification-form"),
    newPassword: document.getElementById("new-password-form"),
};

let signupChallengeId = null;
let passwordResetChallengeId = null;
let passwordResetToken = null;

function fillTargets(targets) {
    document.getElementById("target-calories").value = targets.calories;
    document.getElementById("target-protein").value = targets.protein;
    document.getElementById("target-carbs").value = targets.carbs;
    document.getElementById("target-fat").value = targets.fat;
}

function showAuthView(name) {
    Object.entries(forms).forEach(([formName, form]) => {
        form.hidden = formName !== name;
    });

    const showTabs = name === "login" || name === "signup";
    authTabs.hidden = !showTabs;
    const isLogin = name === "login";
    document.getElementById("show-login").classList.toggle("active", isLogin);
    document.getElementById("show-signup").classList.toggle("active", name === "signup");
    document.getElementById("show-login").setAttribute("aria-selected", String(isLogin));
    document.getElementById("show-signup").setAttribute("aria-selected", String(name === "signup"));
}

async function withSubmitting(form, action) {
    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    try {
        return await action();
    } catch (error) {
        showToast(error.message, "error");
        return null;
    } finally {
        button.disabled = false;
    }
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

    if (isGuest) {
        showAuthView("login");
        return;
    }

    document.getElementById("profile-name").textContent = payload.user.user_name;
    document.getElementById("profile-email").textContent = payload.user.email;
    try {
        await renderStatistics();
    } catch (_error) {
        document.getElementById("profile-stats").textContent = "Statistics unavailable.";
    }
}

export async function loadUser() {
    const payload = await getSession();
    await renderUser(payload);
    return payload;
}

function resetSignupFlow() {
    signupChallengeId = null;
    forms.signupVerification.reset();
    showAuthView("signup");
}

function resetPasswordFlow() {
    passwordResetChallengeId = null;
    passwordResetToken = null;
    forms.forgotPassword.reset();
    forms.passwordVerification.reset();
    forms.newPassword.reset();
    showAuthView("login");
}

export function initUser() {
    document.getElementById("show-login").addEventListener("click", () => showAuthView("login"));
    document.getElementById("show-signup").addEventListener("click", () => showAuthView("signup"));
    document.getElementById("show-forgot-password").addEventListener("click", () => {
        document.getElementById("forgot-email").value = document.getElementById("login-email").value;
        showAuthView("forgotPassword");
    });

    document.querySelectorAll(".back-to-login").forEach((button) => {
        button.addEventListener("click", resetPasswordFlow);
    });
    document.querySelector(".back-to-signup").addEventListener("click", resetSignupFlow);
    document.querySelector(".restart-password-reset").addEventListener("click", () => {
        passwordResetChallengeId = null;
        forms.passwordVerification.reset();
        showAuthView("forgotPassword");
    });

    forms.login.addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = await withSubmitting(forms.login, () => login({
            email: document.getElementById("login-email").value,
            password: document.getElementById("login-password").value,
        }));
        if (!data) return;
        forms.login.reset();
        await renderUser(data);
        showToast(`Welcome, ${data.user.user_name}`);
        document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
    });

    forms.signup.addEventListener("submit", async (event) => {
        event.preventDefault();
        const password = document.getElementById("signup-password").value;
        const confirmPassword = document.getElementById("signup-confirm-password").value;
        if (password !== confirmPassword) {
            showToast("Passwords do not match", "error");
            return;
        }

        const data = await withSubmitting(forms.signup, () => signup({
            user_name: document.getElementById("signup-name").value,
            email: document.getElementById("signup-email").value,
            password,
            confirm_password: confirmPassword,
        }));
        if (!data) return;
        signupChallengeId = data.challenge_id;
        showAuthView("signupVerification");
        document.getElementById("signup-verification-code").focus();
        showToast(data.message);
    });

    forms.signupVerification.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!signupChallengeId) {
            resetSignupFlow();
            showToast("Start the signup process again", "error");
            return;
        }
        const data = await withSubmitting(forms.signupVerification, () => verifySignup({
            challenge_id: signupChallengeId,
            verification_code: document.getElementById("signup-verification-code").value,
        }));
        if (!data) return;
        signupChallengeId = null;
        forms.signup.reset();
        forms.signupVerification.reset();
        await renderUser(data);
        showToast(data.message);
        document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
    });

    forms.forgotPassword.addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = await withSubmitting(forms.forgotPassword, () => requestPasswordReset({
            email: document.getElementById("forgot-email").value,
        }));
        if (!data) return;
        passwordResetChallengeId = data.challenge_id;
        showAuthView("passwordVerification");
        document.getElementById("password-verification-code").focus();
        showToast(data.message);
    });

    forms.passwordVerification.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!passwordResetChallengeId) {
            showAuthView("forgotPassword");
            showToast("Start the password reset again", "error");
            return;
        }
        const data = await withSubmitting(forms.passwordVerification, () => verifyPasswordReset({
            challenge_id: passwordResetChallengeId,
            verification_code: document.getElementById("password-verification-code").value,
        }));
        if (!data) return;
        passwordResetToken = data.reset_token;
        showAuthView("newPassword");
        document.getElementById("new-password").focus();
    });

    forms.newPassword.addEventListener("submit", async (event) => {
        event.preventDefault();
        const newPassword = document.getElementById("new-password").value;
        const confirmNewPassword = document.getElementById("confirm-new-password").value;
        if (newPassword !== confirmNewPassword) {
            showToast("Passwords do not match", "error");
            return;
        }
        if (!passwordResetToken) {
            resetPasswordFlow();
            showToast("Start the password reset again", "error");
            return;
        }
        const data = await withSubmitting(forms.newPassword, () => changePassword({
            reset_token: passwordResetToken,
            new_password: newPassword,
            confirm_new_password: confirmNewPassword,
        }));
        if (!data) return;
        resetPasswordFlow();
        showToast(data.message);
    });

    document.getElementById("logout-button").addEventListener("click", async () => {
        const button = document.getElementById("logout-button");
        button.disabled = true;
        try {
            const data = await logout();
            await renderUser(data);
            showToast("Logged out");
            document.dispatchEvent(new CustomEvent("macrotrackerdatachange"));
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            button.disabled = false;
        }
    });

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

