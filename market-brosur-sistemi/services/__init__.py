# -*- coding: utf-8 -*-
"""
Services package - Core business logic services
"""

from services.excel_io import parse_excel_file, export_to_excel
from services.image_bank import (
    search_image_hierarchy,
    save_to_customer_depot,
    save_to_admin_depot,
    approve_pending_image,
    reject_pending_image,
    standardize_image,
    get_pending_images_list,
    get_admin_images_by_sector,
    get_customer_images,
    delete_image_from_depot
)
from services.external_api import (
    query_camgoz_api,
    download_and_process_image,
    full_barcode_lookup,
    batch_barcode_lookup,
    get_market_price_comparison,
    clear_cache,
    get_cache_stats
)

__all__ = [
    # Excel
    'parse_excel_file', 
    'export_to_excel',
    # Image Bank
    'search_image_hierarchy',
    'save_to_customer_depot',
    'save_to_admin_depot',
    'approve_pending_image',
    'reject_pending_image',
    'standardize_image',
    'get_pending_images_list',
    'get_admin_images_by_sector',
    'get_customer_images',
    'delete_image_from_depot',
    # External API (sadece CAMGOZ)
    'query_camgoz_api',
    'download_and_process_image',
    'full_barcode_lookup',
    'batch_barcode_lookup',
    'get_market_price_comparison',
    'clear_cache',
    'get_cache_stats',
]
