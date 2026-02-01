import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

# Add this to your Purchase Receipt custom class if you have one
# OR keep it as a standalone function

def create_purchase_invoice_async(doc, method=None):
    """
    Called via enqueue_doc - has proper document context
    """
    if doc.workflow_state != "Putaway in Progress":
        return
    
    if doc.get("custom_pi_created"):
        return
    
    if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": doc.name}):
        return
    
    try:
        pi_dict = make_purchase_invoice(doc.name)
        
        if not pi_dict or not pi_dict.get("items"):
            frappe.log_error("No items returned by mapper", f"Auto PI - {doc.name}")
            return
        
        pi = frappe.get_doc(pi_dict)
        pi.set_posting_time = 1
        pi.posting_date = doc.posting_date
        
        pi.insert(ignore_permissions=True)
        pi.submit()
        
        frappe.db.set_value("Purchase Receipt", doc.name, "custom_pi_created", 1, update_modified=False)
        frappe.db.commit()
        
        frappe.publish_realtime(
            "msgprint",
            f"Purchase Invoice {pi.name} created automatically",
            user=frappe.session.user
        )
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(), 
            title=f"Auto PI Failed - {doc.name}"
        )


@frappe.whitelist()
def auto_create_purchase_invoice(purchase_receipt_name):
    """
    Standalone version - can be called directly from server script
    """
    try:
        pr = frappe.get_doc("Purchase Receipt", purchase_receipt_name)
        
        if pr.docstatus != 1:
            return {"success": False, "message": "Purchase Receipt not submitted"}
        
        if pr.workflow_state != "Putaway in Progress":
            return {"success": False, "message": f"Wrong workflow state: {pr.workflow_state}"}
        
        if pr.get("custom_pi_created"):
            return {"success": False, "message": "PI already created"}
        
        if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": pr.name}):
            return {"success": False, "message": "PI already exists"}
        
        pi_dict = make_purchase_invoice(pr.name)
        
        if not pi_dict or not pi_dict.get("items"):
            return {"success": False, "message": "No items to invoice"}
        
        pi = frappe.get_doc(pi_dict)
        pi.set_posting_time = 1
        pi.posting_date = pr.posting_date
        
        pi.insert(ignore_permissions=True)
        pi.submit()
        
        frappe.db.set_value("Purchase Receipt", pr.name, "custom_pi_created", 1, update_modified=False)
        frappe.db.commit()
        
        return {"success": True, "message": f"Purchase Invoice {pi.name} created", "pi_name": pi.name}
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Auto PI Failed - {purchase_receipt_name}"
        )
        return {"success": False, "message": str(e)}
