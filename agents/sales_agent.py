import os
from groq import Groq
import re

class SalesAgent:
    """Sales Agent - Handles customer engagement using Groq AI"""
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'mixtral-8x7b-32768'
    
    def greet_customer(self, user_message):
        """Greet customer with AI-powered response"""
        system_prompt = """You are a friendly Tata Capital loan sales representative. 
        Greet the customer warmly and introduce personal loans. Keep it brief and engaging."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message or 'Hello'}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return {'message': response.choices[0].message.content, 'action': 'greeting'}
    
    def extract_loan_amount(self, user_message):
        """Extract loan amount from user message"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs|lacs)',
            r'(\d+(?:\.\d+)?)\s*(?:thousand|k)',
            r'₹?\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                if 'lakh' in user_message.lower() or 'lac' in user_message.lower():
                    amount *= 100000
                elif 'thousand' in user_message.lower() or 'k' in user_message.lower():
                    amount *= 1000
                return int(amount)
        
        return None
    
    def negotiate_terms(self, customer_data):
        """Suggest loan terms using AI"""
        loan_amount = customer_data.get('loan_amount', 0)
        interest_rate = 12.0
        
        terms = []
        for tenure in [12, 24, 36, 48, 60]:
            monthly_rate = interest_rate / 100 / 12
            emi = (loan_amount * monthly_rate * (1 + monthly_rate) ** tenure) / ((1 + monthly_rate) ** tenure - 1)
            terms.append({
                'tenure': tenure,
                'emi': int(emi),
                'total_amount': int(emi * tenure)
            })
        
        return terms
