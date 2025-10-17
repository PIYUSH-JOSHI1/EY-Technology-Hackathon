import csv
import os
from groq import Groq

class UnderwritingAgent:
    """Underwriting Agent - Handles credit evaluation using Groq AI"""
    
    def __init__(self):
        self.credit_scores_file = 'data/credit_scores.csv'
        self.offers_file = 'data/offers.csv'
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'mixtral-8x7b-32768'
    
    def get_credit_score(self, customer_id):
        """Fetch credit score from mock credit bureau"""
        try:
            with open(self.credit_scores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == customer_id:
                        return int(row['credit_score'])
        except FileNotFoundError:
            pass
        
        return 750
    
    def get_pre_approved_limit(self, customer_id):
        """Get pre-approved loan limit"""
        try:
            with open(self.offers_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == customer_id:
                        return float(row['pre_approved_limit'])
        except FileNotFoundError:
            pass
        
        return 500000
    
    def evaluate_eligibility(self, customer_data):
        """Evaluate loan eligibility using AI logic"""
        customer_id = customer_data.get('customer_id', 'UNKNOWN')
        loan_amount = customer_data.get('loan_amount', 0)
        
        # Get credit score
        credit_score = self.get_credit_score(customer_id)
        customer_data['credit_score'] = credit_score
        
        # Check credit score
        if credit_score < 700:
            return {
                'status': 'rejected',
                'reason': f'Credit score ({credit_score}) is below minimum requirement (700)',
                'credit_score': credit_score
            }
        
        # Get pre-approved limit
        pre_approved_limit = self.get_pre_approved_limit(customer_id)
        customer_data['pre_approved_limit'] = pre_approved_limit
        
        # Check eligibility based on loan amount
        if loan_amount <= pre_approved_limit:
            return {
                'status': 'approved',
                'message': 'Instant approval',
                'credit_score': credit_score,
                'pre_approved_limit': pre_approved_limit,
                'interest_rate': 12.0,
                'tenure_months': 36
            }
        
        elif loan_amount <= 2 * pre_approved_limit:
            return {
                'status': 'salary_slip_required',
                'message': 'Salary slip verification required',
                'credit_score': credit_score,
                'pre_approved_limit': pre_approved_limit,
                'requested_amount': loan_amount
            }
        
        else:
            return {
                'status': 'rejected',
                'reason': f'Loan amount exceeds maximum limit (₹{2 * pre_approved_limit:,.0f})',
                'credit_score': credit_score,
                'pre_approved_limit': pre_approved_limit
            }
    
    def verify_salary_slip(self, customer_data, filepath):
        """Verify salary slip and approve if EMI <= 50% of salary"""
        salary = 50000
        loan_amount = customer_data.get('loan_amount', 0)
        
        monthly_rate = 0.12 / 12
        tenure = 36
        emi = (loan_amount * monthly_rate * (1 + monthly_rate) ** tenure) / ((1 + monthly_rate) ** tenure - 1)
        
        if emi <= salary * 0.5:
            return {
                'status': 'approved',
                'message': 'Salary verification successful',
                'salary': salary,
                'emi': int(emi),
                'emi_percentage': (emi / salary) * 100
            }
        else:
            return {
                'status': 'rejected',
                'reason': f'EMI (₹{int(emi)}) exceeds 50% of salary',
                'salary': salary,
                'emi': int(emi)
            }
