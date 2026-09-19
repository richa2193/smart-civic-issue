/**
 * map.js
 * Handles Leaflet map initialization, dragging, and Geoapify reverse geocoding.
 */

let map = null;
let marker = null;
let apiKey = ''; 

function initLeafletMap(containerId, geoapifyKey, initialLat, initialLng, isInteractive = true) {
    apiKey = geoapifyKey;
    const defaultLocation = [23.0225, 72.5714]; // Default: Ahmedabad, Gujarat

    let startLocation = defaultLocation;
    if (initialLat && initialLng) {
        startLocation = [initialLat, initialLng];
    }

    // Initialize Map
    map = L.map(containerId).setView(startLocation, 13);

    // Set Geoapify Tile Layer
    L.tileLayer(`https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png?apiKey=${apiKey}`, {
        attribution: 'Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | <a href="https://openmaptiles.org/" target="_blank">© OpenMapTiles</a> | <a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap</a>',
        maxZoom: 19
    }).addTo(map);

    // Initialize Marker
    marker = L.marker(startLocation, { draggable: isInteractive }).addTo(map);

    if (isInteractive) {
        // Handle Marker Drag
        marker.on('dragend', function (e) {
            const position = marker.getLatLng();
            updateLocationFields(position.lat, position.lng);
        });

        // Handle Map Click
        map.on('click', function (e) {
            marker.setLatLng(e.latlng);
            updateLocationFields(e.latlng.lat, e.latlng.lng);
        });

        // Try HTML5 geolocation if no initial coordinates are passed
        if (!initialLat || !initialLng) {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const pos = [position.coords.latitude, position.coords.longitude];
                        map.setView(pos, 15);
                        marker.setLatLng(pos);
                        updateLocationFields(pos[0], pos[1]);
                    },
                    (error) => {
                        console.warn("Geolocation failed or blocked, falling back to default.", error);
                        // Default location is already set
                    }
                );
            }
        }
    }
}

/**
 * Updates the hidden latitude/longitude fields and performs Reverse Geocoding.
 */
function updateLocationFields(lat, lng) {
    const latField = document.getElementById('id_latitude');
    const lngField = document.getElementById('id_longitude');
    
    if (latField) latField.value = lat.toFixed(6);
    if (lngField) lngField.value = lng.toFixed(6);

    reverseGeocode(lat, lng);
}

/**
 * Uses Geoapify Reverse Geocoding API via Fetch API.
 */
function reverseGeocode(lat, lng) {
    const addressField = document.getElementById('id_address');
    const overlay = document.getElementById('map-loading');
    const alertContainer = document.getElementById('map-alert');

    if (!addressField) return;

    // Show loading spinner
    if (overlay) overlay.classList.add('active');
    
    // Clear previous alerts
    if (alertContainer) alertContainer.innerHTML = '';

    const url = `https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lng}&apiKey=${apiKey}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.features && data.features.length > 0) {
                const address = data.features[0].properties.formatted;
                addressField.value = address;
            } else {
                addressField.value = "Address not found";
                showMapAlert("Could not pinpoint an exact address here. You can enter it manually.", "warning");
            }
        })
        .catch(error => {
            console.error("Reverse geocoding failed:", error);
            addressField.value = "";
            showMapAlert("Map temporarily unavailable — you can still submit your report.", "warning");
        })
        .finally(() => {
            // Hide loading spinner
            if (overlay) overlay.classList.remove('active');
        });
}

/**
 * Displays a Bootstrap alert over the map.
 */
function showMapAlert(message, type) {
    const alertContainer = document.getElementById('map-alert');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show shadow-sm" role="alert">
                <i class="fa-solid fa-circle-exclamation me-1"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }
}
