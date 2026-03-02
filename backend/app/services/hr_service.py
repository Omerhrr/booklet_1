"""
HR Service - Employees, Payroll, Payslips
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from datetime import date
from app.models import Employee, PayrollConfig, Payslip, PayFrequency, LedgerEntry, Account
from app.schemas import EmployeeCreate, EmployeeUpdate, PayrollConfigCreate


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, employee_id: int, business_id: int, branch_id: int = None) -> Optional[Employee]:
        query = self.db.query(Employee).options(
            joinedload(Employee.payroll_config)
        ).filter(
            Employee.id == employee_id,
            Employee.business_id == business_id
        )
        if branch_id:
            query = query.filter(Employee.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, include_inactive: bool = False) -> List[Employee]:
        query = self.db.query(Employee).filter(
            Employee.branch_id == branch_id,
            Employee.business_id == business_id
        )
        if not include_inactive:
            query = query.filter(Employee.is_active == True)
        return query.order_by(Employee.full_name).all()
    
    def get_all_by_business(self, business_id: int) -> List[Employee]:
        return self.db.query(Employee).options(
            joinedload(Employee.payroll_config)
        ).filter(
            Employee.business_id == business_id
        ).order_by(Employee.full_name).all()
    
    def create(self, employee_data: EmployeeCreate, business_id: int, branch_id: int) -> Employee:
        employee = Employee(
            full_name=employee_data.full_name,
            email=employee_data.email,
            phone_number=employee_data.phone_number,
            address=employee_data.address,
            hire_date=employee_data.hire_date,
            department=employee_data.department,
            position=employee_data.position,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(employee)
        self.db.flush()
        
        # Create payroll config if provided
        if employee_data.payroll_config:
            payroll_config = PayrollConfig(
                gross_salary=employee_data.payroll_config.gross_salary,
                pay_frequency=employee_data.payroll_config.pay_frequency,
                paye_rate=employee_data.payroll_config.paye_rate,
                pension_employee_rate=employee_data.payroll_config.pension_employee_rate,
                pension_employer_rate=employee_data.payroll_config.pension_employer_rate,
                employee_id=employee.id
            )
            self.db.add(payroll_config)
        
        self.db.flush()
        return employee
    
    def update(self, employee_id: int, business_id: int, employee_data: EmployeeUpdate, branch_id: int = None) -> Optional[Employee]:
        employee = self.get_by_id(employee_id, business_id, branch_id)
        if not employee:
            return None
        
        update_data = employee_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(employee, key, value)
        
        self.db.flush()
        return employee
    
    def terminate(self, employee_id: int, business_id: int, termination_date: date, branch_id: int = None) -> Optional[Employee]:
        employee = self.get_by_id(employee_id, business_id, branch_id)
        if not employee:
            return None
        
        employee.termination_date = termination_date
        employee.is_active = False
        
        self.db.flush()
        return employee
    
    def delete(self, employee_id: int, business_id: int, branch_id: int = None) -> bool:
        employee = self.get_by_id(employee_id, business_id, branch_id)
        if not employee:
            return False
        
        # Check for payslips
        has_payslips = self.db.query(Payslip).filter(
            Payslip.employee_id == employee_id
        ).first()
        
        if has_payslips:
            employee.is_active = False
        else:
            self.db.delete(employee)
        
        return True


class PayrollConfigService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_employee(self, employee_id: int) -> Optional[PayrollConfig]:
        return self.db.query(PayrollConfig).filter(
            PayrollConfig.employee_id == employee_id
        ).first()
    
    def create(self, config_data: PayrollConfigCreate, employee_id: int) -> PayrollConfig:
        config = PayrollConfig(
            gross_salary=config_data.gross_salary,
            pay_frequency=config_data.pay_frequency,
            paye_rate=config_data.paye_rate,
            pension_employee_rate=config_data.pension_employee_rate,
            pension_employer_rate=config_data.pension_employer_rate,
            other_deductions=config_data.other_deductions or Decimal("0"),
            other_allowances=config_data.other_allowances or Decimal("0"),
            employee_id=employee_id
        )
        self.db.add(config)
        self.db.flush()
        return config
    
    def update(self, employee_id: int, config_data: dict) -> Optional[PayrollConfig]:
        config = self.get_by_employee(employee_id)
        if not config:
            return None
        
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.flush()
        return config


class PayslipService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, payslip_id: int, business_id: int) -> Optional[Payslip]:
        return self.db.query(Payslip).options(
            joinedload(Payslip.employee)
        ).filter(
            Payslip.id == payslip_id,
            Payslip.business_id == business_id
        ).first()
    
    def get_by_employee(self, employee_id: int) -> List[Payslip]:
        return self.db.query(Payslip).filter(
            Payslip.employee_id == employee_id
        ).order_by(Payslip.pay_period_start.desc()).all()
    
    def get_by_business(self, business_id: int, pay_period_start: date = None, pay_period_end: date = None) -> List[Payslip]:
        query = self.db.query(Payslip).options(
            joinedload(Payslip.employee)
        ).filter(
            Payslip.business_id == business_id
        )
        
        if pay_period_start:
            query = query.filter(Payslip.pay_period_start >= pay_period_start)
        if pay_period_end:
            query = query.filter(Payslip.pay_period_end <= pay_period_end)
        
        return query.order_by(Payslip.pay_period_start.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_payslip = self.db.query(Payslip).filter(
            Payslip.business_id == business_id
        ).order_by(Payslip.id.desc()).first()
        
        if last_payslip:
            try:
                num = int(last_payslip.payslip_number.replace("PS-", ""))
                return f"PS-{num + 1:05d}"
            except ValueError:
                pass
        
        return "PS-00001"
    
    def calculate_deductions(self, gross_salary: Decimal, paye_rate: Decimal, 
                           pension_employee_rate: Decimal) -> Dict[str, Decimal]:
        """Calculate tax and pension deductions"""
        paye_deduction = gross_salary * (paye_rate / 100) if paye_rate else Decimal("0")
        pension_deduction = gross_salary * (pension_employee_rate / 100) if pension_employee_rate else Decimal("0")
        
        return {
            "paye_deduction": paye_deduction,
            "pension_deduction": pension_deduction
        }
    
    def create_payslip(self, employee: Employee, pay_period_start: date, pay_period_end: date, 
                      business_id: int, additional_deductions: Decimal = Decimal("0"),
                      additional_allowances: Decimal = Decimal("0")) -> Payslip:
        """Generate payslip for an employee"""
        if not employee.payroll_config:
            raise ValueError("Employee has no payroll configuration")
        
        # Check for overlapping payslips (duplicate detection)
        existing_payslip = self.db.query(Payslip).filter(
            Payslip.employee_id == employee.id,
            Payslip.pay_period_start <= pay_period_end,
            Payslip.pay_period_end >= pay_period_start
        ).first()
        
        if existing_payslip:
            raise ValueError(
                f"Payslip already exists for this period: {existing_payslip.payslip_number} "
                f"({existing_payslip.pay_period_start} to {existing_payslip.pay_period_end})"
            )
        
        config = employee.payroll_config
        
        # Calculate deductions
        deductions = self.calculate_deductions(
            config.gross_salary,
            config.paye_rate or Decimal("0"),
            config.pension_employee_rate or Decimal("0")
        )
        
        paye_deduction = deductions["paye_deduction"]
        pension_employee = deductions["pension_deduction"]
        pension_employer = config.gross_salary * (config.pension_employer_rate or Decimal("0")) / 100
        other_deductions = config.other_deductions or Decimal("0")
        other_allowances = config.other_allowances or Decimal("0")
        
        basic_salary = config.gross_salary
        allowances = other_allowances + additional_allowances
        gross_salary = basic_salary + allowances
        
        total_deductions = paye_deduction + pension_employee + other_deductions + additional_deductions
        net_salary = gross_salary - total_deductions
        
        # Validate net salary is not negative
        if net_salary < 0:
            raise ValueError(
                f"Deductions exceed gross salary. "
                f"Gross: {gross_salary:.2f}, Total Deductions: {total_deductions:.2f}, "
                f"Net: {net_salary:.2f}"
            )
        
        payslip = Payslip(
            payslip_number=self.get_next_number(business_id),
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            basic_salary=basic_salary,
            allowances=allowances,
            gross_salary=gross_salary,
            paye_deduction=paye_deduction,
            pension_employee=pension_employee,
            pension_employer=pension_employer,
            other_deductions=other_deductions + additional_deductions,
            total_deductions=total_deductions,
            net_salary=net_salary,
            status='pending',
            employee_id=employee.id,
            business_id=business_id
        )
        self.db.add(payslip)
        self.db.flush()
        
        return payslip
    
    def run_payroll(self, business_id: int, branch_id: int, pay_period_start: date, 
                   pay_period_end: date) -> List[Payslip]:
        """Run payroll for all active employees in a branch"""
        employees = self.db.query(Employee).options(
            joinedload(Employee.payroll_config)
        ).filter(
            Employee.business_id == business_id,
            Employee.branch_id == branch_id,
            Employee.is_active == True
        ).all()
        
        payslips = []
        for employee in employees:
            if employee.payroll_config:
                payslip = self.create_payslip(
                    employee, pay_period_start, pay_period_end, business_id
                )
                payslips.append(payslip)
        
        return payslips
    
    def mark_as_paid(self, payslip_id: int, business_id: int, paid_date: date = None, 
                     payment_account_id: int = None) -> Optional[Payslip]:
        """
        Mark payslip as paid and create accounting entries.
        
        Accounting entries created:
        1. Debit Salary Expense (expense increases)
           Credit Salary Payable (liability increases)
        
        2. Debit Pension Expense - Employer portion (expense increases)
           Credit Pension Payable (liability increases)
        
        3. Debit Salary Payable (liability decreases)
           Debit PAYE Payable (liability decreases)  
           Debit Pension Payable - Employee (liability decreases)
           Credit Cash/Bank (asset decreases)
        """
        payslip = self.get_by_id(payslip_id, business_id)
        if not payslip:
            return None
        
        if payslip.status == 'paid':
            raise ValueError("Payslip is already marked as paid")
        
        paid_date = paid_date or date.today()
        
        # Get or create necessary accounts
        salary_expense_account = self._get_or_create_account(
            business_id, payslip.employee.branch_id, 
            "Salary Expense", "6100", "Expense"
        )
        salary_payable_account = self._get_or_create_account(
            business_id, payslip.employee.branch_id,
            "Salary Payable", "2210", "Liability"
        )
        pension_expense_account = self._get_or_create_account(
            business_id, payslip.employee.branch_id,
            "Pension Expense", "6200", "Expense"
        )
        pension_payable_account = self._get_or_create_account(
            business_id, payslip.employee.branch_id,
            "Pension Payable", "2220", "Liability"
        )
        paye_payable_account = self._get_or_create_account(
            business_id, payslip.employee.branch_id,
            "PAYE Payable", "2230", "Liability"
        )
        
        # Entry 1: Record salary expense
        # Debit Salary Expense, Credit Salary Payable
        salary_entry_debit = LedgerEntry(
            transaction_date=paid_date,
            description=f"Salary expense - {payslip.employee.full_name} - {payslip.payslip_number}",
            reference=payslip.payslip_number,
            debit=payslip.gross_salary,
            credit=Decimal("0"),
            account_id=salary_expense_account.id,
            branch_id=payslip.employee.branch_id
        )
        self.db.add(salary_entry_debit)
        
        salary_entry_credit = LedgerEntry(
            transaction_date=paid_date,
            description=f"Salary payable - {payslip.employee.full_name} - {payslip.payslip_number}",
            reference=payslip.payslip_number,
            debit=Decimal("0"),
            credit=payslip.gross_salary,
            account_id=salary_payable_account.id,
            branch_id=payslip.employee.branch_id
        )
        self.db.add(salary_entry_credit)
        
        # Entry 2: Record employer pension expense (if applicable)
        if payslip.pension_employer and payslip.pension_employer > 0:
            pension_expense_debit = LedgerEntry(
                transaction_date=paid_date,
                description=f"Employer pension expense - {payslip.employee.full_name} - {payslip.payslip_number}",
                reference=payslip.payslip_number,
                debit=payslip.pension_employer,
                credit=Decimal("0"),
                account_id=pension_expense_account.id,
                branch_id=payslip.employee.branch_id
            )
            self.db.add(pension_expense_debit)
            
            pension_payable_credit = LedgerEntry(
                transaction_date=paid_date,
                description=f"Employer pension payable - {payslip.employee.full_name} - {payslip.payslip_number}",
                reference=payslip.payslip_number,
                debit=Decimal("0"),
                credit=payslip.pension_employer,
                account_id=pension_payable_account.id,
                branch_id=payslip.employee.branch_id
            )
            self.db.add(pension_payable_credit)
        
        # Entry 3: Payment entry (if payment account provided)
        if payment_account_id:
            payment_account = self.db.query(Account).filter(
                Account.id == payment_account_id,
                Account.business_id == business_id
            ).first()
            
            if not payment_account:
                raise ValueError("Payment account not found")
            
            # Clear Salary Payable
            salary_payment_debit = LedgerEntry(
                transaction_date=paid_date,
                description=f"Payment - {payslip.employee.full_name} - {payslip.payslip_number}",
                reference=payslip.payslip_number,
                debit=payslip.gross_salary,
                credit=Decimal("0"),
                account_id=salary_payable_account.id,
                branch_id=payslip.employee.branch_id
            )
            self.db.add(salary_payment_debit)
            
            # Record PAYE deduction (liability to be paid to tax authority)
            if payslip.paye_deduction and payslip.paye_deduction > 0:
                paye_debit = LedgerEntry(
                    transaction_date=paid_date,
                    description=f"PAYE deduction - {payslip.employee.full_name} - {payslip.payslip_number}",
                    reference=payslip.payslip_number,
                    debit=Decimal("0"),
                    credit=payslip.paye_deduction,
                    account_id=paye_payable_account.id,
                    branch_id=payslip.employee.branch_id
                )
                self.db.add(paye_debit)
            
            # Record pension deduction (employee portion - liability to pension fund)
            if payslip.pension_employee and payslip.pension_employee > 0:
                pension_debit = LedgerEntry(
                    transaction_date=paid_date,
                    description=f"Pension deduction (employee) - {payslip.employee.full_name} - {payslip.payslip_number}",
                    reference=payslip.payslip_number,
                    debit=Decimal("0"),
                    credit=payslip.pension_employee,
                    account_id=pension_payable_account.id,
                    branch_id=payslip.employee.branch_id
                )
                self.db.add(pension_debit)
            
            # Credit Cash/Bank (net payment)
            cash_credit = LedgerEntry(
                transaction_date=paid_date,
                description=f"Net salary payment - {payslip.employee.full_name} - {payslip.payslip_number}",
                reference=payslip.payslip_number,
                debit=Decimal("0"),
                credit=payslip.net_salary,
                account_id=payment_account.id,
                branch_id=payslip.employee.branch_id
            )
            self.db.add(cash_credit)
            
            # Create CashBook entry for salary payment
            self._create_payroll_cashbook_entry(
                payslip, payment_account, paid_date, business_id
            )
        
        # Update payslip status
        payslip.status = 'paid'
        payslip.paid_date = paid_date
        
        self.db.flush()
        return payslip
    
    def _get_or_create_account(self, business_id: int, branch_id: int, 
                                name: str, code: str, account_type: str) -> Account:
        """Get or create a payroll-related account"""
        
        # Try to find existing account
        account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.code == code
        ).first()
        
        if account:
            return account
        
        # Create new account - use string type directly
        account = Account(
            name=name,
            code=code,
            type=account_type,  # Already a string like "Expense" or "Liability"
            description=f"Auto-created for payroll - {name}",
            business_id=business_id,
            is_system_account=False
        )
        self.db.add(account)
        self.db.flush()
        return account
    
    def _create_payroll_cashbook_entry(self, payslip, payment_account: Account, 
                                        paid_date: date, business_id: int):
        """Create a CashBook entry for payroll payment"""
        from app.models import CashBookEntry
        from sqlalchemy import func as sql_func
        
        # Determine account type
        account_type = "cash"
        if payment_account.name and 'bank' in payment_account.name.lower():
            account_type = "bank"
        
        # Get current balance from ledger
        current_balance = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(
            LedgerEntry.account_id == payment_account.id,
            LedgerEntry.branch_id == payslip.employee.branch_id
        ).scalar() or Decimal("0")
        
        balance_after = current_balance - payslip.net_salary
        
        # Generate entry number
        prefix = "CP"  # Cash Payment
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == business_id,
            CashBookEntry.entry_number.like(f'{prefix}-%')
        ).order_by(CashBookEntry.id.desc()).first()
        
        if last_entry:
            try:
                num = int(last_entry.entry_number.replace(f'{prefix}-', ''))
                entry_number = f'{prefix}-{num + 1:05d}'
            except ValueError:
                entry_number = f'{prefix}-00001'
        else:
            entry_number = f'{prefix}-00001'
        
        # Create cash book entry
        cashbook_entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=paid_date,
            entry_type="payment",
            account_id=payment_account.id,
            account_type=account_type,
            amount=payslip.net_salary,
            balance_after=balance_after,
            description=f"Salary payment - {payslip.employee.full_name} - {payslip.payslip_number}",
            reference=payslip.payslip_number,
            payee_payer=payslip.employee.full_name,
            source_type="payroll",
            source_id=payslip.id,
            branch_id=payslip.employee.branch_id,
            business_id=business_id
        )
        self.db.add(cashbook_entry)
    
    def get_payroll_summary(self, business_id: int, pay_period_start: date, pay_period_end: date) -> Dict:
        """Get payroll summary for a period"""
        payslips = self.get_by_business(business_id, pay_period_start, pay_period_end)
        
        total_gross = sum(p.gross_salary for p in payslips)
        total_paye = sum(p.paye_deduction for p in payslips)
        total_pension = sum(p.pension_employee for p in payslips)
        total_deductions = sum(p.total_deductions for p in payslips)
        total_net = sum(p.net_salary for p in payslips)
        
        return {
            "period_start": pay_period_start,
            "period_end": pay_period_end,
            "employee_count": len(payslips),
            "total_gross": total_gross,
            "total_paye": total_paye,
            "total_pension": total_pension,
            "total_deductions": total_deductions,
            "total_net": total_net,
            "payslips": payslips
        }
