
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    function setTheme(isDark) {
        document.documentElement.classList.toggle('dark', isDark);
        themeToggle.querySelector('i').className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    themeToggle?.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        setTheme(isDark);
    });
});
