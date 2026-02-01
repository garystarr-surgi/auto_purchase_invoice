import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

def on_purchase_receipt_submit(doc, method=None):
    """
    Hook function called on Purchase Receipt submit
    Creates PI automatically when workflow state is "Putaway in Progress"
    """
    if doc.workflow_state != "Putaway in Progress":
        return
    
    # Check if PI already exists for this PR
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

