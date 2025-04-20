// MySpot Web Player - Frontend JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const playBtn = document.getElementById('play-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const shuffleBtn = document.getElementById('shuffle-btn');
    const muteBtn = document.getElementById('mute-btn');
    const volumeSlider = document.getElementById('volume-slider');
    const volumeDisplay = document.getElementById('volume-display');
    const trackName = document.getElementById('track-name');
    const trackInfo = document.getElementById('track-info');
    const tracksList = document.getElementById('tracks-list');
    const directoryBtn = document.getElementById('directory-btn');
    const directoryDisplay = document.getElementById('directory-display');
    const directoryModal = document.getElementById('directory-modal');
    const closeModal = document.querySelector('.close-modal');
    const directoryInput = document.getElementById('directory-input');
    const confirmDirectory = document.getElementById('confirm-directory');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Player state
    let currentState = {
        playing: false,
        paused: false,
        muted: false,
        volume: 0.5,
        currentTrack: null,
        tracks: []
    };

    // Update interval for status polling
    const STATUS_UPDATE_INTERVAL = 1000; // 1 second

    // Initialize app
    init();

    async function init() {
        // Show loading overlay
        showLoading('Initializing player...');
        
        // Load initial state
        await fetchStatus();
        await fetchTracks();
        await fetchDirectory();
        
        // Hide loading overlay
        hideLoading();
        
        // Set up update interval
        setInterval(updateStatus, STATUS_UPDATE_INTERVAL);
        
        // Set up event listeners
        setupEventListeners();
    }

    function setupEventListeners() {
        // Playback controls
        playBtn.addEventListener('click', togglePlayPause);
        prevBtn.addEventListener('click', previousTrack);
        nextBtn.addEventListener('click', nextTrack);
        shuffleBtn.addEventListener('click', shufflePlaylist);
        
        // Volume controls
        muteBtn.addEventListener('click', toggleMute);
        volumeSlider.addEventListener('input', handleVolumeChange);
        
        // Directory controls
        directoryBtn.addEventListener('click', () => directoryModal.classList.remove('hidden'));
        closeModal.addEventListener('click', () => directoryModal.classList.add('hidden'));
        confirmDirectory.addEventListener('click', changeDirectory);
        
        // Close modal if clicking outside content
        directoryModal.addEventListener('click', (e) => {
            if (e.target === directoryModal) {
                directoryModal.classList.add('hidden');
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                togglePlayPause();
            } else if (e.key === 'ArrowRight' || e.key === 'n') {
                nextTrack();
            } else if (e.key === 'ArrowLeft' || e.key === 'p') {
                previousTrack();
            } else if (e.key === 'm') {
                toggleMute();
            }
        });
    }

    // API Functions
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            updatePlayerState(data);
            updateUI();
            
            return data;
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }

    async function fetchTracks() {
        try {
            const response = await fetch('/api/tracks');
            const data = await response.json();
            
            if (data.tracks) {
                currentState.tracks = data.tracks;
                renderTracksList();
            }
            
            return data;
        } catch (error) {
            console.error('Error fetching tracks:', error);
        }
    }

    async function fetchDirectory() {
        try {
            const response = await fetch('/api/directory');
            const data = await response.json();
            
            if (data.directory) {
                directoryDisplay.textContent = formatDirectoryPath(data.directory);
                directoryInput.value = data.directory;
            }
            
            return data;
        } catch (error) {
            console.error('Error fetching directory:', error);
        }
    }

    async function togglePlayPause() {
        try {
            const response = await fetch('/api/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            await fetchStatus();
        } catch (error) {
            console.error('Error toggling playback:', error);
        }
    }

    async function nextTrack() {
        try {
            showLoading('Loading next track...');
            
            const response = await fetch('/api/next', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            await fetchStatus();
            await fetchTracks();
            
            hideLoading();
        } catch (error) {
            console.error('Error playing next track:', error);
            hideLoading();
        }
    }

    async function previousTrack() {
        try {
            showLoading('Loading previous track...');
            
            const response = await fetch('/api/previous', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            await fetchStatus();
            await fetchTracks();
            
            hideLoading();
        } catch (error) {
            console.error('Error playing previous track:', error);
            hideLoading();
        }
    }

    async function playTrack(index) {
        try {
            showLoading('Loading track...');
            
            const response = await fetch('/api/play', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index })
            });
            
            await fetchStatus();
            await fetchTracks();
            
            hideLoading();
        } catch (error) {
            console.error('Error playing track:', error);
            hideLoading();
        }
    }

    async function toggleMute() {
        try {
            const response = await fetch('/api/mute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentState.muted = data.muted;
                updateUI();
            }
        } catch (error) {
            console.error('Error toggling mute:', error);
        }
    }

    async function handleVolumeChange() {
        const volume = volumeSlider.value / 100;
        volumeDisplay.textContent = `${volumeSlider.value}%`;
        
        try {
            const response = await fetch('/api/volume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ volume })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentState.volume = data.volume;
            }
        } catch (error) {
            console.error('Error setting volume:', error);
        }
    }

    async function changeDirectory() {
        const directory = directoryInput.value.trim();
        
        if (!directory) return;
        
        try {
            directoryModal.classList.add('hidden');
            showLoading('Loading music directory...');
            
            const response = await fetch('/api/directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ directory })
            });
            
            const data = await response.json();
            
            if (data.success) {
                directoryDisplay.textContent = formatDirectoryPath(data.directory);
                await fetchTracks();
                await fetchStatus();
            } else {
                alert(`Error: ${data.message}`);
            }
            
            hideLoading();
        } catch (error) {
            console.error('Error changing directory:', error);
            hideLoading();
        }
    }

    async function shufflePlaylist() {
        try {
            showLoading('Shuffling playlist...');
            
            const response = await fetch('/api/shuffle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            await fetchStatus();
            await fetchTracks();
            
            hideLoading();
        } catch (error) {
            console.error('Error shuffling playlist:', error);
            hideLoading();
        }
    }

    // UI Update Functions
    async function updateStatus() {
        // Only fetch status if not in a loading state
        if (loadingOverlay.classList.contains('hidden')) {
            await fetchStatus();
        }
    }

    function updatePlayerState(data) {
        currentState.playing = data.playing;
        currentState.paused = data.paused;
        currentState.muted = data.muted;
        currentState.volume = data.volume;
        currentState.currentTrack = data.current_track;
    }

    function updateUI() {
        // Update play/pause button
        if (currentState.playing) {
            playBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
        } else {
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        }
        
        // Update mute button
        if (currentState.muted) {
            muteBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
        } else {
            muteBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
        }
        
        // Update volume display
        const volumePercent = Math.round(currentState.volume * 100);
        volumeSlider.value = volumePercent;
        volumeDisplay.textContent = `${volumePercent}%`;
        
        // Update track info
        if (currentState.currentTrack) {
            trackName.textContent = currentState.currentTrack.filename;
            trackInfo.textContent = `Track ${currentState.currentTrack.index} of ${currentState.currentTrack.total}`;
        } else {
            trackName.textContent = 'No track playing';
            trackInfo.textContent = '';
        }
    }

    function renderTracksList() {
        if (!currentState.tracks || currentState.tracks.length === 0) {
            tracksList.innerHTML = '<div class="empty-playlist">No tracks loaded. Open a music directory to get started.</div>';
            return;
        }
        
        let html = '';
        
        currentState.tracks.forEach((track, index) => {
            const isPlaying = track.is_current;
            
            html += `
                <div class="track-item ${isPlaying ? 'playing' : ''}" data-index="${track.index}">
                    <div class="track-number">${track.index + 1}</div>
                    <div class="track-info">${track.filename}</div>
                </div>
            `;
        });
        
        tracksList.innerHTML = html;
        
        // Add click listeners to track items
        document.querySelectorAll('.track-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                playTrack(index);
            });
        });
    }

    // Helper Functions
    function showLoading(message) {
        document.getElementById('loading-message').textContent = message;
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    function formatDirectoryPath(path) {
        // Truncate very long paths for display
        if (path.length > 40) {
            const parts = path.split(/[\/\\]/);
            if (parts.length > 4) {
                return `.../${parts.slice(-3).join('/')}`;
            }
        }
        return path;
    }
});