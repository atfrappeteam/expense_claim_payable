import frappe

def validate_project(doc, method):
	if doc.project_type == "Internal":
		doc.is_billable = 0
