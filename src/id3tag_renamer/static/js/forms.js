// Form Handling and Mode Switching Logic

// Nav preview button functionality
const navPreviewBtn = document.getElementById('nav-preview-btn');
const mainForm = document.getElementById('main-form');

if (navPreviewBtn) {
    navPreviewBtn.addEventListener('click', function() {
        if (mainForm) {
            mainForm.requestSubmit();
        }
    });
}

// Mode change logic - sync navbar mode selector with hidden input
const modeNav = document.getElementById('mode-nav');
const modeInput = document.getElementById('mode');
const modeInputScan = document.getElementById('mode-input');

if (modeNav) {
    modeNav.addEventListener('change', function(e) {
        const newMode = e.target.value;

        // Reset URL when mode changes
        window.history.replaceState(null, '', '/?mode=' + newMode);

        // Update hidden inputs
        if (modeInput) modeInput.value = newMode;
        if (modeInputScan) modeInputScan.value = newMode;

        // Update UI
        const helpText = document.getElementById('pattern-help');
        const patternInput = document.getElementById('pattern');
        const patternContainer = document.getElementById('pattern-container');
        const manualFields = document.getElementById('manual-fields');
        const mainForm = document.getElementById('main-form');

        if (newMode === 'tag') {
            if (patternContainer) patternContainer.style.display = 'block';
            if (manualFields) manualFields.style.display = 'none';
            if (mainForm) mainForm.action = '/preview';
            if (helpText) helpText.innerHTML = 'Use %tag% format';
            if (patternInput && patternInput.value === '{artist} - {title}') {
                patternInput.value = '%artist% - %title%';
            }
        } else if (newMode === 'manual') {
            if (patternContainer) patternContainer.style.display = 'none';
            if (manualFields) manualFields.style.display = 'block';
            if (mainForm) mainForm.action = '/update_tags';
            updateUIFromSelection();
        } else {
            if (patternContainer) patternContainer.style.display = 'block';
            if (manualFields) manualFields.style.display = 'none';
            if (mainForm) mainForm.action = '/preview';
            if (helpText) helpText.innerHTML = 'Use {tag} format';
            if (patternInput && patternInput.value === '%artist% - %title%') {
                patternInput.value = '{artist} - {title}';
            }
        }
    });
}

// Add selected file indices to form submission
const mainFormElement = document.getElementById('main-form');
if (mainFormElement) {
    mainFormElement.addEventListener('submit', function(e) {
        // Remove any existing hidden inputs for selected files
        this.querySelectorAll('input[name="selected_files"]').forEach(el => el.remove());

        // Add selected file indices
        document.querySelectorAll('.file-select:checked').forEach(checkbox => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'selected_files';
            input.value = checkbox.value;
            this.appendChild(input);
        });
    });
}
