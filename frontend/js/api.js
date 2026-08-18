import { API_BASE_URL } from "./config.js";

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
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

export const getHealth = () => request("/health");
export const getProfiles = () => request("/profiles");
export const getCurrentProfile = () => request("/profiles/current");
export const getToday = () => request("/days/today");
export const getArchive = () => request("/archive");
export const getUserStatistics = () => request("/users/me/statistics");

export function analyzeFood(payload) {
    return request("/foods/analyze", { method: "POST", body: JSON.stringify(payload) });
}

export function addManualFood(payload) {
    return request("/foods/manual", { method: "POST", body: JSON.stringify(payload) });
}

export function addArchivedFoodToToday(entryId) {
    return request(`/foods/${encodeURIComponent(entryId)}/add-to-today`, { method: "POST" });
}

export function deleteFood(entryId) {
    return request(`/foods/${encodeURIComponent(entryId)}`, { method: "DELETE" });
}

export function createProfile(userName) {
    return request("/profiles", {
        method: "POST",
        body: JSON.stringify({ user_name: userName }),
    });
}

export function selectProfile(userId) {
    return request("/profiles/select", {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
    });
}

export function deselectProfile() {
    return request("/profiles/deselect", { method: "POST" });
}

export function updateTargets(payload) {
    return request("/users/me/targets", { method: "PATCH", body: JSON.stringify(payload) });
}
