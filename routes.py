from flask import render_template, request, jsonify, redirect, url_for, flash, session, send_file
from app import app, db
from models import M3UPlaylist, Channel, SearchHistory, UserSession
from m3u_validator import M3UValidator
from web_scraper import get_website_text_content
from datetime import datetime
import hashlib
import threading
import time
import os
import json
from urllib.parse import urlparse, unquote
from werkzeug.utils import secure_filename

@app.route('/')
def index():
    """Main page with upload/URL input options"""
    return render_template('index.html')

@app.route('/home')
def home_original():
    """Original home page"""
    return render_template('index.html')

@app.route('/tartv')
def tartv_home():
    """TarTV homepage with Portuguese interface"""
    return render_template('index_tartv.html')

@app.route('/upload', methods=['POST'])
def upload_m3u():
    """Handle M3U file upload or URL processing"""
    try:
        source_type = request.form.get('source_type', 'url')
        
        if source_type == 'file':
            if 'file' not in request.files:
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(url_for('index'))
            
            file = request.files['file']
            if file.filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(url_for('index'))
            
            if file and file.filename.lower().endswith(('.m3u', '.m3u8', '.txt')):
                content = file.read().decode('utf-8')
                playlist_name = secure_filename(file.filename)
                source_url = None
            else:
                flash('Formato de arquivo não suportado. Use .m3u, .m3u8 ou .txt', 'error')
                return redirect(url_for('index'))
        
        elif source_type == 'url':
            source_url = request.form.get('url')
            if not source_url:
                flash('Por favor, insira uma URL válida', 'error')
                return redirect(url_for('index'))
            
            # Extract content from URL
            validator = M3UValidator()
            content = validator.fetch_m3u_content(source_url)
            
            if not content:
                flash('Erro ao buscar conteúdo da URL', 'error')
                return redirect(url_for('index'))
            
            # Generate playlist name from URL
            parsed_url = urlparse(source_url)
            playlist_name = parsed_url.netloc or 'Playlist M3U'
        
        else:
            flash('Tipo de fonte inválido', 'error')
            return redirect(url_for('index'))
        
        # Create content hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check if playlist already exists
        existing_playlist = M3UPlaylist.query.filter_by(content_hash=content_hash).first()
        if existing_playlist:
            return redirect(url_for('view_playlist', playlist_id=existing_playlist.id))
        
        # Create new playlist
        playlist = M3UPlaylist(
            name=playlist_name,
            source_url=source_url,
            source_type=source_type,
            content_hash=content_hash,
            status='processing'
        )
        db.session.add(playlist)
        db.session.commit()
        
        # Store playlist ID in session
        session['current_playlist_id'] = playlist.id
        
        # Start background processing
        thread = threading.Thread(target=process_m3u_content, args=(playlist.id, content))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('playlist_loading', playlist_id=playlist.id))
        
    except Exception as e:
        app.logger.error(f"Error processing M3U: {e}")
        flash(f'Erro ao processar M3U: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/playlist/<int:playlist_id>/loading')
def playlist_loading(playlist_id):
    """Loading page with progress tracking"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    return render_template('playlist_loading.html', playlist=playlist)

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    """View playlist with category navigation"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    
    # Get category counts
    live_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='live').count()
    movie_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='movie').count()
    series_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='series').count()
    
    return render_template('m3u_viewer.html', 
                         playlist=playlist,
                         live_count=live_count,
                         movie_count=movie_count,
                         series_count=series_count)

@app.route('/playlist/<int:playlist_id>/category/<category_type>')
def view_category(playlist_id, category_type):
    """View channels by category"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    
    # Get channels for the category
    channels = Channel.query.filter_by(
        playlist_id=playlist_id,
        category_type=category_type
    ).order_by(Channel.name).all()
    
    # Get unique groups for filtering
    groups = db.session.query(Channel.group_title).filter_by(
        playlist_id=playlist_id,
        category_type=category_type
    ).distinct().all()
    groups = [g[0] for g in groups if g[0]]
    
    return render_template('category_view.html',
                         playlist=playlist,
                         channels=channels,
                         category_type=category_type,
                         groups=groups)

@app.route('/playlist/<int:playlist_id>/search')
def search_channels():
    """Search channels within a playlist"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    query = request.args.get('q', '').strip()
    category_type = request.args.get('category', 'all')
    group_filter = request.args.get('group', '')
    
    if not query:
        flash('Digite um termo para buscar', 'warning')
        return redirect(url_for('view_playlist', playlist_id=playlist_id))
    
    # Build search query
    search_query = Channel.query.filter_by(playlist_id=playlist_id)
    
    if category_type != 'all':
        search_query = search_query.filter_by(category_type=category_type)
    
    if group_filter:
        search_query = search_query.filter_by(group_title=group_filter)
    
    # Search in name and category
    search_query = search_query.filter(
        Channel.name.ilike(f'%{query}%') |
        Channel.category.ilike(f'%{query}%')
    )
    
    channels = search_query.order_by(Channel.name).all()
    
    # Save search history
    search_history = SearchHistory(
        query=query,
        category_type=category_type,
        playlist_id=playlist_id,
        results_count=len(channels)
    )
    db.session.add(search_history)
    db.session.commit()
    
    return render_template('search_results.html',
                         playlist=playlist,
                         channels=channels,
                         query=query,
                         category_type=category_type,
                         results_count=len(channels))

@app.route('/playlist/<int:playlist_id>/channel/<int:channel_id>')
def play_channel(playlist_id, channel_id):
    """Play a specific channel"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    channel = Channel.query.filter_by(id=channel_id, playlist_id=playlist_id).first_or_404()
    
    return render_template('player.html',
                         playlist=playlist,
                         channel=channel)

@app.route('/api/playlist/<int:playlist_id>/status')
def get_playlist_status(playlist_id):
    """Get playlist processing status"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    
    return jsonify({
        'status': playlist.status,
        'total_channels': playlist.total_channels,
        'valid_channels': playlist.valid_channels,
        'last_updated': playlist.last_updated.isoformat() if playlist.last_updated else None
    })

@app.route('/api/playlist/<int:playlist_id>/progress')
def get_playlist_progress(playlist_id):
    """Get detailed playlist processing progress"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    
    # Get current counts
    total_channels = Channel.query.filter_by(playlist_id=playlist_id).count()
    live_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='live').count()
    movie_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='movie').count()
    series_count = Channel.query.filter_by(playlist_id=playlist_id, category_type='series').count()
    
    # Get recent channels (last 5)
    recent_channels = Channel.query.filter_by(playlist_id=playlist_id)\
        .order_by(Channel.id.desc()).limit(5).all()
    
    recent_channels_data = []
    for channel in recent_channels:
        recent_channels_data.append({
            'id': channel.id,
            'name': channel.name,
            'category_type': channel.category_type,
            'group_title': channel.group_title,
            'logo': channel.logo
        })
    
    return jsonify({
        'status': playlist.status,
        'processed_count': total_channels,
        'total_expected': playlist.total_channels or total_channels,
        'live_count': live_count,
        'movie_count': movie_count,
        'series_count': series_count,
        'recent_channels': recent_channels_data
    })

@app.route('/api/playlist/<int:playlist_id>/export', methods=['POST'])
def export_playlist_api(playlist_id):
    """Export playlist to HTML"""
    playlist = M3UPlaylist.query.get_or_404(playlist_id)
    export_type = request.args.get('type', 'all')
    
    # Get channels based on type
    if export_type == 'processed':
        channels = Channel.query.filter_by(playlist_id=playlist_id).all()
    else:
        channels = Channel.query.filter_by(playlist_id=playlist_id).all()
    
    # Generate HTML content
    html_content = generate_export_html(playlist, channels)
    
    # Create response
    from flask import make_response
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename="{playlist.name}_export.html"'
    
    return response

def generate_export_html(playlist, channels):
    """Generate HTML export for playlist"""
    html_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ playlist_name }} - TarTV Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; }
        .stat-item { background: #2a2a2a; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #17a2b8; }
        .category { margin-bottom: 30px; }
        .category-header { background: #343a40; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        .channels-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
        .channel-card { background: #2a2a2a; padding: 15px; border-radius: 8px; border-left: 4px solid #17a2b8; }
        .channel-name { font-weight: bold; margin-bottom: 5px; }
        .channel-info { font-size: 12px; color: #aaa; margin-bottom: 10px; }
        .channel-url { word-break: break-all; font-size: 11px; color: #17a2b8; }
        .live { border-left-color: #dc3545; }
        .movie { border-left-color: #ffc107; }
        .series { border-left-color: #17a2b8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ playlist_name }}</h1>
        <p>Exportado em {{ export_date }}</p>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-number">{{ total_channels }}</div>
            <div>Total de Canais</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ live_count }}</div>
            <div>Canais AO VIVO</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ movie_count }}</div>
            <div>Filmes</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ series_count }}</div>
            <div>Séries</div>
        </div>
    </div>
    
    {{ channels_html }}
    
    <div style="text-align: center; margin-top: 50px; color: #666;">
        <p>Exportado pelo TarTV - Gerenciador de IPTV</p>
    </div>
</body>
</html>'''
    
    # Categorize channels
    live_channels = [ch for ch in channels if ch.category_type == 'live']
    movie_channels = [ch for ch in channels if ch.category_type == 'movie']
    series_channels = [ch for ch in channels if ch.category_type == 'series']
    
    # Generate channels HTML
    channels_html = ""
    
    for category_name, category_channels, category_class in [
        ("Canais AO VIVO", live_channels, "live"),
        ("Filmes", movie_channels, "movie"),
        ("Séries", series_channels, "series")
    ]:
        if category_channels:
            channels_html += f'''
            <div class="category">
                <div class="category-header">
                    <h2>{category_name} ({len(category_channels)})</h2>
                </div>
                <div class="channels-grid">
            '''
            
            for channel in category_channels:
                channels_html += f'''
                <div class="channel-card {category_class}">
                    <div class="channel-name">{channel.name}</div>
                    <div class="channel-info">
                        {channel.group_title if channel.group_title else 'Sem grupo'}
                    </div>
                    <div class="channel-url">{channel.url}</div>
                </div>
                '''
            
            channels_html += '''
                </div>
            </div>
            '''
    
    # Replace template variables
    html_content = html_template.replace('{{ playlist_name }}', playlist.name)
    html_content = html_content.replace('{{ export_date }}', datetime.now().strftime('%d/%m/%Y %H:%M'))
    html_content = html_content.replace('{{ total_channels }}', str(len(channels)))
    html_content = html_content.replace('{{ live_count }}', str(len(live_channels)))
    html_content = html_content.replace('{{ movie_count }}', str(len(movie_channels)))
    html_content = html_content.replace('{{ series_count }}', str(len(series_channels)))
    html_content = html_content.replace('{{ channels_html }}', channels_html)
    
    return html_content

@app.route('/api/channel/<int:channel_id>/test')
def test_channel(channel_id):
    """Test channel connectivity"""
    channel = Channel.query.get_or_404(channel_id)
    
    def test_in_background():
        with app.app_context():
            validator = M3UValidator()
            is_working = validator.test_stream_connectivity(channel.url)
            
            channel.is_working = is_working
            channel.last_checked = datetime.utcnow()
            db.session.commit()
    
    thread = threading.Thread(target=test_in_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'testing'})

@app.route('/api/channel/<int:channel_id>/status')
def get_channel_status(channel_id):
    """Get channel test status"""
    channel = Channel.query.get_or_404(channel_id)
    
    return jsonify({
        'is_working': channel.is_working,
        'last_checked': channel.last_checked.isoformat() if channel.last_checked else None
    })

def process_m3u_content(playlist_id, content):
    """Background task to process M3U content with progressive loading"""
    with app.app_context():
        try:
            playlist = M3UPlaylist.query.get(playlist_id)
            validator = M3UValidator()
            
            # Parse M3U content
            channels_data = validator.parse_m3u_content(content)
            
            # Update total expected channels
            playlist.total_channels = len(channels_data)
            playlist.status = 'processing'
            db.session.commit()
            
            # Process channels in batches for progressive loading
            batch_size = 50
            processed_count = 0
            
            for i in range(0, len(channels_data), batch_size):
                batch = channels_data[i:i + batch_size]
                
                # Save batch of channels
                for channel_data in batch:
                    # Determine category type based on name and group
                    category_type = categorize_channel(channel_data['name'], channel_data.get('group', ''))
                    
                    channel = Channel(
                        name=channel_data['name'],
                        url=channel_data['url'],
                        category=channel_data.get('category'),
                        category_type=category_type,
                        logo=channel_data.get('logo'),
                        group_title=channel_data.get('group'),
                        tvg_id=channel_data.get('tvg_id'),
                        tvg_name=channel_data.get('tvg_name'),
                        duration=channel_data.get('duration', -1),
                        playlist_id=playlist_id
                    )
                    db.session.add(channel)
                
                # Commit batch
                db.session.commit()
                processed_count += len(batch)
                
                # Update playlist last_updated to show progress
                playlist.last_updated = datetime.utcnow()
                db.session.commit()
                
                # Small delay between batches
                time.sleep(0.1)
            
            # Mark as completed
            playlist.status = 'completed'
            playlist.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Start background validation
            validate_channels_background(playlist_id)
            
        except Exception as e:
            app.logger.error(f"Error processing M3U content: {e}")
            playlist = M3UPlaylist.query.get(playlist_id)
            if playlist:
                playlist.status = 'failed'
                db.session.commit()

def categorize_channel(name, group_title):
    """Automatically categorize channel based on name and group"""
    name_lower = name.lower()
    group_lower = group_title.lower() if group_title else ''
    
    # Movie indicators
    movie_keywords = ['filme', 'movie', 'cinema', 'vod', 'on demand', 'peliculas']
    series_keywords = ['serie', 'series', 'tv show', 'temporada', 'season', 'episodio']
    
    # Check group title first
    if any(keyword in group_lower for keyword in movie_keywords):
        return 'movie'
    elif any(keyword in group_lower for keyword in series_keywords):
        return 'series'
    
    # Check channel name
    if any(keyword in name_lower for keyword in movie_keywords):
        return 'movie'
    elif any(keyword in name_lower for keyword in series_keywords):
        return 'series'
    
    # Default to live TV
    return 'live'

def validate_channels_background(playlist_id):
    """Background validation of channels"""
    with app.app_context():
        channels = Channel.query.filter_by(playlist_id=playlist_id).all()
        validator = M3UValidator()
        valid_count = 0
        
        for channel in channels:
            try:
                is_working = validator.test_stream_connectivity(channel.url)
                channel.is_working = is_working
                channel.last_checked = datetime.utcnow()
                
                if is_working:
                    valid_count += 1
                
                # Small delay to avoid overwhelming servers
                time.sleep(0.1)
                
            except Exception as e:
                app.logger.error(f"Error testing channel {channel.name}: {e}")
                channel.is_working = False
                channel.last_checked = datetime.utcnow()
        
        db.session.commit()
        
        # Update playlist valid channels count
        playlist = M3UPlaylist.query.get(playlist_id)
        playlist.valid_channels = valid_count
        db.session.commit()

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
