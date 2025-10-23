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
