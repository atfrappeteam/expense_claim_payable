frappe.pages['expense-billable'].on_page_load = function(wrapper) {
	$(wrapper).addClass('eb-page-container');
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Expense Bill',
		single_column: true
	});

	// Add top-right button to create a Draft Sales Invoice from selected rows
	page.set_primary_action(__('Sales Invoice'), () => {
		// Gather selected expense rows
		let selected_rows = [];
		$('.row-checkbox:checked').each(function() {
			selected_rows.push($(this).closest('tr').attr('data-id'));
		});

		if (selected_rows.length === 0) {
			frappe.msgprint(__('Please select at least one expense to create a Sales Invoice.'));
			return;
		}

		// Optional: include current filters for customer/project
		let filters = {
			selected_rows: JSON.stringify(selected_rows),
			customer: page.fields_dict.customer.get_value(),
			project: page.fields_dict.project.get_value()
		};

		frappe.call({
			method: "expense_claim_payable.expense_claim_payable.page.expense_billable.expense_billable.create_sales_invoice",
			args: filters,
			freeze: true,
			freeze_message: __('Creating Sales Invoice...'),
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					// Invoices created in Draft – keep rows until invoice is submitted
					let msg = "";
					if (r.message.length === 1) {
						msg = __('Sales Invoice {0} created in Draft', [r.message[0]]);
					} else {
						msg = __('{0} Sales Invoices created: {1}', [r.message.length, r.message.join(', ')]);
					}

					frappe.show_alert({
						message: msg,
						indicator: 'green'
					});
					
					// Update selection banner (no rows selected now)
					$('#eb-select-all').prop('checked', false);
					update_banner();
					// Refresh data to remove billed items from the list
					fetch_data();
				}
			}
		});
	});

	// Dynamically load page stylesheet
	$('<link>')
		.appendTo('head')
		.attr({
			type: 'text/css',
			rel: 'stylesheet',
			href: '/assets/expense_claim_payable/expense_claim_payable/page/expense_billable/expense_billable.css'
		});

	// Add filter fields
	page.add_field({
		fieldname: 'from_date',
		label: __('From Date'),
		fieldtype: 'Date',
		change: function() {
			fetch_data();
		}
	});

	page.add_field({
		fieldname: 'to_date',
		label: __('To Date'),
		fieldtype: 'Date',
		change: function() {
			fetch_data();
		}
	});

	page.add_field({
		fieldname: 'customer',
		label: __('Customer'),
		fieldtype: 'Link',
		options: 'Customer',
		change: function() {
			fetch_data();
		}
	});

	page.add_field({
		fieldname: 'project',
		label: __('Project'),
		fieldtype: 'Link',
		options: 'Project',
		change: function() {
			fetch_data();
		}
	});

	page.add_field({
		fieldname: 'expense_claim_type',
		label: __('Expense Claim Type'),
		fieldtype: 'Link',
		options: 'Expense Claim Type',
		change: function() {
			fetch_data();
		}
	});

	// Append modern table structure to page main
	let container = $(`
		<div class="expense-billable-container">
			<div class="eb-table-wrapper" style="display: none;">
				<table class="eb-table">
					<thead>
						<tr>
							<th class="eb-checkbox-cell">
								<label class="eb-checkbox-wrapper">
									<input type="checkbox" class="eb-checkbox" id="eb-select-all">
								</label>
							</th>
							<th class="eb-date-cell">${__('Date')}</th>
							<th class="eb-project-cell">${__('Project Code')}</th>
							<th class="eb-customer-cell">${__('Customer Name')}</th>
							<th class="eb-type-cell">${__('Expense Claim Type')}</th>
							<th class="eb-description-cell">${__('Description')}</th>
							<th class="eb-amount-cell text-right">${__('Amount')}</th>
						</tr>
					</thead>
					<tbody id="eb-table-body">
						<!-- Dynamic rows -->
					</tbody>
				</table>
			</div>
			<div class="eb-empty-state" id="eb-empty-state">
				<div class="eb-empty-icon">📂</div>
				<div class="eb-empty-title">${__('No Billable Expenses Found')}</div>
				<div class="eb-empty-subtitle">${__('Change your filters or verify that new claims are submitted and approved.')}</div>
			</div>
		</div>

		<div class="eb-action-banner" id="eb-action-banner">
			<div class="eb-selection-details">
				<span class="eb-badge" id="eb-selected-count">0 Selected</span>
				<span>Total Amount: <span class="eb-total-amount" id="eb-selected-amount">0.00</span></span>
			</div>
		</div>
	`).appendTo(page.main);

	// Fetch data from backend
	function fetch_data() {
		let filters = {
			from_date: page.fields_dict.from_date.get_value(),
			to_date: page.fields_dict.to_date.get_value(),
			customer: page.fields_dict.customer.get_value(),
			project: page.fields_dict.project.get_value(),
			expense_claim_type: page.fields_dict.expense_claim_type.get_value()
		};

		frappe.call({
			method: "expense_claim_payable.expense_claim_payable.page.expense_billable.expense_billable.get_billable_expenses",
			args: filters,
			callback: function(r) {
				render_table(r.message || []);
			}
		});
	}

	// Render details in table
	function render_table(data) {
		let tbody = $('#eb-table-body');
		let empty_state = $('#eb-empty-state');
		let table_wrapper = $('.eb-table-wrapper');
		
		tbody.empty();
		$('#eb-select-all').prop('checked', false);
		update_banner();

		if (data.length === 0) {
			empty_state.show();
			table_wrapper.hide();
			return;
		}

		empty_state.hide();
		table_wrapper.show();

		data.forEach(row => {
			let date_str = row.date ? frappe.datetime.str_to_user(row.date) : '';
			let formatted_amount = format_currency(row.amount, frappe.boot.sysdefaults.currency || 'USD');
			let tr = $(`
				<tr data-id="${row.name}" data-amount="${row.amount}">
					<td class="eb-checkbox-cell">
						<label class="eb-checkbox-wrapper">
							<input type="checkbox" class="eb-checkbox row-checkbox">
						</label>
					</td>
					<td class="eb-date-cell">${date_str}</td>
					<td class="eb-project-cell">${row.project ? (row.project_name ? row.project + ' - ' + row.project_name : row.project) : ''}</td>
					<td class="eb-customer-cell">${row.customer_name || ''}</td>
					<td class="eb-type-cell">${row.expense_claim_type || ''}</td>
					<td class="eb-description-cell">${row.description || ''}</td>
					<td class="eb-amount-cell text-right">${formatted_amount}</td>
				</tr>
			`);
			tr.appendTo(tbody);
		});

		bind_events();
	}

	// Bind interactive checkbox/row click handlers
	function bind_events() {
		// Individual checkbox selection
		$('.row-checkbox').off('change').on('change', function() {
			let tr = $(this).closest('tr');
			if (this.checked) {
				tr.addClass('selected-row');
			} else {
				tr.removeClass('selected-row');
			}
			update_banner();
		});

		// Row body click selection toggling
		$('.eb-table tbody tr').off('click').on('click', function(e) {
			if ($(e.target).is('input') || $(e.target).closest('.eb-checkbox-wrapper').length) {
				return;
			}
			let checkbox = $(this).find('.row-checkbox');
			checkbox.prop('checked', !checkbox.prop('checked')).trigger('change');
		});
	}

	// Select all toggle handler
	$('#eb-select-all').on('change', function() {
		let is_checked = this.checked;
		$('.row-checkbox').each(function() {
			$(this).prop('checked', is_checked).trigger('change');
		});
	});

	// Update selection details floating banner
	function update_banner() {
		let checked_boxes = $('.row-checkbox:checked');
		let count = checked_boxes.length;
		let total = 0;

		checked_boxes.each(function() {
			let amt = parseFloat($(this).closest('tr').attr('data-amount')) || 0;
			total += amt;
		});

		if (count > 0) {
			$('#eb-selected-count').text(`${count} ${count === 1 ? 'Item' : 'Items'} Selected`);
			$('#eb-selected-amount').text(format_currency(total, frappe.boot.sysdefaults.currency || 'USD'));
			$('#eb-action-banner').addClass('show');
		} else {
			$('#eb-action-banner').removeClass('show');
		}
	}



	// Run initial fetch
	fetch_data();
}