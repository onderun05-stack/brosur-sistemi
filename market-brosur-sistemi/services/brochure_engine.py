# -*- coding: utf-8 -*-
"""
Brochure Engine Service - Multi-page brochure management system.

Features:
- Multi-page brochure support
- Page management (add, delete, copy, reorder)
- Product placement with drag-and-drop
- Park area for unplaced products
- Page locking
- Layout templates
- JSON-based storage
- Export to PDF/PNG/JPEG
"""

import os
import json
import logging
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# Constants
BROCHURES_DIR = 'data/brochures'
TEMPLATES_DIR = 'data/templates'
MAX_PAGES = 20
DEFAULT_PAGE_SIZE = {'width': 595, 'height': 842}  # A4 in points

# Layout templates
LAYOUT_TEMPLATES = {
    'grid_4x4': {
        'name': 'Grid 4x4',
        'cols': 4,
        'rows': 4,
        'products_per_page': 16
    },
    'grid_3x3': {
        'name': 'Grid 3x3',
        'cols': 3,
        'rows': 3,
        'products_per_page': 9
    },
    'grid_2x3': {
        'name': 'Grid 2x3',
        'cols': 2,
        'rows': 3,
        'products_per_page': 6
    },
    'campaign': {
        'name': 'Kampanya',
        'cols': 2,
        'rows': 2,
        'products_per_page': 4,
        'highlight_first': True
    },
    'manav': {
        'name': 'Manav Reyonu',
        'cols': 3,
        'rows': 4,
        'products_per_page': 12,
        'theme': 'green'
    },
    'free': {
        'name': 'Serbest Düzen',
        'cols': 0,
        'rows': 0,
        'products_per_page': 0
    }
}


def ensure_directories():
    """Ensure brochure directories exist"""
    os.makedirs(BROCHURES_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def get_brochure_path(user_id: int, brochure_id: str) -> str:
    """Get path to brochure JSON file"""
    user_dir = os.path.join(BROCHURES_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, f'{brochure_id}.json')


def generate_brochure_id() -> str:
    """Generate unique brochure ID"""
    return f'br_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:6]}'


def create_empty_page(page_number: int, layout: str = 'grid_4x4') -> Dict:
    """Create an empty brochure page"""
    return {
        'id': f'page_{uuid.uuid4().hex[:8]}',
        'number': page_number,
        'layout': layout,
        'locked': False,
        'products': [],
        'background': None,
        'theme': None,
        'created_at': datetime.now().isoformat()
    }


def create_product_box(product_data: Dict, position: Dict = None) -> Dict:
    """Create a product box for the brochure"""
    return {
        'id': f'prod_{uuid.uuid4().hex[:8]}',
        'barcode': product_data.get('barcode', ''),
        'name': product_data.get('name', ''),
        'normal_price': product_data.get('normal_price', 0),
        'discount_price': product_data.get('discount_price', 0),
        'image_url': product_data.get('image_url', ''),
        'slogan': product_data.get('slogan', ''),
        'product_group': product_data.get('product_group', ''),
        'position': position or {'x': 0, 'y': 0, 'width': 140, 'height': 180},
        'locked': False,
        'z_index': 1,
        'style': {
            'price_tag_style': 'default',
            'show_old_price': product_data.get('normal_price', 0) > 0,
            'font_size': 12,
            'border': False
        }
    }


# ============= BROCHURE CRUD =============

def create_brochure(user_id: int, name: str, sector: str = 'supermarket') -> Dict:
    """
    Create a new brochure with one empty page.
    
    Args:
        user_id: Owner user ID
        name: Brochure name
        sector: Product sector
    
    Returns:
        dict: Brochure data
    """
    ensure_directories()
    
    brochure_id = generate_brochure_id()
    
    brochure = {
        'id': brochure_id,
        'user_id': user_id,
        'name': name,
        'sector': sector,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'page_size': DEFAULT_PAGE_SIZE.copy(),
        'pages': [create_empty_page(1)],
        'parking_area': [],  # Products not yet placed
        'settings': {
            'watermark_enabled': True,
            'watermark_opacity': 25,
            'default_layout': 'grid_4x4',
            'auto_arrange': True
        },
        'metadata': {
            'total_products': 0,
            'export_count': 0,
            'last_export': None
        }
    }
    
    # Save brochure
    brochure_path = get_brochure_path(user_id, brochure_id)
    with open(brochure_path, 'w', encoding='utf-8') as f:
        json.dump(brochure, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Brochure created: {brochure_id} for user {user_id}")
    
    return brochure


def get_brochure(user_id: int, brochure_id: str) -> Optional[Dict]:
    """Get brochure by ID"""
    brochure_path = get_brochure_path(user_id, brochure_id)
    
    if not os.path.exists(brochure_path):
        return None
    
    try:
        with open(brochure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading brochure: {e}")
        return None


def save_brochure(brochure: Dict) -> bool:
    """Save brochure to disk"""
    try:
        brochure['updated_at'] = datetime.now().isoformat()
        brochure_path = get_brochure_path(brochure['user_id'], brochure['id'])
        
        with open(brochure_path, 'w', encoding='utf-8') as f:
            json.dump(brochure, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logging.error(f"Error saving brochure: {e}")
        return False


def delete_brochure(user_id: int, brochure_id: str) -> bool:
    """Delete brochure"""
    brochure_path = get_brochure_path(user_id, brochure_id)
    
    if os.path.exists(brochure_path):
        os.remove(brochure_path)
        logging.info(f"Brochure deleted: {brochure_id}")
        return True
    
    return False


def list_brochures(user_id: int) -> List[Dict]:
    """List all brochures for a user"""
    user_dir = os.path.join(BROCHURES_DIR, str(user_id))
    
    if not os.path.exists(user_dir):
        return []
    
    brochures = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(user_dir, filename), 'r', encoding='utf-8') as f:
                    brochure = json.load(f)
                    brochures.append({
                        'id': brochure['id'],
                        'name': brochure['name'],
                        'sector': brochure.get('sector', 'supermarket'),
                        'page_count': len(brochure.get('pages', [])),
                        'product_count': brochure.get('metadata', {}).get('total_products', 0),
                        'created_at': brochure['created_at'],
                        'updated_at': brochure['updated_at']
                    })
            except:
                pass
    
    # Sort by updated_at (newest first)
    brochures.sort(key=lambda x: x['updated_at'], reverse=True)
    
    return brochures


# ============= PAGE MANAGEMENT =============

def add_page(brochure: Dict, layout: str = None) -> Dict:
    """Add a new page to brochure"""
    if len(brochure['pages']) >= MAX_PAGES:
        return {'success': False, 'error': f'Maximum {MAX_PAGES} pages allowed'}
    
    page_number = len(brochure['pages']) + 1
    layout = layout or brochure['settings'].get('default_layout', 'grid_4x4')
    
    new_page = create_empty_page(page_number, layout)
    brochure['pages'].append(new_page)
    
    save_brochure(brochure)
    
    return {'success': True, 'page': new_page}


def delete_page(brochure: Dict, page_id: str) -> Dict:
    """Delete a page from brochure"""
    if len(brochure['pages']) <= 1:
        return {'success': False, 'error': 'Cannot delete last page'}
    
    page_index = None
    page_to_delete = None
    
    for i, page in enumerate(brochure['pages']):
        if page['id'] == page_id:
            page_index = i
            page_to_delete = page
            break
    
    if page_index is None:
        return {'success': False, 'error': 'Page not found'}
    
    if page_to_delete.get('locked'):
        return {'success': False, 'error': 'Cannot delete locked page'}
    
    # Move products to parking area
    for product in page_to_delete.get('products', []):
        brochure['parking_area'].append(product)
    
    # Remove page
    brochure['pages'].pop(page_index)
    
    # Renumber pages
    for i, page in enumerate(brochure['pages']):
        page['number'] = i + 1
    
    save_brochure(brochure)
    
    return {'success': True, 'moved_to_parking': len(page_to_delete.get('products', []))}


def copy_page(brochure: Dict, page_id: str) -> Dict:
    """Copy a page"""
    if len(brochure['pages']) >= MAX_PAGES:
        return {'success': False, 'error': f'Maximum {MAX_PAGES} pages allowed'}
    
    source_page = None
    source_index = None
    
    for i, page in enumerate(brochure['pages']):
        if page['id'] == page_id:
            source_page = page
            source_index = i
            break
    
    if source_page is None:
        return {'success': False, 'error': 'Page not found'}
    
    # Deep copy page
    new_page = json.loads(json.dumps(source_page))
    new_page['id'] = f'page_{uuid.uuid4().hex[:8]}'
    new_page['number'] = len(brochure['pages']) + 1
    new_page['locked'] = False
    new_page['created_at'] = datetime.now().isoformat()
    
    # Generate new IDs for products
    for product in new_page.get('products', []):
        product['id'] = f'prod_{uuid.uuid4().hex[:8]}'
    
    brochure['pages'].append(new_page)
    save_brochure(brochure)
    
    return {'success': True, 'page': new_page}


def reorder_pages(brochure: Dict, page_order: List[str]) -> Dict:
    """Reorder pages by ID list"""
    # Create page map
    page_map = {page['id']: page for page in brochure['pages']}
    
    # Validate all page IDs exist
    for page_id in page_order:
        if page_id not in page_map:
            return {'success': False, 'error': f'Page {page_id} not found'}
    
    # Reorder
    new_pages = []
    for i, page_id in enumerate(page_order):
        page = page_map[page_id]
        page['number'] = i + 1
        new_pages.append(page)
    
    brochure['pages'] = new_pages
    save_brochure(brochure)
    
    return {'success': True}


def toggle_page_lock(brochure: Dict, page_id: str) -> Dict:
    """Toggle page lock status"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            page['locked'] = not page['locked']
            save_brochure(brochure)
            return {'success': True, 'locked': page['locked']}
    
    return {'success': False, 'error': 'Page not found'}


def set_page_layout(brochure: Dict, page_id: str, layout: str) -> Dict:
    """Set page layout template"""
    if layout not in LAYOUT_TEMPLATES:
        return {'success': False, 'error': 'Invalid layout'}
    
    for page in brochure['pages']:
        if page['id'] == page_id:
            if page.get('locked'):
                return {'success': False, 'error': 'Cannot modify locked page'}
            
            page['layout'] = layout
            save_brochure(brochure)
            return {'success': True, 'layout': layout}
    
    return {'success': False, 'error': 'Page not found'}


# ============= PRODUCT MANAGEMENT =============

def add_product_to_page(brochure: Dict, page_id: str, product_data: Dict, position: Dict = None) -> Dict:
    """Add a product to a specific page"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            if page.get('locked'):
                return {'success': False, 'error': 'Cannot modify locked page'}
            
            product_box = create_product_box(product_data, position)
            page['products'].append(product_box)
            
            # Update metadata
            brochure['metadata']['total_products'] = sum(
                len(p.get('products', [])) for p in brochure['pages']
            ) + len(brochure.get('parking_area', []))
            
            save_brochure(brochure)
            return {'success': True, 'product': product_box}
    
    return {'success': False, 'error': 'Page not found'}


def remove_product_from_page(brochure: Dict, page_id: str, product_id: str, move_to_parking: bool = True) -> Dict:
    """Remove a product from a page"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            if page.get('locked'):
                return {'success': False, 'error': 'Cannot modify locked page'}
            
            for i, product in enumerate(page['products']):
                if product['id'] == product_id:
                    if product.get('locked'):
                        return {'success': False, 'error': 'Product is locked'}
                    
                    removed = page['products'].pop(i)
                    
                    if move_to_parking:
                        brochure['parking_area'].append(removed)
                    
                    save_brochure(brochure)
                    return {'success': True, 'moved_to_parking': move_to_parking}
            
            return {'success': False, 'error': 'Product not found on page'}
    
    return {'success': False, 'error': 'Page not found'}


def move_product(brochure: Dict, product_id: str, target_page_id: str, position: Dict = None) -> Dict:
    """Move product between pages or from parking area"""
    product = None
    source = None
    
    # Check parking area
    for i, p in enumerate(brochure.get('parking_area', [])):
        if p['id'] == product_id:
            product = brochure['parking_area'].pop(i)
            source = 'parking'
            break
    
    # Check pages
    if not product:
        for page in brochure['pages']:
            for i, p in enumerate(page['products']):
                if p['id'] == product_id:
                    if page.get('locked') or p.get('locked'):
                        return {'success': False, 'error': 'Product or page is locked'}
                    product = page['products'].pop(i)
                    source = page['id']
                    break
            if product:
                break
    
    if not product:
        return {'success': False, 'error': 'Product not found'}
    
    # Find target
    if target_page_id == 'parking':
        brochure['parking_area'].append(product)
    else:
        target_page = None
        for page in brochure['pages']:
            if page['id'] == target_page_id:
                target_page = page
                break
        
        if not target_page:
            # Put back to source
            if source == 'parking':
                brochure['parking_area'].append(product)
            else:
                for page in brochure['pages']:
                    if page['id'] == source:
                        page['products'].append(product)
                        break
            return {'success': False, 'error': 'Target page not found'}
        
        if target_page.get('locked'):
            # Put back
            if source == 'parking':
                brochure['parking_area'].append(product)
            return {'success': False, 'error': 'Target page is locked'}
        
        if position:
            product['position'] = position
        
        target_page['products'].append(product)
    
    save_brochure(brochure)
    return {'success': True, 'source': source, 'target': target_page_id}


def update_product_position(brochure: Dict, page_id: str, product_id: str, position: Dict) -> Dict:
    """Update product position on page"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            if page.get('locked'):
                return {'success': False, 'error': 'Page is locked'}
            
            for product in page['products']:
                if product['id'] == product_id:
                    if product.get('locked'):
                        return {'success': False, 'error': 'Product is locked'}
                    
                    product['position'].update(position)
                    save_brochure(brochure)
                    return {'success': True}
            
            return {'success': False, 'error': 'Product not found'}
    
    return {'success': False, 'error': 'Page not found'}


def toggle_product_lock(brochure: Dict, page_id: str, product_id: str) -> Dict:
    """Toggle product lock status"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            for product in page['products']:
                if product['id'] == product_id:
                    product['locked'] = not product.get('locked', False)
                    save_brochure(brochure)
                    return {'success': True, 'locked': product['locked']}
            return {'success': False, 'error': 'Product not found'}
    return {'success': False, 'error': 'Page not found'}


# ============= PARKING AREA =============

def add_to_parking(brochure: Dict, product_data: Dict) -> Dict:
    """Add product directly to parking area"""
    product_box = create_product_box(product_data)
    brochure['parking_area'].append(product_box)
    
    brochure['metadata']['total_products'] = sum(
        len(p.get('products', [])) for p in brochure['pages']
    ) + len(brochure.get('parking_area', []))
    
    save_brochure(brochure)
    return {'success': True, 'product': product_box}


def remove_from_parking(brochure: Dict, product_id: str) -> Dict:
    """Remove product from parking area"""
    for i, product in enumerate(brochure.get('parking_area', [])):
        if product['id'] == product_id:
            brochure['parking_area'].pop(i)
            save_brochure(brochure)
            return {'success': True}
    
    return {'success': False, 'error': 'Product not found in parking'}


def clear_parking(brochure: Dict) -> Dict:
    """Clear all products from parking area"""
    count = len(brochure.get('parking_area', []))
    brochure['parking_area'] = []
    save_brochure(brochure)
    return {'success': True, 'cleared': count}


# ============= AUTO LAYOUT =============

def auto_arrange_page(brochure: Dict, page_id: str) -> Dict:
    """Auto-arrange products on a page based on layout"""
    for page in brochure['pages']:
        if page['id'] == page_id:
            if page.get('locked'):
                return {'success': False, 'error': 'Page is locked'}
            
            layout = LAYOUT_TEMPLATES.get(page.get('layout', 'grid_4x4'))
            if not layout or layout['cols'] == 0:
                return {'success': False, 'error': 'Cannot auto-arrange free layout'}
            
            page_width = brochure['page_size']['width']
            page_height = brochure['page_size']['height']
            
            cols = layout['cols']
            rows = layout['rows']
            
            cell_width = (page_width - 40) // cols
            cell_height = (page_height - 80) // rows
            
            products = [p for p in page['products'] if not p.get('locked')]
            
            for i, product in enumerate(products):
                row = i // cols
                col = i % cols
                
                if row >= rows:
                    # Move to parking if doesn't fit
                    page['products'].remove(product)
                    brochure['parking_area'].append(product)
                else:
                    product['position'] = {
                        'x': 20 + col * cell_width,
                        'y': 40 + row * cell_height,
                        'width': cell_width - 10,
                        'height': cell_height - 10
                    }
            
            save_brochure(brochure)
            return {'success': True, 'arranged': len(products)}
    
    return {'success': False, 'error': 'Page not found'}


def distribute_products_to_pages(brochure: Dict, products: List[Dict]) -> Dict:
    """Distribute products across pages automatically"""
    layout = LAYOUT_TEMPLATES.get(brochure['settings'].get('default_layout', 'grid_4x4'))
    products_per_page = layout.get('products_per_page', 16)
    
    current_page_index = 0
    placed_count = 0
    
    for product_data in products:
        # Find page with space
        while current_page_index < len(brochure['pages']):
            page = brochure['pages'][current_page_index]
            
            if page.get('locked'):
                current_page_index += 1
                continue
            
            if len(page['products']) < products_per_page:
                break
            
            current_page_index += 1
        
        # Add new page if needed
        if current_page_index >= len(brochure['pages']):
            if len(brochure['pages']) >= MAX_PAGES:
                # Put rest in parking
                brochure['parking_area'].append(create_product_box(product_data))
                continue
            
            add_page(brochure)
            current_page_index = len(brochure['pages']) - 1
        
        # Add product to page
        page = brochure['pages'][current_page_index]
        page['products'].append(create_product_box(product_data))
        placed_count += 1
    
    # Auto-arrange all pages
    for page in brochure['pages']:
        if not page.get('locked'):
            auto_arrange_page(brochure, page['id'])
    
    save_brochure(brochure)
    
    return {
        'success': True,
        'placed': placed_count,
        'in_parking': len(brochure['parking_area']),
        'pages_used': len(brochure['pages'])
    }


# ============= TEMPLATES =============

def save_as_template(brochure: Dict, template_name: str) -> Dict:
    """Save current brochure as a reusable template"""
    ensure_directories()
    
    template_id = f'tpl_{uuid.uuid4().hex[:8]}'
    
    # Create template (without product data, only layout)
    template = {
        'id': template_id,
        'name': template_name,
        'user_id': brochure['user_id'],
        'sector': brochure.get('sector', 'supermarket'),
        'created_at': datetime.now().isoformat(),
        'page_size': brochure['page_size'].copy(),
        'settings': brochure['settings'].copy(),
        'pages': []
    }
    
    for page in brochure['pages']:
        template_page = {
            'layout': page.get('layout', 'grid_4x4'),
            'background': page.get('background'),
            'theme': page.get('theme'),
            'product_positions': [
                {
                    'position': p['position'].copy(),
                    'style': p.get('style', {}).copy()
                }
                for p in page.get('products', [])
            ]
        }
        template['pages'].append(template_page)
    
    # Save template
    template_path = os.path.join(TEMPLATES_DIR, str(brochure['user_id']))
    os.makedirs(template_path, exist_ok=True)
    
    with open(os.path.join(template_path, f'{template_id}.json'), 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    return {'success': True, 'template_id': template_id, 'name': template_name}


def list_templates(user_id: int) -> List[Dict]:
    """List user's saved templates"""
    template_path = os.path.join(TEMPLATES_DIR, str(user_id))
    
    if not os.path.exists(template_path):
        return []
    
    templates = []
    for filename in os.listdir(template_path):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(template_path, filename), 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    templates.append({
                        'id': template['id'],
                        'name': template['name'],
                        'sector': template.get('sector'),
                        'page_count': len(template.get('pages', [])),
                        'created_at': template['created_at']
                    })
            except:
                pass
    
    return templates


def apply_template(brochure: Dict, template_id: str) -> Dict:
    """Apply a template to existing brochure"""
    template_path = os.path.join(TEMPLATES_DIR, str(brochure['user_id']), f'{template_id}.json')
    
    if not os.path.exists(template_path):
        return {'success': False, 'error': 'Template not found'}
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        # Apply settings
        brochure['settings'].update(template.get('settings', {}))
        brochure['page_size'] = template.get('page_size', DEFAULT_PAGE_SIZE)
        
        # Apply page layouts
        for i, template_page in enumerate(template.get('pages', [])):
            if i < len(brochure['pages']):
                page = brochure['pages'][i]
                if not page.get('locked'):
                    page['layout'] = template_page.get('layout', 'grid_4x4')
                    page['background'] = template_page.get('background')
                    page['theme'] = template_page.get('theme')
        
        save_brochure(brochure)
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Initialize directories
ensure_directories()

