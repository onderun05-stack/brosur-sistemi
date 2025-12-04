# -*- coding: utf-8 -*-
"""
Version History Service

Manages version history for brochures.
Keeps last N versions for each brochure (user-specific).
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import database


class VersionHistory:
    """
    Version history manager for brochures.
    """
    
    MAX_VERSIONS_PER_BROCHURE = 10  # Keep last 10 versions
    
    def __init__(self):
        self.init_table()
    
    def init_table(self):
        """Create version history table if not exists"""
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brochure_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        brochure_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        version_number INTEGER NOT NULL,
                        data TEXT NOT NULL,
                        action TEXT DEFAULT 'save',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                # Index for fast lookup
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_versions_brochure 
                    ON brochure_versions(brochure_id, version_number DESC)
                ''')
                
                conn.commit()
                logging.info("✅ Version history table initialized")
                
        except Exception as e:
            logging.error(f"Failed to init version history table: {e}")
    
    def save_version(self, brochure_id: str, user_id: int, data: Dict[str, Any], 
                     action: str = 'save') -> Optional[int]:
        """
        Save a new version of a brochure.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
            data: Brochure data to save
            action: Action description (save, auto, restore, etc.)
        
        Returns:
            Version number or None if failed
        """
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                
                # Get next version number
                cursor.execute('''
                    SELECT MAX(version_number) 
                    FROM brochure_versions 
                    WHERE brochure_id = ? AND user_id = ?
                ''', (brochure_id, user_id))
                
                result = cursor.fetchone()
                next_version = (result[0] or 0) + 1
                
                # Save new version
                cursor.execute('''
                    INSERT INTO brochure_versions 
                    (brochure_id, user_id, version_number, data, action)
                    VALUES (?, ?, ?, ?, ?)
                ''', (brochure_id, user_id, next_version, json.dumps(data), action))
                
                # Cleanup old versions
                self._cleanup_old_versions(cursor, brochure_id, user_id)
                
                conn.commit()
                
                logging.info(f"Version {next_version} saved for brochure {brochure_id}")
                return next_version
                
        except Exception as e:
            logging.error(f"Failed to save version: {e}")
            return None
    
    def get_versions(self, brochure_id: str, user_id: int, 
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get version history for a brochure.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
            limit: Maximum number of versions to return
        
        Returns:
            List of version summaries (without full data)
        """
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, version_number, action, created_at
                    FROM brochure_versions
                    WHERE brochure_id = ? AND user_id = ?
                    ORDER BY version_number DESC
                    LIMIT ?
                ''', (brochure_id, user_id, limit))
                
                versions = []
                for row in cursor.fetchall():
                    versions.append({
                        'id': row[0],
                        'version_number': row[1],
                        'action': row[2],
                        'created_at': row[3],
                        'label': self._get_version_label(row[1], row[2], row[3])
                    })
                
                return versions
                
        except Exception as e:
            logging.error(f"Failed to get versions: {e}")
            return []
    
    def get_version(self, brochure_id: str, user_id: int, 
                    version_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific version of a brochure.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
            version_number: Version number to retrieve
        
        Returns:
            Version data or None if not found
        """
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT data, action, created_at
                    FROM brochure_versions
                    WHERE brochure_id = ? AND user_id = ? AND version_number = ?
                ''', (brochure_id, user_id, version_number))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'version_number': version_number,
                        'data': json.loads(row[0]),
                        'action': row[1],
                        'created_at': row[2]
                    }
                
                return None
                
        except Exception as e:
            logging.error(f"Failed to get version: {e}")
            return None
    
    def restore_version(self, brochure_id: str, user_id: int, 
                        version_number: int) -> Optional[Dict[str, Any]]:
        """
        Restore a brochure to a specific version.
        Creates a new version with the restored data.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
            version_number: Version number to restore
        
        Returns:
            Restored version data or None if failed
        """
        try:
            # Get the version to restore
            version = self.get_version(brochure_id, user_id, version_number)
            if not version:
                return None
            
            # Save as new version with restore action
            new_version = self.save_version(
                brochure_id, 
                user_id, 
                version['data'],
                f'restore_from_v{version_number}'
            )
            
            if new_version:
                return {
                    'restored_from': version_number,
                    'new_version': new_version,
                    'data': version['data']
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to restore version: {e}")
            return None
    
    def compare_versions(self, brochure_id: str, user_id: int,
                         version1: int, version2: int) -> Optional[Dict[str, Any]]:
        """
        Compare two versions of a brochure.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
            version1: First version number
            version2: Second version number
        
        Returns:
            Comparison result or None if failed
        """
        try:
            v1 = self.get_version(brochure_id, user_id, version1)
            v2 = self.get_version(brochure_id, user_id, version2)
            
            if not v1 or not v2:
                return None
            
            # Simple comparison
            d1 = v1['data']
            d2 = v2['data']
            
            changes = {
                'version1': version1,
                'version2': version2,
                'pages_added': 0,
                'pages_removed': 0,
                'products_added': 0,
                'products_removed': 0,
                'changes': []
            }
            
            # Compare pages
            pages1 = d1.get('pages', [])
            pages2 = d2.get('pages', [])
            
            if len(pages2) > len(pages1):
                changes['pages_added'] = len(pages2) - len(pages1)
            elif len(pages1) > len(pages2):
                changes['pages_removed'] = len(pages1) - len(pages2)
            
            # Compare products
            products1 = sum(len(p.get('products', [])) for p in pages1)
            products2 = sum(len(p.get('products', [])) for p in pages2)
            
            if products2 > products1:
                changes['products_added'] = products2 - products1
            elif products1 > products2:
                changes['products_removed'] = products1 - products2
            
            return changes
            
        except Exception as e:
            logging.error(f"Failed to compare versions: {e}")
            return None
    
    def delete_versions(self, brochure_id: str, user_id: int) -> bool:
        """
        Delete all versions for a brochure.
        
        Args:
            brochure_id: Brochure ID
            user_id: User ID
        
        Returns:
            True if successful
        """
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM brochure_versions
                    WHERE brochure_id = ? AND user_id = ?
                ''', (brochure_id, user_id))
                conn.commit()
                
                logging.info(f"Deleted all versions for brochure {brochure_id}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to delete versions: {e}")
            return False
    
    def _cleanup_old_versions(self, cursor, brochure_id: str, user_id: int):
        """Delete versions beyond the limit"""
        cursor.execute('''
            DELETE FROM brochure_versions
            WHERE brochure_id = ? AND user_id = ?
            AND id NOT IN (
                SELECT id FROM brochure_versions
                WHERE brochure_id = ? AND user_id = ?
                ORDER BY version_number DESC
                LIMIT ?
            )
        ''', (brochure_id, user_id, brochure_id, user_id, self.MAX_VERSIONS_PER_BROCHURE))
    
    def _get_version_label(self, version_number: int, action: str, 
                           created_at: str) -> str:
        """Generate human-readable version label"""
        try:
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                dt = created_at
            
            time_str = dt.strftime('%H:%M')
            date_str = dt.strftime('%d/%m')
            
            action_labels = {
                'save': 'Kayıt',
                'auto': 'Otomatik',
                'restore': 'Geri Yükleme'
            }
            
            action_label = action_labels.get(action, action)
            if action.startswith('restore_from'):
                action_label = 'Geri Yükleme'
            
            return f"v{version_number} - {action_label} ({date_str} {time_str})"
            
        except Exception:
            return f"Versiyon {version_number}"


# Global instance
version_history = VersionHistory()


# ============= API FUNCTIONS =============

def save_brochure_version(brochure_id: str, user_id: int, data: dict, 
                          action: str = 'save') -> Optional[int]:
    """Save a new version"""
    return version_history.save_version(brochure_id, user_id, data, action)


def get_brochure_versions(brochure_id: str, user_id: int, 
                          limit: int = 10) -> List[Dict]:
    """Get version history"""
    return version_history.get_versions(brochure_id, user_id, limit)


def get_brochure_version(brochure_id: str, user_id: int, 
                         version_number: int) -> Optional[Dict]:
    """Get specific version"""
    return version_history.get_version(brochure_id, user_id, version_number)


def restore_brochure_version(brochure_id: str, user_id: int, 
                             version_number: int) -> Optional[Dict]:
    """Restore to specific version"""
    return version_history.restore_version(brochure_id, user_id, version_number)


def compare_brochure_versions(brochure_id: str, user_id: int,
                              version1: int, version2: int) -> Optional[Dict]:
    """Compare two versions"""
    return version_history.compare_versions(brochure_id, user_id, version1, version2)

