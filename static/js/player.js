// Video player functionality for IPTV Manager

class IPTVPlayer {
    constructor(videoElement) {
        this.video = videoElement;
        this.isPlaying = false;
        this.isMuted = false;
        this.isFullscreen = false;
        
        this.initializePlayer();
        this.setupEventListeners();
    }
    
    initializePlayer() {
        // Set up video attributes
        this.video.setAttribute('playsinline', '');
        this.video.setAttribute('preload', 'metadata');
        
        // Try to enable HLS support
        if (this.video.canPlayType('application/vnd.apple.mpegurl')) {
            console.log('Native HLS support detected');
        } else {
            console.log('No native HLS support, may need additional library');
        }
    }
    
    setupEventListeners() {
        // Video events
        this.video.addEventListener('loadstart', () => {
            console.log('Video loading started');
        });
        
        this.video.addEventListener('loadedmetadata', () => {
            console.log('Video metadata loaded');
        });
        
        this.video.addEventListener('loadeddata', () => {
            console.log('Video data loaded');
        });
        
        this.video.addEventListener('canplay', () => {
            console.log('Video can start playing');
        });
        
        this.video.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayButton();
        });
        
        this.video.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButton();
        });
        
        this.video.addEventListener('ended', () => {
            this.isPlaying = false;
            this.updatePlayButton();
        });
        
        this.video.addEventListener('error', (e) => {
            console.error('Video error:', e);
            this.handleVideoError(e);
        });
        
        this.video.addEventListener('volumechange', () => {
            this.isMuted = this.video.muted;
            this.updateVolumeButton();
        });
        
        // Fullscreen events
        document.addEventListener('fullscreenchange', () => {
            this.isFullscreen = !!document.fullscreenElement;
            this.updateFullscreenButton();
        });
        
        document.addEventListener('webkitfullscreenchange', () => {
            this.isFullscreen = !!document.webkitFullscreenElement;
            this.updateFullscreenButton();
        });
        
        document.addEventListener('mozfullscreenchange', () => {
            this.isFullscreen = !!document.mozFullScreenElement;
            this.updateFullscreenButton();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName.toLowerCase() === 'input') return;
            
            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    this.togglePlay();
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    this.toggleMute();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.seek(-10);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.seek(10);
                    break;
            }
        });
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.video.pause();
        } else {
            this.video.play().catch(e => {
                console.error('Play failed:', e);
                this.handlePlayError(e);
            });
        }
    }
    
    toggleMute() {
        this.video.muted = !this.video.muted;
    }
    
    toggleFullscreen() {
        if (!this.isFullscreen) {
            this.enterFullscreen();
        } else {
            this.exitFullscreen();
        }
    }
    
    enterFullscreen() {
        const element = this.video.parentElement;
        
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }
    }
    
    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
    
    seek(seconds) {
        if (this.video.currentTime !== undefined) {
            this.video.currentTime = Math.max(0, Math.min(this.video.duration, this.video.currentTime + seconds));
        }
    }
    
    updatePlayButton() {
        const playIcon = document.getElementById('playIcon');
        if (playIcon) {
            playIcon.className = this.isPlaying ? 'fas fa-pause' : 'fas fa-play';
        }
    }
    
    updateVolumeButton() {
        const volumeIcon = document.getElementById('volumeIcon');
        if (volumeIcon) {
            volumeIcon.className = this.isMuted ? 'fas fa-volume-mute' : 'fas fa-volume-up';
        }
    }
    
    updateFullscreenButton() {
        const fullscreenIcon = document.querySelector('.fa-expand, .fa-compress');
        if (fullscreenIcon) {
            fullscreenIcon.className = this.isFullscreen ? 'fas fa-compress' : 'fas fa-expand';
        }
    }
    
    handleVideoError(e) {
        const error = e.target.error;
        let message = 'Erro desconhecido ao reproduzir vídeo';
        
        if (error) {
            switch(error.code) {
                case error.MEDIA_ERR_ABORTED:
                    message = 'Reprodução abortada';
                    break;
                case error.MEDIA_ERR_NETWORK:
                    message = 'Erro de rede';
                    break;
                case error.MEDIA_ERR_DECODE:
                    message = 'Erro de decodificação';
                    break;
                case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    message = 'Formato não suportado';
                    break;
            }
        }
        
        this.showError(message);
    }
    
    handlePlayError(e) {
        let message = 'Erro ao iniciar reprodução';
        
        if (e.name === 'NotAllowedError') {
            message = 'Reprodução bloqueada. Clique no botão play para assistir.';
        } else if (e.name === 'NotSupportedError') {
            message = 'Formato de vídeo não suportado pelo navegador';
        }
        
        this.showError(message);
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger mt-3';
        errorDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>Erro de Reprodução</strong>
                    <div class="small">${message}</div>
                </div>
            </div>
        `;
        
        const container = this.video.parentElement;
        container.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 10000);
    }
}

// Global functions for player controls
window.togglePlay = function() {
    if (window.iptvPlayer) {
        window.iptvPlayer.togglePlay();
    }
};

window.toggleMute = function() {
    if (window.iptvPlayer) {
        window.iptvPlayer.toggleMute();
    }
};

window.toggleFullscreen = function() {
    if (window.iptvPlayer) {
        window.iptvPlayer.toggleFullscreen();
    }
};

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const videoElement = document.getElementById('videoPlayer');
    if (videoElement) {
        window.iptvPlayer = new IPTVPlayer(videoElement);
        
        // Auto-play after a short delay (if allowed)
        setTimeout(() => {
            videoElement.play().catch(e => {
                console.log('Auto-play prevented:', e);
            });
        }, 1000);
    }
});

// Additional utility functions
function formatTime(seconds) {
    if (isNaN(seconds) || seconds === Infinity) return '00:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

function updateProgress() {
    const video = document.getElementById('videoPlayer');
    if (!video) return;
    
    const progressBar = document.getElementById('progressBar');
    const currentTimeDisplay = document.getElementById('currentTime');
    const durationDisplay = document.getElementById('duration');
    
    if (progressBar && video.duration) {
        const progress = (video.currentTime / video.duration) * 100;
        progressBar.style.width = progress + '%';
    }
    
    if (currentTimeDisplay) {
        currentTimeDisplay.textContent = formatTime(video.currentTime);
    }
    
    if (durationDisplay) {
        durationDisplay.textContent = formatTime(video.duration);
    }
}

// Update progress every second
setInterval(updateProgress, 1000);

// Volume control
function setVolume(volume) {
    const video = document.getElementById('videoPlayer');
    if (video) {
        video.volume = Math.max(0, Math.min(1, volume));
    }
}

// Quality selection (if supported)
function changeQuality(quality) {
    console.log('Quality change requested:', quality);
    // This would need to be implemented based on the streaming format
}

// Playback speed control
function changeSpeed(speed) {
    const video = document.getElementById('videoPlayer');
    if (video) {
        video.playbackRate = speed;
    }
}

// Picture-in-Picture support
function togglePictureInPicture() {
    const video = document.getElementById('videoPlayer');
    if (!video) return;
    
    if (document.pictureInPictureElement) {
        document.exitPictureInPicture();
    } else if (document.pictureInPictureEnabled) {
        video.requestPictureInPicture().catch(error => {
            console.error('Picture-in-Picture failed:', error);
        });
    }
}

// Export player utilities
window.IPTVPlayerUtils = {
    formatTime,
    updateProgress,
    setVolume,
    changeQuality,
    changeSpeed,
    togglePictureInPicture
};
