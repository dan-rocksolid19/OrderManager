"""
BaseDAO Connection Management - Quick Reference Guide

This file provides concise examples for quick reference when using BaseDAO connection management.
"""

# ============================================================================
# PATTERN 1: Simple Operations (Auto-managed connections)
# ============================================================================

def simple_pattern():
    """Use for single operations - DAO handles connections automatically"""
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    logger = pybrex_logger(__name__)
    business_dao = BusinessInfoDAO(logger)
    
    # Single operation - connection auto-managed
    business_info = business_dao.get_business_info()
    
    # Another single operation - new connection auto-managed
    success = business_dao.update_business_info("New Name", "123 St", "City", "ST", "12345", "555-1234")
    
    return business_info, success


# ============================================================================
# PATTERN 2: Multiple Operations (Shared connection)
# ============================================================================

def efficient_pattern():
    """Use for multiple operations - share single connection for efficiency"""
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    logger = pybrex_logger(__name__)
    business_dao = BusinessInfoDAO(logger)
    
    # Multiple operations sharing one connection
    with business_dao.database.connection_context():
        business_info = business_dao.get_business_info()
        business_dao.ensure_business_info_exists()
        success = business_dao.update_business_info("Updated Name", "456 Ave", "Town", "ST", "67890", "555-5678")
        updated_info = business_dao.get_business_info()
    
    return business_info, success, updated_info


# ============================================================================
# PATTERN 3: Service Layer Method
# ============================================================================

def service_layer_pattern():
    """Service method with multiple database operations"""
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    def update_business_profile(profile_data):
        logger = pybrex_logger(__name__)
        business_dao = BusinessInfoDAO(logger)
        
        with business_dao.database.connection_context():
            # Ensure exists
            if not business_dao.ensure_business_info_exists():
                return False, "Failed to ensure record exists"
            
            # Update
            success = business_dao.update_business_info(
                profile_data['name'],
                profile_data['address'],
                profile_data['city'],
                profile_data['state'],
                profile_data['zip'],
                profile_data['phone']
            )
            
            # Verify
            if success:
                updated = business_dao.get_business_info()
                return True, f"Updated to: {updated.business_name}"
            else:
                return False, "Update failed"
    
    # Usage
    profile = {
        'name': 'Service Co.',
        'address': '789 Service St',
        'city': 'Service City',
        'state': 'SC',
        'zip': '11111',
        'phone': '555-SERVICE'
    }
    
    return update_business_profile(profile)


# ============================================================================
# PATTERN 4: Error Handling
# ============================================================================

def error_handling_pattern():
    """Safe operations with proper error handling"""
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    logger = pybrex_logger(__name__)
    business_dao = BusinessInfoDAO(logger)
    
    try:
        with business_dao.database.connection_context():
            # Safe read
            try:
                info = business_dao.get_business_info()
            except Exception as e:
                return False, f"Read failed: {e}"
            
            # Safe update
            try:
                success = business_dao.update_business_info("Safe Co.", "123 Safe St", "Safe City", "SF", "00000", "555-SAFE")
                if not success:
                    return False, "Update failed"
            except Exception as e:
                return False, f"Update error: {e}"
            
            return True, "All operations successful"
            
    except Exception as e:
        return False, f"Connection error: {e}"


# ============================================================================
# PATTERN 5: UI Component
# ============================================================================

class UIComponentPattern:
    """Example UI component using optimal DAO patterns"""
    
    def __init__(self):
        from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
        from librepy.pybrex.values import pybrex_logger
        
        logger = pybrex_logger(__name__)
        self.business_dao = BusinessInfoDAO(logger)
    
    def load_data(self):
        """Simple load - auto-managed connection"""
        return self.business_dao.get_business_info()
    
    def save_form(self, form_data):
        """Complex save - shared connection"""
        with self.business_dao.database.connection_context():
            # Ensure exists
            if not self.business_dao.ensure_business_info_exists():
                return False, "Failed to ensure record"
            
            # Save
            success = self.business_dao.update_business_info(
                form_data['name'],
                form_data['address'],
                form_data['city'],
                form_data['state'],
                form_data['zip'],
                form_data['phone']
            )
            
            return success, "Saved successfully" if success else "Save failed"


# ============================================================================
# PATTERN 6: Using prefetch() for Related Objects 
# ============================================================================

def prefetch_pattern():
    """
    When returning model instances that might have their relations accessed 
    after the database connection is closed, use prefetch() to pre-load them.
    """
    from librepy.fertilizer_cmd_ctr.data.product_list_dao import ProductListDAO
    from librepy.fertilizer_cmd_ctr.data.category_dao import CategoryDAO
    from librepy.peewee.peewee import prefetch
    from librepy.pybrex.values import pybrex_logger
    
    # Single model with one relation
    def products_prefetch_example():
        dao = ProductListDAO(pybrex_logger(__name__))
        # Simple select that doesn't include related objects
        query = Product.select().order_by(Product.name)
        # Prefetch the related Category and Subcategory objects
        products = list(prefetch(query, Category, Subcategory))
        return products
        # Now UI can safely do product.category.name without a new query
    
    # Single model instance with relation
    def subcategory_prefetch_example():
        dao = SubcategoryDAO(pybrex_logger(__name__))
        try:
            subcategory = Subcategory.get_by_id(42)
            # Eagerly load the parent Category
            return prefetch([subcategory], Category)[0]
        except DoesNotExist:
            return None
        # Now UI can safely do subcategory.parent.name without a new query


# ============================================================================
# DECISION TREE: Which Pattern to Use?
# ============================================================================

"""
🤔 Which pattern should I use?

┌─ Single operation? 
│  └─ ✅ Use simple_pattern() - let DAO auto-manage
│
├─ 2-3 related operations?
│  └─ ✅ Use efficient_pattern() - connection context
│
├─ Service layer method?
│  └─ ✅ Use service_layer_pattern() - connection context
│
├─ Batch processing?
│  └─ ✅ Use efficient_pattern() - connection context
│
├─ Error-prone operations?
│  └─ ✅ Use error_handling_pattern() - try-catch in context
│
├─ UI components accessing model relations?
│  └─ ✅ Use prefetch_pattern() - eager loading with prefetch()
│
├─ UI component?
│  ├─ Loading data? → simple_pattern()
│  └─ Saving form? → efficient_pattern()
│
└─ Not sure?
   └─ ✅ Start with simple_pattern(), optimize later if needed

📊 Performance Guidelines:
- 1 operation: Simple pattern (acceptable overhead)
- 2+ operations: Connection context (optimal)
- Batch/bulk: Always use connection context
- UI showing related models: Always use prefetch() pattern
"""


# ============================================================================
# QUICK EXAMPLES
# ============================================================================

# ✅ GOOD: Simple single operation
def good_single():
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    dao = BusinessInfoDAO(pybrex_logger(__name__))
    return dao.get_business_info()

# ✅ GOOD: Multiple operations with context
def good_multiple():
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    dao = BusinessInfoDAO(pybrex_logger(__name__))
    with dao.database.connection_context():
        info = dao.get_business_info()
        dao.update_business_info("Test", "123 St", "City", "ST", "12345", "555-1234")
        return dao.get_business_info()

# ❌ INEFFICIENT: Multiple operations without context
def inefficient_multiple():
    from librepy.fertilizer_cmd_ctr.data.business_info_dao import BusinessInfoDAO
    from librepy.pybrex.values import pybrex_logger
    
    dao = BusinessInfoDAO(pybrex_logger(__name__))
    # Each call opens/closes its own connection - inefficient!
    info = dao.get_business_info()  # Connection 1
    dao.update_business_info("Test", "123 St", "City", "ST", "12345", "555-1234")  # Connection 2
    return dao.get_business_info()  # Connection 3 