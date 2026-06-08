import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    if not frappe.db.exists("DocType", "Expense Claim Type"):
        return

    custom_fields = {
        "Expense Claim Type": [
            {
                "fieldname": "item",
                "label": "Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "expense_type"
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)