export function showPage(pageId) {
    const page = document.getElementById(pageId);
    if (!page) return;
    document.querySelectorAll(".page").forEach((item) => item.classList.toggle("active", item === page));
    document.querySelectorAll(".nav-links [data-page]").forEach((link) => {
        link.classList.toggle("active", link.dataset.page === pageId);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
}

export function initNavigation({ onNavigate }) {
    document.querySelectorAll("[data-page]").forEach((link) => {
        link.addEventListener("click", () => {
            const pageId = link.dataset.page;
            showPage(pageId);
            onNavigate?.(pageId);
        });
    });

    const requested = window.location.hash.slice(1);
    if (["home", "archive", "user"].includes(requested)) showPage(requested);
}

