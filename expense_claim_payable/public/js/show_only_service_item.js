frappe.ui.form.on('Expense Claim Type', {
    refresh(frm) {
        frm.set_query('item', function() {
            return {
                filters: {
                    is_stock_item: 0
                }
            };
        });
    }
});