import frappe
from frappe import _

from frappe.utils import flt

def validate_expense_claim(doc, method):
	for row in doc.get("expenses"):
		if flt(row.get("amount")) <= 0:
			frappe.throw(_("Row #{0}: Amount must be greater than 0").format(row.idx))
		
		if flt(row.get("sanctioned_amount")) <= 0:
			frappe.throw(_("Row #{0}: Sanctioned Amount must be greater than 0").format(row.idx))
