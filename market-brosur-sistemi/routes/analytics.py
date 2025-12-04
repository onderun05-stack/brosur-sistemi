# -*- coding: utf-8 -*-
"""
Analytics Routes

Provides analytics and statistics for customers and admin.
"""

from flask import Blueprint, jsonify, request, session
from functools import wraps
from datetime import datetime, timedelta
import logging

import database

analytics_bp = Blueprint('analytics', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Giriş yapmalısınız'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Giriş yapmalısınız'}), 401
        
        user = database.get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'error': 'Yetkiniz yok'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ============= CUSTOMER ANALYTICS =============

@analytics_bp.route('/api/analytics/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    """
    Get customer dashboard statistics.
    
    Returns:
        - Total brochures created
        - This month's exports
        - Most used templates
        - Credit usage chart data
        - Recent activities
    """
    user_id = session['user_id']
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Total brochures
            cursor.execute('''
                SELECT COUNT(*) FROM brochures WHERE user_id = ?
            ''', (user_id,))
            total_brochures = cursor.fetchone()[0] or 0
            
            # This month's exports (from logs if available)
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            cursor.execute('''
                SELECT COUNT(*) FROM brochures 
                WHERE user_id = ? AND created_at >= ?
            ''', (user_id, month_start.isoformat()))
            month_exports = cursor.fetchone()[0] or 0
            
            # Total products
            cursor.execute('''
                SELECT COUNT(*) FROM products WHERE user_id = ?
            ''', (user_id,))
            total_products = cursor.fetchone()[0] or 0
            
            # Credit balance
            cursor.execute('''
                SELECT credits FROM users WHERE id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            credits = row[0] if row else 0
            
            # Recent brochures
            cursor.execute('''
                SELECT id, name, created_at 
                FROM brochures 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (user_id,))
            
            recent_brochures = []
            for row in cursor.fetchall():
                recent_brochures.append({
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2]
                })
            
            # Credit usage (last 7 days) - placeholder
            credit_usage = [
                {'date': (datetime.now() - timedelta(days=i)).strftime('%d/%m'), 'used': 0}
                for i in range(6, -1, -1)
            ]
            
        return jsonify({
            'success': True,
            'stats': {
                'total_brochures': total_brochures,
                'month_exports': month_exports,
                'total_products': total_products,
                'credits': credits
            },
            'recent_brochures': recent_brochures,
            'credit_usage': credit_usage
        })
        
    except Exception as e:
        logging.error(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/analytics/usage', methods=['GET'])
@login_required
def get_usage_stats():
    """
    Get detailed usage statistics.
    """
    user_id = session['user_id']
    period = request.args.get('period', 'month')  # week, month, year
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Determine date range
            if period == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif period == 'year':
                start_date = datetime.now() - timedelta(days=365)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Brochures created
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM brochures 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (user_id, start_date.isoformat()))
            
            brochure_data = []
            for row in cursor.fetchall():
                brochure_data.append({
                    'date': row[0],
                    'count': row[1]
                })
            
            # Products added
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM products 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (user_id, start_date.isoformat()))
            
            product_data = []
            for row in cursor.fetchall():
                product_data.append({
                    'date': row[0],
                    'count': row[1]
                })
        
        return jsonify({
            'success': True,
            'period': period,
            'brochures': brochure_data,
            'products': product_data
        })
        
    except Exception as e:
        logging.error(f"Usage stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= ADMIN ANALYTICS =============

@analytics_bp.route('/api/admin/analytics/overview', methods=['GET'])
@admin_required
def get_admin_overview():
    """
    Get admin overview statistics.
    """
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0] or 0
            
            # Active users (today)
            today = datetime.now().replace(hour=0, minute=0, second=0)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM brochures
                WHERE created_at >= ?
            ''', (today.isoformat(),))
            active_today = cursor.fetchone()[0] or 0
            
            # Total brochures
            cursor.execute('SELECT COUNT(*) FROM brochures')
            total_brochures = cursor.fetchone()[0] or 0
            
            # Total products in admin bank
            cursor.execute('SELECT COUNT(*) FROM admin_products')
            total_admin_products = cursor.fetchone()[0] or 0
            
            # Pending approvals
            cursor.execute('''
                SELECT COUNT(*) FROM customer_images 
                WHERE status = 'pending'
            ''')
            pending_approvals = cursor.fetchone()[0] or 0
            
            # User registrations (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users 
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (week_ago.isoformat(),))
            
            registration_data = []
            for row in cursor.fetchall():
                registration_data.append({
                    'date': row[0],
                    'count': row[1]
                })
            
            # Top users by brochure count
            cursor.execute('''
                SELECT u.id, u.name, u.email, COUNT(b.id) as brochure_count
                FROM users u
                LEFT JOIN brochures b ON u.id = b.user_id
                GROUP BY u.id
                ORDER BY brochure_count DESC
                LIMIT 10
            ''')
            
            top_users = []
            for row in cursor.fetchall():
                top_users.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'brochure_count': row[3]
                })
        
        return jsonify({
            'success': True,
            'overview': {
                'total_users': total_users,
                'active_today': active_today,
                'total_brochures': total_brochures,
                'total_admin_products': total_admin_products,
                'pending_approvals': pending_approvals
            },
            'registrations': registration_data,
            'top_users': top_users
        })
        
    except Exception as e:
        logging.error(f"Admin overview error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/admin/analytics/users', methods=['GET'])
@admin_required
def get_user_analytics():
    """
    Get detailed user analytics.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Build query
            query = '''
                SELECT 
                    u.id, u.name, u.email, u.sector, u.credits,
                    u.email_verified, u.created_at,
                    (SELECT COUNT(*) FROM brochures WHERE user_id = u.id) as brochure_count,
                    (SELECT COUNT(*) FROM products WHERE user_id = u.id) as product_count
                FROM users u
                WHERE 1=1
            '''
            params = []
            
            if search:
                query += ' AND (u.name LIKE ? OR u.email LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY u.created_at DESC'
            query += f' LIMIT {per_page} OFFSET {(page - 1) * per_page}'
            
            cursor.execute(query, params)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'sector': row[3],
                    'credits': row[4],
                    'email_verified': bool(row[5]),
                    'created_at': row[6],
                    'brochure_count': row[7],
                    'product_count': row[8]
                })
            
            # Total count
            count_query = 'SELECT COUNT(*) FROM users WHERE 1=1'
            if search:
                count_query += ' AND (name LIKE ? OR email LIKE ?)'
                cursor.execute(count_query, [f'%{search}%', f'%{search}%'])
            else:
                cursor.execute(count_query)
            
            total = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logging.error(f"User analytics error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/admin/analytics/products', methods=['GET'])
@admin_required
def get_product_analytics():
    """
    Get product bank analytics.
    """
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Products by category
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM admin_products
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            by_category = []
            for row in cursor.fetchall():
                by_category.append({
                    'category': row[0] or 'Diğer',
                    'count': row[1]
                })
            
            # Products by source
            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM admin_products
                GROUP BY source
                ORDER BY count DESC
            ''')
            
            by_source = []
            for row in cursor.fetchall():
                by_source.append({
                    'source': row[0] or 'Bilinmiyor',
                    'count': row[1]
                })
            
            # Recent products
            cursor.execute('''
                SELECT id, barcode, name, category, created_at
                FROM admin_products
                ORDER BY created_at DESC
                LIMIT 20
            ''')
            
            recent = []
            for row in cursor.fetchall():
                recent.append({
                    'id': row[0],
                    'barcode': row[1],
                    'name': row[2],
                    'category': row[3],
                    'created_at': row[4]
                })
            
            # Low quality images count
            cursor.execute('''
                SELECT COUNT(*) FROM admin_products
                WHERE quality_score IS NOT NULL AND quality_score < 0.5
            ''')
            low_quality = cursor.fetchone()[0] or 0
        
        return jsonify({
            'success': True,
            'by_category': by_category,
            'by_source': by_source,
            'recent': recent,
            'low_quality_count': low_quality
        })
        
    except Exception as e:
        logging.error(f"Product analytics error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/admin/analytics/performance', methods=['GET'])
@admin_required
def get_performance_stats():
    """
    Get system performance statistics.
    """
    try:
        import os
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Database size
        db_path = 'brosur.db'
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        db_size_mb = round(db_size / (1024 * 1024), 2)
        
        # Uploads folder size
        uploads_path = 'static/uploads'
        uploads_size = 0
        if os.path.exists(uploads_path):
            for dirpath, dirnames, filenames in os.walk(uploads_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    uploads_size += os.path.getsize(fp)
        uploads_size_mb = round(uploads_size / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'performance': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'db_size_mb': db_size_mb,
                'uploads_size_mb': uploads_size_mb
            }
        })
        
    except ImportError:
        # psutil not installed
        return jsonify({
            'success': True,
            'performance': {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'db_size_mb': 0,
                'uploads_size_mb': 0,
                'note': 'psutil not installed'
            }
        })
        
    except Exception as e:
        logging.error(f"Performance stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/admin/analytics/report', methods=['GET'])
@admin_required
def generate_report():
    """
    Generate a comprehensive report (downloadable).
    """
    format_type = request.args.get('format', 'json')  # json, csv
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Collect all statistics
            report = {
                'generated_at': datetime.now().isoformat(),
                'users': {},
                'brochures': {},
                'products': {}
            }
            
            # User stats
            cursor.execute('SELECT COUNT(*) FROM users')
            report['users']['total'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE email_verified = 1')
            report['users']['verified'] = cursor.fetchone()[0]
            
            # Brochure stats
            cursor.execute('SELECT COUNT(*) FROM brochures')
            report['brochures']['total'] = cursor.fetchone()[0]
            
            # Product stats
            cursor.execute('SELECT COUNT(*) FROM admin_products')
            report['products']['admin_bank'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM products')
            report['products']['customer_total'] = cursor.fetchone()[0]
        
        if format_type == 'csv':
            # Generate CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Generated At', report['generated_at']])
            writer.writerow(['Total Users', report['users']['total']])
            writer.writerow(['Verified Users', report['users']['verified']])
            writer.writerow(['Total Brochures', report['brochures']['total']])
            writer.writerow(['Admin Products', report['products']['admin_bank']])
            writer.writerow(['Customer Products', report['products']['customer_total']])
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=report_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Report generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

