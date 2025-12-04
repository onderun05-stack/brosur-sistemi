# -*- coding: utf-8 -*-
"""
Services package - Business logic services
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
from services.brochure_engine import (
    create_brochure,
    get_brochure,
    save_brochure,
    delete_brochure,
    list_brochures,
    add_page,
    delete_page,
    copy_page,
    auto_arrange_page,
    distribute_products_to_pages,
    LAYOUT_TEMPLATES
)
from services.ghost_assistant import (
    get_ghost_greeting,
    analyze_page_design,
    analyze_brochure_design,
    get_layout_recommendation,
    get_price_insight,
    get_next_action_suggestion,
    get_idle_suggestion,
    create_auto_brochure_plan,
    get_workflow_progress,
    ghost_assistant,
    shadow_planner,
    # New Ghost functions (Madde 1, 6, 9, 10)
    normalize_product_name,
    batch_normalize_names,
    get_name_normalization_stats,
    validate_import_data,
    full_clean_brochure,
    name_normalizer
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
    # External API
    'query_camgoz_api',
    'download_and_process_image',
    'full_barcode_lookup',
    'batch_barcode_lookup',
    'get_market_price_comparison',
    'clear_cache',
    'get_cache_stats',
    # Brochure Engine
    'create_brochure',
    'get_brochure',
    'save_brochure',
    'delete_brochure',
    'list_brochures',
    'add_page',
    'delete_page',
    'copy_page',
    'auto_arrange_page',
    'distribute_products_to_pages',
    'LAYOUT_TEMPLATES',
    # Ghost Assistant
    'get_ghost_greeting',
    'analyze_page_design',
    'analyze_brochure_design',
    'get_layout_recommendation',
    'get_price_insight',
    'get_next_action_suggestion',
    'get_idle_suggestion',
    'create_auto_brochure_plan',
    'get_workflow_progress',
    'ghost_assistant',
    'shadow_planner',
    # New Ghost functions
    'normalize_product_name',
    'batch_normalize_names',
    'get_name_normalization_stats',
    'validate_import_data',
    'full_clean_brochure',
    'name_normalizer'
]

