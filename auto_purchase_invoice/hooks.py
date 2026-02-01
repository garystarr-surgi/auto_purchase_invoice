app_name = "auto_purchase_invoice"
app_title = "Auto Purchase Invoice"
app_publisher = "Gary Starr"
app_description = "Auto creates Purchase Invoice when Purchase Receipt reaches Putaway in Progress"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# ... existing content ...

doc_events = {
    "Purchase Receipt": {
        "on_submit": "auto_purchase_invoice.auto_purchase_invoice.on_purchase_receipt_submit"
    }
}
