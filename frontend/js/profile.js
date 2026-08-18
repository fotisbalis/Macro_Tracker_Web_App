export const PROFILE_CHANGE_EVENT = "macrotrackerprofilechange";
let currentProfile = null;

export function setCurrentProfile(profile) {
    currentProfile = profile;
    document.dispatchEvent(new CustomEvent(PROFILE_CHANGE_EVENT, { detail: profile }));
}

export function getCurrentProfileState() {
    return currentProfile;
}
