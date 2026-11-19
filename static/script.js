document.addEventListener('DOMContentLoaded', () => {
    // Form and input elements
    const form = document.getElementById('packing-form');
    const destinationInput = document.getElementById('destination');
    const durationInput = document.getElementById('duration');
    const durationVal = document.getElementById('duration-val');
    const tripCards = document.querySelectorAll('.trip-card');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnIcon = submitBtn.querySelector('.btn-icon');

    // Tabs controls
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Outputs
    const consoleOutput = document.getElementById('console-output');
    const checklistSummary = document.getElementById('checklist-summary');
    const packingChecklist = document.getElementById('packing-checklist');

    // Selected state
    let selectedTripType = 'trekking';

    // 1. Handle Trip Type Selection
    tripCards.forEach(card => {
        card.addEventListener('click', () => {
            tripCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedTripType = card.dataset.type;
        });
    });

    // 2. Handle Duration Slider Input
    durationInput.addEventListener('input', (e) => {
        const val = e.target.value;
        durationVal.textContent = `${val} ${val == 1 ? 'day' : 'days'}`;
    });

    // 3. Tab Switching Logic
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });

    // Switch tab helper function
    function switchTab(tabName) {
        tabBtns.forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.click();
            }
        });
    }

    // 4. Form Submit & Agent Trigger
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const destination = destinationInput.value.trim();
        const duration = parseInt(durationInput.value, 10);

        if (!destination) return;

        // Update button status
        submitBtn.disabled = true;
        btnText.textContent = 'Agent Reasoning...';
        btnIcon.className = 'fa-solid fa-circle-notch fa-spin';

        // Clear and show console tab
        consoleOutput.innerHTML = '<div class="log-line">Initializing Smart Packing Agent engine...</div>';
        const weatherCard = document.getElementById('weather-card');
        if (weatherCard) weatherCard.style.display = 'none';
        switchTab('console');

        try {
            const response = await fetch('/api/pack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    destination,
                    trip_type: selectedTripType,
                    duration
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Server error occurred during packing run.');
            }

            // Stream and format logs to console
            renderLogs(data.logs);

            // Render weather and load packing checklist
            renderWeather(data.weather);
            renderPackingList(data.packing_list, destination, selectedTripType);

            // Switch to packing list tab with a small delay for premium feel
            setTimeout(() => {
                switchTab('packing-list');
            }, 1800);

        } catch (error) {
            consoleOutput.innerHTML += `
                <div class="log-line log-error">
                    <i class="fa-solid fa-triangle-exclamation"></i> [Fatal Error] ${error.message}
                </div>
            `;
        } finally {
            // Restore button
            submitBtn.disabled = false;
            btnText.textContent = 'Initialize Packing Agent';
            btnIcon.className = 'fa-solid fa-rocket';
        }
    });

    // Helper: Formatter for console logs
    function renderLogs(logsText) {
        if (!logsText) return;
        
        consoleOutput.innerHTML = '';
        const lines = logsText.split('\n');

        lines.forEach(line => {
            if (!line.trim()) return;

            let cssClass = 'log-line';
            let icon = '';

            if (line.startsWith('===')) {
                cssClass = 'log-line log-step';
                icon = '<i class="fa-solid fa-chevron-right"></i> ';
            } else if (line.includes('[Warning]')) {
                cssClass = 'log-line log-warning';
                icon = '<i class="fa-solid fa-triangle-exclamation"></i> ';
            } else if (line.includes('[Error]')) {
                cssClass = 'log-line log-error';
                icon = '<i class="fa-solid fa-circle-xmark"></i> ';
            } else if (line.includes('Called add_item') || line.includes('[Safety Check] No required items missing') || line.includes('No required items missing')) {
                cssClass = 'log-line log-success';
                icon = '<i class="fa-solid fa-check"></i> ';
            }

            const element = document.createElement('div');
            element.className = cssClass;
            element.innerHTML = `${icon}${escapeHtml(line)}`;
            consoleOutput.appendChild(element);
        });

        // Scroll console container to bottom
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    // Helper: Render packing list cards
    function renderPackingList(items, destination, tripType) {
        packingChecklist.innerHTML = '';

        if (!items || items.length === 0) {
            checklistSummary.innerHTML = `
                <h3>No Items Recommended</h3>
                <p>Verify parameters or model connection in the console trace.</p>
            `;
            return;
        }

        // Summary details
        checklistSummary.innerHTML = `
            <h3>Checklist for ${escapeHtml(destination)}</h3>
            <p><i class="fa-solid fa-compass"></i> ${capitalize(tripType)} Trip | <i class="fa-solid fa-box"></i> ${items.length} items packed in agent memory.</p>
        `;

        // Load items
        items.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'checklist-item';
            // Stagger animation delay
            li.style.animationDelay = `${index * 50}ms`;

            li.innerHTML = `
                <i class="fa-regular fa-square check-box-icon"></i>
                <span>${escapeHtml(item)}</span>
            `;

            // Toggle check status on click
            li.addEventListener('click', () => {
                li.classList.toggle('checked');
                const icon = li.querySelector('.check-box-icon');
                if (li.classList.contains('checked')) {
                    icon.className = 'fa-solid fa-square-check check-box-icon';
                } else {
                    icon.className = 'fa-regular fa-square check-box-icon';
                }
            });

            packingChecklist.appendChild(li);
        });
    }

    // Helper: Render Current Weather Card
    function renderWeather(weather) {
        const weatherCard = document.getElementById('weather-card');
        const weatherDetails = document.getElementById('weather-details');
        const weatherError = document.getElementById('weather-error');

        if (!weatherCard) return;

        // Show the weather card container
        weatherCard.style.display = 'block';

        if (!weather || weather.error || !weather.city) {
            weatherDetails.style.display = 'none';
            weatherError.style.display = 'block';
            if (weather && weather.error) {
                weatherError.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${escapeHtml(weather.error)}`;
            } else {
                weatherError.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Weather information unavailable';
            }
            return;
        }

        weatherDetails.style.display = 'block';
        weatherError.style.display = 'none';

        // Format and set values safely, fall back to N/A
        const city = weather.city !== undefined && weather.city !== null ? weather.city : 'N/A';
        const tempVal = weather.temperature !== undefined && weather.temperature !== null ? `${Math.round(weather.temperature)}°C` : 'N/A';
        const conditionVal = weather.condition !== undefined && weather.condition !== null ? capitalize(weather.condition) : 'N/A';
        const humidityVal = weather.humidity !== undefined && weather.humidity !== null ? `${weather.humidity}%` : 'N/A';
        const windVal = weather.wind_speed !== undefined && weather.wind_speed !== null ? `${weather.wind_speed} m/s` : 'N/A';

        // Map condition to emoji
        const emojiMap = {
            'clear': '☀️',
            'clouds': '☁️',
            'cloudy': '☁️',
            'rain': '🌧️',
            'drizzle': '🌧️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'mist': '🌫️',
            'smoke': '🌫️',
            'haze': '🌫️',
            'dust': '🌫️',
            'fog': '🌫️',
            'sand': '🌫️',
            'ash': '🌫️',
            'squall': '💨',
            'tornado': '🌪️'
        };
        const condLower = conditionVal.toLowerCase();
        let emoji = '🌡️';
        for (const [key, val] of Object.entries(emojiMap)) {
            if (condLower.includes(key)) {
                emoji = val;
                break;
            }
        }

        document.getElementById('weather-city').textContent = city;
        document.getElementById('weather-temp').innerHTML = `🌡️ ${tempVal}`;
        document.getElementById('weather-condition').innerHTML = `${emoji} ${conditionVal}`;
        document.getElementById('weather-humidity').innerHTML = `💧 ${humidityVal}`;
        document.getElementById('weather-wind').innerHTML = `💨 ${windVal}`;
    }

    // Utility: HTML Escaper to prevent XSS
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    // Utility: Capitalize word
    function capitalize(word) {
        if (!word) return '';
        return word.charAt(0).toUpperCase() + word.slice(1);
    }
});
