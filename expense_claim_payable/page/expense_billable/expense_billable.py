import frappe
from frappe import _

@frappe.whitelist()
def get_billable_expenses(from_date=None, to_date=None, customer=None, project=None, expense_claim_type=None):
	# 1. Fetch approved and submitted parent Expense Claims
	parent_filters = {"docstatus": 1, "approval_status": "Approved"}
	approved_claims = frappe.get_all("Expense Claim", filters=parent_filters, pluck="name")
	
	if not approved_claims:
		return []
		
	# 2. Build filters for details
	filters = {
		"parent": ["in", approved_claims],
		"is_billable": 1,
		"expense_claim_type": 0  # Is Billed = 0
	}
	
	if from_date and to_date:
		filters["expense_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["expense_date"] = [">=", from_date]
	elif to_date:
		filters["expense_date"] = ["<=", to_date]
		
	if project:
		filters["project"] = project
		
	if expense_claim_type:
		filters["expense_type"] = expense_claim_type
		
	# If customer filter is provided, get all projects for this customer
	if customer:
		customer_projects = frappe.get_all("Project", filters={"customer": customer}, pluck="name")
		if not customer_projects:
			return []
		# If project filter was also specified, find intersection
		if project:
			if project not in customer_projects:
				return []
		else:
			filters["project"] = ["in", customer_projects]
			
	# Fetch matching details
	details = frappe.get_all("Expense Claim Detail",
		filters=filters,
		fields=["name", "project", "base_sanctioned_amount", "expense_type", "parent"]
	)
	
	if not details:
		return []
		
	# 3. Resolve customer information and parent claim date for each detail
	# Collect unique projects
	proj_names = list(set([d.get("project") for d in details if d.get("project")]))
	project_customers = {}
	if proj_names:
		projects_data = frappe.get_all("Project",
			filters={"name": ["in", proj_names]},
			fields=["name", "customer"]
		)
		project_customers = {p.name: p.customer for p in projects_data}

	# Collect unique customers to fetch customer names
	cust_ids = list(set([c for c in project_customers.values() if c]))
	customer_names = {}
	if cust_ids:
		customers_data = frappe.get_all("Customer",
			filters={"name": ["in", cust_ids]},
			fields=["name", "customer_name"]
		)
		customer_names = {c.name: c.customer_name for c in customers_data}

	# Collect parent claim dates
	parent_names = list(set([d.get("parent") for d in details if d.get("parent")]))
	parent_dates = {}
	if parent_names:
		claims_data = frappe.get_all("Expense Claim",
			filters={"name": ["in", parent_names]},
			fields=["name", "posting_date", "creation"]
		)
		for c in claims_data:
			parent_dates[c.name] = c.get("posting_date") or c.get("creation")

	# Formulate final response rows
	result = []
	for d in details:
		proj = d.get("project")
		cust_id = project_customers.get(proj) if proj else None
		cust_name = customer_names.get(cust_id) if cust_id else ""
		parent_date = parent_dates.get(d.get("parent"))

		result.append({
			"name": d.get("name"),
			"date": parent_date,
			"project": proj,
			"customer": cust_id,
			"customer_name": cust_name or cust_id or "",
			"expense_claim_type": d.get("expense_type"),
			"amount": d.get("base_sanctioned_amount"),
			"expense_claim": d.get("parent")
		})

	return result

@frappe.whitelist()
def create_billable_expense(selected_rows, customer=None, project=None, from_date=None, to_date=None, expense_claim_type=None):
	import json
	if isinstance(selected_rows, str):
		selected_rows = json.loads(selected_rows)
		
	if not selected_rows:
		frappe.throw(_("No expenses selected"))
		
	doc = frappe.new_doc("Billable Expense")
	# If customer not explicitly provided, infer from the project linked to the first selected expense
	if not customer:
		# Determine customer from the project of the first detail (if any)
		if selected_rows:
			first_detail = frappe.get_all("Expense Claim Detail", filters={"name": selected_rows[0]}, fields=["project"]).pop()
			proj = first_detail.get("project")
			if proj:
				cust = frappe.db.get_value("Project", proj, "customer")
				if cust:
					customer = cust
		doc.customer = customer
	else:
		doc.customer = customer
	doc.project = project
	doc.from_date = from_date
	doc.to_date = to_date
	doc.expense_claim_type = expense_claim_type
	
	# Fetch all details
	details = frappe.get_all("Expense Claim Detail",
		filters={"name": ["in", selected_rows]},
		fields=["name", "expense_date", "project", "amount", "expense_type", "parent"]
	)
	
	# Fetch project customers
	proj_names = list(set([d.get("project") for d in details if d.get("project")]))
	project_customers = {}
	if proj_names:
		projects_data = frappe.get_all("Project", filters={"name": ["in", proj_names]}, fields=["name", "customer"])
		project_customers = {p.name: p.customer for p in projects_data}
		
	for d in details:
		proj = d.get("project")
		cust = project_customers.get(proj) if proj else None
		
		doc.append("billable_expense", {
			"date": d.get("expense_date"),
			"customer": cust,
			"amount": d.get("amount"),
			"project": proj,
			"expense_claim_type": d.get("expense_type"),
			"expense_claim": d.get("parent")
		})
		
	doc.insert()
	doc.save()
	
	# Mark the original details as billed (expense_claim_type = 1)
	for d in details:
		frappe.db.set_value("Expense Claim Detail", d.get("name"), "expense_claim_type", 1, update_modified=False)
		
	frappe.db.commit()
	
	return doc.name

@frappe.whitelist()
def create_sales_invoice(selected_rows, customer=None, project=None):
    import json
    if isinstance(selected_rows, str):
        selected_rows = json.loads(selected_rows)

    if not selected_rows:
        frappe.throw(_("No expenses selected"))

    # Create draft Sales Invoice
    doc = frappe.new_doc("Sales Invoice")

    # Set default company from user defaults
    company = frappe.defaults.get_user_default("Company")
    if not company:
        # Fallback: try to get any company
        company = frappe.get_all("Company", limit=1, pluck="name")[0]
    doc.company = company

        # Fetch the company's primary address (ERPNext 16 may not have 'default_company_address')
    address_name = frappe.get_all("Address", filters={"link_name": company, "is_primary_address": 1}, pluck="name", limit=1)
    if address_name:
        doc.company_address = address_name[0]
        # Set GST Category from address; default to 'Unregistered' if missing or invalid
        gst_cat = frappe.db.get_value("Address", address_name[0], "gst_category")
        if gst_cat not in ("Overseas", "Unregistered"):
            gst_cat = "Unregistered"
        doc.gst_category = gst_cat
    else:
        # Fallback: get any address linked to company
        address_name = frappe.get_all("Address", filters={"link_name": company}, pluck="name", limit=1)
        if address_name:
            doc.company_address = address_name[0]
            gst_cat = frappe.db.get_value("Address", address_name[0], "gst_category")
            if gst_cat:
                doc.gst_category = gst_cat

    # Determine customer if not provided
    if not customer:
        first_detail = frappe.get_all("Expense Claim Detail", filters={"name": selected_rows[0]}, fields=["project"]).pop()
        proj = first_detail.get("project")
        if proj:
            cust = frappe.db.get_value("Project", proj, "customer")
            if cust:
                customer = cust

    doc.customer = customer or ""
    # Populate customer name if customer is set
    if doc.customer:
        cust_name = frappe.db.get_value("Customer", doc.customer, "customer_name")
        if cust_name:
            doc.customer_name = cust_name
    doc.project = project or ""

    # Fetch selected expense details
    details = frappe.get_all("Expense Claim Detail",
        filters={"name": ["in", selected_rows]},
        fields=["name", "expense_type", "base_sanctioned_amount", "project"]
    )

    # Cache Expense Claim Type docs to avoid repeated fetching
    expense_type_cache = {}

    for d in details:
        exp_type = d.get("expense_type")
        # Get or fetch expense claim type doc
        ect_doc = expense_type_cache.get(exp_type)
        if not ect_doc and exp_type:
            ect_doc = frappe.get_doc("Expense Claim Type", exp_type)
            expense_type_cache[exp_type] = ect_doc

        # Determine item code from expense claim type (field 'item')
        item_code = ect_doc.item if ect_doc and hasattr(ect_doc, "item") else "Expense"

        # Get rate from 'Selling Buying' price list for the item
        rate = frappe.get_value("Item Price",
            {"item_code": item_code, "price_list": "Selling Buying"},
            "price_list_rate"
        )
        # Ensure a non-zero rate; fall back to base amount or minimal default
        if not rate or rate <= 0:
            rate = d.get("base_sanctioned_amount") or 0.01

        doc.append("items", {
            "item_code": item_code,
            "description": ect_doc.item_name if ect_doc and hasattr(ect_doc, "item_name") else item_code,
            "qty": 1,
            "rate": rate,
            "project": d.get("project") or ""
        })

    doc.save()

    # Mark original details as billed:
    #   - uncheck 'is_billable' so they no longer show as billable
    #   - check 'expense_claim_type' (Is Billed) so they show as already billed
    for d in details:
        frappe.db.set_value(
            "Expense Claim Detail",
            d.get("name"),
            "expense_claim_type",
            1,
            update_modified=False
        )

    frappe.db.commit()
    return doc.name
