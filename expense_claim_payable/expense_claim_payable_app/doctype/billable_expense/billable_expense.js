// Copyright (c) 2026, Assimilate Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Billable Expense", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Invoice'), () => {
				frappe.new_doc('Sales Invoice', {
					// You can add field mapping here if needed
				});
			}, __('Create'));
		}
	},
});
