
// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', () => {
    // Initialize any interactive elements
    const alerts = document.querySelectorAll('[role="alert"]');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});
