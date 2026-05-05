const ctx = document.getElementById('categoryChart').getContext('2d');

new Chart(ctx, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: [
                '#c9a84c',
                '#4caf82',
                '#e05c5c',
                '#5c9ee0',
                '#e0935c',
                '#a05ce0',
                '#5ce0d8',
                '#e05cb8',
            ],
            borderColor: '#13161e',
            borderWidth: 2,
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: '#e8e6e0',
                    font: { family: 'DM Sans', size: 13 },
                    padding: 16,
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return ` ${context.label}: ${context.parsed}%`;
                    }
                }
            }
        }
    }
});