// Directory Browser Logic
const musicRoot = window.musicRootPath || "";
let currentBrowserPath = "";
let selectedFullPath = window.currentDirectory || "";

const browseModal = document.getElementById('browseModal');
const browserList = document.getElementById('browser-list');
const browserBreadcrumbs = document.getElementById('browser-breadcrumbs');
const selectedPathDisplay = document.getElementById('selected-path-display');
const confirmBrowseBtn = document.getElementById('confirm-browse');
const directoryInput = document.getElementById('directory');

async function loadDirectories(path) {
    currentBrowserPath = path;
    browserList.innerHTML = '<div class="text-center p-3"><div class="spinner-border" role="status"></div></div>';

    try {
        const response = await fetch(`/api/directories?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        browserList.innerHTML = '';
        if (data.directories.length === 0 && path !== "") {
            // This case shouldn't happen much with ".." always there except at root
        }

        data.directories.forEach(dir => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';

            let icon = '📁';
            if (dir.name === '..') icon = '⬆️';

            button.innerHTML = `<span>${icon} ${dir.name}</span>`;
            button.onclick = () => loadDirectories(dir.path);
            browserList.appendChild(button);
        });

        if (data.directories.length === 0) {
            browserList.innerHTML = '<div class="list-group-item text-muted">No subdirectories found</div>';
        }

        // Update breadcrumbs
        updateBreadcrumbs(data.current_path);

        // Update selected display
        selectedFullPath = data.full_path;
        selectedPathDisplay.textContent = selectedFullPath;

    } catch (error) {
        browserList.innerHTML = `<div class="alert alert-danger">Error loading directories: ${error}</div>`;
    }
}

function updateBreadcrumbs(currentPath) {
    browserBreadcrumbs.innerHTML = '<li class="breadcrumb-item"><a href="#" onclick="loadDirectories(\'\'); return false;">Root</a></li>';
    if (currentPath) {
        const parts = currentPath.split('/');
        let cumulativePath = '';
        parts.forEach((part, index) => {
            if (part) {
                cumulativePath += (cumulativePath ? '/' : '') + part;
                const li = document.createElement('li');
                li.className = 'breadcrumb-item' + (index === parts.length - 1 ? ' active' : '');
                if (index === parts.length - 1) {
                    li.textContent = part;
                } else {
                    const a = document.createElement('a');
                    a.href = '#';
                    const pathForLink = cumulativePath;
                    a.onclick = () => { loadDirectories(pathForLink); return false; };
                    a.textContent = part;
                    li.appendChild(a);
                }
                browserBreadcrumbs.appendChild(li);
            }
        });
    }
}

if (browseModal) {
    browseModal.addEventListener('show.bs.modal', function () {
        // Initialize from current input value if possible, or root
        let initialPath = "";
        const currentInput = directoryInput.value;
        if (currentInput.startsWith(musicRoot)) {
            initialPath = currentInput.substring(musicRoot.length).replace(/^\//, '');
        }
        loadDirectories(initialPath);
    });
}

if (confirmBrowseBtn) {
    confirmBrowseBtn.onclick = () => {
        directoryInput.value = selectedFullPath;
        bootstrap.Modal.getInstance(browseModal).hide();
        // Automatically scan when directory is confirmed
        if (directoryInput.value) {
            directoryInput.closest('form').submit();
        }
    };
}
