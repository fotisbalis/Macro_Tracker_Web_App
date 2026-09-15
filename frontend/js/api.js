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
        const error = new Error(typeof detail === "string" ? detail : "Something went wrong");
        error.status = response.status;
        throw error;
    }
    return data;
}

export const getHealth = () => request("/health");
export const getAIStatus = () => request("/ai/status");
export const getProfiles = () => request("/profiles");
export const getCurrentProfile = () => request("/profiles/current");
export const getToday = () => request("/days/today");
export const getDay = (date) => request(`/days/${encodeURIComponent(date)}`);
export const getFavorites = () => request("/favorites");
export const saveFavorite = (entryId) => request(`/favorites/from-entry/${encodeURIComponent(entryId)}`, { method: "POST" });
export const removeFavorite = (favoriteId) => request(`/favorites/${encodeURIComponent(favoriteId)}`, { method: "DELETE" });
export const logFavorite = (favoriteId, date, quantity) => request(`/favorites/${encodeURIComponent(favoriteId)}/log`, {
    method: "POST", body: JSON.stringify({ logged_on: date, quantity }),
});
export const getArchive = () => request("/archive");
export const getUserStatistics = () => request("/users/me/statistics");

export function getPeriodStatistics(startDate, endDate) {
    const query = new URLSearchParams({ start_date: startDate, end_date: endDate });
    return request(`/statistics?${query}`);
}

export function analyzeFood(payload) {
    return request("/foods/analyze", { method: "POST", body: JSON.stringify(payload) });
}

export function saveOpenAIKey(apiKey) {
    return request("/ai/api-key", {
        method: "PUT",
        body: JSON.stringify({ api_key: apiKey }),
    });
}

export function removeOpenAIKey() {
    return request("/ai/api-key", { method: "DELETE" });
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

export function updateFoodQuantity(entryId, quantity) {
    return request(`/foods/${encodeURIComponent(entryId)}/quantity`, {
        method: "PATCH", body: JSON.stringify({ quantity }),
    });
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
