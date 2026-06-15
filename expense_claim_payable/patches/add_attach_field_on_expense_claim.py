import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    if not frappe.db.exists("DocType", "Customer"):
        return

    custom_fields = {
        "Expense Claim Detail": [
            {
                "fieldname": "attach",
                "label": "Attach",
                "fieldtype": "Attach",
                "insert_after": "project",
                "reqd": 1
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)