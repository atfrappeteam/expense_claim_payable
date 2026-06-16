console.log("Expense Claim JS Loaded");

frappe.ui.form.on("Expense Claim", {
	onload: function(frm) {
		console.log("Applying Project Filter (onload)");
		apply_project_filter(frm);
	},
	refresh: function(frm) {
		console.log("Applying Project Filter (refresh)");
		apply_project_filter(frm);
	},
	validate: function(frm) {
		let invalid_amount_rows = [];
		let invalid_sanctioned_rows = [];

		frm.doc.expenses.forEach(row => {
			if (flt(row.amount) <= 0) {
				invalid_amount_rows.push(row.idx);
			}
			if (flt(row.sanctioned_amount) <= 0) {
				invalid_sanctioned_rows.push(row.idx);
			}
		});

		if (invalid_amount_rows.length > 0 || invalid_sanctioned_rows.length > 0) {
			let message = "";
			if (invalid_amount_rows.length > 0) {
				message += __("Row #{0}: Amount must be greater than 0.", [invalid_amount_rows.join(', ')]) + "<br>";
			}
			if (invalid_sanctioned_rows.length > 0) {
				message += __("Row #{0}: Sanctioned Amount must be greater than 0.", [invalid_sanctioned_rows.join(', ')]);
			}

			frappe.msgprint({
				title: __('Validation Error'),
				indicator: 'red',
				message: message
			});
			frappe.validated = false;
		}
	}
});

function apply_project_filter(frm) {
	console.log("Setting query for project in expenses table");
	frm.set_query("project", "expenses", function() {
		console.log("Returning filters for Project status != Cancelled");
		return {
			filters: {
				"status": ["!=", "Cancelled"]
			}
		};
	});
}

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
