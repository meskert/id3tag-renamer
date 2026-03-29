// Preview Modal Logic

// Single file edit modal logic
const editModal = document.getElementById('editModal');
if (editModal) {
    editModal.addEventListener('show.bs.modal', function (event) {
        // Reset URL when opening edit modal
        const currentMode = document.getElementById('mode')?.value || 'rename';
        window.history.replaceState(null, '', '/?mode=' + currentMode);

        const button = event.relatedTarget;
        const index = button.getAttribute('data-index');

        const artist = button.getAttribute('data-artist');
        const album = button.getAttribute('data-album');
        const title = button.getAttribute('data-title');
        const track = button.getAttribute('data-track');
        const genre = button.getAttribute('data-genre');
        const date = button.getAttribute('data-date');
        const comment = button.getAttribute('data-comment');
        const filename = button.getAttribute('data-filename');
        const filenameStem = button.getAttribute('data-filename-stem');

        document.getElementById('edit-file-index').value = index;
        document.getElementById('edit-filename').value = filenameStem;
        document.getElementById('edit-artist').value = artist;
        document.getElementById('edit-album').value = album;
        document.getElementById('edit-title').value = title;
        document.getElementById('edit-track').value = track;
        document.getElementById('edit-genre').value = genre;
        document.getElementById('edit-date').value = date;
        document.getElementById('edit-comment').value = comment;

        // Load existing album art
        const artPreview = document.getElementById('edit-album-art-preview');
        const artContainer = document.getElementById('edit-album-art-container');
        artPreview.src = `/album_art/${index}?t=${new Date().getTime()}`;
        artContainer.style.display = 'block';
        artPreview.onerror = function() {
            artContainer.style.display = 'none';
        };

        document.getElementById('editModalLabel').textContent = `Edit: ${filename}`;

        // Load audio for playback
        const editAudio = document.getElementById('edit-modal-audio');
        if (editAudio) {
            editAudio.src = `/api/stream/${index}`;
        }
    });

    editModal.addEventListener('hidden.bs.modal', function () {
        const editAudio = document.getElementById('edit-modal-audio');
        if (editAudio) {
            editAudio.pause();
            editAudio.src = '';
        }
    });
}

// Image preview for single edit modal
const editArtInput = document.getElementById('edit-album-art-input');
if (editArtInput) {
    editArtInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('edit-album-art-preview').src = e.target.result;
                document.getElementById('edit-album-art-container').style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });
}

// Auto-show preview modal setup
function autoShowPreviewModal() {
    const previewModalEl = document.getElementById('previewModal');
    if (previewModalEl && window.hasChanges) {
        const previewModal = new bootstrap.Modal(previewModalEl);
        previewModal.show();

        // Reset URL when modal is closed
        previewModalEl.addEventListener('hidden.bs.modal', function() {
            const currentMode = window.currentMode || 'rename';
            window.history.replaceState(null, '', '/?mode=' + currentMode);
        });
    }

    // Show uploaded album art in preview if manual mode and file exists
    const uploadedArt = document.getElementById('album_art');
    if (uploadedArt && uploadedArt.files && uploadedArt.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const modalImg = document.getElementById('modal-preview-img');
            const modalArtContainer = document.getElementById('modal-album-art-preview');
            if (modalImg && modalArtContainer) {
                modalImg.src = e.target.result;
                modalArtContainer.style.display = 'block';
            }
        }
        reader.readAsDataURL(uploadedArt.files[0]);
    }
}

// Initialize preview modal if needed
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoShowPreviewModal);
} else {
    autoShowPreviewModal();
}
