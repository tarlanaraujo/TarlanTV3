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
        
        return redirect(url_for('view_playlist', playlist_id=playlist.id))
        
    except Exception as e:
        app.logger.error(f"Error processing M3U: {e}")
        flash(f'Erro ao processar M3U: {str(e)}', 'error')
        return redirect(url_for('index'))

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
    """Background task to process M3U content"""
    with app.app_context():
        try:
            playlist = M3UPlaylist.query.get(playlist_id)
            validator = M3UValidator()
            
            # Parse M3U content
            channels_data = validator.parse_m3u_content(content)
            
            # Save channels with automatic categorization
            for channel_data in channels_data:
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
            
            playlist.total_channels = len(channels_data)
            playlist.status = 'completed'
            playlist.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Start background validation
            validate_channels_background(playlist_id)
            
        except Exception as e:
            app.logger.error(f"Error processing M3U content: {e}")
            playlist = M3UPlaylist.query.get(playlist_id)
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
