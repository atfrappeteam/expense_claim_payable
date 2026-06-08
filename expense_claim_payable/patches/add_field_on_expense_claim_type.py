import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    if not frappe.db.exists("DocType", "Expense Claim Detail"):
        return

    custom_fields = {
        "Expense Claim Detail": [
            {
                "fieldname": "is_billable",
                "label": "Is Billable",
                "fieldtype": "Check",
                "insert_after": "amount"
            },
            {
                "fieldname": "expense_claim_type",
                "label": "Is Billed",
                "fieldtype": "Check",
                "insert_after": "is_billable"
            },
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