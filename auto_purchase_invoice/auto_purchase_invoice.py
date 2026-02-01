import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

def on_purchase_receipt_submit(doc, method=None):
    """
    Hook function called on Purchase Receipt submit
    This runs automatically when PR is submitted via workflow
    """
    # Only create PI if workflow state is "Putaway in Progress"
    if doc.workflow_state != "Putaway in Progress":
        return
    
    if doc.get("custom_pi_created"):
        return
    
    if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": doc.name}):
        return
    
    try:
        pi_dict = make_purchase_invoice(doc.name)
        
        if not pi_dict or not pi_dict.get("items"):
            frappe.log_error("No items to invoice", f"Auto PI - {doc.name}")
            return
        
        pi = frappe.get_doc(pi_dict)
        pi.set_posting_time = 1
        pi.posting_date = doc.posting_date
        
        pi.insert(ignore_permissions=True)
        pi.submit()
        
        frappe.db.set_value(
            "Purchase Receipt", 
            doc.name, 
            "custom_pi_created", 
            1, 
            update_modified=False
        )
        frappe.db.commit()
        
        frappe.msgprint(
            f"Purchase Invoice {pi.name} created and submitted automatically",
            indicator="green",
            alert=True
        )
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Auto Purchase Invoice Failed - {doc.name}"
        )
        frappe.msgprint(
            f"Failed to create Purchase Invoice: {str(e)}",
            indicator="red",
            alert=True
        )


@frappe.whitelist()
def auto_create_purchase_invoice(purchase_receipt_name):
    """
    Standalone function - can be called manually if needed
    """
    try:
        pr = frappe.get_doc("Purchase Receipt", purchase_receipt_name)
        
        if pr.docstatus != 1:
            return {"success": False, "message": "Purchase Receipt not submitted"}
        
        if pr.workflow_state != "Putaway in Progress":
            return {"success": False, "message": f"Wrong workflow state: {pr.workflow_state}"}
        
        if pr.get("custom_pi_created"):
            return {"success": False, "message": "Purchase Invoice already created"}
        
        if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": pr.name}):
            return {"success": False, "message": "Purchase Invoice already exists"}
        
        pi_dict = make_purchase_invoice(pr.name)
        
        if not pi_dict or not pi_dict.get("items"):
            return {"success": False, "message": "No items to invoice"}
        
        pi = frappe.get_doc(pi_dict)
        pi.set_posting_time = 1
        pi.posting_date = pr.posting_date
        
        pi.insert(ignore_permissions=True)
        pi.submit()
        
        frappe.db.set_value(
            "Purchase Receipt", 
            pr.name, 
            "custom_pi_created", 
            1, 
            update_modified=False
        )
        frappe.db.commit()
        
        return {
            "success": True, 
            "message": f"Purchase Invoice {pi.name} created and submitted", 
            "pi_name": pi.name
        }
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Auto Purchase Invoice Failed - {purchase_receipt_name}"
        )
        return {"success": False, "message": f"Error: {str(e)}"}
