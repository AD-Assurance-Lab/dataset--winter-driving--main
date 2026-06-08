// Interactive Telemetry Explorer Logic
document.addEventListener("DOMContentLoaded", () => {
    // 20 Aligned Frames of Sample Telemetry (wmu-jan27-downtown-1 excerpt)
    const runData = [
        { frame: 0, ts: 1769537064.131, speed: 28.5, wheelSpeed: 28.5, steering: -1.2, friction: 0.81, road: "Dry Pavement", temp: -5.4, slip: 0.0, abs: 0 },
        { frame: 1, ts: 1769537064.536, speed: 29.8, wheelSpeed: 29.8, steering: -1.0, friction: 0.80, road: "Dry Pavement", temp: -5.4, slip: 0.0, abs: 0 },
        { frame: 2, ts: 1769537065.012, speed: 31.2, wheelSpeed: 31.3, steering: -0.8, friction: 0.78, road: "Dry Pavement", temp: -5.5, slip: 0.3, abs: 0 },
        { frame: 3, ts: 1769537065.418, speed: 32.5, wheelSpeed: 32.5, steering: -0.5, friction: 0.62, road: "Damp Pavement", temp: -5.6, slip: 0.0, abs: 0 },
        { frame: 4, ts: 1769537065.820, speed: 33.8, wheelSpeed: 34.0, steering: 0.2,  friction: 0.45, road: "Mixed Snow/Ice", temp: -5.8, slip: 0.6, abs: 0 },
        
        { frame: 5, ts: 1769537066.227, speed: 34.9, wheelSpeed: 35.8, steering: 0.8,  friction: 0.30, road: "Packed Snow", temp: -7.0, slip: 2.5, abs: 0 },
        { frame: 6, ts: 1769537066.633, speed: 35.2, wheelSpeed: 36.5, steering: 1.5,  friction: 0.29, road: "Packed Snow", temp: -7.1, slip: 3.7, abs: 0 },
        { frame: 7, ts: 1769537067.042, speed: 35.0, wheelSpeed: 37.2, steering: 2.1,  friction: 0.28, road: "Packed Snow", temp: -7.1, slip: 6.2, abs: 0 },
        { frame: 8, ts: 1769537067.448, speed: 34.2, wheelSpeed: 34.0, steering: -0.5, friction: 0.27, road: "Packed Snow", temp: -7.2, slip: 0.5, abs: 0 },
        { frame: 9, ts: 1769537067.855, speed: 33.0, wheelSpeed: 33.0, steering: -1.2, friction: 0.26, road: "Packed Snow", temp: -7.2, slip: 0.0, abs: 0 },
        
        { frame: 10, ts: 1769537068.262, speed: 32.5, wheelSpeed: 36.1, steering: 3.5,  friction: 0.16, road: "Ice Patch", temp: -7.5, slip: 11.0, abs: 0 },
        { frame: 11, ts: 1769537068.668, speed: 31.8, wheelSpeed: 38.4, steering: 5.8,  friction: 0.15, road: "Ice Patch", temp: -7.6, slip: 20.7, abs: 0 },
        { frame: 12, ts: 1769537069.072, speed: 30.2, wheelSpeed: 21.0, steering: -4.2, friction: 0.14, road: "Ice (ABS Active)", temp: -7.6, slip: 30.4, abs: 1 },
        { frame: 13, ts: 1769537069.475, speed: 27.5, wheelSpeed: 18.2, steering: -2.8, friction: 0.15, road: "Ice (ABS Active)", temp: -7.7, slip: 33.8, abs: 1 },
        { frame: 14, ts: 1769537069.880, speed: 24.1, wheelSpeed: 19.5, steering: 0.5,  friction: 0.18, road: "Mixed Snow/Ice", temp: -7.7, slip: 19.0, abs: 1 },
        
        { frame: 15, ts: 1769537070.285, speed: 21.3, wheelSpeed: 21.1, steering: 1.0,  friction: 0.26, road: "Packed Snow", temp: -7.5, slip: 0.9, abs: 0 },
        { frame: 16, ts: 1769537070.690, speed: 18.8, wheelSpeed: 18.8, steering: 0.5,  friction: 0.28, road: "Packed Snow", temp: -7.4, slip: 0.0, abs: 0 },
        { frame: 17, ts: 1769537071.096, speed: 16.5, wheelSpeed: 16.5, steering: 0.2,  friction: 0.29, road: "Packed Snow", temp: -7.3, slip: 0.0, abs: 0 },
        { frame: 18, ts: 1769537071.502, speed: 14.8, wheelSpeed: 14.8, steering: -0.1, friction: 0.30, road: "Packed Snow", temp: -7.2, slip: 0.0, abs: 0 },
        { frame: 19, ts: 1769537071.908, speed: 13.5, wheelSpeed: 13.5, steering: -0.2, friction: 0.31, road: "Packed Snow", temp: -7.2, slip: 0.0, abs: 0 }
    ];

    // DOM Elements
    const frameSlider = document.getElementById("frame-slider");
    const playPauseBtn = document.getElementById("play-pause-btn");
    const frameCounter = document.getElementById("frame-counter");
    const timestampLabel = document.getElementById("frame-timestamp-label");
    
    // HUD Display Elements
    const hudSpeed = document.getElementById("hud-speed-val");
    const hudSlip = document.getElementById("hud-slip-val");
    const hudFrict = document.getElementById("hud-frict-val");
    const roadScene = document.querySelector(".layer-bg");
    const roadSnow = document.querySelector(".layer-snow");

    let currentFrameIdx = 0;
    let isPlaying = false;
    let playbackInterval = null;

    // Chart.js Configurations
    const speedCtx = document.getElementById("speedChart").getContext("2d");
    const frictionCtx = document.getElementById("frictionChart").getContext("2d");

    const labels = runData.map(d => `${d.frame}s`);
    const speeds = runData.map(d => d.speed);
    const wheelSpeeds = runData.map(d => d.wheelSpeed);
    const steeringAngles = runData.map(d => d.steering);
    const frictions = runData.map(d => d.friction);

    // Speed Chart
    const speedChart = new Chart(speedCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Vehicle Speed (mph)',
                    data: speeds,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Wheel Speed (mph)',
                    data: wheelSpeeds,
                    borderColor: '#a855f7',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    // Friction & Steering Chart
    const frictionChart = new Chart(frictionCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'MARWIS Friction (0-1)',
                    data: frictions,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Steering Angle (deg)',
                    data: steeringAngles,
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                y: { 
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#38bdf8' },
                    min: 0,
                    max: 1.0
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#ef4444' },
                    min: -10,
                    max: 10
                }
            }
        }
    });

    // Custom vertical line plugin to draw vertical scrubber marker
    const drawScrubberLine = (chart, index) => {
        const activeIndex = index;
        const meta = chart.getDatasetMeta(0);
        
        // Ensure index fits in range
        if (activeIndex >= meta.data.length) return;
        
        const xCoord = meta.data[activeIndex].x;
        const ctx = chart.ctx;
        const yAxis = chart.scales.y;
        
        ctx.save();
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.moveTo(xCoord, yAxis.top);
        ctx.lineTo(xCoord, yAxis.bottom);
        ctx.stroke();
        
        // Draw little glowing dot at active speed point
        ctx.beginPath();
        ctx.arc(xCoord, meta.data[activeIndex].y, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#06b6d4';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        
        ctx.restore();
    };

    // Overlay drawing triggers
    speedChart.options.plugins.customLine = true;
    frictionChart.options.plugins.customLine = true;

    // Bind scrubber lines to Chart render cycles
    Chart.register({
        id: 'scrubberLinePlugin',
        afterDraw: (chart) => {
            if (chart.options.plugins.customLine) {
                drawScrubberLine(chart, currentFrameIdx);
            }
        }
    });

    // Update UI and elements for the current frame
    const updateDashboard = (idx) => {
        currentFrameIdx = idx;
        const data = runData[idx];
        
        // Update slider & counter label
        frameSlider.value = idx;
        frameCounter.textContent = `Frame: ${idx} / ${runData.length - 1}`;
        timestampLabel.textContent = `TS: ${data.ts.toFixed(3)}`;
        
        // Update HUD
        hudSpeed.textContent = `${data.speed.toFixed(1)} mph`;
        hudSlip.textContent = `${data.slip.toFixed(1)}%`;
        hudFrict.textContent = `${data.friction.toFixed(2)}`;
        
        // Alert on wheel slip / ABS active
        if (data.slip > 10.0 || data.abs === 1) {
            hudSlip.classList.add("text-red");
            hudFrict.classList.add("text-red");
        } else {
            hudSlip.classList.remove("text-red");
            hudFrict.classList.remove("text-red");
        }
        
        // Dynamically update simulated road scene visuals based on road condition
        let bgSvg = "";
        let snowOpacity = 0.0;
        
        if (data.road === "Dry Pavement") {
            bgSvg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 450'><rect width='800' height='450' fill='%231e293b'/><rect y='250' width='800' height='200' fill='%230f172a'/><polygon points='100,450 380,250 420,250 700,450' fill='%23334155'/><line x1='400' y1='250' x2='400' y2='450' stroke='%23f59e0b' stroke-dasharray='10 10' stroke-width='4'/></svg>";
            snowOpacity = 0.0;
        } else if (data.road === "Damp Pavement" || data.road === "Mixed Snow/Ice") {
            bgSvg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 450'><rect width='800' height='450' fill='%230f172a'/><rect y='250' width='800' height='200' fill='%23090d16'/><polygon points='100,450 380,250 420,250 700,450' fill='%231e293b'/><line x1='400' y1='250' x2='400' y2='450' stroke='%23d97706' stroke-dasharray='10 10' stroke-width='4'/></svg>";
            snowOpacity = 0.35;
        } else if (data.road.includes("Snow")) {
            bgSvg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 450'><rect width='800' height='450' fill='%23334155'/><rect y='250' width='800' height='200' fill='%230f172a'/><polygon points='100,450 380,250 420,250 700,450' fill='%23475569'/><line x1='400' y1='250' x2='400' y2='450' stroke='white' stroke-dasharray='10 10' stroke-width='4'/></svg>";
            snowOpacity = 0.8;
        } else if (data.road.includes("Ice")) {
            bgSvg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 450'><rect width='800' height='450' fill='%230f172a'/><rect y='250' width='800' height='200' fill='%23090d16'/><polygon points='100,450 380,250 420,250 700,450' fill='%2338bdf8' opacity='0.4'/><line x1='400' y1='250' x2='400' y2='450' stroke='white' stroke-dasharray='10 10' stroke-width='4' opacity='0.7'/></svg>";
            snowOpacity = 0.9;
        }
        
        roadScene.style.backgroundImage = `url("${bgSvg}")`;
        roadSnow.style.opacity = snowOpacity;
        
        // Redraw charts to update scrubber vertical line positions
        speedChart.update('none'); // use 'none' to skip heavy animations during scrubbing
        frictionChart.update('none');
    };

    // Slider Event Listener
    frameSlider.addEventListener("input", (e) => {
        updateDashboard(parseInt(e.target.value));
    });

    // Playback Logic
    const togglePlayback = () => {
        isPlaying = !isPlaying;
        if (isPlaying) {
            playPauseBtn.innerHTML = `<i class="fa-solid fa-pause"></i> Pause Run`;
            playbackInterval = setInterval(() => {
                let nextFrame = currentFrameIdx + 1;
                if (nextFrame >= runData.length) {
                    nextFrame = 0; // Loop back
                }
                updateDashboard(nextFrame);
            }, 300); // 300ms per frame
        } else {
            playPauseBtn.innerHTML = `<i class="fa-solid fa-play"></i> Play Run`;
            clearInterval(playbackInterval);
        }
    };

    playPauseBtn.addEventListener("click", togglePlayback);

    // Initial render
    updateDashboard(0);
});

// Copy Bibtex Citation
function copyCitation() {
    const bibtexCode = document.getElementById("bibtex-code").innerText;
    navigator.clipboard.writeText(bibtexCode).then(() => {
        const copyBtn = document.querySelector(".copy-bib-btn");
        copyBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
        setTimeout(() => {
            copyBtn.innerHTML = `<i class="fa-solid fa-copy"></i> Copy`;
        }, 2000);
    });
}
