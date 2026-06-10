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
		fields=["name", "project", "base_sanctioned_amount", "expense_type", "parent", "description"]
	)
	
	if not details:
		return []
		
	# 3. Resolve customer information and parent claim date for each detail
	# Collect unique projects
	proj_names = list(set([d.get("project") for d in details if d.get("project")]))
	project_customers = {}
	project_titles = {}
	if proj_names:
		projects_data = frappe.get_all("Project",
			filters={"name": ["in", proj_names]},
			fields=["name", "customer", "project_name"]
		)
		project_customers = {p.name: p.customer for p in projects_data}
		project_titles = {p.name: p.project_name for p in projects_data}

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
		proj_name = project_titles.get(proj) if proj else ""
		cust_id = project_customers.get(proj) if proj else None
		cust_name = customer_names.get(cust_id) if cust_id else ""
		parent_date = parent_dates.get(d.get("parent"))

		result.append({
			"name": d.get("name"),
			"date": parent_date,
			"project": proj,
			"project_name": proj_name,
			"customer": cust_id,
			"customer_name": cust_name or cust_id or "",
			"expense_claim_type": d.get("expense_type"),
			"description": d.get("description"),
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
		fields=["name", "expense_date", "project", "amount", "expense_type", "parent", "description"]
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
			"description": d.get("description"),
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

    # Fetch selected expense details
    details = frappe.get_all("Expense Claim Detail",
        filters={"name": ["in", selected_rows]},
        fields=["name", "expense_type", "base_sanctioned_amount", "project", "item", "description"]
    )

    # Get project -> customer mapping
    proj_names = list(set([d.get("project") for d in details if d.get("project")]))
    project_customers = {}
    if proj_names:
        projects_data = frappe.get_all("Project",
            filters={"name": ["in", proj_names]},
            fields=["name", "customer"]
        )
        project_customers = {p.name: p.customer for p in projects_data}

    # Group details by (customer, project) or just (customer) based on billable_method
    grouped_details = {}
    for d in details:
        proj = d.get("project")
        cust = project_customers.get(proj) if proj else None
        
        if not cust:
            continue
            
        # Get billable method directly for the customer
        billable_method = frappe.db.get_value("Customer", cust, "billable_method")
        
        # Default to Project-based if not set or if set to Project
        if billable_method and billable_method.strip().lower() == "customer":
            key = (cust, None)  # Consolidated for customer
        else:
            key = (cust, proj)  # Separate per project
            
        if key not in grouped_details:
            grouped_details[key] = []
        grouped_details[key].append(d)

    created_invoices = []
    expense_type_cache = {}

    # Get company and address info once
    company = frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.get_all("Company", limit=1, pluck="name")[0]
    
    company_address = None
    gst_category = None
    address_name = frappe.get_all("Address", filters={"link_name": company, "is_primary_address": 1}, pluck="name", limit=1)
    if not address_name:
        address_name = frappe.get_all("Address", filters={"link_name": company}, pluck="name", limit=1)
    
    if address_name:
        company_address = address_name[0]
        gst_category = frappe.db.get_value("Address", company_address, "gst_category")
        if gst_category not in ("Overseas", "Unregistered"):
            # This is a bit arbitrary but matches previous logic
            pass 

    for (cust, proj), items in grouped_details.items():
        if not cust:
            # Skip items without customer as Sales Invoice requires one
            continue

        doc = frappe.new_doc("Sales Invoice")
        doc.company = company
        doc.customer = cust
        doc.project = proj or ""
        doc.custom_invoice_type = "Services"
        
        if company_address:
            doc.company_address = company_address
        if gst_category:
            doc.gst_category = gst_category

        # Populate customer name
        cust_name = frappe.db.get_value("Customer", cust, "customer_name")
        if cust_name:
            doc.customer_name = cust_name

        for d in items:
            item_code = d.get("item")
            exp_type = d.get("expense_type")
            ect_doc = None
            
            if not item_code:
                ect_doc = expense_type_cache.get(exp_type)
                if not ect_doc and exp_type:
                    ect_doc = frappe.get_doc("Expense Claim Type", exp_type)
                    expense_type_cache[exp_type] = ect_doc
                
                if ect_doc and hasattr(ect_doc, "item"):
                    item_code = ect_doc.item
            
            if not item_code:
                item_code = "Expense"
            
            rate = frappe.get_value("Item Price",
                {"item_code": item_code, "price_list": "Selling Buying"},
                "price_list_rate"
            )
            if not rate or rate <= 0:
                rate = d.get("base_sanctioned_amount") or 0.01

            doc.append("items", {
                "item_code": item_code,
                "description": d.get("description") or (ect_doc.item_name if ect_doc and hasattr(ect_doc, "item_name") else item_code),
                "qty": 1,
                "rate": rate,
                "project": d.get("project") or ""
            })

        doc.insert()
        created_invoices.append(doc.name)

        # Mark original details as billed
        for d in items:
            frappe.db.set_value(
                "Expense Claim Detail",
                d.get("name"),
                "expense_claim_type",
                1,
                update_modified=False
            )

    frappe.db.commit()
    return created_invoices
