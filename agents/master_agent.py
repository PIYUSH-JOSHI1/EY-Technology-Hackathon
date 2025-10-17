import os
from groq import Groq
from .sales_agent import SalesAgent
from .verification_agent import VerificationAgent
from .underwriting_agent import UnderwritingAgent
import json

class MasterAgent:
    """Master Agent - Orchestrates all worker agents using Groq AI"""
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'mixtral-8x7b-32768'
        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.conversation_stage = {}
        
    def process_message(self, user_message, conversation, conversation_id):
        """Process user message and orchestrate worker agents using AI"""
        
        # Initialize conversation stage if new
        if conversation_id not in self.conversation_stage:
            self.conversation_stage[conversation_id] = 'greeting'
        
        stage = self.conversation_stage[conversation_id]
        customer_data = conversation['customer_data']
        
        try:
            # Build conversation history for context
            messages = []
            for msg in conversation['messages'][-6:]:  # Last 6 messages for context
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Add current user message
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            # Get AI response based on current stage
            if stage == 'greeting':
                response = self._handle_greeting_stage(user_message, messages)
            elif stage == 'qualification':
                response = self._handle_qualification_stage(user_message, messages, customer_data)
            elif stage == 'personal_details':
                response = self._handle_personal_details_stage(user_message, messages, customer_data)
            elif stage == 'verification':
                response = self._handle_verification_stage(user_message, messages, customer_data, conversation)
            elif stage == 'underwriting':
                response = self._handle_underwriting_stage(customer_data, conversation)
            elif stage == 'salary_verification':
                response = {'message': "Please upload your salary slip to proceed.", 'action': 'waiting_for_upload'}
            else:
                response = {'message': "How can I assist you with your loan application?"}
            
            # Update conversation data
            conversation['customer_data'] = customer_data
            return response
            
        except Exception as e:
            print(f"Error in master agent: {str(e)}")
            return {'message': "I encountered an error. Please try again.", 'error': str(e)}
    
    def _handle_greeting_stage(self, user_message, messages):
        """Handle greeting stage with AI"""
        system_prompt = """You are a friendly and professional loan sales assistant for Tata Capital. 
        Your goal is to greet the customer warmly and assess if they're interested in a personal loan.
        Keep responses concise and engaging. If they show interest, prepare to move to qualification stage."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                *messages
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        bot_message = response.choices[0].message.content
        
        # Check if customer is interested
        interest_check = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'Determine if the user is interested in a personal loan. Reply with only "yes" or "no".'},
                {'role': 'user', 'content': user_message}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        is_interested = 'yes' in interest_check.choices[0].message.content.lower()
        
        if is_interested:
            self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'qualification'
            return {
                'message': bot_message + "\n\nWhat loan amount are you looking for?",
                'action': 'move_to_qualification'
            }
        
        return {'message': bot_message, 'action': 'greeting'}
    
    def _handle_qualification_stage(self, user_message, messages, customer_data):
        """Handle qualification stage with AI"""
        system_prompt = """You are a loan qualification assistant. Extract the loan amount from the user's message.
        The user might say amounts like "2 lakhs", "5 lakhs", "500000", etc.
        Reply with a JSON object: {"loan_amount": <number>, "message": "<response>"}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            loan_amount = result.get('loan_amount')
            message = result.get('message', '')
            
            if loan_amount:
                customer_data['loan_amount'] = int(loan_amount)
                self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'personal_details'
                return {
                    'message': f"Great! A loan of ₹{loan_amount:,.0f} noted. Now, what's your full name?",
                    'action': 'move_to_personal_details'
                }
        except:
            pass
        
        return {'message': "Could you please specify the loan amount? (e.g., 2 lakhs, 5 lakhs, 500000)"}
    
    def _handle_personal_details_stage(self, user_message, messages, customer_data):
        """Handle personal details collection with AI"""
        if 'name' not in customer_data:
            customer_data['name'] = user_message.strip()
            return {'message': f"Nice to meet you, {user_message}! What's your age?"}
        
        elif 'age' not in customer_data:
            try:
                age = int(user_message.strip())
                if 21 <= age <= 65:
                    customer_data['age'] = age
                    return {'message': "Which city are you based in?"}
                else:
                    return {'message': "Age should be between 21 and 65 years. Please enter a valid age."}
            except:
                return {'message': "Please enter a valid age (number)."}
        
        elif 'city' not in customer_data:
            customer_data['city'] = user_message.strip()
            self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'verification'
            return {
                'message': "Thank you! Now let me verify your KYC details. What's your registered phone number?",
                'action': 'move_to_verification'
            }
        
        return {'message': "Please provide your details."}
    
    def _handle_verification_stage(self, user_message, messages, customer_data, conversation):
        """Handle verification stage with AI"""
        if 'phone' not in customer_data:
            customer_data['phone'] = user_message.strip()
            return {'message': "What's your registered address?"}
        
        elif 'address' not in customer_data:
            customer_data['address'] = user_message.strip()
            
            # Verify with CRM
            verification_result = self.verification_agent.verify_kyc(customer_data)
            
            if verification_result['verified']:
                self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'underwriting'
                return {
                    'message': "Perfect! Your KYC details are verified. Let me check your eligibility...",
                    'action': 'start_underwriting',
                    'data': verification_result
                }
            else:
                conversation['status'] = 'rejected'
                return {
                    'message': "I'm sorry, but your KYC details couldn't be verified. Please contact our support team.",
                    'action': 'verification_failed'
                }
        
        return {'message': "Please provide your details."}
    
    def _handle_underwriting_stage(self, customer_data, conversation):
        """Handle underwriting stage with AI"""
        underwriting_result = self.underwriting_agent.evaluate_eligibility(customer_data)
        
        if underwriting_result['status'] == 'approved':
            self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'approval'
            conversation['status'] = 'completed'
            return {
                'message': f"Excellent news! Your loan of ₹{customer_data['loan_amount']:,.0f} has been approved! Your sanction letter is ready for download.",
                'action': 'loan_approved',
                'data': underwriting_result
            }
        
        elif underwriting_result['status'] == 'salary_slip_required':
            self.conversation_stage[list(self.conversation_stage.keys())[-1]] = 'salary_verification'
            conversation['status'] = 'pending_verification'
            return {
                'message': "Your loan amount requires salary verification. Please upload your latest salary slip (PDF or image).",
                'action': 'upload_salary_slip',
                'data': underwriting_result
            }
        
        else:  # rejected
            conversation['status'] = 'rejected'
            return {
                'message': f"I'm sorry, but based on your credit profile, we cannot approve this loan at this time. Reason: {underwriting_result.get('reason', 'Eligibility criteria not met')}",
                'action': 'loan_rejected',
                'data': underwriting_result
            }
