import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Expense Claim Type": [
            {
                "fieldname": "item",
                "label": "Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "expense_claim_type"
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)