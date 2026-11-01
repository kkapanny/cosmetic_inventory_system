const colorScheme = window.matchMedia("(prefers-color-scheme: dark)");

function applyColorScheme(event) {
    document.documentElement.dataset.bsTheme = event.matches
        ? "dark"
        : "light";
}

applyColorScheme(colorScheme);
colorScheme.addEventListener("change", applyColorScheme);

const currentYear = document.querySelector("[data-current-year]");

if (currentYear) {
    currentYear.textContent = String(new Date().getFullYear());
}
