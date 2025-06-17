document.addEventListener('DOMContentLoaded', function() {
    function updateButtons() {
        const rows = document.querySelectorAll('#input-list .input-group');
        rows.forEach((row, idx) => {
            // Remove all buttons first
            row.querySelectorAll('button').forEach(btn => btn.remove());

            if (idx === 0) {
                // Plus button only on the first row
                const plusBtn = document.createElement('button');
                plusBtn.type = 'button';
                plusBtn.className = 'btn btn-success ms-2 add-btn';
                plusBtn.innerHTML = '&plus;';
                plusBtn.onclick = function() {
                    addInput();
                };
                row.appendChild(plusBtn);
            } else {
                // Minus button on all other rows
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

    const select = document.getElementById('spotify_playlist');
    const nameInput = document.getElementById('spotify_playlist_name');
    if (select && nameInput) {
        select.addEventListener('change', function() {
            const selectedOption = select.options[select.selectedIndex];
            nameInput.value = selectedOption.text;
        });
        // Set initial value if a playlist is pre-selected
        if (select.selectedIndex > 0) {
            nameInput.value = select.options[select.selectedIndex].text;
        }
    }

    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host + '/ws/progress/';
    const socket = new WebSocket(ws_path);

    const toastEl = document.getElementById('blendify-toast');
    const toastBody = document.getElementById('blendify-toast-body');

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        toastBody.textContent = data.message;
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    };

    socket.onclose = function(e) {
        console.log('WebSocket closed');
    };
});