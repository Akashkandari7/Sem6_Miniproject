// ─── Theme Toggle (Light / Dark) ───
(function () {
    const STORAGE_KEY = 'qpgen-theme';

    function getPreferred() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) return saved;
        return 'dark'; // default
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        // Update toggle icon
        const btn = document.getElementById('themeToggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '☀' : '☽';
            btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }
    }

    function toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
    }

    // Apply immediately (before DOM ready) to prevent flash
    applyTheme(getPreferred());

    // Expose toggle globally
    window.toggleTheme = toggle;

    // Re-apply after DOM ready in case the toggle button wasn't there yet
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => applyTheme(getPreferred()));
    }
})();
