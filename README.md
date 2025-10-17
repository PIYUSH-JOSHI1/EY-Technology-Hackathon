# Tata Capital - AI-Driven Personal Loan Chatbot

## Overview

This is a comprehensive Flask-based web application that implements an **Agentic AI solution** for personal loan sales and processing. The system uses a Master Agent that orchestrates multiple Worker Agents to handle the complete loan journey from customer engagement to sanction letter generation.

## Architecture

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER INTERFACE                        │
│              (HTML/CSS/JS Web Chatbot)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   MASTER AGENT                               │
│         (Orchestrates Conversation Flow)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
        ▼            ▼            ▼              ▼
   ┌────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐
   │ SALES  │  │VERIF.    │  │UNDERWRITING│  │SANCTION  │
   │ AGENT  │  │ AGENT    │  │ AGENT      │  │ AGENT    │
   └────────┘  └──────────┘  └────────────┘  └──────────┘
        │            │            │              │
        └────────────┼────────────┼──────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │CUSTOMERS│  │KYC DATA  │  │CREDIT    │
   │CSV      │  │CSV       │  │SCORES CSV│
   └─────────┘  └──────────┘  └──────────┘
\`\`\`

## System Components

### 1. **Master Agent** (`agents/master_agent.py`)
- Manages the entire conversation flow
- Orchestrates Worker Agents based on conversation stage
- Handles state management for each conversation
- Stages: Greeting → Qualification → Personal Details → Verification → Underwriting → Approval

### 2. **Worker Agents**

#### Sales Agent (`agents/sales_agent.py`)
- Greets customers and assesses interest
- Extracts loan amount from user input
- Negotiates loan terms and EMI calculations
- Provides personalized recommendations

#### Verification Agent (`agents/verification_agent.py`)
- Verifies KYC details against CRM database
- Validates customer information
- Retrieves customer history and existing loans
- Confirms eligibility for loan processing

#### Underwriting Agent (`agents/underwriting_agent.py`)
- Fetches credit scores from mock credit bureau
- Evaluates loan eligibility based on:
  - Credit score (minimum 700)
  - Pre-approved limit
  - Loan amount requested
- Determines if salary slip verification is needed
- Calculates EMI and validates against salary

#### Sanction Agent (`agents/sanction_agent.py`)
- Generates professional PDF sanction letters
- Includes customer details, loan terms, and conditions
- Uses ReportLab for PDF generation
- Provides downloadable sanction letter to customer

### 3. **Frontend** (`templates/` & `static/`)
- **Responsive HTML/CSS/JS** (no frameworks)
- **Chatbot Interface**: Real-time conversation with bot
- **Dashboard**: Analytics and conversation tracking
- **Mobile-Optimized**: Works seamlessly on all devices
- **Banking Theme**: Professional blue/green color scheme

### 4. **Data Layer** (`data/`)
- **customers.csv**: Customer master data
- **kyc_data.csv**: KYC verification data
- **credit_scores.csv**: Mock credit bureau data
- **offers.csv**: Pre-approved loan offers

## Loan Processing Flow

\`\`\`
1. GREETING
   └─> Customer expresses interest in personal loan

2. QUALIFICATION
   └─> Extract loan amount needed
   └─> Validate amount range

3. PERSONAL DETAILS
   └─> Collect: Name, Age, City
   └─> Validate information

4. VERIFICATION
   └─> Collect: Phone, Address
   └─> Verify against KYC database
   └─> Retrieve customer history

5. UNDERWRITING
   ├─> Fetch credit score
   ├─> Check credit score >= 700
   ├─> Compare with pre-approved limit
   │
   ├─> IF amount <= pre-approved limit
   │   └─> INSTANT APPROVAL ✓
   │
   ├─> IF amount <= 2x pre-approved limit
   │   └─> REQUEST SALARY SLIP
   │   └─> Verify EMI <= 50% of salary
   │   └─> APPROVE/REJECT
   │
   └─> IF amount > 2x pre-approved limit
       └─> REJECT ✗

6. APPROVAL
   └─> Generate sanction letter PDF
   └─> Provide download link
   └─> Update conversation status
\`\`\`

## Eligibility Criteria

| Criteria | Requirement |
|----------|-------------|
| Credit Score | Minimum 700 |
| Age | 21-65 years |
| Loan Amount (Instant) | ≤ Pre-approved limit |
| Loan Amount (With Salary Slip) | ≤ 2x Pre-approved limit |
| EMI to Salary Ratio | ≤ 50% |
| Interest Rate | 12% p.a. (fixed) |
| Tenure | 12-60 months |

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Steps

1. **Clone/Download the project**
   \`\`\`bash
   cd tata-capital-loan-chatbot
   \`\`\`

2. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Run the Flask app**
   \`\`\`bash
   python app.py
   \`\`\`

4. **Access the application**
   - Open browser: `http://localhost:5000`
   - Chatbot: `http://localhost:5000/`
   - Dashboard: `http://localhost:5000/dashboard`

## Project Structure

\`\`\`
tata-capital-loan-chatbot/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── agents/                         # AI Agent modules
│   ├── master_agent.py            # Master orchestrator
│   ├── sales_agent.py             # Sales engagement
│   ├── verification_agent.py      # KYC verification
│   ├── underwriting_agent.py      # Credit evaluation
│   └── sanction_agent.py          # Letter generation
│
├── data/                          # CSV data files
│   ├── customers.csv              # Customer master data
│   ├── kyc_data.csv               # KYC verification data
│   ├── credit_scores.csv          # Credit bureau data
│   └── offers.csv                 # Pre-approved offers
│
├── templates/                     # HTML templates
│   ├── index.html                 # Chatbot interface
│   └── dashboard.html             # Analytics dashboard
│
├── static/                        # Static assets
│   ├── css/
│   │   ├── style.css              # Global styles
│   │   ├── chatbot.css            # Chatbot styles
│   │   └── dashboard.css          # Dashboard styles
│   └── js/
│       ├── utils.js               # Utility functions
│       ├── chatbot.js             # Chatbot logic
│       └── dashboard.js           # Dashboard logic
│
└── uploads/                       # Salary slip uploads (auto-created)
\`\`\`

## Key Features

### 1. **Conversational AI**
- Natural language understanding
- Context-aware responses
- Multi-stage conversation flow
- Personalized customer engagement

### 2. **Agentic Orchestration**
- Master Agent coordinates multiple Worker Agents
- Each agent has specific responsibilities
- Seamless handoff between agents
- Efficient task delegation

### 3. **Real-time Processing**
- Instant credit score lookup
- KYC verification
- Eligibility evaluation
- Sanction letter generation

### 4. **Responsive UI**
- Mobile-first design
- Works on all screen sizes
- Clean, professional banking theme
- Intuitive user experience

### 5. **Analytics Dashboard**
- Real-time conversation tracking
- Loan approval statistics
- Customer journey visualization
- Performance metrics

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chatbot interface |
| `/dashboard` | GET | Analytics dashboard |
| `/api/chat` | POST | Process chat message |
| `/api/upload-salary-slip` | POST | Upload salary slip |
| `/api/generate-sanction-letter` | POST | Generate PDF letter |
| `/api/dashboard-stats` | GET | Get dashboard statistics |
| `/api/conversation/<id>` | GET | Get conversation details |

## Sample Conversation Flow

\`\`\`
Bot: Hello! Welcome to Tata Capital. I'm your personal loan assistant. 
     Are you interested in a personal loan today?

User: Yes, I need a personal loan

Bot: Great! Let me understand your loan requirements better. 
     What loan amount are you looking for?

User: I need 5 lakhs

Bot: Great! A loan of ₹5,00,000 is a good amount. Now, let me collect 
     your basic details. What's your full name?

User: Rajesh Kumar

Bot: Nice to meet you, Rajesh Kumar! What's your age?

User: 35

Bot: Which city are you based in?

User: Mumbai

Bot: Thank you! Now let me verify your KYC details. 
     What's your registered phone number?

User: 9876543210

Bot: What's your registered address?

User: 123 Marine Drive Mumbai

Bot: Perfect! Your KYC details are verified. Now let me check your eligibility...

Bot: Excellent news! Your loan of ₹5,00,000 has been approved! 
     Your sanction letter is ready for download.

[Download Sanction Letter Button]
\`\`\`

## Testing

### Test Customers
Use these customer details to test the system:

| Name | Phone | Address | Credit Score | Pre-approved Limit |
|------|-------|---------|---------------|--------------------|
| Rajesh Kumar | 9876543210 | 123 Marine Drive Mumbai | 750 | ₹5,00,000 |
| Priya Singh | 9876543211 | 456 Connaught Place Delhi | 800 | ₹4,00,000 |
| Amit Patel | 9876543212 | 789 MG Road Bangalore | 720 | ₹6,00,000 |

### Test Scenarios

1. **Instant Approval**: Request loan ≤ pre-approved limit
2. **Salary Slip Required**: Request loan between 1x-2x pre-approved limit
3. **Rejection**: Request loan > 2x pre-approved limit or credit score < 700

## Customization

### Change Interest Rate
Edit `agents/sales_agent.py` and `agents/underwriting_agent.py`:
\`\`\`python
interest_rate = 12.0  # Change this value
\`\`\`

### Add More Customers
Add rows to `data/customers.csv`, `data/kyc_data.csv`, `data/credit_scores.csv`, and `data/offers.csv`

### Modify UI Theme
Edit `static/css/style.css` and update CSS variables:
\`\`\`css
:root {
    --primary-color: #003366;
    --secondary-color: #0066cc;
    --accent-color: #00a86b;
}
\`\`\`

## Performance Considerations

- **CSV-based data**: Suitable for demo/testing (10-100 customers)
- **For production**: Migrate to database (PostgreSQL, MySQL)
- **Caching**: Implement Redis for frequently accessed data
- **Async processing**: Use Celery for long-running tasks

## Security Notes

- This is a demo application
- For production:
  - Implement proper authentication
  - Use HTTPS/SSL
  - Validate all inputs
  - Implement rate limiting
  - Add CSRF protection
  - Encrypt sensitive data

## Future Enhancements

1. **Multi-language Support**: Hindi, Tamil, Telugu, etc.
2. **Advanced NLP**: Use transformers for better understanding
3. **Video KYC**: Integrate video verification
4. **Mobile App**: React Native/Flutter app
5. **Payment Integration**: Razorpay/Stripe integration
6. **Document Upload**: Support multiple document types
7. **Loan Tracking**: Post-approval loan management
8. **Analytics**: Advanced reporting and insights

## Troubleshooting

### Port Already in Use
\`\`\`bash
# Change port in app.py
app.run(debug=True, port=5001)
\`\`\`

### CSV File Not Found
Ensure `data/` folder exists with all CSV files

### PDF Generation Error
Install reportlab: `pip install reportlab`

## Support

For issues or questions:
1. Check the README
2. Review the code comments
3. Check Flask logs for errors
4. Verify CSV data format

## License

This project is created for Tata Capital as part of the BFSI AI Challenge.

---

**Built with ❤️ using Flask, Python, and Vanilla JavaScript**

# Tata Capital Loan Chatbot

A full-stack web application for loan application processing with AI-powered chatbot assistance.

## Features

- Interactive chatbot for loan applications
- Document upload and verification
- PDF sanction letter generation
- Admin dashboard for application management
- Persistent data storage with CSV
- Real-time conversation management

## Deployment on Render

### Prerequisites

1. GitHub repository with your code
2. Render account
3. Groq API key

### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
     - **Environment Variables**:
       - `GROQ_API_KEY`: Your Groq API key
       - `SECRET_KEY`: Auto-generate or set custom
       - `PYTHON_VERSION`: 3.12.0

3. **Environment Variables Required**
   - `GROQ_API_KEY`: Your Groq API key
   - `SECRET_KEY`: Flask secret key (auto-generated recommended)
   - `PORT`: Auto-set by Render

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_groq_api_key_here

# Run locally
python app.py
```

### Production Features

- Persistent CSV storage for loan applications
- File upload handling
- Error logging and monitoring
- Health check endpoints
- Production-ready gunicorn server
- Environment-based configuration

## API Endpoints

- `GET /` - Main chatbot interface
- `GET /dashboard` - Admin dashboard
- `POST /api/chat` - Chat API
- `POST /api/upload-salary-slip` - Document upload
- `POST /api/generate-sanction-letter` - PDF generation
- `GET /api/dashboard-stats` - Dashboard statistics
- `GET /health` - Health check

## Tech Stack

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **AI**: Groq API
- **Storage**: CSV files
- **Deployment**: Render
- **PDF Generation**: ReportLab
