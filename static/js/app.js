// Main JavaScript functionality for IPTV Manager

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize file input change handler
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileExtension = file.name.split('.').pop().toLowerCase();
                if (!['m3u', 'm3u8', 'txt'].includes(fileExtension)) {
                    showAlert('Formato de arquivo não suportado. Use .m3u, .m3u8 ou .txt', 'danger');
                    this.value = '';
                    return;
                }
                
                if (file.size > 50 * 1024 * 1024) { // 50MB limit
                    showAlert('Arquivo muito grande. Tamanho máximo: 50MB', 'danger');
                    this.value = '';
                    return;
                }
            }
        });
    }

    // Initialize URL input validation
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('input', function(e) {
            const url = e.target.value;
            if (url && !isValidUrl(url)) {
                this.setCustomValidity('Por favor, insira uma URL válida');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Initialize search functionality
    initializeSearch();
    
    // Initialize channel testing
    initializeChannelTesting();

document.addEventListener('DOMContentLoaded', function() {
    const urlForm = document.querySelector('form[action$="/upload_m3u"]');
    const fileForm = document.querySelector('form[action$="/upload_m3u"][enctype="multipart/form-data"]');

    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            showLoadingMessage('Carregando a lista da URL, por favor, aguarde...');
            this.submit();
        });
    }

    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            showLoadingMessage('Carregando a lista do arquivo, por favor, aguarde...');
            this.submit();
        });
    }

    function showLoadingMessage(message) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-message';
        loadingDiv.textContent = message;
        loadingDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.75);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 9999;
        `;
        document.body.appendChild(loadingDiv);
        
        setTimeout(() => loadingDiv.remove(), 5000);
    }
});

    
    // Initialize responsive behavior
    initializeResponsive();
});

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function initializeSearch() {
    const searchForm = document.querySelector('form[action*="search"]');
    if (!searchForm) return;
    
    const searchInput = searchForm.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        
        const query = e.target.value.trim();
        if (query.length < 2) return;
        
        searchTimeout = setTimeout(() => {
            // Could implement live search here
            console.log('Searching for:', query);
        }, 300);
    });
}

function initializeChannelTesting() {
    // Global function for testing channels
    window.testChannel = function(channelId) {
        const button = event.target;
        const card = button.closest('.card');
        const statusBadge = card.querySelector('.channel-status .badge');
        
        if (button.disabled) return;
        
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testando...';
        
        fetch(`/api/channel/${channelId}/test`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'testing') {
                    // Poll for results
                    pollChannelStatus(channelId, button, statusBadge, originalText);
                } else {
                    resetButton(button, originalText);
                }
            })
            .catch(error => {
                console.error('Error testing channel:', error);
                resetButton(button, originalText);
                showToast('Erro ao testar canal', 'danger');
            });
    };
}

function pollChannelStatus(channelId, button, statusBadge, originalText) {
    const pollInterval = setInterval(() => {
        fetch(`/api/channel/${channelId}/status`)
            .then(response => response.json())
            .then(status => {
                if (status.last_checked) {
                    clearInterval(pollInterval);
                    resetButton(button, originalText);
                    
                    if (status.is_working === true) {
                        statusBadge.className = 'badge bg-success';
                        statusBadge.innerHTML = '<i class="fas fa-check-circle me-1"></i>Funcionando';
                        showToast('Canal funcionando!', 'success');
                    } else if (status.is_working === false) {
                        statusBadge.className = 'badge bg-danger';
                        statusBadge.innerHTML = '<i class="fas fa-times-circle me-1"></i>Offline';
                        showToast('Canal offline', 'warning');
                    }
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                resetButton(button, originalText);
                console.error('Error polling channel status:', error);
            });
    }, 1000);
    
    // Stop polling after 30 seconds
    setTimeout(() => {
        clearInterval(pollInterval);
        resetButton(button, originalText);
    }, 30000);
}

function resetButton(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

function initializeResponsive() {
    // Handle responsive navigation
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const navbar = document.querySelector('.navbar-collapse');
            navbar.classList.toggle('show');
        });
    }
    
    // Handle responsive cards
    function handleResponsiveCards() {
        const cards = document.querySelectorAll('.channel-card');
        const isMobile = window.innerWidth < 768;
        
        cards.forEach(card => {
            const actions = card.querySelector('.channel-actions');
            if (actions) {
                if (isMobile) {
                    actions.classList.add('d-flex', 'flex-column');
                    actions.classList.remove('flex-row');
                } else {
                    actions.classList.add('d-flex', 'flex-row');
                    actions.classList.remove('flex-column');
                }
            }
        });
    }
    
    // Initial call
    handleResponsiveCards();
    
    // Handle window resize
    window.addEventListener('resize', handleResponsiveCards);
}

// Utility functions
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text).then(() => {
        showToast('Copiado para a área de transferência!', 'success');
    }).catch(err => {
        console.error('Error copying to clipboard:', err);
        showToast('Erro ao copiar', 'danger');
    });
}

function formatDuration(seconds) {
    if (seconds < 0) return 'Duração desconhecida';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.IPTVManager = {
    showAlert,
    showToast,
    copyToClipboard,
    formatDuration,
    formatFileSize,
    debounce
};
