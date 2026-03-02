"""
Database Migration Script
Adds missing columns to existing database tables without deleting data
"""
import sqlite3
import os

def migrate_database():
    """Run database migrations"""
    # Handle different DATABASE_URL formats
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./erp.db")
    
    # Parse the URL to get the file path
    if db_url.startswith("file:"):
        db_path = db_url[5:]  # Remove 'file:' prefix
    elif db_url.startswith("sqlite:///"):
        db_path = db_url[10:]  # Remove 'sqlite:///'
    elif db_url.startswith("sqlite://"):
        db_path = db_url[9:]  # Remove 'sqlite://'
    else:
        # Relative path
        db_path = db_url
    
    # If the path is relative, make it relative to the backend directory
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(__file__), db_path)
    
    if not os.path.exists(db_path):
        print("Database file not found. It will be created when the app starts.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Helper function to add column if it doesn't exist
    def add_column_if_not_exists(table, column, column_type, default_value=None):
        try:
            if default_value:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} DEFAULT {default_value}")
            else:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            print(f"✓ Added column {column} to {table}")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  Column {column} already exists in {table}")
                return False
            else:
                print(f"✗ Error adding column {column} to {table}: {e}")
                return False

    # Helper function to check if table exists
    def table_exists(table_name):
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        return cursor.fetchone() is not None

    # Helper function to get table columns
    def get_table_columns(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    # Helper function to recreate table with new schema (for complex migrations)
    def recreate_table_with_new_columns(table_name, new_columns_defs):
        """Recreate a table with additional columns (SQLite doesn't support dropping columns directly)"""
        if not table_exists(table_name):
            print(f"  Table {table_name} doesn't exist, skipping recreation")
            return
        
        existing_columns = get_table_columns(table_name)
        new_columns = [col_def.split()[0] for col_def in new_columns_defs if col_def.split()[0] not in existing_columns]
        
        if not new_columns:
            print(f"  Table {table_name} already has all columns")
            return
        
        # Get current table schema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        original_schema = cursor.fetchone()[0]
        
        # Create temporary table with new schema
        temp_table = f"{table_name}_temp"
        columns_str = ", ".join(existing_columns + new_columns_defs)
        
        try:
            # Create new table with all columns
            cursor.execute(f"CREATE TABLE {temp_table} AS SELECT * FROM {table_name}")
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
            print(f"✓ Recreated table {table_name} with new columns: {new_columns}")
        except Exception as e:
            print(f"✗ Error recreating table {table_name}: {e}")
            conn.rollback()

    print("=" * 60)
    print("Starting Database Migration")
    print("=" * 60)
    
    # ==================== FUND TRANSFERS TABLE ====================
    print("\n[1] Checking fund_transfers table...")
    if table_exists('fund_transfers'):
        add_column_if_not_exists('fund_transfers', 'from_account_type', "VARCHAR(20) DEFAULT 'bank'")
        add_column_if_not_exists('fund_transfers', 'from_account_name', 'VARCHAR(255)')
        add_column_if_not_exists('fund_transfers', 'to_account_type', "VARCHAR(20) DEFAULT 'bank'")
        add_column_if_not_exists('fund_transfers', 'to_account_name', 'VARCHAR(255)')
        add_column_if_not_exists('fund_transfers', 'from_coa_id', 'INTEGER REFERENCES accounts(id) ON DELETE SET NULL')
        add_column_if_not_exists('fund_transfers', 'to_coa_id', 'INTEGER REFERENCES accounts(id) ON DELETE SET NULL')
    else:
        print("  fund_transfers table doesn't exist yet")
    
    # ==================== LEDGER ENTRIES TABLE ====================
    print("\n[2] Checking ledger_entries table...")
    add_column_if_not_exists('ledger_entries', 'credit_note_id', 'INTEGER REFERENCES credit_notes(id) ON DELETE SET NULL')
    add_column_if_not_exists('ledger_entries', 'debit_note_id', 'INTEGER REFERENCES debit_notes(id) ON DELETE SET NULL')
    add_column_if_not_exists('ledger_entries', 'expense_id', 'INTEGER REFERENCES expenses(id) ON DELETE SET NULL')
    add_column_if_not_exists('ledger_entries', 'other_income_id', 'INTEGER REFERENCES other_incomes(id) ON DELETE SET NULL')
    add_column_if_not_exists('ledger_entries', 'bank_account_id', 'INTEGER REFERENCES bank_accounts(id) ON DELETE SET NULL')
    
    # ==================== PAYSLIPS TABLE ====================
    print("\n[2b] Checking payslips table...")
    add_column_if_not_exists('payslips', 'basic_salary', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('payslips', 'allowances', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('payslips', 'pension_employee', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('payslips', 'pension_employer', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('payslips', 'status', "VARCHAR(20) DEFAULT 'pending'")
    
    # ==================== CREDIT NOTES TABLE ====================
    print("\n[3] Checking credit_notes table...")
    add_column_if_not_exists('credit_notes', 'customer_id', 'INTEGER REFERENCES customers(id)')
    add_column_if_not_exists('credit_notes', 'status', "VARCHAR(20) DEFAULT 'open'")
    add_column_if_not_exists('credit_notes', 'refund_amount', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('credit_notes', 'refund_method', 'VARCHAR(20)')
    add_column_if_not_exists('credit_notes', 'refund_date', 'DATE')
    
    # ==================== DEBIT NOTES TABLE ====================
    print("\n[4] Checking debit_notes table...")
    add_column_if_not_exists('debit_notes', 'vendor_id', 'INTEGER REFERENCES vendors(id)')
    add_column_if_not_exists('debit_notes', 'status', "VARCHAR(20) DEFAULT 'open'")
    add_column_if_not_exists('debit_notes', 'refund_amount', 'NUMERIC(15, 2) DEFAULT 0.00')
    add_column_if_not_exists('debit_notes', 'refund_method', 'VARCHAR(20)')
    add_column_if_not_exists('debit_notes', 'refund_date', 'DATE')
    
    # ==================== CREDIT NOTE ITEMS TABLE ====================
    print("\n[5] Checking credit_note_items table...")
    add_column_if_not_exists('credit_note_items', 'original_item_id', 'INTEGER REFERENCES sales_invoice_items(id)')
    
    # ==================== DEBIT NOTE ITEMS TABLE ====================
    print("\n[6] Checking debit_note_items table...")
    add_column_if_not_exists('debit_note_items', 'original_item_id', 'INTEGER REFERENCES purchase_bill_items(id)')
    
    # ==================== PAYMENTS TABLE ====================
    print("\n[7] Checking payments table...")
    add_column_if_not_exists('payments', 'account_id', 'INTEGER REFERENCES accounts(id) ON DELETE SET NULL')
    
    # ==================== BANK ACCOUNTS TABLE ====================
    print("\n[8] Checking bank_accounts table...")
    add_column_if_not_exists('bank_accounts', 'chart_of_account_id', 'INTEGER REFERENCES accounts(id) ON DELETE SET NULL')
    
    # ==================== JOURNAL VOUCHERS TABLE ====================
    print("\n[9] Checking journal_vouchers table...")
    add_column_if_not_exists('journal_vouchers', 'is_posted', 'BOOLEAN DEFAULT 0')
    
    # ==================== UPDATE EXISTING DATA ====================
    print("\n[10] Updating existing data...")

    # Fix pay_frequency enum values in payroll_configs - comprehensive fix
    pay_frequency_fixes = [
        ('Monthly', 'MONTHLY'),
        ('monthly', 'MONTHLY'),
        ('WEEKLY', 'WEEKLY'),
        ('Weekly', 'WEEKLY'),
        ('weekly', 'WEEKLY'),
        ('Bi-Weekly', 'BI_WEEKLY'),
        ('Bi_Weekly', 'BI_WEEKLY'),
        ('bi_weekly', 'BI_WEEKLY'),
        ('BI-WEEKLY', 'BI_WEEKLY'),
    ]
    for old_val, new_val in pay_frequency_fixes:
        try:
            cursor.execute("UPDATE payroll_configs SET pay_frequency = ? WHERE pay_frequency = ?", (new_val, old_val))
            if cursor.rowcount > 0:
                print(f"  Fixed {cursor.rowcount} payroll_configs pay_frequency from '{old_val}' to '{new_val}'")
        except Exception as e:
            print(f"  Note: Could not update payroll_configs pay_frequency: {e}")
    
    # ==================== FIX NUMERIC DATA TYPES ====================
    print("\n[10b] Fixing numeric data types...")
    
    # Fix gross_salary in payroll_configs - ensure it's stored as numeric
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET gross_salary = CAST(gross_salary AS REAL)
            WHERE typeof(gross_salary) = 'text'
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs gross_salary from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs gross_salary: {e}")
    
    # Fix paye_rate in payroll_configs
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET paye_rate = CAST(paye_rate AS REAL)
            WHERE typeof(paye_rate) = 'text' AND paye_rate IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs paye_rate from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs paye_rate: {e}")
    
    # Fix pension_employee_rate in payroll_configs
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET pension_employee_rate = CAST(pension_employee_rate AS REAL)
            WHERE typeof(pension_employee_rate) = 'text' AND pension_employee_rate IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs pension_employee_rate from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs pension_employee_rate: {e}")
    
    # Fix pension_employer_rate in payroll_configs
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET pension_employer_rate = CAST(pension_employer_rate AS REAL)
            WHERE typeof(pension_employer_rate) = 'text' AND pension_employer_rate IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs pension_employer_rate from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs pension_employer_rate: {e}")
    
    # Fix other_deductions in payroll_configs
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET other_deductions = CAST(other_deductions AS REAL)
            WHERE typeof(other_deductions) = 'text' AND other_deductions IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs other_deductions from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs other_deductions: {e}")
    
    # Fix other_allowances in payroll_configs
    try:
        cursor.execute("""
            UPDATE payroll_configs 
            SET other_allowances = CAST(other_allowances AS REAL)
            WHERE typeof(other_allowances) = 'text' AND other_allowances IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payroll_configs other_allowances from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payroll_configs other_allowances: {e}")
    
    # ==================== FIX PAYSLIPS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE payslips 
            SET basic_salary = CAST(basic_salary AS REAL)
            WHERE typeof(basic_salary) = 'text' AND basic_salary IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips basic_salary from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips basic_salary: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET allowances = CAST(allowances AS REAL)
            WHERE typeof(allowances) = 'text' AND allowances IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips allowances from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips allowances: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET gross_salary = CAST(gross_salary AS REAL)
            WHERE typeof(gross_salary) = 'text' AND gross_salary IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips gross_salary from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips gross_salary: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET paye_deduction = CAST(paye_deduction AS REAL)
            WHERE typeof(paye_deduction) = 'text' AND paye_deduction IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips paye_deduction from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips paye_deduction: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET pension_employee = CAST(pension_employee AS REAL)
            WHERE typeof(pension_employee) = 'text' AND pension_employee IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips pension_employee from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips pension_employee: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET pension_employer = CAST(pension_employer AS REAL)
            WHERE typeof(pension_employer) = 'text' AND pension_employer IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips pension_employer from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips pension_employer: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET other_deductions = CAST(other_deductions AS REAL)
            WHERE typeof(other_deductions) = 'text' AND other_deductions IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips other_deductions from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips other_deductions: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET total_deductions = CAST(total_deductions AS REAL)
            WHERE typeof(total_deductions) = 'text' AND total_deductions IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips total_deductions from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips total_deductions: {e}")
    
    try:
        cursor.execute("""
            UPDATE payslips 
            SET net_salary = CAST(net_salary AS REAL)
            WHERE typeof(net_salary) = 'text' AND net_salary IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payslips net_salary from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payslips net_salary: {e}")
    
    # ==================== FIX EXPENSES NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE expenses 
            SET sub_total = CAST(sub_total AS REAL)
            WHERE typeof(sub_total) = 'text' AND sub_total IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} expenses sub_total from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix expenses sub_total: {e}")
    
    try:
        cursor.execute("""
            UPDATE expenses 
            SET vat_amount = CAST(vat_amount AS REAL)
            WHERE typeof(vat_amount) = 'text' AND vat_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} expenses vat_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix expenses vat_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE expenses 
            SET amount = CAST(amount AS REAL)
            WHERE typeof(amount) = 'text' AND amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} expenses amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix expenses amount: {e}")
    
    # ==================== FIX OTHER_INCOMES NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE other_incomes 
            SET sub_total = CAST(sub_total AS REAL)
            WHERE typeof(sub_total) = 'text' AND sub_total IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} other_incomes sub_total from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix other_incomes sub_total: {e}")
    
    try:
        cursor.execute("""
            UPDATE other_incomes 
            SET vat_amount = CAST(vat_amount AS REAL)
            WHERE typeof(vat_amount) = 'text' AND vat_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} other_incomes vat_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix other_incomes vat_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE other_incomes 
            SET amount = CAST(amount AS REAL)
            WHERE typeof(amount) = 'text' AND amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} other_incomes amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix other_incomes amount: {e}")
    
    # ==================== FIX BUDGETS & BUDGET_ITEMS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE budget_items 
            SET amount = CAST(amount AS REAL)
            WHERE typeof(amount) = 'text' AND amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} budget_items amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix budget_items amount: {e}")
    
    # ==================== FIX FIXED_ASSETS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE fixed_assets 
            SET purchase_cost = CAST(purchase_cost AS REAL)
            WHERE typeof(purchase_cost) = 'text' AND purchase_cost IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} fixed_assets purchase_cost from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix fixed_assets purchase_cost: {e}")
    
    try:
        cursor.execute("""
            UPDATE fixed_assets 
            SET salvage_value = CAST(salvage_value AS REAL)
            WHERE typeof(salvage_value) = 'text' AND salvage_value IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} fixed_assets salvage_value from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix fixed_assets salvage_value: {e}")
    
    try:
        cursor.execute("""
            UPDATE fixed_assets 
            SET accumulated_depreciation = CAST(accumulated_depreciation AS REAL)
            WHERE typeof(accumulated_depreciation) = 'text' AND accumulated_depreciation IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} fixed_assets accumulated_depreciation from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix fixed_assets accumulated_depreciation: {e}")
    
    try:
        cursor.execute("""
            UPDATE fixed_assets 
            SET book_value = CAST(book_value AS REAL)
            WHERE typeof(book_value) = 'text' AND book_value IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} fixed_assets book_value from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix fixed_assets book_value: {e}")
    
    # ==================== FIX LEDGER_ENTRIES NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE ledger_entries 
            SET debit = CAST(debit AS REAL)
            WHERE typeof(debit) = 'text' AND debit IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} ledger_entries debit from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix ledger_entries debit: {e}")
    
    try:
        cursor.execute("""
            UPDATE ledger_entries 
            SET credit = CAST(credit AS REAL)
            WHERE typeof(credit) = 'text' AND credit IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} ledger_entries credit from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix ledger_entries credit: {e}")
    
    # ==================== FIX SALES_INVOICES NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE sales_invoices 
            SET sub_total = CAST(sub_total AS REAL)
            WHERE typeof(sub_total) = 'text' AND sub_total IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} sales_invoices sub_total from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix sales_invoices sub_total: {e}")
    
    try:
        cursor.execute("""
            UPDATE sales_invoices 
            SET vat_amount = CAST(vat_amount AS REAL)
            WHERE typeof(vat_amount) = 'text' AND vat_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} sales_invoices vat_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix sales_invoices vat_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE sales_invoices 
            SET total_amount = CAST(total_amount AS REAL)
            WHERE typeof(total_amount) = 'text' AND total_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} sales_invoices total_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix sales_invoices total_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE sales_invoices 
            SET paid_amount = CAST(paid_amount AS REAL)
            WHERE typeof(paid_amount) = 'text' AND paid_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} sales_invoices paid_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix sales_invoices paid_amount: {e}")
    
    # ==================== FIX PURCHASE_BILLS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE purchase_bills 
            SET sub_total = CAST(sub_total AS REAL)
            WHERE typeof(sub_total) = 'text' AND sub_total IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} purchase_bills sub_total from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix purchase_bills sub_total: {e}")
    
    try:
        cursor.execute("""
            UPDATE purchase_bills 
            SET vat_amount = CAST(vat_amount AS REAL)
            WHERE typeof(vat_amount) = 'text' AND vat_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} purchase_bills vat_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix purchase_bills vat_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE purchase_bills 
            SET total_amount = CAST(total_amount AS REAL)
            WHERE typeof(total_amount) = 'text' AND total_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} purchase_bills total_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix purchase_bills total_amount: {e}")
    
    try:
        cursor.execute("""
            UPDATE purchase_bills 
            SET paid_amount = CAST(paid_amount AS REAL)
            WHERE typeof(paid_amount) = 'text' AND paid_amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} purchase_bills paid_amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix purchase_bills paid_amount: {e}")
    
    # ==================== FIX PAYMENTS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE payments 
            SET amount = CAST(amount AS REAL)
            WHERE typeof(amount) = 'text' AND amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} payments amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix payments amount: {e}")
    
    # ==================== FIX FUND_TRANSFERS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE fund_transfers 
            SET amount = CAST(amount AS REAL)
            WHERE typeof(amount) = 'text' AND amount IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} fund_transfers amount from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix fund_transfers amount: {e}")
    
    # ==================== FIX PRODUCTS NUMERIC FIELDS ====================
    try:
        cursor.execute("""
            UPDATE products 
            SET purchase_price = CAST(purchase_price AS REAL)
            WHERE typeof(purchase_price) = 'text' AND purchase_price IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} products purchase_price from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix products purchase_price: {e}")
    
    try:
        cursor.execute("""
            UPDATE products 
            SET sales_price = CAST(sales_price AS REAL)
            WHERE typeof(sales_price) = 'text' AND sales_price IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} products sales_price from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix products sales_price: {e}")
    
    try:
        cursor.execute("""
            UPDATE products 
            SET opening_stock = CAST(opening_stock AS REAL)
            WHERE typeof(opening_stock) = 'text' AND opening_stock IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} products opening_stock from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix products opening_stock: {e}")
    
    try:
        cursor.execute("""
            UPDATE products 
            SET stock_quantity = CAST(stock_quantity AS REAL)
            WHERE typeof(stock_quantity) = 'text' AND stock_quantity IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} products stock_quantity from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix products stock_quantity: {e}")
    
    try:
        cursor.execute("""
            UPDATE products 
            SET reorder_level = CAST(reorder_level AS REAL)
            WHERE typeof(reorder_level) = 'text' AND reorder_level IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} products reorder_level from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix products reorder_level: {e}")
    
    # ==================== FIX CUSTOMERS CREDIT_LIMIT ====================
    try:
        cursor.execute("""
            UPDATE customers 
            SET credit_limit = CAST(credit_limit AS REAL)
            WHERE typeof(credit_limit) = 'text' AND credit_limit IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} customers credit_limit from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix customers credit_limit: {e}")
    
    # ==================== ADD ACCOUNT_BALANCE TO CUSTOMERS ====================
    print("\n[11b] Adding account_balance to customers table...")
    add_column_if_not_exists('customers', 'account_balance', 'NUMERIC(15, 2) DEFAULT 0.00')
    
    # ==================== ADD ACCOUNT_BALANCE TO VENDORS ====================
    print("\n[11c] Adding account_balance to vendors table...")
    add_column_if_not_exists('vendors', 'account_balance', 'NUMERIC(15, 2) DEFAULT 0.00')
    
    # ==================== ADD RETURNED_AMOUNT TO SALES_INVOICES ====================
    print("\n[11d] Adding returned_amount to sales_invoices table...")
    add_column_if_not_exists('sales_invoices', 'returned_amount', 'NUMERIC(15, 2) DEFAULT 0.00')
    
    # ==================== ADD RETURNED_AMOUNT TO PURCHASE_BILLS ====================
    print("\n[11e] Adding returned_amount to purchase_bills table...")
    add_column_if_not_exists('purchase_bills', 'returned_amount', 'NUMERIC(15, 2) DEFAULT 0.00')
    
    # ==================== FIX BANK_ACCOUNTS BALANCE ====================
    try:
        cursor.execute("""
            UPDATE bank_accounts 
            SET current_balance = CAST(current_balance AS REAL)
            WHERE typeof(current_balance) = 'text' AND current_balance IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} bank_accounts current_balance from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix bank_accounts current_balance: {e}")
    
    try:
        cursor.execute("""
            UPDATE bank_accounts 
            SET last_reconciliation_balance = CAST(last_reconciliation_balance AS REAL)
            WHERE typeof(last_reconciliation_balance) = 'text' AND last_reconciliation_balance IS NOT NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} bank_accounts last_reconciliation_balance from text to numeric")
    except Exception as e:
        print(f"  Note: Could not fix bank_accounts last_reconciliation_balance: {e}")
    
    # Update existing credit_notes with customer_id from their sales_invoice
    try:
        cursor.execute("""
            UPDATE credit_notes 
            SET customer_id = (SELECT customer_id FROM sales_invoices WHERE sales_invoices.id = credit_notes.sales_invoice_id)
            WHERE customer_id IS NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Updated {cursor.rowcount} credit_notes with customer_id")
    except Exception as e:
        print(f"  Note: Could not update credit_notes customer_id: {e}")
    
    # Update existing debit_notes with vendor_id from their purchase_bill
    try:
        cursor.execute("""
            UPDATE debit_notes 
            SET vendor_id = (SELECT vendor_id FROM purchase_bills WHERE purchase_bills.id = debit_notes.purchase_bill_id)
            WHERE vendor_id IS NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Updated {cursor.rowcount} debit_notes with vendor_id")
    except Exception as e:
        print(f"  Note: Could not update debit_notes vendor_id: {e}")
    
    # Update existing fund_transfers with account names from bank_accounts
    try:
        cursor.execute("""
            UPDATE fund_transfers
            SET from_account_name = (SELECT account_name FROM bank_accounts WHERE bank_accounts.id = fund_transfers.from_account_id),
                to_account_name = (SELECT account_name FROM bank_accounts WHERE bank_accounts.id = fund_transfers.to_account_id),
                from_coa_id = (SELECT chart_of_account_id FROM bank_accounts WHERE bank_accounts.id = fund_transfers.from_account_id),
                to_coa_id = (SELECT chart_of_account_id FROM bank_accounts WHERE bank_accounts.id = fund_transfers.to_account_id)
            WHERE from_account_name IS NULL OR to_account_name IS NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Updated {cursor.rowcount} fund_transfers with account names")
    except Exception as e:
        print(f"  Note: Could not update fund_transfers: {e}")

    # ==================== FIX LEDGER ENTRIES BANK_ACCOUNT_ID ====================
    print("\n[10c] Fixing ledger entries bank_account_id...")

    # Update opening balance ledger entries by matching description to bank account names
    try:
        # Get all bank accounts
        cursor.execute("SELECT id, account_name, chart_of_account_id FROM bank_accounts")
        bank_accounts = cursor.fetchall()

        for ba_id, ba_name, coa_id in bank_accounts:
            # Update ledger entries that are opening balance entries for this bank account
            # Match by description pattern "Opening Balance - {account_name}"
            cursor.execute("""
                UPDATE ledger_entries
                SET bank_account_id = ?
                WHERE description LIKE ? AND bank_account_id IS NULL AND account_id = ?
            """, (ba_id, f"Opening Balance - {ba_name}%", coa_id))
            if cursor.rowcount > 0:
                print(f"  Updated {cursor.rowcount} ledger entries for bank account '{ba_name}'")
    except Exception as e:
        print(f"  Note: Could not update ledger entries bank_account_id: {e}")

    # Check for duplicate chart_of_account_id in bank accounts
    try:
        cursor.execute("""
            SELECT chart_of_account_id, COUNT(*) as cnt
            FROM bank_accounts
            WHERE chart_of_account_id IS NOT NULL
            GROUP BY chart_of_account_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print("\n  WARNING: Multiple bank accounts share the same chart_of_account_id!")
            print("  This will cause balance issues. Please delete and recreate bank accounts with unique accounts.")
            for coa_id, cnt in duplicates:
                cursor.execute("SELECT account_name FROM bank_accounts WHERE chart_of_account_id = ?", (coa_id,))
                names = [row[0] for row in cursor.fetchall()]
                print(f"    COA ID {coa_id} used by: {', '.join(names)}")
    except Exception as e:
        print(f"  Note: Could not check for duplicate chart_of_account_id: {e}")

    # ==================== CREATE INDEXES ====================
    print("\n[11] Creating indexes...")
    indexes = [
        ('idx_ledger_entries_account_id', 'ledger_entries(account_id)'),
        ('idx_ledger_entries_transaction_date', 'ledger_entries(transaction_date)'),
        ('idx_ledger_entries_bank_account_id', 'ledger_entries(bank_account_id)'),
        ('idx_payments_account_id', 'payments(account_id)'),
        ('idx_fund_transfers_coa', 'fund_transfers(from_coa_id, to_coa_id)'),
        ('idx_budgets_business_id', 'budgets(business_id)'),
        ('idx_budgets_fiscal_year', 'budgets(fiscal_year)'),
        ('idx_budget_items_budget_id', 'budget_items(budget_id)'),
        ('idx_budget_items_account_id', 'budget_items(account_id)'),
        ('idx_fixed_assets_business_id', 'fixed_assets(business_id)'),
        ('idx_fixed_assets_branch_id', 'fixed_assets(branch_id)'),
    ]
    
    for index_name, index_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
            print(f"  ✓ Created index {index_name}")
        except Exception as e:
            print(f"  Note: Index {index_name} may already exist: {e}")
    
    # ==================== CREATE MISSING TABLES ====================
    print("\n[12] Checking for missing tables...")
    
    # Check and create employees table if missing
    if not table_exists('employees'):
        print("  Creating employees table...")
        cursor.execute("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone_number VARCHAR(50),
                address TEXT,
                hire_date DATE NOT NULL,
                termination_date DATE,
                department VARCHAR(100),
                position VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created employees table")
    
    # Check and create payroll_configs table if missing
    if not table_exists('payroll_configs'):
        print("  Creating payroll_configs table...")
        cursor.execute("""
            CREATE TABLE payroll_configs (
                id INTEGER PRIMARY KEY,
                gross_salary NUMERIC(15, 2) DEFAULT 0.00,
                pay_frequency VARCHAR(20) DEFAULT 'MONTHLY',
                paye_rate NUMERIC(5, 2) DEFAULT 0.00,
                pension_employee_rate NUMERIC(5, 2) DEFAULT 0.00,
                pension_employer_rate NUMERIC(5, 2) DEFAULT 0.00,
                other_deductions NUMERIC(15, 2) DEFAULT 0.00,
                other_allowances NUMERIC(15, 2) DEFAULT 0.00,
                employee_id INTEGER NOT NULL UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created payroll_configs table")
    
    # Check and create payslips table if missing
    if not table_exists('payslips'):
        print("  Creating payslips table...")
        cursor.execute("""
            CREATE TABLE payslips (
                id INTEGER PRIMARY KEY,
                payslip_number VARCHAR(50) NOT NULL,
                pay_period_start DATE NOT NULL,
                pay_period_end DATE NOT NULL,
                basic_salary NUMERIC(15, 2) DEFAULT 0.00,
                allowances NUMERIC(15, 2) DEFAULT 0.00,
                gross_salary NUMERIC(15, 2) DEFAULT 0.00,
                paye_deduction NUMERIC(15, 2) DEFAULT 0.00,
                pension_employee NUMERIC(15, 2) DEFAULT 0.00,
                pension_employer NUMERIC(15, 2) DEFAULT 0.00,
                other_deductions NUMERIC(15, 2) DEFAULT 0.00,
                total_deductions NUMERIC(15, 2) DEFAULT 0.00,
                net_salary NUMERIC(15, 2) DEFAULT 0.00,
                status VARCHAR(20) DEFAULT 'pending',
                paid_date DATE,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(payslip_number, business_id)
            )
        """)
        print("  ✓ Created payslips table")
    
    # Check and create journal_vouchers table if missing
    if not table_exists('journal_vouchers'):
        print("  Creating journal_vouchers table...")
        cursor.execute("""
            CREATE TABLE journal_vouchers (
                id INTEGER PRIMARY KEY,
                voucher_number VARCHAR(50) NOT NULL,
                transaction_date DATE NOT NULL,
                description TEXT,
                reference VARCHAR(100),
                is_posted BOOLEAN DEFAULT 0,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created journal_vouchers table")
    
    # Check and create expenses table if missing
    if not table_exists('expenses'):
        print("  Creating expenses table...")
        cursor.execute("""
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY,
                expense_number VARCHAR(50) NOT NULL,
                expense_date DATE NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                sub_total NUMERIC(15, 2) DEFAULT 0.00,
                vat_amount NUMERIC(15, 2) DEFAULT 0.00,
                amount NUMERIC(15, 2) DEFAULT 0.00,
                vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
                paid_from_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                expense_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(expense_number, business_id)
            )
        """)
        print("  ✓ Created expenses table")
    
    # Check and create other_incomes table if missing
    if not table_exists('other_incomes'):
        print("  Creating other_incomes table...")
        cursor.execute("""
            CREATE TABLE other_incomes (
                id INTEGER PRIMARY KEY,
                income_number VARCHAR(50) NOT NULL,
                income_date DATE NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                sub_total NUMERIC(15, 2) DEFAULT 0.00,
                vat_amount NUMERIC(15, 2) DEFAULT 0.00,
                amount NUMERIC(15, 2) DEFAULT 0.00,
                customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
                received_in_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                income_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(income_number, business_id)
            )
        """)
        print("  ✓ Created other_incomes table")
    
    # Check and create ledger_entries table if missing (must be after expenses and other_incomes)
    if not table_exists('ledger_entries'):
        print("  Creating ledger_entries table...")
        cursor.execute("""
            CREATE TABLE ledger_entries (
                id INTEGER PRIMARY KEY,
                transaction_date DATE NOT NULL,
                description TEXT,
                reference VARCHAR(100),
                debit NUMERIC(15, 2) DEFAULT 0.00,
                credit NUMERIC(15, 2) DEFAULT 0.00,
                account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                journal_voucher_id INTEGER REFERENCES journal_vouchers(id) ON DELETE CASCADE,
                sales_invoice_id INTEGER REFERENCES sales_invoices(id) ON DELETE SET NULL,
                purchase_bill_id INTEGER REFERENCES purchase_bills(id) ON DELETE SET NULL,
                credit_note_id INTEGER REFERENCES credit_notes(id) ON DELETE SET NULL,
                debit_note_id INTEGER REFERENCES debit_notes(id) ON DELETE SET NULL,
                expense_id INTEGER REFERENCES expenses(id) ON DELETE SET NULL,
                other_income_id INTEGER REFERENCES other_incomes(id) ON DELETE SET NULL,
                customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
                vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
                branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created ledger_entries table")
    
    # Check and create budgets table if missing
    if not table_exists('budgets'):
        print("  Creating budgets table...")
        cursor.execute("""
            CREATE TABLE budgets (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                fiscal_year INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, fiscal_year, business_id)
            )
        """)
        print("  ✓ Created budgets table")
    
    # Check and create budget_items table if missing
    if not table_exists('budget_items'):
        print("  Creating budget_items table...")
        cursor.execute("""
            CREATE TABLE budget_items (
                id INTEGER PRIMARY KEY,
                amount NUMERIC(15, 2) DEFAULT 0.00,
                month INTEGER,
                account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created budget_items table")
    
    # Check and create fixed_assets table if missing
    if not table_exists('fixed_assets'):
        print("  Creating fixed_assets table...")
        cursor.execute("""
            CREATE TABLE fixed_assets (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                asset_code VARCHAR(50),
                description TEXT,
                purchase_date DATE NOT NULL,
                purchase_cost NUMERIC(15, 2) DEFAULT 0.00,
                salvage_value NUMERIC(15, 2) DEFAULT 0.00,
                useful_life_years INTEGER DEFAULT 5,
                depreciation_method VARCHAR(50) DEFAULT 'straight_line',
                accumulated_depreciation NUMERIC(15, 2) DEFAULT 0.00,
                book_value NUMERIC(15, 2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT 1,
                account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created fixed_assets table")
    
    # Add new columns to fixed_assets table if not exists
    print("  Checking fixed_assets table columns...")
    fixed_assets_cols = cursor.execute("PRAGMA table_info(fixed_assets)").fetchall()
    col_names = [col[1] for col in fixed_assets_cols]
    
    new_columns = [
        ("branch_id", "INTEGER REFERENCES branches(id) ON DELETE SET NULL"),
        ("category", "VARCHAR(100)"),
        ("location", "VARCHAR(255)"),
        ("vendor_id", "INTEGER REFERENCES vendors(id) ON DELETE SET NULL"),
        ("depreciation_rate", "NUMERIC(5, 2) DEFAULT 0.00"),
        ("last_depreciation_date", "DATE"),
        ("status", "VARCHAR(20) DEFAULT 'active'"),
        ("disposal_date", "DATE"),
        ("disposal_amount", "NUMERIC(15, 2)"),
        ("disposal_reason", "TEXT"),
        ("warranty_expiry", "DATE"),
        ("insurance_policy", "VARCHAR(100)"),
        ("insurance_expiry", "DATE"),
        ("asset_account_id", "INTEGER REFERENCES accounts(id) ON DELETE SET NULL"),
        ("depreciation_account_id", "INTEGER REFERENCES accounts(id) ON DELETE SET NULL"),
        ("expense_account_id", "INTEGER REFERENCES accounts(id) ON DELETE SET NULL"),
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in col_names:
            try:
                cursor.execute(f"ALTER TABLE fixed_assets ADD COLUMN {col_name} {col_type}")
                print(f"  Added column {col_name} to fixed_assets")
            except Exception as e:
                print(f"  Note: Could not add column {col_name}: {e}")
    
    # Update existing records to have 'active' status
    cursor.execute("UPDATE fixed_assets SET status = 'active' WHERE status IS NULL")
    
    # Check and create depreciation_records table if missing
    if not table_exists('depreciation_records'):
        print("  Creating depreciation_records table...")
        cursor.execute("""
            CREATE TABLE depreciation_records (
                id INTEGER PRIMARY KEY,
                asset_id INTEGER NOT NULL REFERENCES fixed_assets(id) ON DELETE CASCADE,
                depreciation_date DATE NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                amount NUMERIC(15, 2) NOT NULL,
                method VARCHAR(50) DEFAULT 'straight_line',
                description TEXT,
                journal_voucher_id INTEGER REFERENCES journal_vouchers(id) ON DELETE SET NULL,
                branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_depreciation_records_asset_id ON depreciation_records(asset_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_depreciation_records_date ON depreciation_records(depreciation_date)")
        print("  ✓ Created depreciation_records table")
    
    # Check and create cash_book_entries table if missing
    if not table_exists('cash_book_entries'):
        print("  Creating cash_book_entries table...")
        cursor.execute("""
            CREATE TABLE cash_book_entries (
                id INTEGER PRIMARY KEY,
                entry_number VARCHAR(50) NOT NULL,
                entry_date DATE NOT NULL,
                entry_type VARCHAR(20) NOT NULL,
                account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                account_type VARCHAR(20) DEFAULT 'cash',
                amount NUMERIC(15, 2) NOT NULL,
                balance_after NUMERIC(15, 2),
                description TEXT,
                reference VARCHAR(100),
                payee_payer VARCHAR(255),
                source_type VARCHAR(50),
                source_id INTEGER,
                transfer_id INTEGER REFERENCES fund_transfers(id) ON DELETE SET NULL,
                is_transfer BOOLEAN DEFAULT 0,
                transfer_direction VARCHAR(10),
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entry_number, business_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_cash_book_entries_date ON cash_book_entries(entry_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_cash_book_entries_account ON cash_book_entries(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_cash_book_entries_type ON cash_book_entries(entry_type)")
        print("  ✓ Created cash_book_entries table")
    
    # ==================== ADD BAD_DEBT_ID TO LEDGER_ENTRIES ====================
    print("\n[13] Adding bad_debt_id to ledger_entries table...")
    add_column_if_not_exists('ledger_entries', 'bad_debt_id', 'INTEGER REFERENCES bad_debts(id) ON DELETE SET NULL')
    
    # ==================== CREATE BAD_DEBTS TABLE ====================
    print("\n[14] Checking bad_debts table...")
    if not table_exists('bad_debts'):
        print("  Creating bad_debts table...")
        cursor.execute("""
            CREATE TABLE bad_debts (
                id INTEGER PRIMARY KEY,
                bad_debt_number VARCHAR(50) NOT NULL,
                write_off_date DATE NOT NULL,
                amount NUMERIC(15, 2) NOT NULL,
                reason TEXT,
                status VARCHAR(20) DEFAULT 'written_off',
                sales_invoice_id INTEGER REFERENCES sales_invoices(id) ON DELETE SET NULL,
                customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
                recovered_amount NUMERIC(15, 2) DEFAULT 0.00,
                recovery_date DATE,
                bad_debt_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                approved_at DATETIME,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bad_debt_number, business_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_bad_debts_business_id ON bad_debts(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_bad_debts_customer_id ON bad_debts(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_bad_debts_date ON bad_debts(write_off_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_bad_debts_status ON bad_debts(status)")
        print("  ✓ Created bad_debts table")
    else:
        print("  bad_debts table already exists")
    
    # ==================== ADD BAD DEBT EXPENSE ACCOUNT ====================
    print("\n[15] Checking for Bad Debt Expense account...")
    # Get all businesses
    cursor.execute("SELECT id FROM businesses")
    businesses = cursor.fetchall()

    for business in businesses:
        business_id = business[0]
        # Check if Bad Debt Expense account exists
        cursor.execute("""
            SELECT id FROM accounts 
            WHERE business_id = ? AND name = 'Bad Debt Expense'
        """, (business_id,))
        if not cursor.fetchone():
            # Get max code for expense accounts
            cursor.execute("""
                SELECT MAX(CAST(code AS INTEGER)) FROM accounts 
                WHERE business_id = ? AND type = 'EXPENSE'
            """, (business_id,))
            max_code = cursor.fetchone()[0]
            next_code = (max_code or 6800) + 10

            # Create Bad Debt Expense account
            cursor.execute("""
                INSERT INTO accounts (name, code, type, description, is_system_account, is_active, business_id, created_at)
                VALUES ('Bad Debt Expense', ?, 'EXPENSE', 'Account for recording uncollectible receivables written off as bad debts', 0, 1, ?, datetime('now'))
            """, (str(next_code), business_id))
            print(f"  ✓ Created Bad Debt Expense account for business {business_id}")

    # ==================== ADD OPENING BALANCE EQUITY ACCOUNT ====================
    print("\n[16] Checking for Opening Balance Equity account...")
    for business in businesses:
        business_id = business[0]
        # Check if Opening Balance Equity account exists
        cursor.execute("""
            SELECT id FROM accounts
            WHERE business_id = ? AND name = 'Opening Balance Equity'
        """, (business_id,))
        if not cursor.fetchone():
            # Create Opening Balance Equity account
            cursor.execute("""
                INSERT INTO accounts (name, code, type, description, is_system_account, is_active, business_id, created_at)
                VALUES ('Opening Balance Equity', '3200', 'EQUITY', 'Account for recording opening balances when setting up the system', 1, 1, ?, datetime('now'))
            """, (business_id,))
            print(f"  ✓ Created Opening Balance Equity account for business {business_id}")

    # ==================== FIX ACCOUNT TYPE ENUM VALUES ====================
    print("\n[17] Fixing account type enum values...")
    type_fixes = [
        ('Asset', 'ASSET'),
        ('Liability', 'LIABILITY'),
        ('Equity', 'EQUITY'),
        ('Revenue', 'REVENUE'),
        ('Expense', 'EXPENSE'),
    ]
    for old_val, new_val in type_fixes:
        try:
            cursor.execute(f"UPDATE accounts SET type = ? WHERE type = ?", (new_val, old_val))
            if cursor.rowcount > 0:
                print(f"  Fixed {cursor.rowcount} accounts type from '{old_val}' to '{new_val}'")
        except Exception as e:
            print(f"  Note: Could not fix account type {old_val}: {e}")

    # ==================== FIX NULL created_at IN ACCOUNTS ====================
    print("\n[18] Fixing NULL created_at in accounts...")
    try:
        cursor.execute("""
            UPDATE accounts SET created_at = datetime('now')
            WHERE created_at IS NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Fixed {cursor.rowcount} accounts with NULL created_at")
    except Exception as e:
        print(f"  Note: Could not fix accounts created_at: {e}")

    # Check and create audit_logs table if missing
    if not table_exists('audit_logs'):
        print("  Creating audit_logs table...")
        cursor.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                username VARCHAR(100),
                ip_address VARCHAR(50),
                user_agent VARCHAR(500),
                action VARCHAR(50) NOT NULL,
                resource_type VARCHAR(100) NOT NULL,
                resource_id INTEGER,
                business_id INTEGER REFERENCES businesses(id) ON DELETE SET NULL,
                branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
                description TEXT,
                old_values TEXT,
                new_values TEXT,
                request_method VARCHAR(10),
                request_path VARCHAR(500),
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT
            )
        """)
        # Create indexes for audit_logs
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_business_id ON audit_logs(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
        print("  ✓ Created audit_logs table")
    
    # ==================== FIX BANK ACCOUNTS WITHOUT COA ====================
    print("\n[14] Fixing bank accounts without chart_of_account_id...")
    
    # Get bank accounts without chart_of_account_id
    try:
        cursor.execute("""
            SELECT ba.id, ba.account_name, ba.bank_name, ba.business_id, ba.opening_balance
            FROM bank_accounts ba
            WHERE ba.chart_of_account_id IS NULL
        """)
        bank_accounts_without_coa = cursor.fetchall()
        
        if bank_accounts_without_coa:
            print(f"  Found {len(bank_accounts_without_coa)} bank accounts without COA link")
            
            for ba_id, ba_name, ba_bank, business_id, opening_balance in bank_accounts_without_coa:
                # Generate a unique code for the new account
                cursor.execute("""
                    SELECT code FROM accounts 
                    WHERE business_id = ? AND type = 'Asset'
                    ORDER BY code DESC LIMIT 1
                """, (business_id,))
                last_account = cursor.fetchone()
                
                if last_account and last_account[0]:
                    try:
                        # Try to increment the code
                        code_num = int(last_account[0].replace("1", "").lstrip("0") or "0") + 1
                        new_code = f"1{code_num:03d}"
                    except ValueError:
                        new_code = "1101"
                else:
                    new_code = "1101"
                
                # Ensure code is unique
                cursor.execute("""
                    SELECT id FROM accounts 
                    WHERE business_id = ? AND code = ?
                """, (business_id, new_code))
                if cursor.fetchone():
                    # Find next available code
                    for i in range(1, 1000):
                        test_code = f"1{i:03d}"
                        cursor.execute("""
                            SELECT id FROM accounts 
                            WHERE business_id = ? AND code = ?
                        """, (business_id, test_code))
                        if not cursor.fetchone():
                            new_code = test_code
                            break
                
                # Create new COA account for this bank account
                cursor.execute("""
                    INSERT INTO accounts (name, code, type, description, is_active, business_id, created_at)
                    VALUES (?, ?, 'Asset', ?, 1, ?, datetime('now'))
                """, (f"Bank - {ba_name}", new_code, f"Bank account: {ba_bank or ba_name}", business_id))
                
                new_coa_id = cursor.lastrowid
                print(f"  Created COA account '{new_code} - Bank - {ba_name}' for bank account {ba_id}")
                
                # Update bank account with the new COA ID
                cursor.execute("""
                    UPDATE bank_accounts 
                    SET chart_of_account_id = ?
                    WHERE id = ?
                """, (new_coa_id, ba_id))
                
                # Create ledger entry for opening balance if exists
                if opening_balance and float(opening_balance) > 0:
                    # Find or create Opening Balance Equity account
                    cursor.execute("""
                        SELECT id FROM accounts 
                        WHERE business_id = ? AND name = 'Opening Balance Equity'
                    """, (business_id,))
                    equity_account = cursor.fetchone()
                    
                    if not equity_account:
                        # Find any equity account
                        cursor.execute("""
                            SELECT id FROM accounts 
                            WHERE business_id = ? AND type = 'Equity'
                            LIMIT 1
                        """, (business_id,))
                        equity_account = cursor.fetchone()
                    
                    if not equity_account:
                        # Create Opening Balance Equity account
                        cursor.execute("""
                            INSERT INTO accounts (name, code, type, is_active, business_id, created_at)
                            VALUES ('Opening Balance Equity', '3200', 'Equity', 1, ?, datetime('now'))
                        """, (business_id,))
                        equity_id = cursor.lastrowid
                    else:
                        equity_id = equity_account[0]
                    
                    # Create journal voucher
                    cursor.execute("""
                        SELECT voucher_number FROM journal_vouchers 
                        WHERE business_id = ?
                        ORDER BY id DESC LIMIT 1
                    """, (business_id,))
                    last_voucher = cursor.fetchone()
                    
                    if last_voucher:
                        try:
                            num = int(last_voucher[0].replace("JV-", "")) + 1
                            voucher_number = f"JV-{num:05d}"
                        except ValueError:
                            voucher_number = "JV-00001"
                    else:
                        voucher_number = "JV-00001"
                    
                    # Get branch_id for this bank account
                    cursor.execute("SELECT branch_id FROM bank_accounts WHERE id = ?", (ba_id,))
                    branch_row = cursor.fetchone()
                    branch_id = branch_row[0] if branch_row else None
                    
                    cursor.execute("""
                        INSERT INTO journal_vouchers (voucher_number, transaction_date, description, reference, branch_id, business_id, is_posted, created_at)
                        VALUES (?, date('now'), ?, ?, ?, ?, 1, datetime('now'))
                    """, (voucher_number, f"Opening Balance - {ba_name}", f"BANK-{ba_id}", branch_id, business_id))
                    
                    voucher_id = cursor.lastrowid
                    
                    # Debit entry (bank)
                    cursor.execute("""
                        INSERT INTO ledger_entries (transaction_date, description, debit, credit, account_id, bank_account_id, journal_voucher_id, branch_id, created_at)
                        VALUES (date('now'), ?, ?, 0, ?, ?, ?, ?, datetime('now'))
                    """, (f"Opening Balance - {ba_name}", opening_balance, new_coa_id, ba_id, voucher_id, branch_id))
                    
                    # Credit entry (equity)
                    cursor.execute("""
                        INSERT INTO ledger_entries (transaction_date, description, debit, credit, account_id, journal_voucher_id, branch_id, created_at)
                        VALUES (date('now'), ?, 0, ?, ?, ?, ?, datetime('now'))
                    """, (f"Opening Balance - {ba_name}", opening_balance, equity_id, voucher_id, branch_id))
                    
                    print(f"    Created opening balance entry: {opening_balance}")
        else:
            print("  All bank accounts have COA link")
    except Exception as e:
        print(f"  Note: Could not fix bank accounts COA: {e}")
    
    # ==================== UPDATE FUND TRANSFERS COA LINKS ====================
    print("\n[15] Updating fund_transfers COA links...")
    
    try:
        # Update fund_transfers where from_coa_id or to_coa_id is NULL
        # This uses the chart_of_account_id from the bank_accounts table
        cursor.execute("""
            UPDATE fund_transfers
            SET from_coa_id = (
                SELECT ba.chart_of_account_id 
                FROM bank_accounts ba 
                WHERE ba.id = fund_transfers.from_account_id OR ba.chart_of_account_id = fund_transfers.from_account_id
            ),
            to_coa_id = (
                SELECT ba.chart_of_account_id 
                FROM bank_accounts ba 
                WHERE ba.id = fund_transfers.to_account_id OR ba.chart_of_account_id = fund_transfers.to_account_id
            )
            WHERE from_coa_id IS NULL OR to_coa_id IS NULL
        """)
        if cursor.rowcount > 0:
            print(f"  Updated {cursor.rowcount} fund_transfers with COA links")
    except Exception as e:
        print(f"  Note: Could not update fund_transfers COA: {e}")
    
    # ==================== SYNC BANK BALANCES WITH CASHBOOK ====================
    print("\n[16] Syncing bank balances with cashbook entries...")
    
    try:
        # Get all bank accounts with their COA IDs
        cursor.execute("""
            SELECT id, chart_of_account_id, account_name
            FROM bank_accounts
            WHERE chart_of_account_id IS NOT NULL
        """)
        bank_accounts = cursor.fetchall()
        
        for ba_id, coa_id, ba_name in bank_accounts:
            # Calculate balance from cashbook entries
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN entry_type = 'receipt' THEN amount ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN entry_type = 'payment' THEN amount ELSE 0 END), 0) +
                    COALESCE(SUM(CASE WHEN is_transfer = 1 AND transfer_direction = 'in' THEN amount ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN is_transfer = 1 AND transfer_direction = 'out' THEN amount ELSE 0 END), 0)
                FROM cash_book_entries
                WHERE account_id = ?
            """, (coa_id,))
            result = cursor.fetchone()
            calculated_balance = result[0] if result and result[0] else 0
            
            # Update the bank account's current_balance to match
            cursor.execute("""
                UPDATE bank_accounts 
                SET current_balance = ?
                WHERE id = ? AND chart_of_account_id = ?
            """, (calculated_balance, ba_id, coa_id))
            
            if cursor.rowcount > 0:
                print(f"  Synced balance for '{ba_name}': {calculated_balance}")
    except Exception as e:
        print(f"  Note: Could not sync bank balances: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    migrate_database()
