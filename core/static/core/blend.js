function showBlendifyAlert(message, type = "success") {
    // type can be "success", "danger", "warning", "info"
    const container = document.getElementById('blendify-toast-container');
    if (!container) return;

    // Remove any existing alert
    container.innerHTML = '';

    // Create the alert div
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} mb-3 fade show`;
    alertDiv.role = "alert";
    alertDiv.innerHTML = `${message}`;

    container.appendChild(alertDiv);
}

document.addEventListener('DOMContentLoaded', function() {

    // Button Control + and -
    function updateButtons() {
        const rows = document.querySelectorAll('#input-list .input-group');
        rows.forEach((row, idx) => {
            // Remove all buttons first
            row.querySelectorAll('button').forEach(btn => btn.remove());
    
            if (idx === 0) {
                // First row: no button
                return;
            }
            else if (idx === 1) {
                // Second row: plus button
                const plusBtn = document.createElement('button');
                plusBtn.type = 'button';
                plusBtn.className = 'btn btn-success ms-2 add-btn';
                plusBtn.innerHTML = '&plus;';
                plusBtn.onclick = function() {
                    addInput();
                };
                row.appendChild(plusBtn);
            }
            else {
                // All other rows: minus button
                const minusBtn = document.createElement('button');
                minusBtn.type = 'button';
                minusBtn.className = 'btn btn-danger ms-2 remove-btn';
                minusBtn.innerHTML = '&minus;';
                minusBtn.onclick = function() {
                    row.remove();
                    updateButtons();
                };
                row.appendChild(minusBtn);
            }
        });
    }

    // Add Theme Row
    function addInput() {
        const inputList = document.getElementById('input-list');
        const newRow = document.createElement('div');
        newRow.className = 'input-group mb-2';
        newRow.innerHTML = `
            <input type="text" class="form-control" name="theme" placeholder="Enter a theme">
        `;
        inputList.appendChild(newRow);
        updateButtons();
    }

    updateButtons();

    // New Playlist Section
    const select = document.getElementById('spotify_playlist');
    const nameInput = document.getElementById('spotify_playlist_name');
    const newPlaylistSection = document.getElementById('new-playlist-section');
    const newPlaylistNameInput = document.getElementById('new_playlist_name');
    
    if (select && nameInput) {
        select.addEventListener('change', function() {
            if (select.value === 'create_new') {
                // Show the new playlist name input
                newPlaylistSection.style.display = 'block';
                nameInput.value = '';
                newPlaylistNameInput.required = true;
            } else {
                // Hide the new playlist name input
                newPlaylistSection.style.display = 'none';
                newPlaylistNameInput.required = false;
                newPlaylistNameInput.value = '';
        
                // Set the selected playlist name
                const selectedOption = select.options[select.selectedIndex];
                nameInput.value = selectedOption.text;
            }
        
            // Fetch and fill themes if not creating new
            if (select.value && select.value !== 'create_new') {
                const url = `/get_playlist_themes/?playlist_name=${encodeURIComponent(nameInput.value)}`;
                fetch(url)
                    .then(response => {
                        return response.json();
                    })
                    .then(data => {
                        const inputList = document.getElementById('input-list');
                        inputList.innerHTML = '';
                        if (data.themes && data.themes.length > 0) {
                            data.themes.forEach(theme => {
                                const newRow = document.createElement('div');
                                newRow.className = 'input-group mb-2';
                                newRow.innerHTML = `
                                    <input type="text" class="form-control" name="theme" value="${theme}" placeholder="Enter a theme">
                                `;
                                inputList.appendChild(newRow);
                            });
                        } else {
                            for (let i = 0; i < 2; i++) {
                                const newRow = document.createElement('div');
                                newRow.className = 'input-group mb-2';
                                newRow.innerHTML = `
                                    <input type="text" class="form-control" name="theme" placeholder="Enter a theme">
                                `;
                                inputList.appendChild(newRow);
                            }
                        }
                        updateButtons();
                    });
            }
        });
        
        if (select.selectedIndex > 0) {
            nameInput.value = select.options[select.selectedIndex].text;
        }
    }

    const form = document.getElementById('blendify-form');
    const submitButton = form ? form.querySelector('button[type="submit"]') : null;
    
    if (form && submitButton) {
        form.addEventListener('submit', function(e) {
            // Disable the submit button immediately
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
            submitButton.classList.add('btn-secondary');
            submitButton.classList.remove('btn-violet');
            
            // Optional: Add a loading spinner
            // submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
        });
    }

    // WebSockets
    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host + '/ws/progress/';
    const socket = new WebSocket(ws_path);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        showBlendifyAlert(data.message, data.type || "info");
    };

    socket.onclose = function(e) {
        console.log('WebSocket closed');
        // Re-enable the button if WebSocket closes unexpectedly
        if (submitButton && submitButton.disabled) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-magic"></i> Submit';
            submitButton.classList.remove('btn-secondary');
            submitButton.classList.add('btn-violet');
        }
    };

    socket.onerror = function(e) {
        console.log('WebSocket error');
        // Re-enable the button on error
        if (submitButton && submitButton.disabled) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-magic"></i> Submit';
            submitButton.classList.remove('btn-secondary');
            submitButton.classList.add('btn-violet');
        }
    };
});