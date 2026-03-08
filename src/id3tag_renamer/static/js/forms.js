// Form Handling, Mode Switching, Sidebar, and Clear-Tag Logic

// ── Sidebar ──────────────────────────────────────────────────────────────────

const sidebar = document.getElementById('mode-sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

// Restore collapsed state
if (sidebar && localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
}

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
}

// ── Mode switching via sidebar buttons ───────────────────────────────────────

function applyMode(newMode) {
    const modeInput = document.getElementById('mode');
    const modeInputScan = document.getElementById('mode-input');
    const helpText = document.getElementById('pattern-help');
    const patternInput = document.getElementById('pattern');
    const patternContainer = document.getElementById('pattern-container');
    const manualFields = document.getElementById('manual-fields');
    const mainForm = document.getElementById('main-form');

    // Sync hidden inputs
    if (modeInput) modeInput.value = newMode;
    if (modeInputScan) modeInputScan.value = newMode;

    // Update URL
    window.history.replaceState(null, '', '/?mode=' + newMode);

    if (newMode === 'manual') {
        patternContainer?.classList.add('d-none');
        manualFields?.classList.remove('d-none');
        if (mainForm) mainForm.action = '/update_tags';
        updateUIFromSelection();
    } else {
        patternContainer?.classList.remove('d-none');
        manualFields?.classList.add('d-none');
        if (mainForm) mainForm.action = '/preview';
        if (newMode === 'tag') {
            if (helpText) helpText.innerHTML = 'Use %tag% format';
            if (patternInput && patternInput.value === '{artist} - {title}') {
                patternInput.value = '%artist% - %title%';
            }
        } else {
            if (helpText) helpText.innerHTML = 'Use {tag} format';
            if (patternInput && patternInput.value === '%artist% - %title%') {
                patternInput.value = '{artist} - {title}';
            }
        }
    }
}

document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const newMode = btn.dataset.mode;
        // Update active state
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyMode(newMode);
    });
});

// ── Preview button ────────────────────────────────────────────────────────────

const navPreviewBtn = document.getElementById('nav-preview-btn');
const mainForm = document.getElementById('main-form');

if (navPreviewBtn) {
    navPreviewBtn.addEventListener('click', function () {
        if (mainForm) {
            mainForm.requestSubmit();
        }
    });
}

// ── Clear-tag buttons ─────────────────────────────────────────────────────────

document.querySelectorAll('.clear-tag-btn').forEach(btn => {
    const tag = btn.dataset.tag;
    const input = document.getElementById(tag);
    if (!input) return;

    btn.addEventListener('click', () => {
        input.value = '';
        input.dataset.cleared = '1';
        input.placeholder = '(will be cleared)';
        input.classList.add('is-cleared');
    });

    // If user types again, remove the cleared marker
    input.addEventListener('input', () => {
        if (input.value !== '') {
            delete input.dataset.cleared;
            input.classList.remove('is-cleared');
        }
    });
});

// ── Form submission: attach selected files + clear_tags ──────────────────────

const mainFormElement = document.getElementById('main-form');
if (mainFormElement) {
    mainFormElement.addEventListener('submit', function (e) {
        // Remove any previously injected hidden inputs
        this.querySelectorAll('input[name="selected_files"]').forEach(el => el.remove());
        this.querySelectorAll('input[name="clear_tags"]').forEach(el => el.remove());

        // Add selected file indices
        document.querySelectorAll('.file-select:checked').forEach(checkbox => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'selected_files';
            input.value = checkbox.value;
            this.appendChild(input);
        });

        // Add clear_tags for any cleared fields
        document.querySelectorAll('.manual-tag-input[data-cleared="1"]').forEach(tagInput => {
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'clear_tags';
            hidden.value = tagInput.id;
            this.appendChild(hidden);
        });
    });
}
