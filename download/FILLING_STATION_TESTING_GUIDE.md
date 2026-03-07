# Filling Station ERP System - Complete Testing Guide

## Overview
This guide will walk you through testing all features of the ERP system using a **filling station (petrol station)** business scenario.

---

## PART 1: FRESH START SETUP

### Step 1: Delete Existing Database
```bash
cd /mnt/c/Users/USER/desktop/booklet_/backend
rm -f erp.db
python migrate_db.py
```

### Step 2: Start the Servers
```bash
# Terminal 1 - Backend
cd /mnt/c/Users/USER/desktop/booklet_/backend
python run.py

# Terminal 2 - Frontend  
cd /mnt/c/Users/USER/desktop/booklet_/frontend
python run.py
```

### Step 3: Access the Application
- Open browser: `http://localhost:5000`
- You should see the login page

---

## PART 2: INITIAL BUSINESS SETUP

### Test 2.1: User Registration
1. Click **"Register"** on the login page
2. Fill in the form:
   - **Business Name:** `SpeedWay Filling Station`
   - **Business Address:** `123 Highway Road, Lagos`
   - **Business Phone:** `+234-801-234-5678`
   - **Business Email:** `info@speedway.ng`
   - **Tax ID:** `TIN-2024-001234`
   - **VAT Registered:** Check the box
   - **VAT Rate:** `7.5` (%)
   - **Username:** `admin`
   - **Email:** `admin@speedway.ng`
   - **Password:** `Admin@123`
   - **Full Name:** `John Manager`

3. Click **"Register"**
4. **Expected:** Successfully registered, redirected to dashboard

---

## PART 3: CHART OF ACCOUNTS SETUP

### Test 3.1: View Default Accounts
1. Go to **Settings → Chart of Accounts**
2. **Expected:** See pre-created accounts organized by type:
   - **Assets:** Cash, Bank Accounts, Accounts Receivable, Inventory
   - **Liabilities:** Accounts Payable, VAT Payable
   - **Equity:** Owner's Equity, Retained Earnings
   - **Revenue:** Sales Revenue
   - **Expenses:** Cost of Goods Sold, Operating Expenses

### Test 3.2: Add Filling Station Specific Accounts
Navigate to **Settings → Chart of Accounts → Add Account**

Add these accounts:

| Account Name | Code | Type | Description |
|-------------|------|------|-------------|
| Petrol Inventory | 1300 | Asset | Petrol/Fuel stock |
| Diesel Inventory | 1310 | Asset | Diesel stock |
| Kerosene Inventory | 1320 | Asset | Kerosene stock |
| Pump Sales - Petrol | 4010 | Revenue | Sales from petrol pumps |
| Pump Sales - Diesel | 4020 | Revenue | Sales from diesel pumps |
| Shop Sales | 4030 | Revenue | Convenience store sales |
| Cost of Sales - Petrol | 5010 | Expense | Cost of petrol sold |
| Cost of Sales - Diesel | 5020 | Expense | Cost of diesel sold |
| Fuel Delivery Expenses | 6010 | Expense | Transport costs for fuel delivery |
| Pump Maintenance | 6020 | Expense | Pump servicing and repairs |
| Station Security | 6030 | Expense | Security services |
| Generator Expenses | 6040 | Expense | Generator fuel and maintenance |
| Bad Debt Expense | 6900 | Expense | Uncollectible receivables |

---

## PART 4: CUSTOMERS SETUP

### Test 4.1: Add Customers
Go to **CRM → Customers → Add Customer**

#### Customer 1: Corporate Account
| Field | Value |
|-------|-------|
| Name | `ABC Transport Company` |
| Email | `accounts@abctransport.ng` |
| Phone | `+234-802-111-2222` |
| Address | `45 Industrial Layout, Ikeja, Lagos` |
| Tax ID | `TIN-ABC-001` |
| Credit Limit | `5,000,000.00` |

#### Customer 2: Corporate Account
| Field | Value |
|-------|-------|
| Name | `Lagos City Council` |
| Email | `procurement@lagoscouncil.gov.ng` |
| Phone | `+234-803-222-3333` |
| Address | `City Hall, Lagos Island` |
| Tax ID | `TIN-LCC-002` |
| Credit Limit | `10,000,000.00` |

#### Customer 3: Individual/Walk-in
| Field | Value |
|-------|-------|
| Name | `Walk-in Customers` |
| Email | `walkin@speedway.ng` |
| Phone | `N/A` |
| Address | `Various` |
| Credit Limit | `0.00` |

#### Customer 4: Test Bad Debt
| Field | Value |
|-------|-------|
| Name | `XYZ Logistics (Defaulted)` |
| Email | `info@xyzlogistics.ng` |
| Phone | `+234-804-333-4444` |
| Address | `78 Commercial Avenue, Yaba` |
| Credit Limit | `500,000.00` |

---

## PART 5: VENDORS/SUPPLIERS SETUP

### Test 5.1: Add Vendors
Go to **CRM → Vendors → Add Vendor**

#### Vendor 1: Fuel Supplier
| Field | Value |
|-------|-------|
| Name | `NNPC Petroleum Depot` |
| Email | `supply@nnpcdepot.ng` |
| Phone | `+234-805-444-5555` |
| Address | `Apapa Refinery Road, Lagos` |
| Tax ID | `TIN-NNPC-001` |

#### Vendor 2: Lubricants Supplier
| Field | Value |
|-------|-------|
| Name | `Total Lubricants Nigeria` |
| Email | `orders@totallub.ng` |
| Phone | `+234-806-555-6666` |
| Address | `15 Marina, Lagos` |
| Tax ID | `TIN-TOTAL-002` |

#### Vendor 3: Shop Supplier
| Field | Value |
|-------|-------|
| Name | `Global Supplies Ltd` |
| Email | `sales@globalsupplies.ng` |
| Phone | `+234-807-666-7777` |
| Address | `23 Trade Fair Complex, Lagos` |
| Tax ID | `TIN-GLOBAL-003` |

#### Vendor 4: Services Provider
| Field | Value |
|-------|-------|
| Name | `PumpTech Services` |
| Email | `service@pumptech.ng` |
| Phone | `+234-808-777-8888` |
| Address | `88 Service Road, Ikeja` |
| Tax ID | `TIN-PUMP-004` |

---

## PART 6: PRODUCTS/INVENTORY SETUP

### Test 6.1: Add Product Categories
Go to **Inventory → Categories → Add Category**

| Category Name | Description |
|--------------|-------------|
| Fuel Products | Petrol, Diesel, Kerosene |
| Lubricants | Engine oils and lubricants |
| Shop Items | Convenience store products |
| Services | Services offered |

### Test 6.2: Add Products
Go to **Inventory → Products → Add Product**

#### Fuel Products

| Field | Product 1 | Product 2 | Product 3 |
|-------|-----------|-----------|-----------|
| Name | `Premium Motor Spirit (Petrol)` | `Automotive Gas Oil (Diesel)` | `Dual Purpose Kerosene` |
| SKU | `PMS-001` | `AGO-001` | `DPK-001` |
| Category | Fuel Products | Fuel Products | Fuel Products |
| Unit | Litres | Litres | Litres |
| Purchase Price | `650.00` | `720.00` | `450.00` |
| Sales Price | `750.00` | `850.00` | `550.00` |
| Opening Stock | `50000` | `30000` | `10000` |
| Reorder Level | `15000` | `10000` | `3000` |

#### Lubricants

| Field | Product 4 | Product 5 |
|-------|-----------|-----------|
| Name | `Engine Oil 20W-50` | `Gear Oil 90` |
| SKU | `OIL-001` | `OIL-002` |
| Category | Lubricants | Lubricants |
| Unit | Litres | Litres |
| Purchase Price | `2500.00` | `3000.00` |
| Sales Price | `3500.00` | `4200.00` |
| Opening Stock | `200` | `100` |
| Reorder Level | `50` | `30` |

#### Shop Items

| Field | Product 6 | Product 7 | Product 8 |
|-------|-----------|-----------|-----------|
| Name | `Bottled Water` | `Soft Drinks` | `Car Freshener` |
| SKU | `SHOP-001` | `SHOP-002` | `SHOP-003` |
| Category | Shop Items | Shop Items | Shop Items |
| Unit | Pieces | Pieces | Pieces |
| Purchase Price | `80.00` | `100.00` | `500.00` |
| Sales Price | `150.00` | `200.00` | `800.00` |
| Opening Stock | `500` | `300` | `100` |
| Reorder Level | `100` | `50` | `20` |

---

## PART 7: BANK ACCOUNTS SETUP

### Test 7.1: Add Bank Accounts
Go to **Banking → Bank Accounts → Add Account**

#### Bank Account 1
| Field | Value |
|-------|-------|
| Account Name | `SpeedWay Filling Station - Main` |
| Bank Name | `First Bank of Nigeria` |
| Account Number | `2034567890` |
| Currency | `NGN` |
| Opening Balance | `5000000.00` |

#### Bank Account 2
| Field | Value |
|-------|-------|
| Account Name | `SpeedWay Filling Station - Operations` |
| Bank Name | `GTBank` |
| Account Number | `0123456789` |
| Currency | `NGN` |
| Opening Balance | `2000000.00` |

#### Cash Account (Petty Cash)
| Field | Value |
|-------|-------|
| Account Name | `Petty Cash - Station` |
| Bank Name | `N/A (Cash)` |
| Account Number | `N/A` |
| Currency | `NGN` |
| Opening Balance | `100000.00` |

---

## PART 8: EMPLOYEES & PAYROLL SETUP

### Test 8.1: Add Employees
Go to **HR → Employees → Add Employee**

#### Employee 1: Station Manager
| Field | Value |
|-------|-------|
| Full Name | `Adekunle Johnson` |
| Email | `adekunle@speedway.ng` |
| Phone | `+234-809-888-0001` |
| Address | `15 Staff Quarters, Lagos` |
| Hire Date | `2023-01-15` |
| Department | `Management` |
| Position | `Station Manager` |

#### Employee 2: Pump Attendant
| Field | Value |
|-------|-------|
| Full Name | `Ibrahim Musa` |
| Email | `ibrahim@speedway.ng` |
| Phone | `+234-809-888-0002` |
| Address | `22 Yaba Road, Lagos` |
| Hire Date | `2023-03-01` |
| Department | `Operations` |
| Position | `Pump Attendant` |

#### Employee 3: Pump Attendant
| Field | Value |
|-------|-------|
| Full Name | `Chioma Okafor` |
| Email | `chioma@speedway.ng` |
| Phone | `+234-809-888-0003` |
| Address | `45 Adeola Street, Lagos` |
| Hire Date | `2023-03-01` |
| Department | `Operations` |
| Position | `Pump Attendant` |

#### Employee 4: Shop Attendant
| Field | Value |
|-------|-------|
| Full Name | `Fatima Abubakar` |
| Email | `fatima@speedway.ng` |
| Phone | `+234-809-888-0004` |
| Address | `10 Maitama Street, Lagos` |
| Hire Date | `2023-06-15` |
| Department | `Retail` |
| Position | `Shop Attendant` |

#### Employee 5: Security Guard
| Field | Value |
|-------|-------|
| Full Name | `Emmanuel Peters` |
| Email | `emmanuel@speedway.ng` |
| Phone | `+234-809-888-0005` |
| Address | `8 Guards Quarters, Lagos` |
| Hire Date | `2023-04-01` |
| Department | `Security` |
| Position | `Security Guard` |

### Test 8.2: Configure Payroll
For each employee, click **Configure Payroll**:

#### Station Manager Payroll
| Field | Value |
|-------|-------|
| Gross Salary | `250000.00` |
| Pay Frequency | `Monthly` |
| PAYE Rate | `7` |
| Pension Employee Rate | `8` |
| Pension Employer Rate | `10` |
| Other Allowances | `25000.00` |

#### Pump Attendants Payroll (Same for both)
| Field | Value |
|-------|-------|
| Gross Salary | `75000.00` |
| Pay Frequency | `Monthly` |
| PAYE Rate | `5` |
| Pension Employee Rate | `8` |
| Pension Employer Rate | `10` |
| Other Allowances | `5000.00` |

#### Shop Attendant Payroll
| Field | Value |
|-------|-------|
| Gross Salary | `65000.00` |
| Pay Frequency | `Monthly` |
| PAYE Rate | `5` |
| Pension Employee Rate | `8` |
| Pension Employer Rate | `10` |

#### Security Guard Payroll
| Field | Value |
|-------|-------|
| Gross Salary | `55000.00` |
| Pay Frequency | `Monthly` |
| PAYE Rate | `0` |
| Pension Employee Rate | `8` |
| Pension Employer Rate | `10` |

---

## PART 9: FISCAL YEAR SETUP

### Test 9.1: Create Fiscal Year
Go to **Settings → Fiscal Year → Add Fiscal Year**

| Field | Value |
|-------|-------|
| Name | `FY 2024` |
| Start Date | `2024-01-01` |
| End Date | `2024-12-31` |
| Period Type | `Monthly` |
| Auto-create Periods | Check the box |

**Expected:** Creates 12 monthly periods + 1 adjustment period

---

## PART 10: PURCHASES & INVENTORY TESTING

### Test 10.1: Record Fuel Purchase
Go to **Purchases → Bills → Create Bill**

#### Purchase Bill 1: Fuel from NNPC
| Field | Value |
|-------|-------|
| Vendor | `NNPC Petroleum Depot` |
| Bill Date | `2024-01-05` |
| Due Date | `2024-01-20` |
| Reference | `PO-2024-001` |
| Notes | `Monthly fuel supply` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `40000` | `650.00` |
| Automotive Gas Oil (Diesel) | `20000` | `720.00` |
| Dual Purpose Kerosene | `5000` | `450.00` |

**Expected Totals:**
- Sub-total: 41,450,000.00
- VAT (7.5%): 3,108,750.00
- **Total: 44,558,750.00**

### Test 10.2: Pay Vendor
On the purchase bill detail page:

1. Click **Record Payment**
2. Fill in:
   - Payment Date: `2024-01-10`
   - Amount: `44558750.00`
   - Payment Account: `First Bank - Main`
   - Reference: `BANK-TRF-001`

**Expected:** 
- Bill status changes to "Paid"
- Bank account balance decreases
- Ledger entries created

### Test 10.3: Record Lubricants Purchase
Create another purchase bill:

| Field | Value |
|-------|-------|
| Vendor | `Total Lubricants Nigeria` |
| Bill Date | `2024-01-08` |
| Due Date | `2024-01-25` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Engine Oil 20W-50 | `100` | `2500.00` |
| Gear Oil 90 | `50` | `3000.00` |

**Expected Totals:**
- Sub-total: 400,000.00
- VAT (7.5%): 30,000.00
- **Total: 430,000.00**

### Test 10.4: Partial Payment Test
Record partial payment of `200000.00` from GTBank Operations account.

**Expected:**
- Bill status changes to "Partial"
- Remaining balance: 230,000.00

---

## PART 11: SALES TESTING

### Test 11.1: Walk-in Cash Sales
Go to **Sales → Invoices → Create Invoice**

#### Invoice 1: Daily Walk-in Sales
| Field | Value |
|-------|-------|
| Customer | `Walk-in Customers` |
| Invoice Date | `2024-01-15` |
| Due Date | `2024-01-15` (Same day for cash) |
| Notes | `Daily pump sales - Jan 15` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `5000` | `750.00` |
| Automotive Gas Oil (Diesel) | `2000` | `850.00` |
| Engine Oil 20W-50 | `20` | `3500.00` |

**Expected Totals:**
- Sub-total: 5,570,000.00
- VAT (7.5%): 417,750.00
- **Total: 5,987,750.00**

### Test 11.2: Record Full Payment
1. On invoice detail, click **Record Payment**
2. Amount: `5987750.00`
3. Payment Account: `Petty Cash - Station`
4. Payment Date: `2024-01-15`

**Expected:**
- Invoice status: "Paid"
- Stock decreases
- Revenue recorded

### Test 11.3: Corporate Credit Sales
Create invoice for ABC Transport:

| Field | Value |
|-------|-------|
| Customer | `ABC Transport Company` |
| Invoice Date | `2024-01-16` |
| Due Date | `2024-02-16` (30 days credit) |
| Notes | `Monthly fuel supply contract` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `15000` | `720.00` (Discounted rate) |
| Automotive Gas Oil (Diesel) | `8000` | `820.00` (Discounted rate) |

**Expected Totals:**
- Sub-total: 17,560,000.00
- VAT (7.5%): 1,317,000.00
- **Total: 18,877,000.00**

### Test 11.4: Partial Payment from Corporate Customer
Record payment of `10000000.00` from First Bank Main.

**Expected:**
- Invoice status: "Partial"
- Remaining balance: 8,877,000.00

### Test 11.5: Government Customer Invoice
Create invoice for Lagos City Council:

| Field | Value |
|-------|-------|
| Customer | `Lagos City Council` |
| Invoice Date | `2024-01-20` |
| Due Date | `2024-03-20` (60 days credit) |
| Notes | `Government fleet refueling` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `20000` | `730.00` |
| Automotive Gas Oil (Diesel) | `10000` | `830.00` |

**Expected Totals:**
- Sub-total: 22,900,000.00
- VAT (7.5%): 1,717,500.00
- **Total: 24,617,500.00**

---

## PART 12: CUSTOMER PREPAYMENT/ADVANCE TESTING

### Test 12.1: Fund Customer Account
Go to **Cashbook → Fund Customer Account**

| Field | Value |
|-------|-------|
| Customer | `ABC Transport Company` |
| Amount | `5000000.00` |
| Payment Account | `First Bank - Main` |
| Date | `2024-01-25` |
| Description | `Advance payment for February supply` |

**Expected:**
- Customer's account_balance increases to 5,000,000.00
- Bank balance decreases

### Test 12.2: Verify Auto-Deduction
Create new invoice for ABC Transport:

| Field | Value |
|-------|-------|
| Customer | `ABC Transport Company` |
| Invoice Date | `2024-02-01` |
| Due Date | `2024-02-28` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `8000` | `720.00` |

**Expected Totals:**
- Total: 6,192,000.00 (including VAT)
- Auto-deduct 5,000,000.00 from prepaid balance
- Remaining balance: 1,192,000.00
- Invoice status: "Partial"

---

## PART 13: CREDIT NOTE TESTING (Sales Return)

### Test 13.1: Create Credit Note
Go to Sales → Invoices → Open invoice for ABC Transport → Create Credit Note

| Field | Value |
|-------|-------|
| Credit Note Date | `2024-02-05` |
| Reason | `Quality complaint - contaminated fuel` |

**Items to Return:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `500` | `720.00` |

**Expected:**
- Credit note created with number `CN-00001`
- Stock increases
- Customer balance reduced

### Test 13.2: Apply Credit Note
1. Go to Credit Notes list
2. Click on the credit note
3. Click **Apply to Invoice**

**Expected:**
- Credit note status: "Applied"
- Invoice balance reduced by credit note amount

---

## PART 14: BAD DEBT WRITE-OFF TESTING

### Test 14.1: Create Invoice for Defaulted Customer
Create invoice for XYZ Logistics:

| Field | Value |
|-------|-------|
| Customer | `XYZ Logistics (Defaulted)` |
| Invoice Date | `2024-01-10` |
| Due Date | `2024-02-10` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `3000` | `750.00` |
| Automotive Gas Oil (Diesel) | `2000` | `850.00` |

**Expected Total:** 4,337,500.00 (including VAT)

### Test 14.2: Write Off as Bad Debt
1. Go to invoice detail for XYZ Logistics
2. In the Write Off panel:
   - Write Off Date: `2024-06-01`
   - Reason: `Customer declared bankruptcy - unable to recover`
3. Click **Write Off as Bad Debt**

**Expected:**
- Invoice status: "Written Off"
- Bad debt record created (BD-00001)
- Ledger entries: Debit Bad Debt Expense, Credit Accounts Receivable

### Test 14.3: View Bad Debt Records
Go to **Sales → Bad Debts** (or API: `GET /sales/bad-debts`)

**Expected:** See the written off debt with all details

---

## PART 15: VENDOR PREPAYMENT TESTING

### Test 15.1: Fund Vendor Account
Go to **Cashbook → Fund Vendor Account**

| Field | Value |
|-------|-------|
| Vendor | `NNPC Petroleum Depot` |
| Amount | `10000000.00` |
| Payment Account | `First Bank - Main` |
| Date | `2024-02-01` |
| Description | `Prepayment for next delivery` |

**Expected:**
- Vendor's account_balance increases
- Bank balance decreases

### Test 15.2: Create Purchase Bill (Auto-Deduct)
Create new purchase bill from NNPC:

| Field | Value |
|-------|-------|
| Vendor | `NNPC Petroleum Depot` |
| Bill Date | `2024-02-05` |
| Due Date | `2024-02-20` |

**Items:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `10000` | `650.00` |

**Expected Total:** 6,987,500.00 (including VAT)
- Auto-deduct from vendor prepaid balance
- Remaining vendor balance: 3,012,500.00

---

## PART 16: DEBIT NOTE TESTING (Purchase Return)

### Test 16.1: Create Debit Note
Go to Purchases → Bills → Open NNPC bill → Create Debit Note

| Field | Value |
|-------|-------|
| Debit Note Date | `2024-02-10` |
| Reason | `Short supply - 500 litres missing` |

**Items to Return:**
| Product | Quantity | Price |
|---------|----------|-------|
| Premium Motor Spirit (Petrol) | `500` | `650.00` |

**Expected:**
- Debit note created with number `DN-00001`
- Stock decreases
- Vendor balance adjusted

---

## PART 17: EXPENSES TESTING

### Test 17.1: Record Operating Expenses
Go to **Expenses → Create Expense**

#### Expense 1: Pump Maintenance
| Field | Value |
|-------|-------|
| Expense Date | `2024-01-20` |
| Category | `Pump Maintenance` |
| Description | `Monthly pump calibration and servicing` |
| Sub Total | `150000.00` |
| VAT | `11250.00` |
| Total | `161250.00` |
| Vendor | `PumpTech Services` |
| Paid From | `Petty Cash - Station` |

#### Expense 2: Security Services
| Field | Value |
|-------|-------|
| Expense Date | `2024-01-31` |
| Category | `Station Security` |
| Description | `January 2024 security services` |
| Sub Total | `80000.00` |
| VAT | `6000.00` |
| Total | `86000.00` |
| Vendor | (Leave blank - cash payment) |
| Paid From | `Petty Cash - Station` |

#### Expense 3: Generator Expenses
| Field | Value |
|-------|-------|
| Expense Date | `2024-01-25` |
| Category | `Generator Expenses` |
| Description | `Generator diesel and servicing` |
| Sub Total | `45000.00` |
| VAT | `3375.00` |
| Total | `48375.00` |
| Paid From | `Petty Cash - Station` |

---

## PART 18: OTHER INCOME TESTING

### Test 18.1: Record Other Income
Go to **Other Income → Create Income**

| Field | Value |
|-------|-------|
| Income Date | `2024-01-31` |
| Category | `Rent Income` |
| Description | `Rent from ATM machine space` |
| Sub Total | `50000.00` |
| VAT | `3750.00` |
| Total | `53750.00` |
| Received In | `First Bank - Main` |

---

## PART 19: FUND TRANSFER TESTING

### Test 19.1: Transfer Between Bank Accounts
Go to **Banking → Fund Transfers → Create Transfer**

| Field | Value |
|-------|-------|
| Transfer Date | `2024-01-25` |
| From Account | `First Bank - Main` |
| To Account | `Petty Cash - Station` |
| Amount | `500000.00` |
| Description | `Petty cash replenishment` |
| Reference | `TRF-001` |

**Expected:**
- First Bank balance decreases
- Petty Cash balance increases
- Ledger entries created

---

## PART 20: CASHBOOK TESTING

### Test 20.1: Manual Cash Book Entry
Go to **Cashbook → Manual Entry**

#### Receipt Entry
| Field | Value |
|-------|-------|
| Entry Date | `2024-01-31` |
| Entry Type | `Receipt` |
| Account | `First Bank - Main` |
| Amount | `100000.00` |
| Description | `Promotional rebate from supplier` |
| Payee/Payer | `Total Lubricants Nigeria` |

#### Payment Entry
| Field | Value |
|-------|-------|
| Entry Date | `2024-01-31` |
| Entry Type | `Payment` |
| Account | `Petty Cash - Station` |
| Amount | `25000.00` |
| Description | `Station cleaning supplies` |
| Payee/Payer | `Local Supplier` |

---

## PART 21: JOURNAL VOUCHER TESTING

### Test 21.1: Manual Journal Entry
Go to **Accounting → Journal Vouchers → Create Voucher**

| Field | Value |
|-------|-------|
| Transaction Date | `2024-01-31` |
| Description | `Year-end adjustment for accrued expenses` |
| Reference | `ADJ-2024-001` |

**Lines:**
| Account | Debit | Credit |
|---------|-------|--------|
| Operating Expenses | `50000.00` | |
| Accounts Payable | | `50000.00` |

**Expected:**
- Voucher created with number `JV-00001`
- Can post to make permanent

---

## PART 22: PAYROLL TESTING

### Test 22.1: Generate Payslips
Go to **HR → Payroll → Generate Payslips**

| Field | Value |
|-------|-------|
| Pay Period Start | `2024-01-01` |
| Pay Period End | `2024-01-31` |

Click **Generate**

**Expected:** 5 payslips created (one for each employee)

### Test 22.2: Review Payslip Details
Click on each payslip to verify:
- Basic salary correct
- PAYE calculated correctly
- Pension deductions correct
- Net salary = Gross - Total Deductions

### Test 22.3: Process Payroll Payment
1. Select all payslips
2. Click **Process Payment**
3. Select Payment Account: `First Bank - Main`
4. Payment Date: `2024-01-31`

**Expected:**
- Payslips marked as "Paid"
- Bank balance decreases by total net salary
- Ledger entries created

---

## PART 23: FIXED ASSETS TESTING

### Test 23.1: Add Fixed Assets
Go to **Fixed Assets → Add Asset**

#### Asset 1: Fuel Dispenser
| Field | Value |
|-------|-------|
| Name | `Fuel Dispenser - Pump 1` |
| Asset Code | `FA-001` |
| Category | `Equipment` |
| Description | `Digital fuel dispenser - 4 nozzles` |
| Purchase Date | `2023-01-01` |
| Purchase Cost | `5000000.00` |
| Salvage Value | `200000.00` |
| Useful Life | `10` years |
| Depreciation Method | `Straight Line` |
| Location | `Main Station` |

#### Asset 2: Underground Tank
| Field | Value |
|-------|-------|
| Name | `Underground Storage Tank` |
| Asset Code | `FA-002` |
| Category | `Infrastructure` |
| Description | `50000 litre underground fuel tank` |
| Purchase Date | `2023-01-01` |
| Purchase Cost | `15000000.00` |
| Salvage Value | `500000.00` |
| Useful Life | `20` years |
| Depreciation Method | `Straight Line` |
| Location | `Main Station` |

#### Asset 3: Generator
| Field | Value |
|-------|-------|
| Name | `Backup Generator` |
| Asset Code | `FA-003` |
| Category | `Equipment` |
| Description | `100KVA diesel generator` |
| Purchase Date | `2023-01-01` |
| Purchase Cost | `8000000.00` |
| Salvage Value | `300000.00` |
| Useful Life | `15` years |
| Depreciation Method | `Straight Line` |
| Location | `Generator House` |

### Test 23.2: Record Depreciation
Go to Fixed Assets → Run Depreciation

| Field | Value |
|-------|-------|
| Period Start | `2024-01-01` |
| Period End | `2024-01-31` |

**Expected:**
- Depreciation records created
- Journal voucher created
- Asset book values updated

---

## PART 24: REPORTS TESTING

### Test 24.1: Trial Balance
Go to **Reports → Trial Balance**

**Verify:**
- Total debits = Total credits
- All accounts show correct balances

### Test 24.2: Balance Sheet
Go to **Reports → Balance Sheet**

**Verify:**
- Assets = Liabilities + Equity
- All balances reasonable

### Test 24.3: Income Statement (Profit & Loss)
Go to **Reports → Income Statement**

**Verify:**
- Revenue accounts show sales
- Expense accounts show costs
- Net Income calculated correctly

### Test 24.4: General Ledger
Go to **Reports → General Ledger**

Select an account and verify all transactions are recorded.

### Test 24.5: Aged Receivables
Go to **Reports → Aged Receivables**

**Verify:**
- Shows customers with outstanding balances
- Aging buckets (Current, 30, 60, 90+ days)

### Test 24.6: Aged Payables
Go to **Reports → Aged Payables**

**Verify:**
- Shows vendors with outstanding bills
- Aging buckets correct

### Test 24.7: Inventory Report
Go to **Inventory → Reports → Stock Levels**

**Verify:**
- All products listed
- Stock quantities correct after all transactions
- Low stock alerts for items below reorder level

---

## TESTING CHECKLIST

Use this checklist to track your testing progress:

### Setup
- [ ] Database deleted and recreated
- [ ] Servers started successfully
- [ ] User registration completed

### Configuration
- [ ] Chart of Accounts created
- [ ] Customers added (4 customers)
- [ ] Vendors added (4 vendors)
- [ ] Products added (8 products)
- [ ] Bank accounts added (3 accounts)
- [ ] Employees added (5 employees)
- [ ] Payroll configured
- [ ] Fiscal year created

### Purchases
- [ ] Fuel purchase bill created
- [ ] Vendor payment recorded
- [ ] Lubricants purchase created
- [ ] Partial payment recorded

### Sales
- [ ] Cash sale completed
- [ ] Corporate credit sale created
- [ ] Partial payment from corporate
- [ ] Government customer invoice

### Advanced Features
- [ ] Customer prepayment funded
- [ ] Auto-deduction from prepaid verified
- [ ] Credit note created and applied
- [ ] Bad debt write-off completed
- [ ] Vendor prepayment funded
- [ ] Debit note created

### Operations
- [ ] Expenses recorded
- [ ] Other income recorded
- [ ] Fund transfer completed
- [ ] Manual cashbook entry
- [ ] Journal voucher created
- [ ] Payroll generated and paid
- [ ] Fixed assets added
- [ ] Depreciation recorded

### Reports
- [ ] Trial Balance verified
- [ ] Balance Sheet verified
- [ ] Income Statement verified
- [ ] General Ledger verified
- [ ] Aged Receivables verified
- [ ] Aged Payables verified
- [ ] Inventory Report verified

---

## COMMON ISSUES TO WATCH FOR

1. **Currency Display:** Check that NGN displays correctly
2. **Number Formatting:** Verify amounts have proper commas
3. **Stock Deduction:** Verify stock decreases after sales
4. **Balance Updates:** Verify account balances update after transactions
5. **Permission Errors:** Test with different user roles
6. **Date Handling:** Check date pickers and date displays
7. **VAT Calculation:** Verify 7.5% VAT calculates correctly
8. **Ledger Balance:** Ensure debits = credits in all transactions

---

## FEEDBACK TEMPLATE

When reporting issues, please include:

```
**Issue Title:** [Brief description]

**Location:** [Which page/feature]

**Steps to Reproduce:**
1. Go to...
2. Click on...
3. Enter...

**Expected Result:** [What should happen]

**Actual Result:** [What actually happened]

**Error Messages:** [Any error messages displayed]
```
