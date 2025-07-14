def generate_offline_html(m3u_content):
    """Generate complete offline HTML with all dependencies embedded"""
    
    # FontAwesome icons as Unicode
    icon_mappings = {
        'fas fa-film': '🎬',
        'fas fa-th': '⊞',
        'fas fa-list': '☰',
        'fas fa-download': '⬇',
        'fas fa-code': '⌨',
        'fas fa-search': '🔍',
        'fas fa-info-circle': 'ℹ',
        'fas fa-play': '▶',
        'fas fa-copy': '📋',
        'fas fa-check-circle': '✓',
        'fas fa-times': '✕'
    }
    
    html_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Navegador de Filmes M3U - Offline</title>
    <style>
        /* Reset e base */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #0d6efd;
            --secondary: #6c757d;
            --success: #198754;
            --info: #0dcaf0;
            --warning: #ffc107;
            --danger: #dc3545;
            --light: #f8f9fa;
            --dark: #212529;
            --gray-100: #f8f9fa;
            --gray-200: #e9ecef;
            --gray-300: #dee2e6;
            --gray-400: #ced4da;
            --gray-500: #adb5bd;
            --gray-600: #6c757d;
            --gray-700: #495057;
            --gray-800: #343a40;
            --gray-900: #212529;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--gray-900);
            color: var(--light);
            line-height: 1.5;
        }
        
        .container-fluid { 
            max-width: 100%; 
            margin: 0 auto; 
            padding: 0 15px; 
        }
        
        /* Botões */
        .btn {
            display: inline-block;
            padding: 0.375rem 0.75rem;
            margin-bottom: 0;
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.5;
            text-align: center;
            text-decoration: none;
            vertical-align: middle;
            cursor: pointer;
            user-select: none;
            border: 1px solid transparent;
            border-radius: 0.375rem;
            transition: all 0.15s ease-in-out;
        }
        
        .btn-primary { background-color: var(--primary); border-color: var(--primary); color: white; }
        .btn-success { background-color: var(--success); border-color: var(--success); color: white; }
        .btn-info { background-color: var(--info); border-color: var(--info); color: black; }
        .btn-warning { background-color: var(--warning); border-color: var(--warning); color: black; }
        .btn-outline-primary { border-color: var(--primary); color: var(--primary); background: transparent; }
        .btn-outline-success { border-color: var(--success); color: var(--success); background: transparent; }
        .btn-outline-info { border-color: var(--info); color: var(--info); background: transparent; }
        .btn-outline-secondary { border-color: var(--secondary); color: var(--secondary); background: transparent; }
        
        .btn:hover { opacity: 0.85; }
        .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
        
        /* Grid e Layout */
        .row { display: flex; flex-wrap: wrap; margin-left: -0.75rem; margin-right: -0.75rem; }
        .col-12 { flex: 0 0 100%; max-width: 100%; padding: 0 0.75rem; }
        .col-md-6 { flex: 0 0 50%; max-width: 50%; padding: 0 0.75rem; }
        .col-md-3 { flex: 0 0 25%; max-width: 25%; padding: 0 0.75rem; }
        .col-6 { flex: 0 0 50%; max-width: 50%; padding: 0 0.75rem; }
        
        @media (max-width: 768px) {
            .col-md-6, .col-md-3 { flex: 0 0 100%; max-width: 100%; }
        }
        
        /* Formulários */
        .form-control, .form-select {
            display: block;
            width: 100%;
            padding: 0.375rem 0.75rem;
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.5;
            color: var(--light);
            background-color: var(--gray-800);
            border: 1px solid var(--gray-600);
            border-radius: 0.375rem;
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: var(--primary);
            outline: 0;
            box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
        }
        
        .input-group {
            position: relative;
            display: flex;
            flex-wrap: wrap;
            align-items: stretch;
            width: 100%;
        }
        
        .input-group-text {
            display: flex;
            align-items: center;
            padding: 0.375rem 0.75rem;
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.5;
            color: var(--light);
            text-align: center;
            white-space: nowrap;
            background-color: var(--gray-700);
            border: 1px solid var(--gray-600);
            border-radius: 0.375rem;
            border-top-right-radius: 0;
            border-bottom-right-radius: 0;
        }
        
        .input-group .form-control {
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }
        
        /* Utilitários */
        .d-flex { display: flex; }
        .justify-content-between { justify-content: space-between; }
        .align-items-center { align-items: center; }
        .text-center { text-align: center; }
        .mb-0 { margin-bottom: 0; }
        .mb-3 { margin-bottom: 1rem; }
        .me-2 { margin-right: 0.5rem; }
        .gap-2 { gap: 0.5rem; }
        .h3 { font-size: 1.75rem; }
        .h4 { font-size: 1.5rem; }
        .text-primary { color: var(--primary); }
        .text-success { color: var(--success); }
        .text-info { color: var(--info); }
        .text-warning { color: var(--warning); }
        .text-muted { color: var(--gray-500); }
        
        /* Spinner */
        .spinner-border {
            display: inline-block;
            width: 2rem;
            height: 2rem;
            vertical-align: text-bottom;
            border: 0.25em solid currentColor;
            border-right-color: transparent;
            border-radius: 50%;
            animation: spinner-border 0.75s linear infinite;
        }
        
        @keyframes spinner-border {
            to { transform: rotate(360deg); }
        }
        
        .visually-hidden {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* Modal */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            z-index: 1050;
            display: none;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: rgba(0, 0, 0, 0.5);
        }
        
        .modal.show { display: block; }
        
        .modal-dialog {
            position: relative;
            width: auto;
            margin: 1.75rem auto;
            max-width: 800px;
        }
        
        .modal-content {
            position: relative;
            background-color: var(--gray-800);
            border: 1px solid var(--gray-600);
            border-radius: 0.375rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            border-bottom: 1px solid var(--gray-600);
        }
        
        .modal-title {
            margin-bottom: 0;
            line-height: 1.5;
        }
        
        .modal-body {
            position: relative;
            flex: 1 1 auto;
            padding: 1rem;
        }
        
        .btn-close {
            box-sizing: content-box;
            width: 1em;
            height: 1em;
            padding: 0.25em;
            color: var(--light);
            background: transparent;
            border: 0;
            border-radius: 0.375rem;
            opacity: 0.5;
            cursor: pointer;
        }
        
        .btn-close:hover { opacity: 0.75; }
        
        .btn-close::before {
            content: "✕";
            font-size: 1rem;
        }
        
        .img-fluid {
            max-width: 100%;
            height: auto;
        }
        
        .rounded {
            border-radius: 0.375rem;
        }
        
        /* Componentes específicos do M3U */
        .movie-card {
            height: 400px;
            border: 1px solid var(--gray-700);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background: var(--dark);
        }
        
        .movie-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
        }
        
        .movie-poster {
            height: 250px;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            position: relative;
        }
        
        .movie-poster img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: opacity 0.3s ease;
        }
        
        .movie-poster .no-image {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: white;
            font-size: 2rem;
        }
        
        .movie-info {
            padding: 1rem;
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .movie-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            line-height: 1.2;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        .movie-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: auto;
        }
        
        .search-container {
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--dark);
            padding: 1rem 0;
            border-bottom: 1px solid var(--gray-700);
        }
        
        .stats-container {
            background: var(--gray-900);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .loading {
            text-align: center;
            padding: 3rem;
        }
        
        .movie-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .category-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }
        
        .no-results {
            text-align: center;
            padding: 3rem;
            color: var(--gray-400);
        }
        
        .no-results .icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .toast-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            z-index: 9999;
            animation: slideIn 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="search-container">
            <div class="row">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h1 class="h3 mb-0">
                            🎬 Navegador de Filmes M3U - Offline
                        </h1>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-primary" onclick="toggleGridView()">
                                <span id="view-icon">⊞</span>
                            </button>
                            <button class="btn btn-outline-success" onclick="exportM3U()">
                                ⬇ Exportar M3U
                            </button>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <div class="input-group">
                                <span class="input-group-text">
                                    🔍
                                </span>
                                <input type="text" class="form-control" id="searchInput" 
                                       placeholder="Buscar filmes..." onkeyup="filterMovies()">
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <select class="form-select" id="categoryFilter" onchange="filterMovies()">
                                <option value="">Todas as Categorias</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="stats-container">
                        <div class="row text-center">
                            <div class="col-6 col-md-3">
                                <div class="h4 mb-0 text-primary" id="totalMovies">0</div>
                                <small class="text-muted">Total de Filmes</small>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="h4 mb-0 text-success" id="visibleMovies">0</div>
                                <small class="text-muted">Filmes Visíveis</small>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="h4 mb-0 text-info" id="totalCategories">0</div>
                                <small class="text-muted">Categorias</small>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="h4 mb-0 text-warning" id="loadingProgress">0%</div>
                                <small class="text-muted">Carregamento</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loadingIndicator">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
            <div class="mt-2">Carregando filmes...</div>
        </div>
        
        <div class="movie-grid" id="movieGrid" style="display: none;">
            <!-- Movies will be dynamically loaded here -->
        </div>
        
        <div class="no-results" id="noResults" style="display: none;">
            <div class="icon">🔍</div>
            <h4>Nenhum filme encontrado</h4>
            <p>Tente ajustar os filtros de busca ou categoria</p>
        </div>
    </div>

    <!-- Modal para exibir detalhes do filme -->
    <div class="modal fade" id="movieModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalTitle"></h5>
                    <button type="button" class="btn-close" onclick="closeModal()"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-4">
                            <img id="modalPoster" class="img-fluid rounded" style="width: 100%;">
                        </div>
                        <div class="col-md-8">
                            <div class="mb-3">
                                <strong>Categoria:</strong> <span id="modalCategory"></span>
                            </div>
                            <div class="mb-3">
                                <strong>URL do Filme:</strong>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="modalUrl" readonly>
                                    <button class="btn btn-outline-primary" onclick="copyUrl()">
                                        📋
                                    </button>
                                </div>
                            </div>
                            <div class="d-flex gap-2">
                                <a id="modalPlayButton" class="btn btn-success" target="_blank">
                                    ▶ Reproduzir
                                </a>
                                <button class="btn btn-primary" onclick="downloadMovie()">
                                    ⬇ Download
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let allMovies = [];
        let filteredMovies = [];
        let categories = new Set();
        let currentGridView = 'grid';
        
        // M3U content embedded in the file
        const m3uContent = `{M3U_CONTENT}`;
        
        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            parseM3UContent();
            setupEventListeners();
        });
        
        function parseM3UContent() {
            const lines = m3uContent.split('\\n');
            let currentMovie = null;
            let processed = 0;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                
                if (line.startsWith('#EXTINF:')) {
                    currentMovie = parseExtinf(line);
                } else if (line && !line.startsWith('#') && currentMovie) {
                    currentMovie.url = line;
                    allMovies.push(currentMovie);
                    categories.add(currentMovie.category || 'Sem Categoria');
                    currentMovie = null;
                }
                
                // Update progress
                processed++;
                const progress = Math.round((processed / lines.length) * 100);
                document.getElementById('loadingProgress').textContent = progress + '%';
            }
            
            filteredMovies = [...allMovies];
            updateUI();
            hideLoading();
        }
        
        function parseExtinf(line) {
            const movie = {
                name: '',
                logo: '',
                category: '',
                url: ''
            };
            
            // Extract name (after last comma)
            const nameMatch = line.match(/,(.+)$/);
            if (nameMatch) {
                movie.name = nameMatch[1].trim();
            }
            
            // Extract logo
            const logoMatch = line.match(/tvg-logo="([^"]+)"/);
            if (logoMatch) {
                movie.logo = logoMatch[1];
            }
            
            // Extract category
            const categoryMatch = line.match(/group-title="([^"]+)"/);
            if (categoryMatch) {
                movie.category = categoryMatch[1];
            }
            
            return movie;
        }
        
        function updateUI() {
            updateStats();
            updateCategoryFilter();
            renderMovies();
        }
        
        function updateStats() {
            document.getElementById('totalMovies').textContent = allMovies.length;
            document.getElementById('visibleMovies').textContent = filteredMovies.length;
            document.getElementById('totalCategories').textContent = categories.size;
            document.getElementById('loadingProgress').textContent = '100%';
        }
        
        function updateCategoryFilter() {
            const categoryFilter = document.getElementById('categoryFilter');
            categoryFilter.innerHTML = '<option value="">Todas as Categorias</option>';
            
            Array.from(categories).sort().forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            });
        }
        
        function renderMovies() {
            const movieGrid = document.getElementById('movieGrid');
            const noResults = document.getElementById('noResults');
            
            if (filteredMovies.length === 0) {
                movieGrid.style.display = 'none';
                noResults.style.display = 'block';
                return;
            }
            
            movieGrid.style.display = 'grid';
            noResults.style.display = 'none';
            movieGrid.innerHTML = '';
            
            filteredMovies.forEach((movie, index) => {
                const movieCard = createMovieCard(movie, index);
                movieGrid.appendChild(movieCard);
            });
        }
        
        function createMovieCard(movie, index) {
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.innerHTML = `
                <div class="movie-poster">
                    ${movie.logo ? 
                        `<img src="${movie.logo}" alt="${movie.name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                         <div class="no-image" style="display: none;">
                             🎬
                         </div>` :
                        `<div class="no-image">
                             🎬
                         </div>`
                    }
                    <div class="category-badge">${movie.category || 'Sem Categoria'}</div>
                </div>
                <div class="movie-info">
                    <div class="movie-title">${movie.name}</div>
                    <div class="movie-actions">
                        <button class="btn btn-sm btn-primary" onclick="showMovieDetails(${index})">
                            ℹ
                        </button>
                        <button class="btn btn-sm btn-success" onclick="playMovie('${movie.url}')">
                            ▶
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="copyMovieUrl('${movie.url}')">
                            📋
                        </button>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function filterMovies() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const categoryFilter = document.getElementById('categoryFilter').value;
            
            filteredMovies = allMovies.filter(movie => {
                const matchesSearch = movie.name.toLowerCase().includes(searchTerm);
                const matchesCategory = !categoryFilter || movie.category === categoryFilter;
                return matchesSearch && matchesCategory;
            });
            
            renderMovies();
            updateStats();
        }
        
        function showMovieDetails(index) {
            const movie = filteredMovies[index];
            document.getElementById('modalTitle').textContent = movie.name;
            document.getElementById('modalCategory').textContent = movie.category || 'Sem Categoria';
            document.getElementById('modalUrl').value = movie.url;
            document.getElementById('modalPlayButton').href = movie.url;
            
            if (movie.logo) {
                document.getElementById('modalPoster').src = movie.logo;
            }
            
            document.getElementById('movieModal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('movieModal').classList.remove('show');
        }
        
        function playMovie(url) {
            window.open(url, '_blank');
        }
        
        function copyMovieUrl(url) {
            navigator.clipboard.writeText(url).then(() => {
                showToast('URL copiada!', 'A URL do filme foi copiada para a área de transferência.');
            });
        }
        
        function copyUrl() {
            const urlInput = document.getElementById('modalUrl');
            urlInput.select();
            document.execCommand('copy');
            showToast('URL copiada!', 'A URL foi copiada para a área de transferência.');
        }
        
        function downloadMovie() {
            const url = document.getElementById('modalUrl').value;
            const a = document.createElement('a');
            a.href = url;
            a.download = '';
            a.click();
        }
        
        function exportM3U() {
            const m3uContent = generateM3UContent();
            const blob = new Blob([m3uContent], { type: 'application/x-mpegurl' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'filmes_' + new Date().toISOString().split('T')[0] + '.m3u';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function generateM3UContent() {
            let content = '#EXTM3U\\n';
            filteredMovies.forEach(movie => {
                content += `#EXTINF:-1 tvg-name="${movie.name}"`;
                if (movie.logo) content += ` tvg-logo="${movie.logo}"`;
                if (movie.category) content += ` group-title="${movie.category}"`;
                content += `,${movie.name}\\n`;
                content += `${movie.url}\\n`;
            });
            return content;
        }
        
        function toggleGridView() {
            const movieGrid = document.getElementById('movieGrid');
            const viewIcon = document.getElementById('view-icon');
            
            if (currentGridView === 'grid') {
                movieGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))';
                viewIcon.textContent = '☰';
                currentGridView = 'compact';
            } else {
                movieGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
                viewIcon.textContent = '⊞';
                currentGridView = 'grid';
            }
        }
        
        function hideLoading() {
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('movieGrid').style.display = 'grid';
        }
        
        function setupEventListeners() {
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key === 'f') {
                    e.preventDefault();
                    document.getElementById('searchInput').focus();
                }
                if (e.key === 'Escape') {
                    closeModal();
                }
            });
            
            // Close modal when clicking outside
            document.getElementById('movieModal').addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal();
                }
            });
        }
        
        function showToast(title, message) {
            const toast = document.createElement('div');
            toast.className = 'toast-notification';
            toast.innerHTML = `<strong>${title}</strong><br>${message}`;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 3000);
        }
    </script>
</body>
</html>'''
    
    # Replace the M3U content placeholder
    escaped_content = m3u_content.replace('`', '\\`').replace('\\', '\\\\')
    return html_template.replace('{M3U_CONTENT}', escaped_content)