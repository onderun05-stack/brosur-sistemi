# -*- coding: utf-8 -*-
"""
Main routes - Home, dashboard, editor and other page routes
"""

from flask import Blueprint, render_template, redirect, session, send_file, request, abort, make_response
import requests
from utils.helpers import get_current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Root route - redirect to login or dashboard"""
    user = get_current_user()
    if user:
        return redirect('/dashboard')
    return redirect('/login')


@main_bp.route('/login')
def login_page():
    """Login page"""
    user = get_current_user()
    if user:
        return redirect('/dashboard')
    return render_template('login.html')


@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard / user panel"""
    user = get_current_user()
    if not user:
        return redirect('/login')
    
    # Get user data for template
    user_data = {
        'id': user.get('id'),
        'name': user.get('name', 'Kullanıcı'),
        'email': user.get('email', ''),
        'role': user.get('role', 'customer'),
        'sector': user.get('sector', 'supermarket'),
        'credits': user.get('credits', 0)
    }
    
    return render_template('index.html', user=user_data)


@main_bp.route('/editor')
def editor():
    """Brochure editor page"""
    user = get_current_user()
    if not user:
        return redirect('/login')
    
    user_data = {
        'id': user.get('id'),
        'name': user.get('name', 'Kullanıcı'),
        'email': user.get('email', ''),
        'role': user.get('role', 'customer'),
        'sector': user.get('sector', 'supermarket'),
        'credits': user.get('credits', 0)
    }
    
    return render_template('editor.html', user=user_data)


@main_bp.route('/home')
def home_page():
    """Public home/landing page"""
    return render_template('home.html')


@main_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/login')


@main_bp.route('/pre-approval')
def pre_approval():
    """Pre-approval page for product upload"""
    user = get_current_user()
    if not user:
        return redirect('/login')
    return render_template('pre_approval.html', user=user)


@main_bp.route('/canvas-test')
def canvas_test():
    """Canvas test page - sıfırdan inşa"""
    return render_template('canvas_test.html')


@main_bp.route('/market')
def market_redirect():
    """Market panel redirect"""
    user = get_current_user()
    if user:
        return redirect('/dashboard')
    return redirect('/login')


# ============= DOWNLOAD ROUTES =============

@main_bp.route('/download/csv-template')
def download_csv_template():
    """Download simple CSV template"""
    return send_file('attached_assets/urun_sablonu.csv',
                     as_attachment=True,
                     download_name='AEU_Urun_Sablonu.csv',
                     mimetype='text/csv')


@main_bp.route('/modul/urun-yukle-formu')
def view_urun_yukle_formu():
    """View standalone product upload form in browser (opens in new tab)"""
    return send_file(
        'static/moduller/urun-yukle-formu/index.html',
        mimetype='text/html'
    )


@main_bp.route('/download/modul/urun-yukle-formu')
def download_urun_yukle_formu():
    """Download standalone product upload form module (saves as file)"""
    return send_file(
        'static/moduller/urun-yukle-formu/index.html',
        as_attachment=True,
        download_name='AEU_Urun_Yukle_Formu.html',
        mimetype='text/html'
    )


@main_bp.route('/proxy-image')
def proxy_image():
    """Proxy external images to avoid CORS issues on canvas exports"""
    image_url = request.args.get('url')
    if not image_url:
        abort(400, description='Missing url parameter')

    if not image_url.startswith('http://') and not image_url.startswith('https://'):
        abort(400, description='Invalid image URL')

    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        abort(502, description='Failed to fetch image')

    response = make_response(resp.content)
    response.headers['Content-Type'] = resp.headers.get('Content-Type', 'image/jpeg')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

