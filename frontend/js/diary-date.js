export function localToday() {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
}

let selectedDate = localToday();

export const getDiaryDate = () => selectedDate;
export function setDiaryDate(value) {
    selectedDate = value;
}

export function formatDate(value) {
    return value ? value.split("-").reverse().join("/") : "";
}

export function parseDate(value) {
    const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value);
    if (!match) return null;
    const [, day, month, year] = match;
    if (Number(year) < 1) return null;
    const date = new Date(0);
    date.setFullYear(Number(year), Number(month) - 1, Number(day));
    date.setHours(12, 0, 0, 0);
    if (date.getFullYear() !== Number(year) || date.getMonth() !== Number(month) - 1 || date.getDate() !== Number(day)) return null;
    return `${year}-${month}-${day}`;
}
