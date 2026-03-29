const miniPlayer = document.getElementById('mini-player');
const playerAudio = document.getElementById('player-audio');
const playerFilename = document.getElementById('player-filename');
const playerClose = document.getElementById('player-close');

let currentPlayIndex = null;

function setPlayBtn(index, playing) {
    const btn = document.querySelector(`.play-btn[data-index="${index}"]`);
    if (btn) btn.querySelector('small').textContent = playing ? '⏸' : '▶';
}

document.addEventListener('click', (e) => {
    const btn = e.target.closest('.play-btn');
    if (!btn) return;

    const index = btn.dataset.index;
    const filename = btn.dataset.filename;

    // Toggle pause if same track
    if (currentPlayIndex === index) {
        if (playerAudio.paused) {
            playerAudio.play();
            setPlayBtn(index, true);
        } else {
            playerAudio.pause();
            setPlayBtn(index, false);
        }
        return;
    }

    // Switch track
    if (currentPlayIndex !== null) setPlayBtn(currentPlayIndex, false);
    currentPlayIndex = index;

    playerAudio.src = `/api/stream/${index}`;
    playerFilename.textContent = filename;
    miniPlayer.classList.remove('d-none');
    playerAudio.play();
    setPlayBtn(index, true);
});

playerAudio.addEventListener('ended', () => {
    if (currentPlayIndex !== null) setPlayBtn(currentPlayIndex, false);
});

playerAudio.addEventListener('pause', () => {
    if (currentPlayIndex !== null) setPlayBtn(currentPlayIndex, false);
});

playerAudio.addEventListener('play', () => {
    if (currentPlayIndex !== null) setPlayBtn(currentPlayIndex, true);
});

playerClose.addEventListener('click', () => {
    playerAudio.pause();
    playerAudio.src = '';
    if (currentPlayIndex !== null) setPlayBtn(currentPlayIndex, false);
    currentPlayIndex = null;
    miniPlayer.classList.add('d-none');
});
