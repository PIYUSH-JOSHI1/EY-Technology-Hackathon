import csv
import os
from groq import Groq

class VerificationAgent:
    """Verification Agent - Handles KYC verification using Groq AI"""
    
    def __init__(self):
        self.kyc_data_file = 'data/kyc_data.csv'
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'mixtral-8x7b-32768'
    
    def verify_kyc(self, customer_data):
        """Verify customer KYC details from CRM"""
        name = customer_data.get('name', '').lower()
        phone = customer_data.get('phone', '')
        
        try:
            with open(self.kyc_data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['name'].lower() == name and row['phone'] == phone):
                        customer_data['customer_id'] = row['customer_id']
                        customer_data['email'] = row['email']
                        customer_data['verified'] = True
                        return {
                            'verified': True,
                            'message': 'KYC verification successful',
                            'customer_id': row['customer_id']
                        }
        except FileNotFoundError:
            pass
        
        return {'verified': False, 'message': 'KYC verification failed'}
    
    def get_customer_history(self, customer_id):
        """Get customer's loan history"""
        try:
            with open('data/customers.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == customer_id:
                        return {
                            'existing_loans': int(row['existing_loans']),
                            'total_outstanding': float(row['total_outstanding']),
                            'payment_history': row['payment_history']
                        }
        except FileNotFoundError:
            pass
        
        return None
