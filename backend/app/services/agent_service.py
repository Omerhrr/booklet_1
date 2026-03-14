"""
Agent Service - Automation, Audit, and Doc Wizard Agents

This module provides three types of agents:
1. Automation Agent - Runs automated tasks (bad debt, depreciation, etc.)
2. Audit Agent - Audits records, generates PDF reports, sends emails
3. Doc Wizard - Guides users on fixing issues
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
import os
import asyncio
import httpx
from io import BytesIO

from app.models import (
    User, Business, Branch, 
    AgentConfiguration, AgentExecution, AgentFinding, AgentType, AgentStatus,
    DocWizardSession, DocWizardMessage,
    SalesInvoice, PurchaseBill, Customer, Vendor, Product, Expense,
    Employee, Account, LedgerEntry, BankAccount, CashBookEntry,
    FixedAsset, DepreciationRecord, BadDebt, AuditLog,
    FiscalYear, FiscalPeriod, JournalVoucher
)
from app.services.permission_service import PermissionService
from app.services.accounting_service import AccountService, JournalVoucherService, ReportService
from app.services.fixed_assets_service import FixedAssetService
from app.services.sales_service import SalesService

logger = logging.getLogger(__name__)


class AgentService:
    """Base service for all agents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CONFIGURATION MANAGEMENT ====================
    
    def get_configuration(self, business_id: int, agent_type: str) -> Optional[AgentConfiguration]:
        """Get agent configuration for a business"""
        return self.db.query(AgentConfiguration).filter(
            AgentConfiguration.business_id == business_id,
            AgentConfiguration.agent_type == agent_type
        ).first()
    
    def get_all_configurations(self, business_id: int) -> List[AgentConfiguration]:
        """Get all agent configurations for a business"""
        return self.db.query(AgentConfiguration).filter(
            AgentConfiguration.business_id == business_id
        ).all()
    
    def create_or_update_configuration(
        self,
        business_id: int,
        agent_type: str,
        config: Optional[Dict] = None,
        schedule_enabled: bool = False,
        schedule_cron: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        email_enabled: bool = False,
        is_enabled: bool = True
    ) -> AgentConfiguration:
        """Create or update agent configuration"""
        existing = self.get_configuration(business_id, agent_type)
        
        if existing:
            if config is not None:
                existing.config = json.dumps(config)
            existing.schedule_enabled = schedule_enabled
            if schedule_cron:
                existing.schedule_cron = schedule_cron
            if email_recipients is not None:
                existing.email_recipients = json.dumps(email_recipients)
            existing.email_enabled = email_enabled
            existing.is_enabled = is_enabled
        else:
            existing = AgentConfiguration(
                business_id=business_id,
                agent_type=agent_type,
                config=json.dumps(config) if config else None,
                schedule_enabled=schedule_enabled,
                schedule_cron=schedule_cron,
                email_recipients=json.dumps(email_recipients) if email_recipients else None,
                email_enabled=email_enabled,
                is_enabled=is_enabled
            )
            self.db.add(existing)
        
        self.db.commit()
        self.db.refresh(existing)
        return existing
    
    # ==================== EXECUTION MANAGEMENT ====================
    
    def create_execution(
        self,
        configuration_id: int,
        business_id: int,
        branch_id: Optional[int] = None
    ) -> AgentExecution:
        """Create a new execution record"""
        execution = AgentExecution(
            agent_configuration_id=configuration_id,
            business_id=business_id,
            branch_id=branch_id,
            status=AgentStatus.PENDING.value,
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def update_execution(
        self,
        execution_id: int,
        status: str,
        result_summary: Optional[str] = None,
        result_details: Optional[Dict] = None,
        error_message: Optional[str] = None,
        records_processed: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        records_flagged: int = 0,
        report_path: Optional[str] = None
    ) -> AgentExecution:
        """Update execution record"""
        execution = self.db.query(AgentExecution).get(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution.status = status
        if result_summary:
            execution.result_summary = result_summary
        if result_details:
            execution.result_details = json.dumps(result_details)
        if error_message:
            execution.error_message = error_message
        if status == AgentStatus.COMPLETED.value or status == AgentStatus.FAILED.value:
            execution.completed_at = datetime.utcnow()
        execution.records_processed = records_processed
        execution.records_created = records_created
        execution.records_updated = records_updated
        execution.records_flagged = records_flagged
        if report_path:
            execution.report_path = report_path
        
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def get_executions(
        self,
        business_id: int,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[AgentExecution]:
        """Get executions for a business"""
        query = self.db.query(AgentExecution).filter(
            AgentExecution.business_id == business_id
        )
        
        if agent_type:
            query = query.join(AgentConfiguration).filter(
                AgentConfiguration.agent_type == agent_type
            )
        if status:
            query = query.filter(AgentExecution.status == status)
        
        return query.order_by(desc(AgentExecution.started_at)).limit(limit).all()
    
    # ==================== FINDING MANAGEMENT ====================
    
    def create_finding(
        self,
        execution_id: int,
        business_id: int,
        finding_type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        related_model: Optional[str] = None,
        related_record_id: Optional[int] = None,
        branch_id: Optional[int] = None
    ) -> AgentFinding:
        """Create a finding record"""
        finding = AgentFinding(
            execution_id=execution_id,
            business_id=business_id,
            finding_type=finding_type,
            severity=severity,
            title=title,
            description=description,
            related_model=related_model,
            related_record_id=related_record_id,
            branch_id=branch_id
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return finding
    
    def get_findings(
        self,
        business_id: int,
        severity: Optional[str] = None,
        resolution_status: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentFinding]:
        """Get findings for a business"""
        query = self.db.query(AgentFinding).filter(
            AgentFinding.business_id == business_id
        )
        
        if severity:
            query = query.filter(AgentFinding.severity == severity)
        if resolution_status:
            query = query.filter(AgentFinding.resolution_status == resolution_status)
        
        return query.order_by(desc(AgentFinding.created_at)).limit(limit).all()
    
    def resolve_finding(
        self,
        finding_id: int,
        resolved_by: int,
        resolution_notes: Optional[str] = None,
        dismiss: bool = False
    ) -> AgentFinding:
        """Resolve or dismiss a finding"""
        finding = self.db.query(AgentFinding).get(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found")
        
        finding.resolution_status = 'dismissed' if dismiss else 'resolved'
        finding.resolution_notes = resolution_notes
        finding.resolved_by = resolved_by
        finding.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(finding)
        return finding


class AutomationAgentService(AgentService):
    """
    Automation Agent - Runs automated tasks
    
    Tasks:
    - Bad debt analysis and write-off
    - Depreciation calculation
    - Aging report generation
    - Overdue invoice detection
    """
    
    def run_automations(self, business_id: int, user_id: int) -> AgentExecution:
        """Run all automated tasks for a business"""
        # Get or create configuration
        config = self.get_configuration(business_id, AgentType.AUTOMATION.value)
        if not config:
            config = self.create_or_update_configuration(
                business_id=business_id,
                agent_type=AgentType.AUTOMATION.value,
                is_enabled=True
            )
        
        # Create execution record
        execution = self.create_execution(
            configuration_id=config.id,
            business_id=business_id
        )
        
        try:
            # Update status to running
            self.update_execution(execution.id, AgentStatus.RUNNING.value)
            
            results = {
                'bad_debt': self._run_bad_debt_check(business_id, execution.id),
                'depreciation': self._run_depreciation(business_id, execution.id),
                'overdue_invoices': self._check_overdue_invoices(business_id, execution.id)
            }
            
            total_processed = sum(r.get('processed', 0) for r in results.values())
            total_flagged = sum(r.get('flagged', 0) for r in results.values())
            
            # Update configuration last run
            config.last_run_at = datetime.utcnow()
            self.db.commit()
            
            self.update_execution(
                execution.id,
                AgentStatus.COMPLETED.value,
                result_summary=f"Processed {total_processed} records, flagged {total_flagged} issues",
                result_details=results,
                records_processed=total_processed,
                records_flagged=total_flagged
            )
            
            return execution
            
        except Exception as e:
            logger.error(f"Automation agent error: {e}")
            self.update_execution(
                execution.id,
                AgentStatus.FAILED.value,
                error_message=str(e)
            )
            raise
    
    def _run_bad_debt_check(self, business_id: int, execution_id: int) -> Dict:
        """Check for potential bad debts"""
        # Find overdue invoices over 90 days
        overdue_threshold = date.today() - timedelta(days=90)
        
        overdue_invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.status.in_(['overdue', 'partially_paid']),
            SalesInvoice.due_date < overdue_threshold,
            SalesInvoice.total_amount > SalesInvoice.paid_amount
        ).all()
        
        flagged = 0
        for invoice in overdue_invoices:
            outstanding = invoice.total_amount - invoice.paid_amount
            if outstanding > 0:
                # Create finding
                self.create_finding(
                    execution_id=execution_id,
                    business_id=business_id,
                    finding_type='bad_debt_candidate',
                    severity='high',
                    title=f'Potential Bad Debt: {invoice.invoice_number}',
                    description=f'Invoice {invoice.invoice_number} is over 90 days overdue with outstanding balance of {outstanding:.2f}',
                    related_model='SalesInvoice',
                    related_record_id=invoice.id,
                    branch_id=invoice.branch_id
                )
                flagged += 1
        
        return {
            'processed': len(overdue_invoices),
            'flagged': flagged
        }
    
    def _run_depreciation(self, business_id: int, execution_id: int) -> Dict:
        """Run depreciation for fixed assets"""
        # Get assets that need depreciation
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        assets = self.db.query(FixedAsset).filter(
            FixedAsset.business_id == business_id,
            FixedAsset.status == 'active'
        ).all()
        
        processed = 0
        for asset in assets:
            # Check if depreciation already run this month
            existing_dep = self.db.query(DepreciationRecord).filter(
                DepreciationRecord.fixed_asset_id == asset.id,
                func.extract('month', DepreciationRecord.depreciation_date) == current_month,
                func.extract('year', DepreciationRecord.depreciation_date) == current_year
            ).first()
            
            if not existing_dep and asset.depreciation_method != 'none':
                # Calculate monthly depreciation
                if asset.depreciation_method == 'straight_line':
                    monthly_dep = (asset.purchase_cost - asset.salvage_value) / asset.useful_life_years / 12
                    
                    # Create depreciation record
                    dep_record = DepreciationRecord(
                        fixed_asset_id=asset.id,
                        depreciation_date=today,
                        amount=Decimal(str(monthly_dep)),
                        method=asset.depreciation_method,
                        notes=f'Automated monthly depreciation via Automation Agent'
                    )
                    self.db.add(dep_record)
                    
                    # Update asset accumulated depreciation
                    asset.accumulated_depreciation = (asset.accumulated_depreciation or 0) + Decimal(str(monthly_dep))
                    processed += 1
        
        self.db.commit()
        
        return {
            'processed': len(assets),
            'depreciation_records_created': processed
        }
    
    def _check_overdue_invoices(self, business_id: int, execution_id: int) -> Dict:
        """Check and update overdue invoice statuses"""
        today = date.today()
        
        # Find invoices that are past due but not marked as overdue
        invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.status == 'pending',
            SalesInvoice.due_date < today
        ).all()
        
        updated = 0
        for invoice in invoices:
            invoice.status = 'overdue'
            updated += 1
        
        self.db.commit()
        
        return {
            'processed': len(invoices),
            'updated': updated
        }


class AuditAgentService(AgentService):
    """
    Audit Agent - Comprehensive business auditing
    
    Tasks:
    - Check all records across branches
    - Look for discrepancies
    - Generate PDF reports
    - Send reports via email at scheduled times
    """
    
    async def run_audit(
        self,
        business_id: int,
        branch_id: Optional[int] = None,
        send_email: bool = True
    ) -> AgentExecution:
        """Run comprehensive audit for a business"""
        config = self.get_configuration(business_id, AgentType.AUDIT.value)
        if not config:
            config = self.create_or_update_configuration(
                business_id=business_id,
                agent_type=AgentType.AUDIT.value,
                email_enabled=send_email
            )
        
        execution = self.create_execution(
            configuration_id=config.id,
            business_id=business_id,
            branch_id=branch_id
        )
        
        try:
            self.update_execution(execution.id, AgentStatus.RUNNING.value)
            
            # Run all audit checks
            results = {
                'ledger_balance': self._check_ledger_balance(business_id, branch_id, execution.id),
                'invoice_reconciliation': self._check_invoice_reconciliation(business_id, branch_id, execution.id),
                'inventory_discrepancies': self._check_inventory_discrepancies(business_id, branch_id, execution.id),
                'audit_log_review': self._review_audit_logs(business_id, branch_id, execution.id),
                'branch_comparison': self._compare_branches(business_id, execution.id) if not branch_id else {}
            }
            
            total_processed = sum(r.get('processed', 0) for r in results.values())
            total_flagged = sum(r.get('flagged', 0) for r in results.values())
            
            # Generate PDF report
            report_path = await self._generate_audit_report(business_id, execution.id, results)
            
            # Update configuration
            config.last_run_at = datetime.utcnow()
            self.db.commit()
            
            self.update_execution(
                execution.id,
                AgentStatus.COMPLETED.value,
                result_summary=f"Audit complete. Processed {total_processed} records, found {total_flagged} issues.",
                result_details=results,
                records_processed=total_processed,
                records_flagged=total_flagged,
                report_path=report_path
            )
            
            # Send email if configured
            if send_email and config.email_enabled and config.email_recipients:
                await self._send_audit_report_email(business_id, execution.id, report_path, config)
            
            return execution
            
        except Exception as e:
            logger.error(f"Audit agent error: {e}")
            self.update_execution(
                execution.id,
                AgentStatus.FAILED.value,
                error_message=str(e)
            )
            raise
    
    def _check_ledger_balance(self, business_id: int, branch_id: Optional[int], execution_id: int) -> Dict:
        """Check if ledger entries are balanced"""
        query = self.db.query(
            Account.id,
            Account.name,
            Account.code,
            func.sum(LedgerEntry.debit).label('total_debit'),
            func.sum(LedgerEntry.credit).label('total_credit')
        ).join(LedgerEntry, LedgerEntry.account_id == Account.id, isouter=True).filter(
            Account.business_id == business_id
        )
        
        if branch_id:
            query = query.filter(LedgerEntry.branch_id == branch_id)
        
        results = query.group_by(Account.id).all()
        
        flagged = 0
        for row in results:
            debit = float(row.total_debit or 0)
            credit = float(row.total_credit or 0)
            
            # Check if imbalanced (allowing for small floating point differences)
            if abs(debit - credit) > 0.01:
                self.create_finding(
                    execution_id=execution_id,
                    business_id=business_id,
                    finding_type='ledger_imbalance',
                    severity='high',
                    title=f'Ledger Imbalance: {row.code} - {row.name}',
                    description=f'Account {row.code} ({row.name}) has debit total of {debit:.2f} and credit total of {credit:.2f}. Difference: {abs(debit - credit):.2f}',
                    related_model='Account',
                    related_record_id=row.id,
                    branch_id=branch_id
                )
                flagged += 1
        
        return {'processed': len(results), 'flagged': flagged}
    
    def _check_invoice_reconciliation(self, business_id: int, branch_id: Optional[int], execution_id: int) -> Dict:
        """Check for invoice/receipt mismatches"""
        flagged = 0
        processed = 0
        
        # Check for sales invoices with payments > total
        sales_query = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id
        )
        if branch_id:
            sales_query = sales_query.filter(SalesInvoice.branch_id == branch_id)
        
        for invoice in sales_query.all():
            processed += 1
            if invoice.paid_amount > invoice.total_amount:
                self.create_finding(
                    execution_id=execution_id,
                    business_id=business_id,
                    finding_type='overpayment',
                    severity='medium',
                    title=f'Overpayment on Invoice {invoice.invoice_number}',
                    description=f'Invoice {invoice.invoice_number} has paid amount ({invoice.paid_amount:.2f}) greater than total ({invoice.total_amount:.2f})',
                    related_model='SalesInvoice',
                    related_record_id=invoice.id,
                    branch_id=invoice.branch_id
                )
                flagged += 1
        
        return {'processed': processed, 'flagged': flagged}
    
    def _check_inventory_discrepancies(self, business_id: int, branch_id: Optional[int], execution_id: int) -> Dict:
        """Check for inventory discrepancies"""
        flagged = 0
        
        # Check for negative stock
        query = self.db.query(Product).filter(
            Product.business_id == business_id,
            Product.stock_quantity < 0
        )
        if branch_id:
            query = query.filter(Product.branch_id == branch_id)
        
        negative_stock = query.all()
        
        for product in negative_stock:
            self.create_finding(
                execution_id=execution_id,
                business_id=business_id,
                finding_type='negative_stock',
                severity='high',
                title=f'Negative Stock: {product.sku} - {product.name}',
                description=f'Product {product.sku} ({product.name}) has negative stock quantity: {product.stock_quantity}',
                related_model='Product',
                related_record_id=product.id,
                branch_id=product.branch_id
            )
            flagged += 1
        
        return {'processed': self.db.query(Product).filter(Product.business_id == business_id).count(), 'flagged': flagged}
    
    def _review_audit_logs(self, business_id: int, branch_id: Optional[int], execution_id: int) -> Dict:
        """Review recent audit logs for suspicious activity"""
        # Get audit logs from last 24 hours
        threshold = datetime.utcnow() - timedelta(hours=24)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.business_id == business_id,
            AuditLog.created_at >= threshold
        )
        if branch_id:
            query = query.filter(AuditLog.branch_id == branch_id)
        
        recent_logs = query.order_by(desc(AuditLog.created_at)).limit(1000).all()
        
        # Look for suspicious patterns
        flagged = 0
        delete_count = sum(1 for log in recent_logs if log.action == 'delete')
        
        if delete_count > 10:  # More than 10 deletes in 24 hours
            self.create_finding(
                execution_id=execution_id,
                business_id=business_id,
                finding_type='high_delete_activity',
                severity='medium',
                title='High Delete Activity Detected',
                description=f'{delete_count} records were deleted in the last 24 hours. This may warrant investigation.',
                branch_id=branch_id
            )
            flagged += 1
        
        return {'processed': len(recent_logs), 'flagged': flagged}
    
    def _compare_branches(self, business_id: int, execution_id: int) -> Dict:
        """Compare metrics across branches"""
        branches = self.db.query(Branch).filter(
            Branch.business_id == business_id
        ).all()
        
        branch_metrics = []
        for branch in branches:
            # Get basic metrics
            sales_total = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
                SalesInvoice.business_id == business_id,
                SalesInvoice.branch_id == branch.id
            ).scalar() or 0
            
            purchases_total = self.db.query(func.sum(PurchaseBill.total_amount)).filter(
                PurchaseBill.business_id == business_id,
                PurchaseBill.branch_id == branch.id
            ).scalar() or 0
            
            branch_metrics.append({
                'branch_id': branch.id,
                'branch_name': branch.name,
                'sales_total': float(sales_total),
                'purchases_total': float(purchases_total),
                'gross_profit': float(sales_total) - float(purchases_total)
            })
        
        return {
            'processed': len(branches),
            'branch_metrics': branch_metrics
        }
    
    async def _generate_audit_report(
        self,
        business_id: int,
        execution_id: int,
        results: Dict
    ) -> str:
        """Generate PDF audit report"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
        except ImportError:
            logger.warning("reportlab not installed, skipping PDF generation")
            return None
        
        business = self.db.query(Business).get(business_id)
        execution = self.db.query(AgentExecution).get(execution_id)
        findings = self.db.query(AgentFinding).filter(
            AgentFinding.execution_id == execution_id
        ).all()
        
        # Create report directory
        report_dir = '/home/z/my-project/download/audit_reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = f'{report_dir}/audit_report_{business_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        doc = SimpleDocTemplate(report_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f'Audit Report - {business.name}', title_style))
        story.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph('Executive Summary', heading_style))
        story.append(Paragraph(execution.result_summary or 'No summary available', styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Findings Summary
        story.append(Paragraph('Findings Summary', heading_style))
        
        if findings:
            findings_data = [['Severity', 'Type', 'Title', 'Status']]
            for f in findings:
                findings_data.append([
                    f.severity,
                    f.finding_type,
                    f.title[:50] + '...' if len(f.title) > 50 else f.title,
                    f.resolution_status
                ])
            
            findings_table = Table(findings_data, colWidths=[1*inch, 1.5*inch, 3*inch, 1*inch])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(findings_table)
        else:
            story.append(Paragraph('No findings to report.', styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Detailed Results
        story.append(Paragraph('Detailed Audit Results', heading_style))
        
        for check_name, check_result in results.items():
            story.append(Paragraph(f'{check_name.replace("_", " ").title()}', styles['Heading3']))
            story.append(Paragraph(
                f"Processed: {check_result.get('processed', 0)} records, Flagged: {check_result.get('flagged', 0)} issues",
                styles['Normal']
            ))
        
        doc.build(story)
        
        return report_path
    
    async def _send_audit_report_email(
        self,
        business_id: int,
        execution_id: int,
        report_path: str,
        config: AgentConfiguration
    ):
        """Send audit report via email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
        except ImportError:
            logger.warning("smtplib not available, skipping email")
            return
        
        if not config.email_recipients:
            return
        
        recipients = json.loads(config.email_recipients)
        business = self.db.query(Business).get(business_id)
        
        # Create email
        msg = MIMEMultipart()
        msg['Subject'] = f'Daily Audit Report - {business.name}'
        msg['From'] = 'booklet@noreply.com'
        msg['To'] = ', '.join(recipients)
        
        body = f"""
        <html>
        <body>
        <h2>Daily Audit Report - {business.name}</h2>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        <p>Please find attached the comprehensive audit report for your business.</p>
        <p>This is an automated message from Booklet ERP System.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach PDF
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= audit_report_{datetime.now().strftime("%Y%m%d")}.pdf'
                )
                msg.attach(part)
        
        # Note: In production, configure SMTP settings properly
        # This is a placeholder for the email sending logic
        logger.info(f"Would send audit report email to: {recipients}")


class DocWizardService(AgentService):
    """
    Doc Wizard - Guides users on fixing issues
    
    Has knowledge of the entire system and can guide users on:
    - Sales vs Purchase mistakes
    - Accounting corrections
    - Journal entry fixes
    - Data reconciliation
    """
    
    # System knowledge base
    SYSTEM_KNOWLEDGE = {
        'sales_vs_purchase': {
            'keywords': ['sale', 'purchase', 'invoice', 'bill', 'wrong direction', 'mistake'],
            'guidance': """
When you've recorded a transaction in the wrong direction (sales instead of purchase or vice versa):

1. **Identify the Issue**: Check if the invoice/bill was created with the wrong party type.

2. **Correction Steps**:
   a. If it's a sales invoice that should be a purchase:
      - Void or delete the sales invoice (if unpaid)
      - Create a new purchase bill with the vendor
   
   b. If it's a purchase bill that should be a sales invoice:
      - Void or delete the purchase bill (if unpaid)
      - Create a new sales invoice with the customer

3. **Ledger Impact**: The system automatically reverses ledger entries when voiding transactions.

4. **Prevention**: Always verify the transaction type before saving.
"""
        },
        'duplicate_entry': {
            'keywords': ['duplicate', 'double', 'twice', 'repeated'],
            'guidance': """
When you've accidentally created duplicate entries:

1. **Identify Duplicates**: Look for entries with same:
   - Invoice/Bill number
   - Same amounts and dates
   - Same counterparty

2. **Resolution**:
   - If unpaid: Delete the duplicate
   - If partially/fully paid: Create a credit/debit note to reverse

3. **Prevention**: Use unique reference numbers for each transaction.
"""
        },
        'wrong_account': {
            'keywords': ['wrong account', 'incorrect account', 'misclassified', 'category'],
            'guidance': """
When transactions are posted to wrong accounts:

1. **Create a Journal Voucher** to correct:
   - Debit the correct account
   - Credit the incorrectly used account

2. **Example**: If office expense was recorded as rent:
   - Debit: Office Expense Account
   - Credit: Rent Expense Account

3. **Add Notes**: Always add clear notes explaining the correction.
"""
        },
        'reconciliation_issue': {
            'keywords': ['reconcile', 'match', 'balance', 'discrepancy', 'difference'],
            'guidance': """
For bank reconciliation discrepancies:

1. **Check for**:
   - Outstanding checks/deposits
   - Bank fees not recorded
   - Timing differences
   - Duplicate entries

2. **Resolution**:
   - Record missing transactions
   - Create adjustment entries if needed
   - Mark reconciled items

3. **Tips**:
   - Reconcile regularly (weekly/monthly)
   - Keep bank statements for reference
"""
        }
    }
    
    def create_session(
        self,
        business_id: int,
        user_id: int,
        issue_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> DocWizardSession:
        """Create a new Doc Wizard session"""
        session = DocWizardSession(
            business_id=business_id,
            user_id=user_id,
            issue_type=issue_type,
            description=description
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        suggested_actions: Optional[List[Dict]] = None
    ) -> DocWizardMessage:
        """Add a message to a session"""
        message = DocWizardMessage(
            session_id=session_id,
            role=role,
            content=content,
            suggested_actions=json.dumps(suggested_actions) if suggested_actions else None
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_session(self, session_id: int) -> Optional[DocWizardSession]:
        """Get a session by ID"""
        return self.db.query(DocWizardSession).get(session_id)
    
    def get_user_sessions(self, user_id: int, business_id: int, limit: int = 20) -> List[DocWizardSession]:
        """Get sessions for a user"""
        return self.db.query(DocWizardSession).filter(
            DocWizardSession.user_id == user_id,
            DocWizardSession.business_id == business_id
        ).order_by(desc(DocWizardSession.created_at)).limit(limit).all()
    
    def get_session_messages(self, session_id: int) -> List[DocWizardMessage]:
        """Get all messages in a session"""
        return self.db.query(DocWizardMessage).filter(
            DocWizardMessage.session_id == session_id
        ).order_by(asc(DocWizardMessage.created_at)).all()
    
    def analyze_issue(self, description: str) -> Tuple[str, List[Dict]]:
        """Analyze the user's issue description and provide guidance"""
        description_lower = description.lower()
        
        # Find matching issue type
        for issue_type, data in self.SYSTEM_KNOWLEDGE.items():
            if any(kw in description_lower for kw in data['keywords']):
                return data['guidance'], self._get_actions_for_issue(issue_type)
        
        # Default guidance for unknown issues
        return """
I understand you're facing an issue. Let me help you resolve it.

To provide the best guidance, could you tell me:
1. What type of transaction or record is affected?
2. When did this issue occur?
3. What have you already tried to fix it?

Common issues I can help with:
- Sales vs Purchase mix-ups
- Duplicate entries
- Wrong account postings
- Bank reconciliation problems
- Journal entry corrections
""", []
    
    def _get_actions_for_issue(self, issue_type: str) -> List[Dict]:
        """Get suggested actions for an issue type"""
        actions = {
            'sales_vs_purchase': [
                {'label': 'View Sales Invoices', 'action': 'navigate', 'path': '/sales/invoices'},
                {'label': 'View Purchase Bills', 'action': 'navigate', 'path': '/purchases/bills'},
                {'label': 'Create Journal Entry', 'action': 'navigate', 'path': '/accounting/journal/new'}
            ],
            'duplicate_entry': [
                {'label': 'Check for Duplicates', 'action': 'analyze', 'type': 'duplicates'},
                {'label': 'View Audit Log', 'action': 'navigate', 'path': '/audit/logs'}
            ],
            'wrong_account': [
                {'label': 'Create Journal Voucher', 'action': 'navigate', 'path': '/accounting/journal/new'},
                {'label': 'View Chart of Accounts', 'action': 'navigate', 'path': '/accounting/accounts'}
            ],
            'reconciliation_issue': [
                {'label': 'Bank Reconciliation', 'action': 'navigate', 'path': '/banking/reconciliation'},
                {'label': 'View Bank Accounts', 'action': 'navigate', 'path': '/banking/accounts'}
            ]
        }
        return actions.get(issue_type, [])
    
    def resolve_session(self, session_id: int, resolution_summary: str) -> DocWizardSession:
        """Mark a session as resolved"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.resolved = True
        session.resolution_summary = resolution_summary
        self.db.commit()
        self.db.refresh(session)
        return session


# ==================== SCHEDULER SERVICE ====================

class AgentSchedulerService:
    """Service for scheduling and running agents automatically"""
    
    def __init__(self, db: Session):
        self.db = db
        self.automation_agent = AutomationAgentService(db)
        self.audit_agent = AuditAgentService(db)
    
    def get_due_agents(self) -> List[AgentConfiguration]:
        """Get agents that are due to run"""
        now = datetime.utcnow()
        
        return self.db.query(AgentConfiguration).filter(
            AgentConfiguration.is_enabled == True,
            AgentConfiguration.schedule_enabled == True,
            or_(
                AgentConfiguration.next_run_at == None,
                AgentConfiguration.next_run_at <= now
            )
        ).all()
    
    async def run_scheduled_agents(self):
        """Run all scheduled agents"""
        due_agents = self.get_due_agents()
        
        for config in due_agents:
            try:
                if config.agent_type == AgentType.AUTOMATION.value:
                    # Run automation agent (needs a user for audit purposes)
                    user = self.db.query(User).filter(
                        User.business_id == config.business_id
                    ).first()
                    if user:
                        await asyncio.to_thread(
                            self.automation_agent.run_automations,
                            config.business_id,
                            user.id
                        )
                
                elif config.agent_type == AgentType.AUDIT.value:
                    await self.audit_agent.run_audit(config.business_id)
                
                # Update next run time
                self._update_next_run_time(config)
                
            except Exception as e:
                logger.error(f"Failed to run scheduled agent {config.id}: {e}")
    
    def _update_next_run_time(self, config: AgentConfiguration):
        """Update the next run time based on cron schedule"""
        if config.schedule_cron:
            # Parse cron expression (simplified - runs daily at midnight by default)
            # In production, use a proper cron parser
            config.next_run_at = datetime.utcnow() + timedelta(days=1)
            config.next_run_at = config.next_run_at.replace(hour=0, minute=0, second=0)
        else:
            # Default: run daily at midnight
            config.next_run_at = datetime.utcnow() + timedelta(days=1)
            config.next_run_at = config.next_run_at.replace(hour=0, minute=0, second=0)
        
        self.db.commit()
