// Online Metadata Lookup Functionality

let lookupResults = null;
let lookupSelections = {};

// Initialize lookup button
const lookupBtn = document.getElementById('lookup-btn');
const lookupModal = document.getElementById('lookupModal');
const lookupApplyBtn = document.getElementById('lookup-apply-btn');
const lookupLoading = document.getElementById('lookup-loading');
const lookupError = document.getElementById('lookup-error');
const lookupErrorMessage = document.getElementById('lookup-error-message');
const lookupWarning = document.getElementById('lookup-warning');
const lookupWarningMessage = document.getElementById('lookup-warning-message');
const lookupResultsDiv = document.getElementById('lookup-results');
const lookupResultsContainer = document.getElementById('lookup-results-container');
const lookupUseFingerprint = document.getElementById('lookup-use-fingerprint');
const lookupSelectAllBest = document.getElementById('lookup-select-all-best');

if (lookupBtn) {
    lookupBtn.addEventListener('click', async function() {
        // Get selected files
        const selectedCheckboxes = document.querySelectorAll('.file-select:checked');

        if (selectedCheckboxes.length === 0) {
            alert('Please select at least one file to lookup metadata.');
            return;
        }

        // Get file indices
        const fileIndices = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

        // Open modal and start lookup
        const modal = new bootstrap.Modal(lookupModal);
        modal.show();

        // Reset state
        lookupResults = null;
        lookupSelections = {};
        lookupApplyBtn.disabled = true;
        lookupLoading.classList.remove('d-none');
        lookupError.classList.add('d-none');
        lookupWarning.classList.add('d-none');
        lookupResultsDiv.classList.add('d-none');
        lookupResultsContainer.innerHTML = '';
        if (lookupSelectAllBest) lookupSelectAllBest.classList.add('d-none');

        // Perform lookup
        try {
            const response = await fetch('/api/lookup_metadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_indices: fileIndices,
                    use_fingerprint: lookupUseFingerprint.checked
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            lookupResults = data.results;

            // Check for warnings
            const warnings = lookupResults.filter(r => r.warning).map(r => r.warning);
            if (warnings.length > 0) {
                lookupWarning.classList.remove('d-none');
                lookupWarningMessage.textContent = warnings[0]; // Show first warning
            }

            // Hide loading, show results
            lookupLoading.classList.add('d-none');
            lookupResultsDiv.classList.remove('d-none');
            if (lookupSelectAllBest) lookupSelectAllBest.classList.remove('d-none');

            // Display results
            displayLookupResults(lookupResults);

        } catch (error) {
            console.error('Lookup error:', error);
            lookupLoading.classList.add('d-none');
            lookupError.classList.remove('d-none');
            lookupErrorMessage.textContent = error.message || 'Failed to lookup metadata. Please try again.';
        }
    });
}

if (lookupSelectAllBest) {
    lookupSelectAllBest.addEventListener('click', function() {
        if (!lookupResults) return;

        lookupResults.forEach(result => {
            if (result.matches && result.matches.length > 0) {
                // Find the radio for the first match of this file
                // We'll use the result.index as data-file-index and matchIndex 0
                const radio = document.querySelector(`.lookup-match-radio[data-file-index="${result.index}"][value="0"]`);
                if (radio) {
                    radio.checked = true;
                    lookupSelections[result.index] = result.matches[0];
                } else {
                    // Fallback: just use the first match if radio not found for some reason
                    lookupSelections[result.index] = result.matches[0];
                }
            }
        });
        updateApplyButton();
    });
}

function displayLookupResults(results) {
    lookupResultsContainer.innerHTML = '';

    results.forEach((result, resultIndex) => {
        // Clone template
        const template = document.getElementById('lookup-file-result-template');
        const fileResultDiv = template.content.cloneNode(true);

        // Set filename
        fileResultDiv.querySelector('.lookup-filename').textContent = result.filename;

        // Set current tags
        const currentTags = result.existing_tags;
        const currentTagsStr = `${currentTags.artist || 'No Artist'} - ${currentTags.title || 'No Title'}`;
        fileResultDiv.querySelector('.lookup-current-tags').textContent = currentTagsStr;

        const matchesList = fileResultDiv.querySelector('.lookup-matches-list');
        const noMatchesDiv = fileResultDiv.querySelector('.lookup-no-matches');

        if (result.error) {
            noMatchesDiv.textContent = `Error: ${result.error}`;
            noMatchesDiv.classList.remove('d-none');
        } else if (!result.matches || result.matches.length === 0) {
            noMatchesDiv.classList.remove('d-none');
        } else {
            // Set match count
            fileResultDiv.querySelector('.lookup-match-count').textContent = `${result.matches.length} matches found`;

            // Add matches
            result.matches.forEach((match, matchIndex) => {
                const matchTemplate = document.getElementById('lookup-match-template');
                const matchItem = matchTemplate.content.cloneNode(true);

                const radio = matchItem.querySelector('.lookup-match-radio');
                const radioName = `lookup-match-${result.index}`;
                radio.name = radioName;
                radio.value = matchIndex;
                radio.dataset.fileIndex = result.index;
                radio.dataset.resultIndex = resultIndex;

                // Event listener for selection
                radio.addEventListener('change', function() {
                    if (this.checked) {
                        lookupSelections[result.index] = match;
                        updateApplyButton();
                    }
                });

                // Set match details
                matchItem.querySelector('.lookup-match-title').textContent = match.title;
                matchItem.querySelector('.lookup-match-artist').textContent = match.artist;
                matchItem.querySelector('.lookup-match-score').textContent = `${Math.round(match.score || 0)}%`;

                // Set optional fields
                const albumSpan = matchItem.querySelector('.lookup-match-album');
                const dateSpan = matchItem.querySelector('.lookup-match-date');
                const trackSpan = matchItem.querySelector('.lookup-match-track');
                const genreSpan = matchItem.querySelector('.lookup-match-genre');

                if (match.album) {
                    albumSpan.textContent = `Album: ${match.album}`;
                } else {
                    albumSpan.remove();
                    matchItem.querySelector('.lookup-match-separator').remove();
                }

                if (match.date) {
                    dateSpan.textContent = match.date;
                } else {
                    dateSpan.remove();
                }

                if (match.track) {
                    trackSpan.textContent = `Track: ${match.track}`;
                } else {
                    trackSpan.remove();
                    matchItem.querySelector('.lookup-match-track-separator')?.remove();
                }

                if (match.genre) {
                    genreSpan.textContent = match.genre;
                } else {
                    genreSpan.remove();
                    matchItem.querySelector('.lookup-match-genre-separator')?.remove();
                }

                matchesList.appendChild(matchItem);
            });
        }

        lookupResultsContainer.appendChild(fileResultDiv);
    });
}

function updateApplyButton() {
    // Enable apply button if at least one selection is made
    if (Object.keys(lookupSelections).length > 0) {
        lookupApplyBtn.disabled = false;
    } else {
        lookupApplyBtn.disabled = true;
    }
}

// Apply selected metadata
if (lookupApplyBtn) {
    lookupApplyBtn.addEventListener('click', async function() {
        if (Object.keys(lookupSelections).length === 0) {
            alert('Please select at least one match to apply.');
            return;
        }

        lookupApplyBtn.disabled = true;
        lookupApplyBtn.textContent = 'Applying…';

        try {
            const updates = Object.entries(lookupSelections).map(([index, match]) => ({
                index: parseInt(index),
                tags: {
                    artist: match.artist,
                    album: match.album,
                    title: match.title,
                    track: match.track,
                    genre: match.genre,
                    date: match.date
                }
            }));

            const response = await fetch('/api/apply_metadata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ updates, apply_directly: true })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const modal = bootstrap.Modal.getInstance(lookupModal);
            modal.hide();
            window.location.href = `/?mode=manual`;

        } catch (error) {
            console.error('Apply error:', error);
            alert('Failed to apply metadata: ' + error.message);
            lookupApplyBtn.disabled = false;
            lookupApplyBtn.textContent = 'Apply Selected';
        }
    });
}
