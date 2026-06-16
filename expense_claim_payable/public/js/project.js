frappe.ui.form.on('Project', {
	refresh: function(frm) {
		// Make is_billable read-only when project_type is 'Internal'
		frm.set_df_property('is_billable', 'read_only', frm.doc.project_type === 'Internal');
	},
	project_type: function(frm) {
		// Set is_billable to 0 and make it read-only when project_type is 'Internal'
		if (frm.doc.project_type === 'Internal') {
			frm.set_value('is_billable', 0);
		}
		frm.set_df_property('is_billable', 'read_only', frm.doc.project_type === 'Internal');
	}
});
