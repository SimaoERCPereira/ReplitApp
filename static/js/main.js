// The People's Pitch Main JavaScript

// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileToggle = document.getElementById('mobile-nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Set active nav link based on current page
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-links a');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath || (currentPath.includes(href) && href !== '/')) {
            item.classList.add('active');
        }
    });
    
    // Add click handler for theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);
            
            // Change icon based on theme
            const icon = themeToggle.querySelector('i');
            if (isDarkMode) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        });
    }
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme === 'true') {
        document.body.classList.add('dark-mode');
        const icon = document.querySelector('#theme-toggle i');
        if (icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    }
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        // Simple tooltip implementation
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('title') || this.getAttribute('data-title');
            if (!tooltipText) return;
            
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'tooltip';
            tooltipEl.textContent = tooltipText;
            document.body.appendChild(tooltipEl);
            
            const rect = this.getBoundingClientRect();
            tooltipEl.style.top = (rect.top - tooltipEl.offsetHeight - 10) + 'px';
            tooltipEl.style.left = (rect.left + rect.width/2 - tooltipEl.offsetWidth/2) + 'px';
            tooltipEl.style.opacity = '1';
            
            this.addEventListener('mouseleave', function onLeave() {
                tooltipEl.remove();
                this.removeEventListener('mouseleave', onLeave);
            });
        });
    });
});

// Match live updates simulation
function initMatchLiveUpdates() {
    const liveMatches = document.querySelectorAll('.badge-live');
    if (liveMatches.length > 0) {
        // Simulate score updates for live matches every 30 seconds
        setInterval(() => {
            liveMatches.forEach(match => {
                // Only update randomly with 20% chance
                if (Math.random() > 0.8) {
                    let scoreParts = match.textContent.split(':');
                    if (scoreParts.length === 2) {
                        let homeScore = parseInt(scoreParts[0].trim());
                        let awayScore = parseInt(scoreParts[1].trim());
                        
                        // Random goal with 30% chance for home, 30% for away
                        const rand = Math.random();
                        if (rand < 0.3) {
                            homeScore += 1;
                        } else if (rand < 0.6) {
                            awayScore += 1;
                        }
                        
                        match.textContent = `${homeScore} : ${awayScore}`;
                        
                        // Flash effect
                        match.classList.add('score-update');
                        setTimeout(() => {
                            match.classList.remove('score-update');
                        }, 2000);
                    }
                }
            });
        }, 30000); // 30 seconds interval
    }
}

// Initialize live updates if there are any live matches
document.addEventListener('DOMContentLoaded', initMatchLiveUpdates);
