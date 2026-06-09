app_name = "expense_claim_payable"
app_title = "Expense Claim Payable"
app_publisher = "Assimilate Technologies Pvt Ltd"
app_description = "Expense Claim Payable"
app_email = "info@assimilatetechnologies.com"
app_license = "mit"

after_migrate = [
    "expense_claim_payable.patches.add_is_billable_checkbox_on_expense_claim.execute",
    "expense_claim_payable.patches.add_field_on_expense_claim_type.execute",
    "expense_claim_payable.patches.add_item_on_expense_claim_type.execute"
]

doctype_js = {
	"Expense Claim": "public/js/expense_claim.js"
}
