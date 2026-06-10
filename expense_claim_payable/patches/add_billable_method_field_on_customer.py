import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    if not frappe.db.exists("DocType", "Customer"):
        return

    custom_fields = {
        "Customer": [
            {
                "fieldname": "is_billable",
                "label": "Is Billable",
                "fieldtype": "Select",
                "options": "\nCustomer\nProject",
                "insert_after": "customer_name",
                "is_mandatory": 1
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)