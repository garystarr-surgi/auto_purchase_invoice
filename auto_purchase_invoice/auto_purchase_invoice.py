import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

@frappe.whitelist()
def auto_create_purchase_invoice(purchase_receipt_name):
    """
    Creates and submits a Purchase Invoice automatically when
    Purchase Receipt reaches 'Putaway in Progress'.
    """
    try:
        pr = frappe.get_doc("Purchase Receipt", purchase_receipt_name)
        
        # Validation checks
        if pr.docstatus != 1:
            frappe.log_error(f"PR {pr.name} not submitted", "Auto PI Skipped")
            return {"success": False, "message": "Purchase Receipt not submitted yet."}
        
        if pr.workflow_state != "Putaway in Progress":
            return {"success": False, "message": f"Workflow state is '{pr.workflow_state}', not 'Putaway in Progress'."}
        
        # Check if already created
        if pr.get("custom_pi_created"):
            return {"success": False, "message": "Purchase Invoice already created (custom flag set)."}
        
        if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": pr.name}):
            return {"success": False, "message": "Purchase Invoice already exists for this Purchase Receipt."}
        
        # THIS WAS MISSING - Actually call the mapper function
        pi_dict = make_purchase_invoice(pr.name)
        
        if not pi_dict or not pi_dict.get("items"):
            frappe.throw("No items returned by Purchase Invoice mapper.")
        
        # Create PI from mapped data
        pi = frappe.get_doc(pi_dict)
        pi.set_posting_time = 1  # Use PR posting date
        pi.posting_date = pr.posting_date
        
        pi.insert(ignore_permissions=True)
        pi.submit()
        
        # Mark PR as processed
        frappe.db.set_value("Purchase Receipt", pr.name, "custom_pi_created", 1, update_modified=False)
        frappe.db.commit()
        
        return {"success": True, "message": f"Purchase Invoice {pi.name} created successfully.", "pi_name": pi.name}
        
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title=f"Auto Purchase Invoice Failed - {purchase_receipt_name}")
        return {"success": False, "message": f"Failed: {str(e)}"}
