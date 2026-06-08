import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    if not frappe.db.exists("DocType", "Project"):
        return

    custom_fields = {
        "Project": [
            {
                "fieldname": "is_billable",
                "label": "Is Billable",
                "fieldtype": "Check",
                "insert_after": "is_active"
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)