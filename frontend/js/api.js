import { API_BASE_URL } from "./config.js";

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials: "include",
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {}),
        },
    });

    let data = {};
    try {
        data = await response.json();
    } catch (_error) {
        data = {};
    }

    if (!response.ok) {
        const detail = Array.isArray(data.detail)
            ? data.detail.map((item) => item.msg).join(", ")
            : data.detail;
        throw new Error(typeof detail === "string" ? detail : "Something went wrong");
    }
    return data;
}

export const getSession = () => request("/session/user");
export const getToday = () => request("/days/today");
export const getArchive = () => request("/archive");
export const getUserStatistics = () => request("/users/me/statistics");

export function analyzeFood(payload) {
    return request("/foods/analyze", { method: "POST", body: JSON.stringify(payload) });
}

export function deleteFood(entryId) {
    return request(`/foods/${encodeURIComponent(entryId)}`, { method: "DELETE" });
}

export function login(payload) {
    return request("/login", { method: "POST", body: JSON.stringify(payload) });
}

export function signup(payload) {
    return request("/signup", { method: "POST", body: JSON.stringify(payload) });
}

export function verifySignup(payload) {
    return request("/signup", { method: "POST", body: JSON.stringify(payload) });
}

export function requestPasswordReset(payload) {
    return request("/login/forgot-password", { method: "POST", body: JSON.stringify(payload) });
}

export function verifyPasswordReset(payload) {
    return request("/login/forgot-password/verify", { method: "POST", body: JSON.stringify(payload) });
}

export function changePassword(payload) {
    return request("/login/change-password", { method: "POST", body: JSON.stringify(payload) });
}

export function logout() {
    return request("/logout", { method: "POST" });
}

export function updateTargets(payload) {
    return request("/users/me/targets", { method: "PATCH", body: JSON.stringify(payload) });
}
