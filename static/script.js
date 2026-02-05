let map = L.map('map').setView([28.6139, 77.2090], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

let routeLayers = {};
let startMarker, endMarker, userMarker;
let currentUserLocation = null;


const violetIcon = new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/purple-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

const redIcon = new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

const userIcon = new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});


async function generateRoute() {

    clearMap();

    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;

    const startCoords = await geocode(start);
    const endCoords = await geocode(end);

    startMarker = L.marker(startCoords, { icon: violetIcon }).addTo(map).bindPopup("Start");
    endMarker = L.marker(endCoords, { icon: redIcon }).addTo(map).bindPopup("Destination");

    // simulated user at start
    currentUserLocation = { lat: startCoords[0], lng: startCoords[1] };

    userMarker = L.marker(startCoords, { icon: userIcon })
        .addTo(map)
        .bindPopup("User");

    const res = await fetch("/safe-route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start: startCoords, end: endCoords })
    });

    const data = await res.json();
    if (data.error) return alert(data.error);

    drawRoutes(data);
    highlightSafest();
    showInfo(data);
}

// -------- ROUTES --------

function drawRoutes(data) {

    routeLayers["safest"] = L.polyline(
        data.safest.coordinates.map(c => [c[1], c[0]]),
        { color: "#22c55e", weight: 6, opacity: 0.7 }
    ).addTo(map);

    if (data.moderate) {
        routeLayers["moderate"] = L.polyline(
            data.moderate.coordinates.map(c => [c[1], c[0]]),
            { color: "#facc15", weight: 6, opacity: 0.7 }
        ).addTo(map);
    }
}

// -------- HIGHLIGHT --------

function highlightSafest() {
    resetStyles();
    routeLayers["safest"].setStyle({ weight: 10, opacity: 1 });
}

function highlightModerate() {
    resetStyles();
    if (routeLayers["moderate"])
        routeLayers["moderate"].setStyle({ weight: 10, opacity: 1 });
}

function resetStyles() {
    if (routeLayers["safest"])
        routeLayers["safest"].setStyle({ weight: 6, opacity: 0.7 });
    if (routeLayers["moderate"])
        routeLayers["moderate"].setStyle({ weight: 6, opacity: 0.7 });
}

// -------- INFO --------

function showInfo(data) {
    document.getElementById("info").innerHTML = `
        <div class="route-box safe" onclick="highlightSafest()">
            <h4>🛡 Safest Route</h4>
            Distance: ${data.safest.distance} km<br>
            Time: ${data.safest.duration} min<br>
            Safety Score: ${data.safest.safety.final}
        </div>

        ${data.moderate ? `
        <div class="route-box balanced" onclick="highlightModerate()">
            <h4>🟡 Moderate Route</h4>
            Distance: ${data.moderate.distance} km<br>
            Time: ${data.moderate.duration} min<br>
            Safety Score: ${data.moderate.safety.final}
        </div>` : ""}
    `;
}

// -------- SOS --------

async function saveContact() {
    const name = cname.value;
    const phone = cphone.value;
    const email = cemail.value;

    await fetch("/save-contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone, email })
    });

    alert("Contact saved!");
}

function sendSOS() {
    if (!currentUserLocation) return alert("User location not set");

    fetch("/sos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentUserLocation)
    }).then(() => alert("🚨 SOS sent successfully!"));
}

// -------- UTILS --------

function clearMap() {
    Object.values(routeLayers).forEach(r => map.removeLayer(r));
    routeLayers = {};
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    if (userMarker) map.removeLayer(userMarker);
}

async function geocode(place) {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${place}`);
    const data = await res.json();
    return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
}
