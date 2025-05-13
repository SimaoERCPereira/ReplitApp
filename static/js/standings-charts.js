// The People's Pitch Standings Charts
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we have the standings-chart canvas
    const chartElement = document.getElementById('standings-chart');
    if (!chartElement) return;
    
    // Get teams data from the hidden element
    const teamsDataElement = document.getElementById('teams-data');
    if (!teamsDataElement) return;
    
    let teamsData;
    try {
        teamsData = JSON.parse(teamsDataElement.textContent);
    } catch (e) {
        console.error('Failed to parse teams data:', e);
        return;
    }
    
    // Extract data for charts
    const teamNames = teamsData.map(team => team.name);
    const points = teamsData.map(team => team.points);
    const wins = teamsData.map(team => team.win);
    const draws = teamsData.map(team => team.draw);
    const losses = teamsData.map(team => team.loss);
    
    // Get only top 10 teams for better readability
    const top10TeamNames = teamNames.slice(0, 10);
    const top10Points = points.slice(0, 10);
    
    // Generate color gradients for bars
    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
    const secondaryColor = getComputedStyle(document.documentElement).getPropertyValue('--secondary-color').trim();
    
    // Create bar chart
    new Chart(chartElement, {
        type: 'bar',
        data: {
            labels: top10TeamNames,
            datasets: [{
                label: 'Points',
                data: top10Points,
                backgroundColor: primaryColor,
                borderColor: 'rgba(0, 0, 0, 0.1)',
                borderWidth: 1,
                borderRadius: 6,
                barThickness: 16,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: secondaryColor,
                    titleFont: {
                        family: "'Inter', sans-serif",
                        size: 14
                    },
                    bodyFont: {
                        family: "'Inter', sans-serif",
                        size: 13
                    },
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        display: true,
                        drawBorder: false,
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12
                        }
                    }
                }
            }
        }
    });
    
    // Stats distribution pie chart
    const distributionChart = document.getElementById('distribution-chart');
    if (distributionChart) {
        // Calculate total matches played across all teams
        const totalWins = wins.reduce((acc, val) => acc + val, 0);
        const totalDraws = draws.reduce((acc, val) => acc + val, 0);
        const totalLosses = losses.reduce((acc, val) => acc + val, 0);
        
        const successColor = getComputedStyle(document.documentElement).getPropertyValue('--success-color').trim();
        const warningColor = getComputedStyle(document.documentElement).getPropertyValue('--warning-color').trim();
        const dangerColor = getComputedStyle(document.documentElement).getPropertyValue('--danger-color').trim();
        
        new Chart(distributionChart, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Draws', 'Losses'],
                datasets: [{
                    data: [totalWins, totalDraws, totalLosses],
                    backgroundColor: [successColor, warningColor, dangerColor],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12
                            },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: secondaryColor,
                        titleFont: {
                            family: "'Inter', sans-serif",
                            size: 14
                        },
                        bodyFont: {
                            family: "'Inter', sans-serif",
                            size: 13
                        },
                        padding: 12,
                        cornerRadius: 8
                    }
                }
            }
        });
    }
});
