# -*- coding: utf-8 -*-
"""
Bulk Operations Service

Handles bulk operations on products:
- Bulk price update
- Bulk image change
- Bulk slogan generation
- Bulk delete
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import database


class BulkOperations:
    """
    Bulk operations manager for products.
    """
    
    def __init__(self):
        pass
    
    def bulk_update_prices(self, user_id: int, products: List[Dict], 
                           operation: str = 'set', value: float = 0) -> Dict[str, Any]:
        """
        Bulk update product prices.
        
        Args:
            user_id: User ID
            products: List of {barcode, current_price}
            operation: 'set', 'increase', 'decrease', 'percent_increase', 'percent_decrease'
            value: Value for the operation
        
        Returns:
            Result with updated count and errors
        """
        updated = 0
        errors = []
        
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                
                for product in products:
                    barcode = product.get('barcode')
                    current_price = product.get('price', 0)
                    
                    try:
                        new_price = self._calculate_new_price(current_price, operation, value)
                        
                        # Update in database
                        cursor.execute('''
                            UPDATE products 
                            SET price = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE barcode = ? AND user_id = ?
                        ''', (new_price, barcode, user_id))
                        
                        if cursor.rowcount > 0:
                            updated += 1
                        else:
                            # Try customer custom products
                            cursor.execute('''
                                UPDATE customer_custom_products
                                SET price = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE barcode = ? AND user_id = ?
                            ''', (new_price, barcode, user_id))
                            
                            if cursor.rowcount > 0:
                                updated += 1
                            else:
                                errors.append(f"{barcode}: Ürün bulunamadı")
                                
                    except Exception as e:
                        errors.append(f"{barcode}: {str(e)}")
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Bulk price update failed: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'updated': updated,
            'errors': errors,
            'total': len(products)
        }
    
    def _calculate_new_price(self, current_price: float, operation: str, value: float) -> float:
        """Calculate new price based on operation"""
        if operation == 'set':
            return max(0, value)
        elif operation == 'increase':
            return max(0, current_price + value)
        elif operation == 'decrease':
            return max(0, current_price - value)
        elif operation == 'percent_increase':
            return max(0, current_price * (1 + value / 100))
        elif operation == 'percent_decrease':
            return max(0, current_price * (1 - value / 100))
        else:
            return current_price
    
    def bulk_update_images(self, user_id: int, products: List[Dict]) -> Dict[str, Any]:
        """
        Bulk update product images.
        
        Args:
            user_id: User ID
            products: List of {barcode, image_url}
        
        Returns:
            Result with updated count and errors
        """
        updated = 0
        errors = []
        
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                
                for product in products:
                    barcode = product.get('barcode')
                    image_url = product.get('image_url')
                    
                    if not barcode or not image_url:
                        errors.append(f"{barcode}: Barkod veya görsel eksik")
                        continue
                    
                    try:
                        # Update in database
                        cursor.execute('''
                            UPDATE products 
                            SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE barcode = ? AND user_id = ?
                        ''', (image_url, barcode, user_id))
                        
                        if cursor.rowcount > 0:
                            updated += 1
                        else:
                            cursor.execute('''
                                UPDATE customer_custom_products
                                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE barcode = ? AND user_id = ?
                            ''', (image_url, barcode, user_id))
                            
                            if cursor.rowcount > 0:
                                updated += 1
                            else:
                                errors.append(f"{barcode}: Ürün bulunamadı")
                                
                    except Exception as e:
                        errors.append(f"{barcode}: {str(e)}")
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Bulk image update failed: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'updated': updated,
            'errors': errors,
            'total': len(products)
        }
    
    def bulk_generate_slogans(self, user_id: int, products: List[Dict]) -> Dict[str, Any]:
        """
        Bulk generate AI slogans for products.
        
        Args:
            user_id: User ID
            products: List of {barcode, name, category}
        
        Returns:
            Result with generated slogans
        """
        generated = []
        errors = []
        
        try:
            # Check if OpenAI is available
            try:
                import openai
                from openai import OpenAI
                client = OpenAI()
                has_ai = True
            except Exception:
                has_ai = False
            
            for product in products:
                barcode = product.get('barcode')
                name = product.get('name', '')
                category = product.get('category', '')
                
                try:
                    if has_ai:
                        # Generate with AI
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{
                                "role": "user",
                                "content": f"'{name}' ürünü için kısa ve çekici bir market broşürü sloganı yaz. Kategori: {category}. Maksimum 10 kelime."
                            }],
                            max_tokens=50
                        )
                        slogan = response.choices[0].message.content.strip()
                    else:
                        # Fallback slogans
                        slogans = [
                            f"En taze {name}!",
                            f"{name} - Kaçırılmaz fırsat!",
                            f"Kaliteli {name} uygun fiyata",
                            f"Sezonun en iyisi: {name}",
                            f"{name} şimdi çok uygun!"
                        ]
                        import random
                        slogan = random.choice(slogans)
                    
                    generated.append({
                        'barcode': barcode,
                        'name': name,
                        'slogan': slogan
                    })
                    
                except Exception as e:
                    errors.append(f"{barcode}: {str(e)}")
                    
        except Exception as e:
            logging.error(f"Bulk slogan generation failed: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'generated': generated,
            'errors': errors,
            'total': len(products)
        }
    
    def bulk_delete_products(self, user_id: int, barcodes: List[str]) -> Dict[str, Any]:
        """
        Bulk delete products.
        
        Args:
            user_id: User ID
            barcodes: List of barcodes to delete
        
        Returns:
            Result with deleted count
        """
        deleted = 0
        errors = []
        
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                
                for barcode in barcodes:
                    try:
                        # Delete from products
                        cursor.execute('''
                            DELETE FROM products 
                            WHERE barcode = ? AND user_id = ?
                        ''', (barcode, user_id))
                        
                        if cursor.rowcount > 0:
                            deleted += 1
                        else:
                            # Try customer custom products
                            cursor.execute('''
                                DELETE FROM customer_custom_products
                                WHERE barcode = ? AND user_id = ?
                            ''', (barcode, user_id))
                            
                            if cursor.rowcount > 0:
                                deleted += 1
                            else:
                                errors.append(f"{barcode}: Ürün bulunamadı")
                                
                    except Exception as e:
                        errors.append(f"{barcode}: {str(e)}")
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Bulk delete failed: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'deleted': deleted,
            'errors': errors,
            'total': len(barcodes)
        }
    
    def bulk_add_labels(self, user_id: int, products: List[Dict], 
                        labels: List[str]) -> Dict[str, Any]:
        """
        Bulk add labels/tags to products.
        
        Args:
            user_id: User ID
            products: List of {barcode}
            labels: Labels to add ('Yeni', 'İndirimli', 'Sınırlı Stok', etc.)
        
        Returns:
            Result with updated count
        """
        updated = 0
        errors = []
        
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                
                # Ensure labels column exists
                try:
                    cursor.execute('ALTER TABLE products ADD COLUMN labels TEXT')
                except:
                    pass  # Column already exists
                
                labels_json = ','.join(labels)
                
                for product in products:
                    barcode = product.get('barcode')
                    
                    try:
                        cursor.execute('''
                            UPDATE products 
                            SET labels = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE barcode = ? AND user_id = ?
                        ''', (labels_json, barcode, user_id))
                        
                        if cursor.rowcount > 0:
                            updated += 1
                        else:
                            errors.append(f"{barcode}: Ürün bulunamadı")
                            
                    except Exception as e:
                        errors.append(f"{barcode}: {str(e)}")
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Bulk add labels failed: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'updated': updated,
            'errors': errors,
            'total': len(products)
        }


# Global instance
bulk_ops = BulkOperations()


# ============= API FUNCTIONS =============

def bulk_update_prices(user_id: int, products: List[Dict], 
                       operation: str, value: float) -> Dict:
    """Bulk update prices"""
    return bulk_ops.bulk_update_prices(user_id, products, operation, value)


def bulk_update_images(user_id: int, products: List[Dict]) -> Dict:
    """Bulk update images"""
    return bulk_ops.bulk_update_images(user_id, products)


def bulk_generate_slogans(user_id: int, products: List[Dict]) -> Dict:
    """Bulk generate slogans"""
    return bulk_ops.bulk_generate_slogans(user_id, products)


def bulk_delete_products(user_id: int, barcodes: List[str]) -> Dict:
    """Bulk delete products"""
    return bulk_ops.bulk_delete_products(user_id, barcodes)


def bulk_add_labels(user_id: int, products: List[Dict], labels: List[str]) -> Dict:
    """Bulk add labels"""
    return bulk_ops.bulk_add_labels(user_id, products, labels)

