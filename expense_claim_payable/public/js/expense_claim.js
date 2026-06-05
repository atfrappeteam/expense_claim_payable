console.log("Expense Claim JS Loaded");

frappe.ui.form.on("Expense Claim Detail", {
	project: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		console.log("Project changed", row.project);
		if (row.project) {
			frappe.db.get_value("Project", row.project, "is_billable", (r) => {
				if (r && r.is_billable) {
					frappe.model.set_value(cdt, cdn, "is_billable", 1);
				} else {
					frappe.model.set_value(cdt, cdn, "is_billable", 0);
				}
			});
		}
	},
	expense_type: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		console.log("Expense Type changed (expense_type):", row.expense_type);
		if (row.expense_type) {
			frappe.db.get_value("Expense Claim Type", row.expense_type, "item", (r) => {
				console.log("Fetched item:", r);
				if (r && r.item) {
					frappe.model.set_value(cdt, cdn, "item", r.item);
				}
			});
		}
	},
	// Adding this just in case the link field is named expense_claim_type
	expense_claim_type: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		console.log("Expense Type changed (expense_claim_type):", row.expense_claim_type);
		if (row.expense_claim_type && typeof row.expense_claim_type === 'string') {
			frappe.db.get_value("Expense Claim Type", row.expense_claim_type, "item", (r) => {
				console.log("Fetched item:", r);
				if (r && r.item) {
					frappe.model.set_value(cdt, cdn, "item", r.item);
				}
			});
		}
	}
});
