# Copyright (c) 2026, Assimilate Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today

class BillableExpense(Document):
	pass

@frappe.whitelist()
def create_sales_invoice(source_name):
	doc = frappe.get_doc("Billable Expense", source_name)
	
	if not doc.billable_expense:
		frappe.throw(_("No expenses to invoice"))
		
	# Group by customer (and project if method is Project)
	grouped_expenses = {}
	for row in doc.billable_expense:
		if not row.customer:
			frappe.throw(_("Customer is missing in row {0}").format(row.idx))
		
		# Get billable method directly for the customer
		billable_method = frappe.db.get_value("Customer", row.customer, "billable_method")
		
		# Default to Project-based if not set or if set to Project
		if billable_method and billable_method.strip().lower() == "customer":
			key = (row.customer, None)  # Consolidated for customer
		else:
			key = (row.customer, row.project)  # Separate per project
			
		if key not in grouped_expenses:
			grouped_expenses[key] = []
		grouped_expenses[key].append(row)
		
	created_invoices = []
	
	for (customer, project), rows in grouped_expenses.items():
		# Try to get company from first row's expense claim
		company = None
		if rows[0].expense_claim:
			company = frappe.db.get_value("Expense Claim", rows[0].expense_claim, "company")
		
		if not company:
			# Fallback to default company
			company = frappe.db.get_default("company") or frappe.get_all("Company", limit=1, fields=["name"])[0].name
			
		si = frappe.new_doc("Sales Invoice")
		si.customer = customer
		si.company = company
		si.project = project
		si.posting_date = today()
		# Set other mandatory fields if needed
		si.set_missing_values()
		
		for row in rows:
			# Get item from expense claim type
			item_code = frappe.db.get_value("Expense Claim Type", row.expense_claim_type, "item")
			if not item_code:
				frappe.throw(_("Item not linked to Expense Claim Type {0}").format(row.expense_claim_type))
				
			si.append("items", {
				"item_code": item_code,
				"qty": 1,
				"rate": row.amount,
				"allow_zero_valuation_rate": 1,
				"ignore_pricing_rule": 1,
				"description": _("Expense Claim: {0}").format(row.expense_claim) if row.expense_claim else "",
				"project": row.project or ""
			})
			
		si.set_missing_values()
		si.insert()
		si.save()
		created_invoices.append(si.name)
		
	return created_invoices
