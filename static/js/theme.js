function setTheme(theme) {
    localStorage.setItem("theme", theme);
    applyTheme();
}

function applyTheme() {
    let theme = localStorage.getItem("theme") || "light";

    if (theme === "system") {
        const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        theme = dark ? "dark" : "light";
    }

    document.body.setAttribute("data-theme", theme);
}