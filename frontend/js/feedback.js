const toastRegion = document.getElementById("toast-region");

export function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastRegion.append(toast);
    window.setTimeout(() => toast.classList.add("visible"), 10);
    window.setTimeout(() => {
        toast.classList.remove("visible");
        window.setTimeout(() => toast.remove(), 250);
    }, 3200);
}

