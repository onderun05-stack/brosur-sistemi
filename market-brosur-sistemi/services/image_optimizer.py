# -*- coding: utf-8 -*-
"""
Image Optimization Service

Handles image compression, resizing, and optimization for:
- Upload optimization
- Thumbnail generation
- WebP conversion
- Quality-based compression
"""

import os
import logging
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image

# Standard image sizes
THUMBNAIL_SIZE = (150, 150)
MEDIUM_SIZE = (500, 500)
LARGE_SIZE = (1024, 1024)
BROCHURE_SIZE = (1200, 1200)

# Quality settings
QUALITY_HIGH = 95
QUALITY_MEDIUM = 85
QUALITY_LOW = 70

# Maximum file size (bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class ImageOptimizer:
    """
    Image optimization utility class.
    """
    
    def __init__(self, upload_folder: str = 'static/uploads'):
        self.upload_folder = upload_folder
        
    def optimize(self, image_path: str, output_path: str = None,
                 max_size: Tuple[int, int] = LARGE_SIZE,
                 quality: int = QUALITY_MEDIUM,
                 format: str = 'PNG') -> Optional[str]:
        """
        Optimize an image file.
        
        Args:
            image_path: Path to source image
            output_path: Path for output (None = overwrite)
            max_size: Maximum dimensions (width, height)
            quality: JPEG/WebP quality (1-100)
            format: Output format (PNG, JPEG, WEBP)
        
        Returns:
            Path to optimized image or None if failed
        """
        try:
            if not os.path.exists(image_path):
                logging.error(f"Image not found: {image_path}")
                return None
            
            # Open image
            img = Image.open(image_path)
            
            # Convert to RGB if needed (for JPEG)
            if format.upper() == 'JPEG' and img.mode in ('RGBA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if larger than max_size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.LANCZOS)
            
            # Determine output path
            if output_path is None:
                output_path = image_path
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save with optimization
            save_kwargs = {'optimize': True}
            
            if format.upper() == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['progressive'] = True
            elif format.upper() == 'PNG':
                save_kwargs['optimize'] = True
            elif format.upper() == 'WEBP':
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6  # Best compression
            
            img.save(output_path, format=format.upper(), **save_kwargs)
            
            # Log size reduction
            original_size = os.path.getsize(image_path)
            new_size = os.path.getsize(output_path)
            reduction = ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0
            
            logging.info(f"Image optimized: {image_path} -> {output_path}")
            logging.info(f"  Size: {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB ({reduction:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logging.error(f"Image optimization failed: {e}")
            return None
    
    def create_thumbnail(self, image_path: str, output_path: str = None,
                         size: Tuple[int, int] = THUMBNAIL_SIZE) -> Optional[str]:
        """
        Create a thumbnail version of an image.
        
        Args:
            image_path: Path to source image
            output_path: Path for thumbnail (None = auto-generate)
            size: Thumbnail size
        
        Returns:
            Path to thumbnail or None if failed
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_thumb{ext}"
            
            img = Image.open(image_path)
            
            # Create square thumbnail (crop to center)
            width, height = img.size
            min_dim = min(width, height)
            
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            
            img = img.crop((left, top, right, bottom))
            img.thumbnail(size, Image.LANCZOS)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            img.save(output_path, optimize=True)
            
            logging.info(f"Thumbnail created: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Thumbnail creation failed: {e}")
            return None
    
    def convert_to_webp(self, image_path: str, output_path: str = None,
                        quality: int = QUALITY_MEDIUM) -> Optional[str]:
        """
        Convert an image to WebP format.
        
        Args:
            image_path: Path to source image
            output_path: Path for WebP (None = same name with .webp)
            quality: WebP quality (1-100)
        
        Returns:
            Path to WebP image or None if failed
        """
        try:
            if output_path is None:
                base = os.path.splitext(image_path)[0]
                output_path = f"{base}.webp"
            
            img = Image.open(image_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            img.save(output_path, 'WEBP', quality=quality, method=6)
            
            logging.info(f"Converted to WebP: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"WebP conversion failed: {e}")
            return None
    
    def compress_for_size(self, image_path: str, target_size: int = 500000,
                          min_quality: int = 30) -> Optional[str]:
        """
        Compress image to meet target file size.
        
        Args:
            image_path: Path to source image
            target_size: Target file size in bytes
            min_quality: Minimum quality to use
        
        Returns:
            Path to compressed image or None if failed
        """
        try:
            img = Image.open(image_path)
            
            # Convert RGBA to RGB for JPEG
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            quality = 95
            output = BytesIO()
            
            # Binary search for optimal quality
            while quality >= min_quality:
                output = BytesIO()
                img.save(output, 'JPEG', quality=quality, optimize=True)
                
                if output.tell() <= target_size:
                    break
                
                quality -= 5
            
            # Save to file
            output_path = os.path.splitext(image_path)[0] + '_compressed.jpg'
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())
            
            logging.info(f"Compressed to {output.tell()/1024:.1f}KB at quality {quality}")
            return output_path
            
        except Exception as e:
            logging.error(f"Compression failed: {e}")
            return None
    
    def remove_background_simple(self, image_path: str, 
                                  output_path: str = None) -> Optional[str]:
        """
        Simple background removal (white to transparent).
        For better results, use AI-based removal.
        
        Args:
            image_path: Path to source image
            output_path: Path for output (None = auto)
        
        Returns:
            Path to image with transparent background
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_nobg.png"
            
            img = Image.open(image_path)
            img = img.convert('RGBA')
            
            data = img.getdata()
            new_data = []
            
            # Define white threshold
            threshold = 240
            
            for item in data:
                # If pixel is white-ish, make it transparent
                if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            
            img.putdata(new_data)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            img.save(output_path, 'PNG')
            
            logging.info(f"Background removed: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Background removal failed: {e}")
            return None
    
    def get_image_info(self, image_path: str) -> Optional[dict]:
        """
        Get information about an image.
        
        Returns:
            dict with width, height, format, size, mode
        """
        try:
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path)
            
            return {
                'width': img.size[0],
                'height': img.size[1],
                'format': img.format,
                'mode': img.mode,
                'size_bytes': file_size,
                'size_kb': round(file_size / 1024, 2),
                'aspect_ratio': round(img.size[0] / img.size[1], 2) if img.size[1] > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"Failed to get image info: {e}")
            return None
    
    def batch_optimize(self, folder_path: str, output_folder: str = None,
                       max_size: Tuple[int, int] = LARGE_SIZE,
                       quality: int = QUALITY_MEDIUM) -> dict:
        """
        Batch optimize all images in a folder.
        
        Args:
            folder_path: Source folder
            output_folder: Output folder (None = in-place)
            max_size: Maximum dimensions
            quality: Output quality
        
        Returns:
            dict with success count, error count, total saved bytes
        """
        results = {
            'processed': 0,
            'errors': 0,
            'saved_bytes': 0
        }
        
        if output_folder is None:
            output_folder = folder_path
        
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            
            for filename in os.listdir(folder_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue
                
                input_path = os.path.join(folder_path, filename)
                output_path = os.path.join(output_folder, filename)
                
                original_size = os.path.getsize(input_path)
                
                result = self.optimize(input_path, output_path, max_size, quality)
                
                if result:
                    new_size = os.path.getsize(output_path)
                    results['processed'] += 1
                    results['saved_bytes'] += (original_size - new_size)
                else:
                    results['errors'] += 1
            
            logging.info(f"Batch optimization complete: {results}")
            
        except Exception as e:
            logging.error(f"Batch optimization failed: {e}")
        
        return results


# Global instance
image_optimizer = ImageOptimizer()


# ============= API FUNCTIONS =============

def optimize_image(image_path: str, **kwargs) -> Optional[str]:
    """Optimize an image"""
    return image_optimizer.optimize(image_path, **kwargs)


def create_thumbnail(image_path: str, **kwargs) -> Optional[str]:
    """Create thumbnail"""
    return image_optimizer.create_thumbnail(image_path, **kwargs)


def convert_to_webp(image_path: str, **kwargs) -> Optional[str]:
    """Convert to WebP"""
    return image_optimizer.convert_to_webp(image_path, **kwargs)


def get_image_info(image_path: str) -> Optional[dict]:
    """Get image info"""
    return image_optimizer.get_image_info(image_path)


def batch_optimize(folder_path: str, **kwargs) -> dict:
    """Batch optimize folder"""
    return image_optimizer.batch_optimize(folder_path, **kwargs)

