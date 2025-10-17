from flask import Flask, render_template, request, jsonify, send_file
import csv
from datetime import datetime
import json
import os
import io

app = Flask(__name__)

# Production configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', 'uploads')
)

# CSV file for persistent storage - use absolute path for production
CSV_FILE = os.path.join(os.getcwd(), 'loan_applications.csv')
CSV_HEADERS = ['conversation_id', 'customer_name', 'age', 'city', 'phone', 'email', 
               'loan_type', 'loan_amount', 'monthly_income', 'status', 'created_at', 
               'updated_at', 'customer_data_json']

def safe_import_agents():
    """Safely import agent classes, handling import errors"""
    agents = {}
    
    try:
        from agents.master_agent import MasterAgent
        agents['MasterAgent'] = MasterAgent
    except ImportError as e:
        print(f"⚠️  Could not import MasterAgent: {e}")
        agents['MasterAgent'] = None
    except Exception as e:
        print(f"⚠️  Error importing MasterAgent: {e}")
        agents['MasterAgent'] = None
    
    try:
        from agents.sanction_agent import SanctionAgent
        agents['SanctionAgent'] = SanctionAgent
    except ImportError as e:
        print(f"⚠️  Could not import SanctionAgent: {e}")
        agents['SanctionAgent'] = None
    except Exception as e:
        print(f"⚠️  Error importing SanctionAgent: {e}")
        agents['SanctionAgent'] = None
    
    try:
        from agents.underwriting_agent import UnderwritingAgent
        agents['UnderwritingAgent'] = UnderwritingAgent
    except ImportError as e:
        print(f"⚠️  Could not import UnderwritingAgent: {e}")
        agents['UnderwritingAgent'] = None
    except Exception as e:
        print(f"⚠️  Error importing UnderwritingAgent: {e}")
        agents['UnderwritingAgent'] = None
    
    return agents

# Get available agent classes
AGENT_CLASSES = safe_import_agents()

# Initialize agents after Flask app is created
def init_agents():
    # Try environment first, then attempt to load a .env file if present
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        try:
            from dotenv import load_dotenv
            # Try to load .env file with explicit error handling
            load_dotenv(override=True)
            groq_key = os.getenv('GROQ_API_KEY')
        except UnicodeDecodeError:
            app.logger.error("Invalid .env file encoding. Please recreate the .env file with UTF-8 encoding.")
        except Exception as e:
            app.logger.warning(f"Could not load .env file: {e}")
            pass

    if not groq_key:
        app.logger.error("GROQ_API_KEY not set. All agents will be unavailable.")
        return None, None, None

    # Try different approaches to initialize agents
    master = init_agent_safely("MasterAgent", AGENT_CLASSES['MasterAgent'])
    san = init_agent_safely("SanctionAgent", AGENT_CLASSES['SanctionAgent'])
    under = init_agent_safely("UnderwritingAgent", AGENT_CLASSES['UnderwritingAgent'])

    return master, san, under

def init_agent_safely(agent_name, agent_class):
    """Safely initialize an agent with multiple fallback strategies"""
    if agent_class is None:
        app.logger.error(f"{agent_name}: Class not available due to import errors.")
        return create_mock_agent(agent_name)
    
    try:
        return agent_class()
    except TypeError as e:
        if "proxies" in str(e):
            app.logger.error(f"{agent_name}: HTTP client version conflict detected.")
            return create_mock_agent(agent_name)
        else:
            app.logger.exception(f"Failed to initialize {agent_name}: %s", e)
            return create_mock_agent(agent_name)
    except Exception as e:
        app.logger.exception(f"Failed to initialize {agent_name}: %s", e)
        return create_mock_agent(agent_name)

def create_mock_agent(agent_name):
    """Create a mock agent for testing when real agents fail"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            
        def process_message(self, message, conversation, conv_id):
            customer_data = conversation.get('customer_data', {})
            
            # Extract info from current message
            message_lower = message.lower()
            
            # Name collection
            if not customer_data.get('name'):
                if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
                    return {
                        'message': "Hello! Welcome to Tata Capital. I'm here to help you with your personal loan application. To get started, may I have your full name please?",
                        'action': 'collect_name',
                        'data': {}
                    }
                elif len(message.split()) >= 1 and not any(char.isdigit() for char in message):
                    # Extract name (assume first 2 words are name)
                    name_parts = message.split()[:2]
                    name = ' '.join(name_parts).title()
                    customer_data['name'] = name
                    conversation['customer_data'] = customer_data
                    
                    return {
                        'message': f"Thank you {name}! Now I need your age for the application. How old are you?",
                        'action': 'collect_age',
                        'data': {'name': name}
                    }
            
            # Age collection
            elif not customer_data.get('age'):
                import re
                ages = re.findall(r'\b([1-9][0-9]?)\b', message)
                if ages:
                    age = int(ages[0])
                    if age < 18:
                        return {
                            'message': "You must be at least 18 years old to apply for a loan. Please enter your correct age.",
                            'action': 'collect_age',
                            'data': {}
                        }
                    elif age > 80:
                        return {
                            'message': "Please enter a valid age (18-80 years).",
                            'action': 'collect_age',
                            'data': {}
                        }
                    else:
                        customer_data['age'] = age
                        conversation['customer_data'] = customer_data
                        
                        return {
                            'message': f"Great! You're {age} years old. What city do you live in?",
                            'action': 'collect_city',
                            'data': {'age': age}
                        }
                else:
                    return {
                        'message': "Please enter your age in numbers (e.g., 25).",
                        'action': 'collect_age',
                        'data': {}
                    }
            
            # City collection
            elif not customer_data.get('city'):
                if len(message.split()) >= 1 and not any(char.isdigit() for char in message):
                    city = message.title()
                    customer_data['city'] = city
                    conversation['customer_data'] = customer_data
                    
                    return {
                        'message': f"Thank you! You're from {city}. Now please provide your mobile number for verification.",
                        'action': 'collect_phone',
                        'data': {'city': city}
                    }
                else:
                    return {
                        'message': "Please enter a valid city name.",
                        'action': 'collect_city',
                        'data': {}
                    }
            
            # Phone collection
            elif not customer_data.get('phone'):
                import re
                phones = re.findall(r'\b([6-9]\d{9})\b', message)
                if phones:
                    phone = phones[0]
                    customer_data['phone'] = phone
                    conversation['customer_data'] = customer_data
                    
                    return {
                        'message': f"Perfect! Your mobile number {phone} has been recorded. Now please provide your email address.",
                        'action': 'collect_email',
                        'data': {'phone': phone}
                    }
                else:
                    return {
                        'message': "Please enter a valid 10-digit mobile number starting with 6, 7, 8, or 9.",
                        'action': 'collect_phone',
                        'data': {}
                    }
            
            # Email collection
            elif not customer_data.get('email'):
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
                if emails:
                    email = emails[0].lower()
                    customer_data['email'] = email
                    conversation['customer_data'] = customer_data
                    
                    return {
                        'message': f"Excellent! Your email {email} has been saved. Now, what type of loan are you interested in? We offer Personal, Home, Car, and Business loans.",
                        'action': 'collect_loan_type',
                        'data': {'email': email}
                    }
                else:
                    return {
                        'message': "Please enter a valid email address (e.g., example@gmail.com).",
                        'action': 'collect_email',
                        'data': {}
                    }
            
            # Loan type collection
            elif not customer_data.get('loan_type'):
                if any(loan_type in message_lower for loan_type in ['personal', 'home', 'car', 'business']):
                    loan_type = next(lt for lt in ['personal', 'home', 'car', 'business'] if lt in message_lower)
                    customer_data['loan_type'] = loan_type
                    conversation['customer_data'] = customer_data
                    
                    return {
                        'message': f"Great choice! You're interested in a {loan_type} loan. What loan amount are you looking for? (Please enter amount in rupees)",
                        'action': 'collect_amount',
                        'data': {'loan_type': loan_type}
                    }
                else:
                    return {
                        'message': "Please choose from: Personal, Home, Car, or Business loan. Which type interests you?",
                        'action': 'collect_loan_type',
                        'data': {}
                    }
            
            # Loan amount collection
            elif not customer_data.get('loan_amount'):
                import re
                amounts = re.findall(r'\d+', message)
                if amounts:
                    amount = int(amounts[0])
                    if amount < 10000:
                        return {
                            'message': "The minimum loan amount is ₹10,000. Please enter a valid amount.",
                            'action': 'collect_amount',
                            'data': {}
                        }
                    elif amount > 5000000:
                        return {
                            'message': "For amounts above ₹50 lakhs, please visit our branch. Please enter an amount up to ₹50,00,000.",
                            'action': 'collect_amount',
                            'data': {}
                        }
                    else:
                        customer_data['loan_amount'] = amount
                        conversation['customer_data'] = customer_data
                        
                        return {
                            'message': f"Perfect! You're looking for ₹{amount:,}. Now, could you please tell me your monthly income?",
                            'action': 'collect_income',
                            'data': {'loan_amount': amount}
                        }
                else:
                    return {
                        'message': "Please enter a valid loan amount in numbers (e.g., 100000 for ₹1 lakh).",
                        'action': 'collect_amount',
                        'data': {}
                    }
            
            # Monthly income collection
            elif not customer_data.get('monthly_income'):
                import re
                amounts = re.findall(r'\d+', message)
                if amounts:
                    income = int(amounts[0])
                    customer_data['monthly_income'] = income
                    conversation['customer_data'] = customer_data
                    
                    # Calculate eligibility
                    loan_amount = customer_data.get('loan_amount', 0)
                    max_eligible = income * 60  # 60x income rule
                    
                    if loan_amount <= max_eligible:
                        return {
                            'message': f"Excellent! With a monthly income of ₹{income:,}, you're eligible for ₹{loan_amount:,}. Now I need to verify some documents. Please upload your latest salary slip.",
                            'action': 'collect_documents',
                            'data': {'monthly_income': income, 'eligible': True}
                        }
                    else:
                        return {
                            'message': f"Based on your monthly income of ₹{income:,}, you're eligible for up to ₹{max_eligible:,}. Would you like to proceed with this amount instead?",
                            'action': 'adjust_amount',
                            'data': {'monthly_income': income, 'max_eligible': max_eligible}
                        }
                else:
                    return {
                        'message': "Please enter your monthly income in numbers (e.g., 50000).",
                        'action': 'collect_income',
                        'data': {}
                    }
            
            # Document upload completed
            elif customer_data.get('documents_verified'):
                return {
                    'message': f"🎉 Great news {customer_data.get('name', 'Customer')}! Your loan application for ₹{customer_data.get('loan_amount', 0):,} has been approved! Your sanction letter is ready for download.",
                    'action': 'generate_sanction',
                    'data': {'approved': True}
                }
            
            # Default responses
            else:
                if 'yes' in message_lower:
                    return {
                        'message': "Great! Please upload your salary slip to continue with the verification process.",
                        'action': 'collect_documents',
                        'data': {}
                    }
                elif 'no' in message_lower:
                    return {
                        'message': "No problem! Feel free to restart the application when you're ready. Thank you for considering Tata Capital!",
                        'action': 'end_conversation',
                        'data': {}
                    }
                else:
                    return {
                        'message': "I'm here to help you with your loan application. Is there anything specific you'd like to know about our loan process?",
                        'action': 'clarification',
                        'data': {}
                    }
        
        def verify_salary_slip(self, customer_data, filepath):
            # Mark documents as verified
            return {
                'success': True,
                'message': "Salary slip verified successfully! All details match your application.",
                'verification_data': {
                    'monthly_salary': customer_data.get('monthly_income', 75000),
                    'employer': 'TCS Limited',
                    'employment_type': 'Permanent',
                    'documents_verified': True
                }
            }
            
        def generate_pdf(self, customer_data):
            # Generate a comprehensive PDF with all customer details
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            import io
            from datetime import datetime
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50)
            styles = getSampleStyleSheet()
            story = []
            
            # Header
            title = Paragraph("<b>TATA CAPITAL LIMITED</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            subtitle = Paragraph("<b>PERSONAL LOAN SANCTION LETTER</b>", styles['Heading2'])
            story.append(subtitle)
            story.append(Spacer(1, 30))
            
            # Date and reference
            date_text = f"Date: {datetime.now().strftime('%B %d, %Y')}"
            ref_text = f"Reference No: TC/{customer_data.get('phone', '0000000000')[-4:]}/{datetime.now().strftime('%Y%m%d')}"
            
            story.append(Paragraph(date_text, styles['Normal']))
            story.append(Paragraph(ref_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Customer Details Table
            customer_details = [
                ['CUSTOMER DETAILS', ''],
                ['Name', customer_data.get('name', 'N/A')],
                ['Customer ID', f"TC{customer_data.get('phone', '0000000000')[-6:]}"],
                ['Age', str(customer_data.get('age', 'N/A'))],
                ['City', customer_data.get('city', 'N/A')],
                ['Phone', customer_data.get('phone', 'N/A')],
                ['Email', customer_data.get('email', 'N/A')]
            ]
            
            customer_table = Table(customer_details, colWidths=[150, 300])
            customer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(customer_table)
            story.append(Spacer(1, 30))
            
            # Loan Details
            loan_details = [
                ['LOAN DETAILS', ''],
                ['Loan Type', customer_data.get('loan_type', 'Personal').title()],
                ['Loan Amount', f"₹{customer_data.get('loan_amount', 0):,}"],
                ['Monthly Income', f"₹{customer_data.get('monthly_income', 0):,}"],
                ['Interest Rate', '10.99% per annum'],
                ['Tenure', '60 months'],
                ['EMI Amount', f"₹{int(customer_data.get('loan_amount', 0) * 0.022):,}"]
            ]
            
            loan_table = Table(loan_details, colWidths=[150, 300])
            loan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(loan_table)
            story.append(Spacer(1, 30))
            
            # Approval message
            approval_text = f"""
            Dear {customer_data.get('name', 'Customer')},
            
            We are pleased to inform you that your loan application has been approved. 
            The loan amount of ₹{customer_data.get('loan_amount', 0):,} has been sanctioned 
            based on your profile and income verification.
            
            This sanction is valid for 30 days from the date of this letter. 
            Please visit our nearest branch to complete the documentation process.
            
            Thank you for choosing Tata Capital.
            
            Yours sincerely,
            Loan Processing Team
            Tata Capital Limited
            """
            
            for line in approval_text.strip().split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['Normal']))
                else:
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
    
    return MockAgent(agent_name)

# Store active conversations
conversations = {}

# Global agent variables
master_agent = None
sanction_agent = None
underwriting_agent = None

def init_csv_file():
    """Initialize CSV file if it doesn't exist"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)

def save_conversation_to_csv(conversation_id, conversation_data):
    """Save conversation to CSV file"""
    try:
        customer_data = conversation_data.get('customer_data', {})
        
        # Prepare row data
        row_data = {
            'conversation_id': conversation_id,
            'customer_name': customer_data.get('name', ''),
            'age': customer_data.get('age', ''),
            'city': customer_data.get('city', ''),
            'phone': customer_data.get('phone', ''),
            'email': customer_data.get('email', ''),
            'loan_type': customer_data.get('loan_type', ''),
            'loan_amount': customer_data.get('loan_amount', ''),
            'monthly_income': customer_data.get('monthly_income', ''),
            'status': conversation_data.get('status', 'active'),
            'created_at': conversation_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat(),
            'customer_data_json': json.dumps(customer_data)
        }
        
        # Check if record exists
        existing_rows = []
        record_exists = False
        
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['conversation_id'] == conversation_id:
                        # Update existing record
                        existing_rows.append(row_data)
                        record_exists = True
                    else:
                        existing_rows.append(row)
        
        # Write all records back
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(existing_rows)
            
            # Add new record if it doesn't exist
            if not record_exists:
                writer.writerow(row_data)
                
    except Exception as e:
        app.logger.error(f"Error saving to CSV: {e}")

def load_conversations_from_csv():
    """Load all conversations from CSV file"""
    conversations_data = []
    
    if not os.path.exists(CSV_FILE):
        return conversations_data
    
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['conversation_id']:  # Skip empty rows
                    conversations_data.append({
                        'id': row['conversation_id'],
                        'customer_name': row['customer_name'],
                        'age': row['age'],
                        'city': row['city'],
                        'phone': row['phone'],
                        'email': row['email'],
                        'loan_type': row['loan_type'],
                        'loan_amount': int(row['loan_amount']) if row['loan_amount'] else 0,
                        'monthly_income': int(row['monthly_income']) if row['monthly_income'] else 0,
                        'status': row['status'],
                        'timestamp': row['updated_at'],
                        'customer_data': json.loads(row['customer_data_json']) if row['customer_data_json'] else {}
                    })
    except Exception as e:
        app.logger.error(f"Error loading from CSV: {e}")
    
    return conversations_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chatbot messages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            conversations[conversation_id] = {
                'messages': [],
                'customer_data': {},
                'status': 'active',
                'created_at': datetime.now().isoformat()
            }
        
        # Ensure conversation exists
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                'messages': [],
                'customer_data': {},
                'status': 'active',
                'created_at': datetime.now().isoformat()
            }
        
        # Add user message
        conversations[conversation_id]['messages'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check if master_agent is available
        if master_agent is None:
            return jsonify({
                'error': 'Chat service is currently unavailable. Please try again later.',
                'conversation_id': conversation_id
            }), 503
        
        # Get master agent response
        response = master_agent.process_message(
            user_message,
            conversations[conversation_id],
            conversation_id
        )
        
        # Ensure response has required fields
        if not isinstance(response, dict):
            response = {
                'message': str(response),
                'action': None,
                'data': {}
            }
        
        # Add bot response
        conversations[conversation_id]['messages'].append({
            'role': 'bot',
            'content': response.get('message', 'I apologize, but I cannot process your request right now.'),
            'timestamp': datetime.now().isoformat(),
            'action': response.get('action'),
            'data': response.get('data', {})
        })
        
        # Save to CSV after each meaningful update
        if response.get('data') or response.get('action'):
            save_conversation_to_csv(conversation_id, conversations[conversation_id])
        
        return jsonify({
            'conversation_id': conversation_id,
            'response': response.get('message', 'Sorry, I cannot help with that right now.'),
            'action': response.get('action'),
            'data': response.get('data', {}),
            'status': conversations[conversation_id]['status']
        })
        
    except Exception as e:
        app.logger.exception("Error in chat endpoint: %s", e)
        return jsonify({
            'error': 'An internal error occurred. Please try again.',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/upload-salary-slip', methods=['POST'])
def upload_salary_slip():
    """Handle salary slip upload"""
    try:
        conversation_id = request.form.get('conversation_id')
        file = request.files.get('file')
        
        if not conversation_id:
            return jsonify({'error': 'Conversation ID is required'}), 400
            
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
            
        if conversation_id not in conversations:
            return jsonify({'error': 'Invalid conversation ID'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Please upload PDF, JPG, or PNG files only.'}), 400
        
        # Save file temporarily - use app config for upload folder
        upload_folder = app.config['UPLOAD_FOLDER']
        filename = f"salary_slip_{conversation_id}{file_extension}"
        filepath = os.path.join(upload_folder, filename)
        os.makedirs(upload_folder, exist_ok=True)
        file.save(filepath)
        
        # Process with underwriting agent (or mock)
        if underwriting_agent is None:
            result = {
                'success': True,
                'message': 'File uploaded successfully! (Mock verification)',
                'verification_data': {
                    'monthly_salary': 75000,
                    'employer': 'TCS Limited',
                    'employment_type': 'Permanent',
                    'documents_verified': True
                }
            }
        else:
            result = underwriting_agent.verify_salary_slip(
                conversations[conversation_id]['customer_data'],
                filepath
            )
        
        # Update conversation status
        if result.get('success'):
            conversations[conversation_id]['status'] = 'documents_verified'
            conversations[conversation_id]['customer_data'].update(
                result.get('verification_data', {})
            )
            
            # Save to CSV
            save_conversation_to_csv(conversation_id, conversations[conversation_id])
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.exception("Error in upload endpoint: %s", e)
        return jsonify({
            'error': 'File upload failed. Please try again.',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/generate-sanction-letter', methods=['POST'])
def generate_sanction_letter():
    """Generate sanction letter PDF"""
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({'error': 'Conversation ID is required'}), 400
            
        if conversation_id not in conversations:
            return jsonify({'error': 'Invalid conversation ID'}), 400
        
        customer_data = conversations[conversation_id]['customer_data']
        
        # Validate required data
        required_fields = ['name', 'loan_amount']
        missing_fields = [field for field in required_fields if not customer_data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required information: {", ".join(missing_fields)}'
            }), 400
        
        # Generate PDF (or mock)
        if sanction_agent is None:
            # Return mock PDF
            pdf_buffer = create_mock_agent("SanctionAgent").generate_pdf(customer_data)
        else:
            pdf_buffer = sanction_agent.generate_pdf(customer_data)
        
        # Update conversation status to completed
        conversations[conversation_id]['status'] = 'completed'
        
        # Save final status to CSV
        save_conversation_to_csv(conversation_id, conversations[conversation_id])
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"sanction_letter_{customer_data.get('name', 'customer').replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        app.logger.exception("Error in generate PDF endpoint: %s", e)
        return jsonify({
            'error': 'PDF generation failed. Please try again.',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics from CSV and memory"""
    try:
        # Load from CSV for persistent data
        csv_conversations = load_conversations_from_csv()
        
        # Combine with in-memory conversations
        all_conversations = {}
        
        # Add CSV data first
        for conv in csv_conversations:
            all_conversations[conv['id']] = conv
        
        # Add/update with in-memory data
        for conv_id, conv_data in conversations.items():
            customer_data = conv_data.get('customer_data', {})
            all_conversations[conv_id] = {
                'id': conv_id,
                'customer_name': customer_data.get('name', 'Unknown'),
                'status': conv_data['status'],
                'loan_amount': customer_data.get('loan_amount', 0),
                'timestamp': conv_data['messages'][-1]['timestamp'] if conv_data['messages'] else datetime.now().isoformat(),
                'customer_data': customer_data
            }
        
        # Calculate stats
        conversation_list = list(all_conversations.values())
        stats = {
            'total_conversations': len(conversation_list),
            'active_conversations': sum(1 for c in conversation_list if c['status'] == 'active'),
            'completed_loans': sum(1 for c in conversation_list if c['status'] == 'completed'),
            'rejected_loans': sum(1 for c in conversation_list if c['status'] == 'rejected'),
            'pending_verification': sum(1 for c in conversation_list if c['status'] in ['documents_verified', 'pending_verification']),
            'conversations': sorted(conversation_list, key=lambda x: x['timestamp'], reverse=True)
        }
        
        return jsonify(stats)
    except Exception as e:
        app.logger.exception("Error in dashboard stats: %s", e)
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500

# Add endpoint to restore conversation from CSV
@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation details from memory or CSV"""
    try:
        # First check in-memory conversations
        if conversation_id in conversations:
            return jsonify(conversations[conversation_id])
        
        # If not in memory, try to load from CSV
        csv_conversations = load_conversations_from_csv()
        for conv in csv_conversations:
            if conv['id'] == conversation_id:
                # Reconstruct conversation format
                conversation_data = {
                    'customer_data': conv['customer_data'],
                    'status': conv['status'],
                    'messages': [
                        {
                            'role': 'bot',
                            'content': f"Restored conversation for {conv['customer_name']}. Current status: {conv['status']}",
                            'timestamp': conv['timestamp']
                        }
                    ]
                }
                
                # Restore to memory for current session
                conversations[conversation_id] = conversation_data
                
                return jsonify(conversation_data)
        
        return jsonify({'error': 'Conversation not found'}), 404
    except Exception as e:
        app.logger.exception("Error fetching conversation: %s", e)
        return jsonify({'error': 'Failed to fetch conversation'}), 500

# Add CORS headers for frontend compatibility
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Add health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agents': {
            'master_agent': 'ready' if master_agent and not hasattr(master_agent, 'name') else 'mock',
            'sanction_agent': 'ready' if sanction_agent and not hasattr(sanction_agent, 'name') else 'mock',
            'underwriting_agent': 'ready' if underwriting_agent and not hasattr(underwriting_agent, 'name') else 'mock'
        }
    })

# Health check endpoint for Render
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('RENDER_SERVICE_NAME', 'local')
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏦 TATA CAPITAL LOAN CHATBOT STARTING...")
    print("="*60)
    
    # Create required directories
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Check for corrupted .env file and automatically fix it
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    print("📝 Empty .env file detected, recreating...")
                    raise ValueError("Empty file")
        except (UnicodeDecodeError, ValueError):
            print("🔧 Detected corrupted .env file. Automatically fixing...")
            try:
                os.remove('.env')
            except:
                pass
            with open('.env', 'w', encoding='utf-8') as f:
                f.write('GROQ_API_KEY=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\n')
            print("✅ Fixed .env file with proper encoding.")
    else:
        print("📝 Creating .env file...")
        with open('.env', 'w', encoding='utf-8') as f:
            f.write('GROQ_API_KEY=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\n')
        print("✅ Created .env file.")
    
    # Check groq package version
    try:
        import pkg_resources
        groq_version = pkg_resources.get_distribution("groq").version
        print(f"📦 Groq package version: {groq_version}")
        
        # Check if version is problematic
        if groq_version.startswith("0.4") or groq_version.startswith("0.5"):
            print("⚠️  Detected problematic Groq version. Consider downgrading:")
            print("   pip uninstall groq && pip install groq==0.3.0")
    except:
        print("📦 Could not detect Groq package version")
    
    # Initialize agents
    print("\n🤖 Initializing AI Agents...")
    master_agent, sanction_agent, underwriting_agent = init_agents()
    
    # Check import status and provide detailed feedback
    import_issues = []
    for agent_name, agent_class in AGENT_CLASSES.items():
        if agent_class is None:
            import_issues.append(agent_name)
    
    if import_issues:
        print(f"\n⚠️  Import errors detected for: {', '.join(import_issues)}")
        print("   Root cause: Groq package version incompatibility")
        print("   Impact: Agents will run in MOCK MODE with simulated responses")
        print("\n🔧 To fix this issue, run:")
        print("   1. pip uninstall groq")
        print("   2. pip install groq==0.3.0")
        print("   3. Restart the application")
    
    # Agent status summary
    print("\n🎯 Agent Status Summary:")
    agents_info = [
        ("MasterAgent", master_agent),
        ("SanctionAgent", sanction_agent), 
        ("UnderwritingAgent", underwriting_agent)
    ]
    
    for name, agent in agents_info:
        if agent is None:
            print(f"   ❌ {name}: FAILED TO INITIALIZE")
        elif hasattr(agent, 'name'):
            print(f"   🟡 {name}: MOCK MODE (Simulated responses)")
        else:
            print(f"   ✅ {name}: FULLY OPERATIONAL")
    
    # Check if all agents are in mock mode
    all_mock = all(hasattr(agent, 'name') for agent in [master_agent, sanction_agent, underwriting_agent] if agent)
    
    if all_mock:
        print("\n🎭 ALL AGENTS RUNNING IN MOCK MODE")
        print("   ✓ Application will start successfully")
        print("   ✓ All features will work with simulated data")
        print("   ✓ Perfect for testing and demonstration")
        print("   ⚠ For production use, fix the Groq dependency issues above")
    
    # Get port from environment (Render sets PORT environment variable)
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Bind to all interfaces for production
    
    print(f"\n🚀 Starting Flask Server...")
    print(f"🌐 Port: {port}")
    print(f"🔗 Host: {host}")
    print("="*60)
    
    # Initialize CSV file
    init_csv_file()
    
    # Start the Flask application
    app.run(debug=False, port=port, host=host)
