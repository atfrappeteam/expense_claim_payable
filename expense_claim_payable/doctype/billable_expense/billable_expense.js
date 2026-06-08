// Copyright (c) 2026, Assimilate Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Billable Expense", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Invoice'), () => {
				frappe.call({
					method: "expense_claim_payable.doctype.billable_expense.billable_expense.create_sales_invoice",
					args: {
						source_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							if (Array.isArray(r.message) && r.message.length > 0) {
								if (r.message.length === 1) {
									frappe.set_route("Form", "Sales Invoice", r.message[0]);
								} else {
									frappe.msgprint(__('Created Invoices: ') + r.message.join(', '));
								}
							} else if (typeof r.message === 'string') {
								frappe.set_route("Form", "Sales Invoice", r.message);
							}
						}
					}
				});
			}, __('Create'));
		}
	},
});
