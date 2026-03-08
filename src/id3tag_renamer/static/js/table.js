// Table Selection and Sorting Logic

// Select all checkbox functionality
const selectAllCheckbox = document.getElementById('select-all');
if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function(e) {
        document.querySelectorAll('.file-select').forEach(checkbox => {
            checkbox.checked = e.target.checked;
        });
        updateUIFromSelection();
    });
}

// Individual checkbox change
document.querySelectorAll('.file-select').forEach(checkbox => {
    checkbox.addEventListener('change', updateUIFromSelection);
});

// Update manual mode fields based on selected files and enable/disable preview button
function updateUIFromSelection() {
    const navPreviewBtn = document.getElementById('nav-preview-btn');
    const previewBtnText = document.getElementById('preview-btn-text');
    const selectedCheckboxes = document.querySelectorAll('.file-select:checked');
    const mode = document.getElementById('mode')?.value;

    if (navPreviewBtn) {
        navPreviewBtn.disabled = selectedCheckboxes.length === 0;
        if (previewBtnText) {
            previewBtnText.textContent = mode === 'manual' ? 'Apply' : 'Preview';
        }
    }

    if (mode !== 'manual') return;

    if (selectedCheckboxes.length === 0) {
        // No selection - clear all fields
        ['artist', 'album', 'title', 'track', 'genre', 'date', 'comment'].forEach(tag => {
            const input = document.getElementById(tag);
            if (input) {
                input.value = '';
                input.placeholder = tag.charAt(0).toUpperCase() + tag.slice(1);
                input.style.fontStyle = 'normal';
                input.style.color = '';
            }
        });
        return;
    }

    // Build files data from table rows
    const filesData = [];
    document.querySelectorAll('#files-table tbody tr').forEach((row) => {
        const checkbox = row.querySelector('.file-select');
        if (!checkbox) return;

        const cells = row.querySelectorAll('td');
        if (cells.length < 10) return;

        filesData.push({
            index: parseInt(checkbox.value),
            artist: cells[3].textContent.trim(),
            album: cells[4].textContent.trim(),
            title: cells[5].textContent.trim(),
            track: cells[6].textContent.trim(),
            genre: cells[7].textContent.trim(),
            date: cells[8].textContent.trim(),
            comment: cells[9].textContent.trim()
        });
    });

    // Get selected files data
    const selectedFiles = [];
    selectedCheckboxes.forEach(checkbox => {
        const fileIndex = parseInt(checkbox.value);
        const fileData = filesData.find(f => f.index === fileIndex);
        if (fileData) selectedFiles.push(fileData);
    });

    // Update each tag field
    ['artist', 'album', 'title', 'track', 'genre', 'date', 'comment'].forEach(tag => {
        const input = document.getElementById(tag);
        if (!input) return;

        const values = selectedFiles.map(f => f[tag]);
        const uniqueValues = [...new Set(values)];

        if (uniqueValues.length === 1) {
            // All same value
            input.value = uniqueValues[0];
            input.placeholder = tag.charAt(0).toUpperCase() + tag.slice(1);
            input.style.fontStyle = 'normal';
            input.style.color = '';
        } else {
            // Multiple different values
            input.value = '';
            input.placeholder = '<multiple values>';
            input.style.fontStyle = 'italic';
            input.style.color = '#6c757d';
        }
    });
}

// Initialize on page load
updateUIFromSelection();

// Table sorting functionality
const table = document.getElementById('files-table');
if (table) {
    const headers = table.querySelectorAll('.sortable');
    let currentSort = { column: -1, direction: 'asc' };

    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = parseInt(this.dataset.column);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Toggle direction if same column, otherwise default to ascending
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.direction = 'asc';
                currentSort.column = column;
            }

            // Remove sorting classes from all headers
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            // Add sorting class to current header
            this.classList.add(currentSort.direction);

            // Sort rows (column + 1 because of checkbox column)
            rows.sort((a, b) => {
                const aText = a.cells[column + 1].textContent.trim();
                const bText = b.cells[column + 1].textContent.trim();

                const comparison = aText.localeCompare(bText, undefined, { numeric: true, sensitivity: 'base' });
                return currentSort.direction === 'asc' ? comparison : -comparison;
            });

            // Reorder rows in DOM
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Resizable columns logic
const initResizers = () => {
    const table = document.getElementById('files-table');
    if (!table) return;

    const cols = table.querySelectorAll('thead th');
    cols.forEach(col => {
        if (col.cellIndex === 0) return; // Skip checkbox column
        const resizer = document.createElement('div');
        resizer.classList.add('resizer');
        col.appendChild(resizer);

        let startX, startWidth;

        const onMouseMove = (e) => {
            const width = startWidth + (e.pageX - startX);
            if (width > 30) {
                col.style.width = width + 'px';
                col.style.minWidth = width + 'px';
            }
        };

        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            resizer.classList.remove('resizing');
        };

        resizer.addEventListener('mousedown', (e) => {
            startX = e.pageX;
            startWidth = col.offsetWidth;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            resizer.classList.add('resizing');
            e.preventDefault();
        });
    });
};

if (table) {
    initResizers();
}
