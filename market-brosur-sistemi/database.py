import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from utils.constants import SECTORS, get_all_sectors, get_product_groups_for_sector

DB_PATH = 'brosur.db'

# Context manager for database connections
from contextlib import contextmanager

@contextmanager
def get_db():
    """
    Context manager for database connections.
    Ensures connections are properly closed.
    
    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

# SECTORS artık utils/constants.py'dan geliyor
# Eski format için uyumluluk fonksiyonu
def get_sectors_list():
    """Get sectors as list of dicts (eski format uyumluluğu için)"""
    return get_all_sectors()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'customer',
        sector TEXT DEFAULT 'supermarket',
        credits REAL DEFAULT 100.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add sector column if not exists (migration)
    try:
        c.execute("ALTER TABLE users ADD COLUMN sector TEXT DEFAULT 'supermarket'")
    except:
        pass
    
    # Add credits column if not exists (migration)
    try:
        c.execute("ALTER TABLE users ADD COLUMN credits REAL DEFAULT 100.0")
    except:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        barcode TEXT NOT NULL,
        name TEXT NOT NULL,
        product_group TEXT,
        normal_price REAL,
        discount_price REAL,
        image_url TEXT,
        image_source TEXT,
        source_type TEXT DEFAULT 'external',
        page_no INTEGER DEFAULT NULL,
        upload_order INTEGER,
        market_price REAL DEFAULT 0,
        market_price_tax REAL DEFAULT 0,
        approval_status TEXT DEFAULT 'pending',
        approved_at TIMESTAMP DEFAULT NULL,
        approved_by INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Add approval_status column if not exists (migration)
    try:
        c.execute("ALTER TABLE products ADD COLUMN approval_status TEXT DEFAULT 'pending'")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN approved_at TIMESTAMP DEFAULT NULL")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN approved_by INTEGER DEFAULT NULL")
    except:
        pass
    
    # Add market_price columns if not exists (migration)
    try:
        c.execute("ALTER TABLE products ADD COLUMN market_price REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN market_price_tax REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN source_type TEXT DEFAULT 'external'")
    except:
        pass
    
    # Add short_name column if not exists (migration) - Broşür için kısa isim
    try:
        c.execute("ALTER TABLE products ADD COLUMN short_name TEXT DEFAULT NULL")
    except:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN page_no INTEGER")
    except:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS customer_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        barcode TEXT NOT NULL,
        image_url TEXT NOT NULL,
        approved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE NOT NULL,
        product_name TEXT,
        image_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Barcode verification cache table
    c.execute('''CREATE TABLE IF NOT EXISTS barcode_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'unverified',
        matched_images_count INTEGER DEFAULT 0,
        verification_data TEXT,
        verified_product_name TEXT,
        verified_brand TEXT,
        verification_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # AdminProduct - Ana urun deposu (golden record)
    c.execute('''CREATE TABLE IF NOT EXISTS admin_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        product_group TEXT DEFAULT 'Genel',
        sector TEXT DEFAULT 'supermarket',
        image_path TEXT,
        image_width INTEGER DEFAULT 0,
        image_height INTEGER DEFAULT 0,
        image_quality TEXT DEFAULT 'unknown',
        market_price REAL DEFAULT 0,
        market_price_tax REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add market_price columns if not exists (migration)
    try:
        c.execute("ALTER TABLE admin_products ADD COLUMN market_price REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE admin_products ADD COLUMN market_price_tax REAL DEFAULT 0")
    except:
        pass
    
    # CustomerCustomProduct - Musteri ozellestirmeleri
    c.execute('''CREATE TABLE IF NOT EXISTS customer_custom_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        barcode TEXT NOT NULL,
        custom_name TEXT,
        custom_image TEXT,
        status TEXT DEFAULT NULL,
        market_price REAL DEFAULT 0,
        market_price_tax REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES users(id),
        UNIQUE(customer_id, barcode)
    )''')
    
    # Add market_price columns if not exists (migration)
    try:
        c.execute("ALTER TABLE customer_custom_products ADD COLUMN market_price REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE customer_custom_products ADD COLUMN market_price_tax REAL DEFAULT 0")
    except:
        pass
    
    # CustomerCredits - Premium baski kredileri
    c.execute('''CREATE TABLE IF NOT EXISTS customer_credits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER UNIQUE NOT NULL,
        credits INTEGER DEFAULT 0,
        history TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES users(id)
    )''')
    
    # User settings table
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        settings TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS product_update_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        barcode TEXT NOT NULL,
        changes TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    admin_exists = c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone()
    if not admin_exists:
        c.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
                 ('admin@brosur.com', generate_password_hash('admin123'), 'Admin', 'admin'))
    
    demo_customer = c.execute("SELECT id FROM users WHERE email='demo@market.com' LIMIT 1").fetchone()
    if not demo_customer:
        c.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
                 ('demo@market.com', generate_password_hash('demo123'), 'Demo Market', 'customer'))
        demo_id = c.lastrowid
        
        demo_products = [
            ('8690000001', 'Süt 1L', 45.00, 32.90, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400'),
            ('8690000002', 'Ekmek', 15.00, 10.00, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400'),
            ('8690000003', 'Yumurta 30lu', 180.00, 139.90, 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400'),
            ('8690000004', 'Beyaz Peynir 1kg', 350.00, 279.90, 'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400'),
            ('8690000005', 'Ayçiçek Yağı 5L', 450.00, 349.90, 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400'),
            ('8690000006', 'Domates 1kg', 35.00, 24.90, 'https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=400'),
            ('8690000007', 'Patates 2.5kg', 60.00, 44.90, 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400'),
            ('8690000008', 'Makarna 500g', 28.00, 19.90, 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400'),
        ]
        
        for barcode, name, normal, discount, img in demo_products:
            c.execute('''INSERT INTO products (user_id, barcode, name, product_group, normal_price, discount_price, image_url, image_source, source_type, page_no)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (demo_id, barcode, name, 'Genel', normal, discount, img, 'admin', 'depo', 1))
            
            c.execute('''INSERT OR IGNORE INTO admin_images (barcode, product_name, image_url)
                        VALUES (?, ?, ?)''', (barcode, name, img))
    
    conn.commit()
    conn.close()

def get_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user = c.execute("SELECT id, email, name, role, password FROM users WHERE email=?",
                    (email,)).fetchone()
    conn.close()
    if user:
        try:
            if check_password_hash(user[4], password):
                return {'id': user[0], 'email': user[1], 'name': user[2], 'role': user[3]}
        except Exception as e:
            print(f"Password check error: {e}")
            return None
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user = c.execute("SELECT id, email, name, role, sector, credits FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'email': user[1], 'name': user[2], 'role': user[3], 
                'sector': user[4] or 'supermarket', 'credits': user[5] or 100.0}
    return None


def get_user_by_email(email):
    """Get user by email address"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user = c.execute("SELECT id, email, name, role, sector, credits FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'email': user[1], 'name': user[2], 'role': user[3], 
                'sector': user[4] or 'supermarket', 'credits': user[5] or 100.0}
    return None

def create_user(email, password, name=None, sector='supermarket', role='customer', credits=100):
    """Create a new user with email/password"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        user_name = name or email.split('@')[0]
        c.execute("INSERT INTO users (email, password, name, role, sector, credits) VALUES (?, ?, ?, ?, ?, ?)",
                 (email, generate_password_hash(password), user_name, role, sector, float(credits)))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def create_user_full(name, email, password, role='customer', sector='supermarket', credits=100):
    """Create a new user with all parameters - used by admin panel"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password, name, role, sector, credits) VALUES (?, ?, ?, ?, ?, ?)",
                 (email, generate_password_hash(password), name, role, sector, float(credits)))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {'id': user_id, 'email': email, 'name': name, 'role': role, 'sector': sector, 'credits': credits}
    except sqlite3.IntegrityError:
        conn.close()
        return None

def update_user_sector(user_id, sector):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET sector=? WHERE id=?", (sector, user_id))
    conn.commit()
    conn.close()


def update_user(user_id, updates):
    """Update user with given fields"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    for key, value in updates.items():
        if key == 'password':
            c.execute("UPDATE users SET password=? WHERE id=?", 
                     (generate_password_hash(value), user_id))
        elif key in ['name', 'email', 'role', 'sector']:
            c.execute(f"UPDATE users SET {key}=? WHERE id=?", (value, user_id))
        elif key == 'credits':
            c.execute("UPDATE users SET credits=? WHERE id=?", (value, user_id))
    
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Delete user by ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def update_user_credits(user_id, new_credits):
    """Update user's credits"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits=? WHERE id=?", (new_credits, user_id))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    """Get user data (alias for get_user_by_id for compatibility)"""
    return get_user_by_id(user_id)

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    users = c.execute("SELECT id, email, name, role, sector, credits, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(u) for u in users]

def get_products(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    products = c.execute("SELECT * FROM products WHERE user_id=? ORDER BY created_at DESC",
                        (user_id,)).fetchall()
    conn.close()
    return [dict(p) for p in products]

def add_product(user_id, barcode, name, normal_price, discount_price, image_url,
                image_source, product_group=None, upload_order=0,
                market_price=0, market_price_tax=0, source_type='external',
                page_no=None, approval_status='pending', short_name=None):
    """
    Add a new product to the database.
    
    approval_status:
    - 'pending': Yeni ürün, admin onayı bekliyor
    - 'approved': Admin onayladı
    - 'rejected': Admin reddetti
    
    short_name: Broşür için kısaltılmış ürün adı (AI tarafından oluşturulur)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO products (user_id, barcode, name, short_name, product_group, normal_price, discount_price, image_url, image_source, source_type, page_no, upload_order, market_price, market_price_tax, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id, barcode, name, short_name, product_group, normal_price, discount_price,
              image_url, image_source, source_type, page_no, upload_order,
              market_price, market_price_tax, approval_status))
    conn.commit()
    product_id = c.lastrowid
    conn.close()
    return product_id


def update_product(user_id, barcode, name=None, short_name=None, normal_price=None, 
                   discount_price=None, image_url=None, product_group=None):
    """
    Update product fields by barcode.
    Only updates fields that are provided (not None).
    """
    updates = {}
    if name is not None:
        updates['name'] = name
    if short_name is not None:
        updates['short_name'] = short_name
    if normal_price is not None:
        updates['normal_price'] = normal_price
    if discount_price is not None:
        updates['discount_price'] = discount_price
    if image_url is not None:
        updates['image_url'] = image_url
    if product_group is not None:
        updates['product_group'] = product_group
    
    if not updates:
        return False
    
    return update_product_fields(user_id, barcode, updates)


def update_product_fields(user_id, barcode, updates):
    """
    Update selected columns of a product row.
    """
    if not updates:
        return False
    allowed_fields = {
        'name', 'short_name', 'product_group', 'normal_price', 'discount_price',
        'image_url', 'image_source', 'upload_order', 'market_price',
        'market_price_tax', 'source_type', 'page_no'
    }
    assignments = []
    values = []
    for key, value in updates.items():
        if key in allowed_fields:
            assignments.append(f"{key}=?")
            values.append(value)
    if not assignments:
        return False
    values.extend([user_id, barcode])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE products SET {', '.join(assignments)} WHERE user_id=? AND barcode=?", values)
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated


# ============= ADMIN ONAY FONKSİYONLARI =============

def get_pending_products(sector=None):
    """
    Get all products waiting for admin approval.
    
    Args:
        sector: Optional sector filter
    
    Returns:
        List of pending products with user info
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = '''
        SELECT p.*, u.name as user_name, u.email as user_email, u.sector as user_sector
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.approval_status = 'pending'
    '''
    params = []
    
    if sector:
        query += ' AND u.sector = ?'
        params.append(sector)
    
    query += ' ORDER BY p.created_at DESC'
    
    c.execute(query, params)
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return products


def approve_product(product_id, admin_id):
    """
    Approve a pending product.
    
    Args:
        product_id: Product ID to approve
        admin_id: Admin user ID who approved
    
    Returns:
        bool: Success status
    """
    from datetime import datetime
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE products 
        SET approval_status = 'approved', 
            approved_at = ?, 
            approved_by = ?
        WHERE id = ? AND approval_status = 'pending'
    ''', (datetime.now().isoformat(), admin_id, product_id))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated


def reject_product(product_id, admin_id, reason=None):
    """
    Reject a pending product.
    
    Args:
        product_id: Product ID to reject
        admin_id: Admin user ID who rejected
        reason: Optional rejection reason
    
    Returns:
        bool: Success status
    """
    from datetime import datetime
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE products 
        SET approval_status = 'rejected', 
            approved_at = ?, 
            approved_by = ?
        WHERE id = ? AND approval_status = 'pending'
    ''', (datetime.now().isoformat(), admin_id, product_id))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated


def get_pending_count():
    """Get count of pending products for admin badge."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products WHERE approval_status = 'pending'")
    count = c.fetchone()[0]
    conn.close()
    return count


def log_product_update_request(user_id, barcode, changes):
    """
    Create a pending update request entry for depot products.
    """
    if not changes:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO product_update_requests (user_id, barcode, changes)
                 VALUES (?, ?, ?)''',
              (user_id, barcode, json.dumps(changes, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_product_by_barcode(user_id, barcode):
    """Get a product by user_id and barcode"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    product = c.execute(
        "SELECT * FROM products WHERE user_id=? AND barcode=?", 
        (user_id, barcode)
    ).fetchone()
    conn.close()
    return dict(product) if product else None


def update_product_image(user_id, barcode, image_url):
    """Update product image by barcode"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE products SET image_url=? WHERE user_id=? AND barcode=?",
        (image_url, user_id, barcode)
    )
    conn.commit()
    conn.close()


def find_image(barcode, user_id):
    """
    Barkod için resim ara - Arama Hiyerarşisi:
    1. ÖNCE Admin Deposu (onaylanmış genel ürünler)
    2. SONRA Müşteri Deposu (kullanıcıya özel)
    3. Bulunamazsa None döner (caller CAMGOZ API'yi dener)
    
    NOT: Admin deposunda varsa CAMGOZ sorgusu YAPILMAZ!
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. ÖNCE Admin Deposunu kontrol et (onaylanmış ürünler)
    admin_img = c.execute("SELECT image_url FROM admin_images WHERE barcode=?",
                         (barcode,)).fetchone()
    if admin_img:
        conn.close()
        return {'source': 'admin', 'url': admin_img[0]}
    
    # 2. Admin deposunda yoksa müşteri deposuna bak
    customer_img = c.execute("SELECT image_url FROM customer_images WHERE user_id=? AND barcode=? AND approved=1",
                            (user_id, barcode)).fetchone()
    if customer_img:
        conn.close()
        return {'source': 'customer', 'url': customer_img[0]}
    
    # 3. Hiçbir yerde bulunamadı - caller CAMGOZ API'yi deneyecek
    conn.close()
    return None

def save_customer_image(user_id, barcode, image_url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO customer_images (user_id, barcode, image_url, approved)
                VALUES (?, ?, ?, ?)''', (user_id, barcode, image_url, False))
    conn.commit()
    conn.close()

# Barcode Verification Functions
def get_barcode_verification(barcode):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    verification = c.execute("SELECT * FROM barcode_verifications WHERE barcode=?", (barcode,)).fetchone()
    conn.close()
    return dict(verification) if verification else None

def save_barcode_verification(barcode, status, matched_count=0, product_name=None, brand=None, reason=None, data=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    existing = c.execute("SELECT id FROM barcode_verifications WHERE barcode=?", (barcode,)).fetchone()
    
    verification_data = json.dumps(data) if data else None
    
    if existing:
        c.execute('''UPDATE barcode_verifications SET 
                    status=?, matched_images_count=?, verified_product_name=?, verified_brand=?, 
                    verification_reason=?, verification_data=?, updated_at=CURRENT_TIMESTAMP
                    WHERE barcode=?''',
                 (status, matched_count, product_name, brand, reason, verification_data, barcode))
    else:
        c.execute('''INSERT INTO barcode_verifications 
                    (barcode, status, matched_images_count, verified_product_name, verified_brand, verification_reason, verification_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (barcode, status, matched_count, product_name, brand, reason, verification_data))
    
    conn.commit()
    conn.close()

def is_barcode_verified(barcode):
    verification = get_barcode_verification(barcode)
    return verification and verification.get('status') == 'verified' and verification.get('matched_images_count', 0) >= 3

def save_user_settings(user_id, settings):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        company_name TEXT,
        address TEXT,
        city TEXT,
        district TEXT,
        phone TEXT,
        social_media TEXT,
        meal_cards TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    existing = c.execute("SELECT id FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
    
    social_media_json = json.dumps(settings.get('socialMedia', {}))
    meal_cards_json = json.dumps(settings.get('mealCards', {}))
    
    if existing:
        c.execute('''UPDATE user_settings SET 
                    company_name=?, address=?, city=?, district=?, phone=?, 
                    social_media=?, meal_cards=?, updated_at=CURRENT_TIMESTAMP
                    WHERE user_id=?''',
                 (settings.get('name'), settings.get('address'), 
                  settings.get('city'), settings.get('district'),
                  settings.get('phone'), social_media_json, meal_cards_json, user_id))
    else:
        c.execute('''INSERT INTO user_settings 
                    (user_id, company_name, address, city, district, phone, social_media, meal_cards)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, settings.get('name'), settings.get('address'),
                  settings.get('city'), settings.get('district'),
                  settings.get('phone'), social_media_json, meal_cards_json))
    
    conn.commit()
    conn.close()

def get_user_settings(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        company_name TEXT,
        address TEXT,
        city TEXT,
        district TEXT,
        phone TEXT,
        social_media TEXT,
        meal_cards TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    
    settings = c.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    
    if settings:
        result = {
            'name': settings['company_name'],
            'address': settings['address'],
            'city': settings['city'],
            'district': settings['district'],
            'phone': settings['phone']
        }
        try:
            result['socialMedia'] = json.loads(settings['social_media']) if settings['social_media'] else {}
        except:
            result['socialMedia'] = {}
        try:
            result['mealCards'] = json.loads(settings['meal_cards']) if settings['meal_cards'] else {}
        except:
            result['mealCards'] = {}
        return result
    return None

# ========== BARCODE SEARCH FUNCTIONS ==========
def search_image_bank_by_barcode(barcode):
    """Search for product in admin image bank by barcode"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # First check which columns exist in admin_images table
    columns_info = c.execute("PRAGMA table_info(admin_images)").fetchall()
    column_names = [col['name'] for col in columns_info]
    
    # Build query based on available columns
    select_cols = ['barcode', 'image_url']
    if 'product_name' in column_names:
        select_cols.append('product_name')
    if 'product_group' in column_names:
        select_cols.append('product_group')
    
    query = f"SELECT {', '.join(select_cols)} FROM admin_images WHERE barcode = ?"
    admin_img = c.execute(query, (barcode,)).fetchone()
    
    conn.close()
    
    if admin_img:
        result = {
            'barcode': admin_img['barcode'],
            'image_url': admin_img['image_url'],
            'product_name': '',
            'product_group': ''
        }
        if 'product_name' in column_names and admin_img['product_name']:
            result['product_name'] = admin_img['product_name']
        if 'product_group' in column_names and admin_img['product_group']:
            result['product_group'] = admin_img['product_group']
        return result
    return None

def search_customer_products_by_barcode(user_id, barcode):
    """Search for product in customer's product history by barcode"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Search in products table for this user
    product = c.execute("""
        SELECT barcode, name, product_group, normal_price, discount_price, image_url 
        FROM products 
        WHERE user_id = ? AND barcode = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id, barcode)).fetchone()
    
    conn.close()
    
    if product:
        return {
            'barcode': product['barcode'],
            'name': product['name'],
            'product_group': product['product_group'] or '',
            'normal_price': product['normal_price'] or 0,
            'discount_price': product['discount_price'] or 0,
            'image_url': product['image_url'] or ''
        }
    return None
