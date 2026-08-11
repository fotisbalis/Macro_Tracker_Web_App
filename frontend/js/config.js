const isStandaloneFrontend = window.location.port === "5500";
export const API_BASE_URL = isStandaloneFrontend
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : window.location.origin;

export const THEME_KEY = "macro_tracker_theme";

export const USER_TYPES = Object.freeze({
    GUEST: "guest",
    ADMIN: "admin",
    SIGNED: "signed",
});

