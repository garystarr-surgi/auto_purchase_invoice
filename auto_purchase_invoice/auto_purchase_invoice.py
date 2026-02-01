import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

@frappe.whitelist()
def auto_create_purchase_invoice(purchase_receipt_name):
    """
    Creates and submits a Purchase Invoice automatically when
    Purchase Receipt reaches 'Putaway in Progress'.
    """
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt_name)

    if pr.docstatus != 1:
        return "Purchase Receipt not submitted yet."

    if pr.workflow_state != "Putaway in Progress":
        return f"Workflow state is '{pr.workflow_state}', not 'Putaway in Progress'."

    if pr.get("custom_pi_created"):
        return "Purchase Invoice already created (custom flag set)."

    if frappe.db.exists("Purchase Invoice Item", {"purchase_receipt": pr.name}):
        return "Purchase Invoice already exists for this Purchase Receipt."

    try:
        pi_doc = make_purchase_invoice(pr.name)

        if not pi_doc or not pi_doc.get("items"):
            frappe.throw("No items returned by Purchase Invoice mapper.")

        pi = frappe.get_doc(pi_doc)
        pi.insert(ignore_permissions=True)
        pi.submit()

        pr.db_set("custom_pi_created", 1)
        frappe.db.commit()

        return f"Purchase Invoice {pi.name} created successfully."

    except Exception as e:
        frappe.log_error(message=str(e), title="Auto Purchase Invoice Failed")
        return f"Failed to create Purchase Invoice: {str(e)}"
