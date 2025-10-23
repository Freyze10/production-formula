# global_var.py
# Global Variables for Data Caching

# ========== FORMULATION CACHED DATA ==========
all_formula_data = []  # Main cache for formulation records
rm_list = []  # Cache for RM codes
customer_lists = []  # Cache for customer names (formulation)
product_code_lists = []  # Cache for product codes (formulation)
formula_uid_lists = []  # Cache for formula UIDs
formulation_data_loaded = False  # Flag to track if initial load is done
# =============================================

# ========== PRODUCTION CACHED DATA ===========
all_production_data = []  # Main cache for production records
production_customer_lists = []  # Cache for customer names (production)
production_product_code_lists = []  # Cache for product codes (production)
production_lot_no_lists = []  # Cache for lot numbers
production_data_loaded = False  # Flag to track if production data is loaded
# =============================================

# ========== HELPER FUNCTIONS =================

def clear_formulation_caches():
    """Clear all cached formulation data."""
    global all_formula_data, customer_lists, product_code_lists, formula_uid_lists
    all_formula_data = []
    customer_lists = []
    product_code_lists = []
    formula_uid_lists = []

def clear_production_caches():
    """Clear all cached production data."""
    global all_production_data, production_customer_lists, production_product_code_lists, production_lot_no_lists
    all_production_data = []
    production_customer_lists = []
    production_product_code_lists = []
    production_lot_no_lists = []

def clear_all_caches():
    """Clear all cached data (formulation + production)."""
    clear_formulation_caches()
    clear_production_caches()

def is_formulation_cache_empty():
    """Check if the formulation cache is empty."""
    return len(all_formula_data) == 0

def is_production_cache_empty():
    """Check if the production cache is empty."""
    return len(all_production_data) == 0

def get_formulation_cache_size():
    """Return the number of cached formulation records."""
    return len(all_formula_data)

def get_production_cache_size():
    """Return the number of cached production records."""
    return len(all_production_data)

def get_cache_stats():
    """Return statistics about all caches."""
    return {
        'formulation_records': len(all_formula_data),
        'production_records': len(all_production_data),
        'rm_codes': len(rm_list),
        'formulation_customers': len(customer_lists),
        'production_customers': len(production_customer_lists),
        'formulation_product_codes': len(product_code_lists),
        'production_product_codes': len(production_product_code_lists),
        'lot_numbers': len(production_lot_no_lists),
        'formulation_loaded': formulation_data_loaded,
        'production_loaded': production_data_loaded
    }
# =============================================