from flask import render_template, request, jsonify, redirect, url_for, flash, send_file
from app import app, db
from models import SearchHistory, Channel, PlaylistExport
from m3u_validator import M3UValidator
from web_scraper import get_website_text_content
from offline_html_generator import generate_offline_html
from datetime import datetime
import re
import io
import threading
import time
import os


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            flash('Por favor, insira uma URL válida', 'error')
            return redirect(url_for('search'))

        # Create search entry
        search_entry = SearchHistory(url=url,
                                     title='Processando...',
                                     channels_found=0,
                                     valid_channels=0,
                                     search_date=datetime.utcnow(),
                                     status='processing')
        db.session.add(search_entry)
        db.session.commit()

        # Start background processing
        thread = threading.Thread(target=process_playlist,
                                  args=(search_entry.id, url))
        thread.daemon = True
        thread.start()

        return redirect(url_for('validate', search_id=search_entry.id))

    return render_template('search.html')


@app.route('/m3u_import', methods=['GET', 'POST'])
def m3u_import():
    """Importar lista M3U pelo link e visualizar o conteúdo"""
    if request.method == 'POST':
        m3u_link = request.form.get('m3u_link')
        if not m3u_link:
            flash('Por favor, insira um link válido.', 'error')
            return redirect(url_for('m3u_import'))

        validator = M3UValidator()
        m3u_content = validator.fetch_m3u_content(m3u_link)

        if not m3u_content:
            flash('Erro ao buscar o conteúdo da lista M3U.', 'error')
            return redirect(url_for('m3u_import'))

        return render_template('m3u_viewer.html', m3u_content=m3u_content)

    return render_template('m3u_import.html')


#final da inha 47


@app.route('/validate/<int:search_id>')
def validate(search_id):
    search_entry = SearchHistory.query.get_or_404(search_id)
    channels = Channel.query.filter_by(search_history_id=search_id).all()

    return render_template('validate.html',
                           search_entry=search_entry,
                           channels=channels)


@app.route('/history')
def history():
    searches = SearchHistory.query.order_by(
        SearchHistory.search_date.desc()).all()
    return render_template('history.html', searches=searches)


@app.route('/api/search/<int:search_id>/status')
def search_status(search_id):
    search_entry = SearchHistory.query.get_or_404(search_id)
    return jsonify({
        'status': search_entry.status,
        'title': search_entry.title,
        'channels_found': search_entry.channels_found,
        'valid_channels': search_entry.valid_channels
    })


@app.route('/api/channel/<int:channel_id>/test')
def test_channel(channel_id):
    thread = threading.Thread(target=test_channel_connectivity,
                              args=(channel_id, ))
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'testing'})


@app.route('/export/<int:search_id>')
def export_playlist(search_id):
    search_entry = SearchHistory.query.get_or_404(search_id)
    channels = Channel.query.filter_by(search_history_id=search_id,
                                       is_working=True).all()

    if not channels:
        flash('Nenhum canal válido encontrado para exportar', 'error')
        return redirect(url_for('validate', search_id=search_id))

    # Generate M3U content
    m3u_content = "#EXTM3U\n"
    for channel in channels:
        m3u_content += f'#EXTINF:-1 tvg-name="{channel.name}"'
        if channel.logo:
            m3u_content += f' tvg-logo="{channel.logo}"'
        if channel.category:
            m3u_content += f' group-title="{channel.category}"'
        m3u_content += f',{channel.name}\n'
        m3u_content += f'{channel.url}\n'

    # Save export
    export = PlaylistExport(
        filename=
        f"{search_entry.title or 'playlist'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u",
        content=m3u_content,
        channels_count=len(channels),
        export_date=datetime.utcnow(),
        export_type='m3u')
    db.session.add(export)
    db.session.commit()

    # Send file
    file_buffer = io.BytesIO()
    file_buffer.write(m3u_content.encode('utf-8'))
    file_buffer.seek(0)

    return send_file(file_buffer,
                     mimetype='application/x-mpegurl',
                     as_attachment=True,
                     download_name=export.filename)


def process_playlist(search_id, url):
    """Background task to process playlist"""
    with app.app_context():
        try:
            search_entry = SearchHistory.query.get(search_id)
            validator = M3UValidator()

            # Try to fetch content
            content = None
            if url.endswith('.m3u') or url.endswith('.m3u8'):
                content = validator.fetch_m3u_content(url)
            else:
                # Try to scrape website for M3U content
                try:
                    web_content = get_website_text_content(url)
                    if web_content and '#EXTM3U' in web_content:
                        content = web_content
                except Exception as e:
                    app.logger.error(f"Error scraping website: {e}")

            if not content:
                search_entry.status = 'failed'
                search_entry.title = 'Erro ao buscar conteúdo'
                db.session.commit()
                return

            # Parse M3U content
            channels_data = validator.parse_m3u_content(content)

            # Extract title from content
            title_match = re.search(r'#EXTM3U.*?title="([^"]*)"', content,
                                    re.IGNORECASE)
            if title_match:
                search_entry.title = title_match.group(1)
            else:
                search_entry.title = f"Lista IPTV - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Save channels
            for channel_data in channels_data:
                channel = Channel(name=channel_data['name'],
                                  url=channel_data['url'],
                                  category=channel_data.get('category'),
                                  logo=channel_data.get('logo'),
                                  group=channel_data.get('group'),
                                  search_history_id=search_id)
                db.session.add(channel)

            search_entry.channels_found = len(channels_data)
            search_entry.status = 'completed'
            db.session.commit()

            # Start testing channels
            test_all_channels(search_id)

        except Exception as e:
            app.logger.error(f"Error processing playlist: {e}")
            search_entry = SearchHistory.query.get(search_id)
            search_entry.status = 'failed'
            search_entry.title = f'Erro: {str(e)}'
            db.session.commit()


def test_all_channels(search_id):
    """Test all channels for a search"""
    with app.app_context():
        channels = Channel.query.filter_by(search_history_id=search_id).all()
        validator = M3UValidator()

        for channel in channels:
            try:
                is_working = validator.test_stream_connectivity(channel.url)
                channel.is_working = is_working
                channel.last_checked = datetime.utcnow()
                time.sleep(0.1)  # Small delay to avoid overwhelming servers
            except Exception as e:
                app.logger.error(f"Error testing channel {channel.name}: {e}")
                channel.is_working = False
                channel.last_checked = datetime.utcnow()

        db.session.commit()

        # Update search entry
        search_entry = SearchHistory.query.get(search_id)
        search_entry.valid_channels = len(
            [c for c in channels if c.is_working == True])
        db.session.commit()


def test_channel_connectivity(channel_id):
    """Test single channel connectivity"""
    with app.app_context():
        channel = Channel.query.get(channel_id)
        if channel:
            validator = M3UValidator()
            try:
                is_working = validator.test_stream_connectivity(channel.url)
                channel.is_working = is_working
                channel.last_checked = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error testing channel {channel.name}: {e}")
                channel.is_working = False
                channel.last_checked = datetime.utcnow()
                db.session.commit()


@app.route('/m3u_viewer')
def m3u_viewer():
    """Render M3U viewer page"""
    return render_template('m3u_viewer.html', m3u_content='')


@app.route('/m3u_viewer/<path:filename>')
def m3u_viewer_file(filename):
    """Render M3U viewer page with file content"""
    try:
        # Read the M3U file content
        file_path = os.path.join('attached_assets', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                m3u_content = f.read()
        else:
            m3u_content = ''

        return render_template('m3u_viewer.html', m3u_content=m3u_content)
    except Exception as e:
        app.logger.error(f"Error loading M3U file: {e}")
        return render_template('m3u_viewer.html', m3u_content='')


@app.route('/m3u_viewer_upload', methods=['GET', 'POST'])
def m3u_viewer_upload():
    """Upload and view M3U file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)

        if file and file.filename.lower().endswith(('.m3u', '.m3u8', '.txt')):
            try:
                m3u_content = file.read().decode('utf-8')
                return render_template('m3u_viewer.html',
                                       m3u_content=m3u_content)
            except Exception as e:
                flash(f'Erro ao processar arquivo: {e}', 'error')
                return redirect(request.url)
        else:
            flash('Formato de arquivo não suportado. Use .m3u, .m3u8 ou .txt',
                  'error')
            return redirect(request.url)

    return render_template('m3u_upload.html')


@app.route('/proxy_m3u')
def proxy_m3u():
    """Proxy endpoint to fetch M3U content and avoid CORS issues"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    try:
        validator = M3UValidator()
        content = validator.fetch_m3u_content(url)
        
        if content:
            return jsonify({'content': content, 'success': True})
        else:
            return jsonify({'error': 'Failed to fetch M3U content', 'success': False}), 400
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/demo_m3u')
def demo_m3u():
    """Demo page with the provided M3U content"""
    demo_content = """#EXTM3U
#EXTINF:-1 tvg-id="" tvg-name="Kill O Massacre no Trem" tvg-logo="https://image.tmdb.org/t/p/w400/mxgrtJvngNhppjCwu2AvdCtvSXa.jpg" group-title="(VOD BR) Filmes",Kill O Massacre no Trem
https://apiceplay.nexus/movie/20613489/69683690/1511266.mp4
#EXTINF:-1 tvg-id="" tvg-name="Martha" tvg-logo="https://image.tmdb.org/t/p/w400/4WN19oCTXlK8jXC0QZgNkBpcJcw.jpg" group-title="(VOD BR) Filmes",Martha
https://apiceplay.nexus/movie/20613489/69683690/1510096.mp4
#EXTINF:-1 tvg-id="" tvg-name="Sorria 2" tvg-logo="https://image.tmdb.org/t/p/w400/tPGaWmxdPumgOAzbGHu8aRJTaXx.jpg" group-title="(VOD BR) Filmes",Sorria 2
https://apiceplay.nexus/movie/20613489/69683690/1156771.mp4
#EXTINF:-1 tvg-id="" tvg-name="Grande Sertao" tvg-logo="https://image.tmdb.org/t/p/w400/ps1SI5yGewDlSBANLW5kzAqwQfT.jpg" group-title="(VOD BR) Filmes",Grande Sertao
https://apiceplay.nexus/movie/20613489/69683690/1156809.mp4
#EXTINF:-1 tvg-id="" tvg-name="Nao Fale o Mal" tvg-logo="https://image.tmdb.org/t/p/w400/cTcqksGeVKtHelStB7eKrSckczN.jpg" group-title="(VOD BR) Filmes",Nao Fale o Mal
https://apiceplay.nexus/movie/20613489/69683690/1157168.mp4
#EXTINF:-1 tvg-id="" tvg-name="Meu Filho Nosso Mundo" tvg-logo="https://image.tmdb.org/t/p/w400/iP1wYVjnBKUyeRyf2qDtP2GEB60.jpg" group-title="(VOD BR) Filmes",Meu Filho Nosso Mundo
https://apiceplay.nexus/movie/20613489/69683690/1157594.mp4
#EXTINF:-1 tvg-id="" tvg-name="Enfeiticados" tvg-logo="https://image.tmdb.org/t/p/w400/s9NYuPqsxxeoheDxSR419SS3Uf3.jpg" group-title="(VOD BR) Filmes",Enfeiticados
https://apiceplay.nexus/movie/20613489/69683690/1157929.mp4
#EXTINF:-1 tvg-id="" tvg-name="Robo Selvagem" tvg-logo="https://image.tmdb.org/t/p/w400/cWsd33Nwp3tgYB5LMMadl3qVMKh.jpg" group-title="(VOD BR) Filmes",Robo Selvagem
https://apiceplay.nexus/movie/20613489/69683690/1157930.mp4
#EXTINF:-1 tvg-id="" tvg-name="From the River to the Sea Um Filme Sobre a Guerra em Israel" tvg-logo="https://image.tmdb.org/t/p/w400/3iFmtROx5NIuXpJ1GuqvBZV3W7C.jpg" group-title="(VOD BR) Filmes",From the River to the Sea Um Filme Sobre a Guerra em Israel
https://apiceplay.nexus/movie/20613489/69683690/1157932.mp4
#EXTINF:-1 tvg-id="" tvg-name="Alice Subservience" tvg-logo="https://image.tmdb.org/t/p/w400/6EO0cjZt2vzAOmuDJZGED6GQmi4.jpg" group-title="(VOD BR) Filmes",Alice Subservience
https://apiceplay.nexus/movie/20613489/69683690/1511250.mp4
#EXTINF:-1 tvg-id="" tvg-name="Livre Encanto criminal" tvg-logo="https://image.tmdb.org/t/p/w400/cE7C87RQUMRVwAShtNeua49mHsy.jpg" group-title="(VOD BR) Filmes",Livre Encanto criminal
https://apiceplay.nexus/movie/20613489/69683690/1510098.mp4
#EXTINF:-1 tvg-id="" tvg-name="HAIKYU The Dumpster Battle" tvg-logo="https://image.tmdb.org/t/p/w400/pRfLrwbfUWmUj1Jh1NGLSQceHoT.jpg" group-title="(VOD BR) Filmes",HAIKYU The Dumpster Battle
https://apiceplay.nexus/movie/20613489/69683690/1510101.mp4
#EXTINF:-1 tvg-id="" tvg-name="Gigantes" tvg-logo="https://image.tmdb.org/t/p/w400/t1NFp7n2h2CTVC1KD5x2ZYFNfHl.jpg" group-title="(VOD BR) Filmes",Gigantes
https://apiceplay.nexus/movie/20613489/69683690/1510102.mp4
#EXTINF:-1 tvg-id="" tvg-name="O Quiosque" tvg-logo="https://image.tmdb.org/t/p/w400/eZExVc4fuAFSdh2VsHI1pN4Izqp.jpg" group-title="(VOD BR) Filmes",O Quiosque
https://apiceplay.nexus/movie/20613489/69683690/1510676.mp4
#EXTINF:-1 tvg-id="" tvg-name="SeAcabo Diario das Campeas" tvg-logo="https://image.tmdb.org/t/p/w400/AbhsO718qA8qeHyF00FsvG7vt3f.jpg" group-title="(VOD BR) Filmes",SeAcabo Diario das Campeas
https://apiceplay.nexus/movie/20613489/69683690/1511132.mp4
#EXTINF:-1 tvg-id="" tvg-name="Cumplice em Fuga" tvg-logo="https://image.tmdb.org/t/p/w400/j0U1I5lz9ueoxqpCObKkKwS6clg.jpg" group-title="(VOD BR) Filmes",Cumplice em Fuga
https://apiceplay.nexus/movie/20613489/69683690/1511249.mp4
#EXTINF:-1 tvg-id="" tvg-name="Nosso Segredinho" tvg-logo="https://image.tmdb.org/t/p/w400/u2WzilmXnBEAuGjOWIuY1a7k6yA.jpg" group-title="(VOD BR) Filmes",Nosso Segredinho
https://apiceplay.nexus/movie/20613489/69683690/1511253.mp4
#EXTINF:-1 tvg-id="" tvg-name="A Porta do Porao" tvg-logo="https://image.tmdb.org/t/p/w400/jNLBN8Hbz6wkklvfgjW41PW4rd5.jpg" group-title="(VOD BR) Filmes",A Porta do Porao
https://apiceplay.nexus/movie/20613489/69683690/1511256.mp4
#EXTINF:-1 tvg-id="" tvg-name="Saudade fez Morada aqui Dentro" tvg-logo="https://image.tmdb.org/t/p/w400/bawj0qlu7msZUIvnxk8yGnL5SdD.jpg" group-title="(VOD BR) Filmes",Saudade fez Morada aqui Dentro
https://apiceplay.nexus/movie/20613489/69683690/1511262.mp4
#EXTINF:-1 tvg-id="" tvg-name="Quem Ve Cara" tvg-logo="https://image.tmdb.org/t/p/w400/3HoQz6lQzvWQ59sE02YNMN8zaUj.jpg" group-title="(VOD BR) Filmes",Quem Ve Cara
https://apiceplay.nexus/movie/20613489/69683690/1511263.mp4
#EXTINF:-1 tvg-id="" tvg-name="Fique Acordado" tvg-logo="https://image.tmdb.org/t/p/w400/izPVZlS3FcfVjiQ4kjQKppIwja0.jpg" group-title="(VOD BR) Filmes",Fique Acordado
https://apiceplay.nexus/movie/20613489/69683690/1135312.mp4"""

    return render_template('m3u_viewer.html', m3u_content=demo_content)


@app.route('/download_html')
def download_html():
    """Download HTML file with M3U content"""
    m3u_content = request.args.get('content', '')

    # Generate complete HTML file
    html_content = generate_offline_html(m3u_content)

    # Create file in memory
    file_buffer = io.BytesIO()
    file_buffer.write(html_content.encode('utf-8'))
    file_buffer.seek(0)

    filename = f"visualizador_m3u_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    return send_file(file_buffer,
                     mimetype='text/html',
                     as_attachment=True,
                     download_name=filename)
