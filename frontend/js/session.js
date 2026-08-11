import { USER_TYPES } from "./config.js";

export const SESSION_CHANGE_EVENT = "macrotrackersessionchange";
let currentSession = null;

export function setCurrentSession(payload) {
    currentSession = payload;
    document.dispatchEvent(new CustomEvent(SESSION_CHANGE_EVENT, { detail: payload }));
}

export function getCurrentSession() {
    return currentSession;
}

export function isGuest() {
    return !currentSession || currentSession.user.user_type === USER_TYPES.GUEST;
}

