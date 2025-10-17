# Tata Capital Loan Chatbot - Quick Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Groq API Key (Free tier available at https://console.groq.com)

## Installation Steps

### 1. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Configure Groq API Key
Create a `.env` file in the project root:
\`\`\`bash
echo "GROQ_API_KEY=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" > .env
\`\`\`

Or manually create `.env` with:
\`\`\`
GROQ_API_KEY=your_groq_api_key_here
\`\`\`

### 3. Run the Application
\`\`\`bash
python app.py
\`\`\`

### 4. Access the Application
- **Chatbot**: http://localhost:5000
- **Dashboard**: http://localhost:5000/dashboard

## Project Structure

\`\`\`
tata-capital-loan-chatbot/
├── app.py                    # Main Flask application
├── config.py                 # Configuration (Groq API)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # Full documentation
├── SETUP_GUIDE.md           # This file
│
├── agents/                   # AI Agents
│   ├── master_agent.py      # Master orchestrator (Groq AI)
│   ├── sales_agent.py       # Sales engagement
│   ├── verification_agent.py # KYC verification
│   ├── underwriting_agent.py # Credit evaluation
│   └── sanction_agent.py    # PDF generation
│
├── data/                     # CSV Data Files
│   ├── customers.csv         # 10 test customers
│   ├── kyc_data.csv          # KYC verification data
│   ├── credit_scores.csv     # Credit scores
│   └── offers.csv            # Pre-approved limits
│
├── templates/                # HTML Templates
│   ├── index.html            # Chatbot interface
│   └── dashboard.html        # Analytics dashboard
│
└── static/                   # Frontend Assets
    ├── css/
    │   ├── style.css         # Global styles
    │   ├── chatbot.css       # Chatbot UI
    │   └── dashboard.css     # Dashboard UI
    └── js/
        ├── utils.js          # Utility functions
        ├── chatbot.js        # Chatbot logic
        └── dashboard.js      # Dashboard logic
\`\`\`

## Key Features

✓ **Groq AI Integration** - Natural language understanding
✓ **Master Agent Orchestration** - Coordinates 4 Worker Agents
✓ **6-Stage Conversation Flow** - Greeting to Approval
✓ **Real-time Processing** - Instant eligibility checks
✓ **PDF Generation** - Professional sanction letters
✓ **Responsive UI** - Mobile & desktop optimized
✓ **Analytics Dashboard** - Real-time statistics
✓ **CSV Data Management** - Easy to test and modify

## Loan Processing Stages

1. **Greeting** - Welcome customer
2. **Qualification** - Extract loan amount
3. **Personal Details** - Collect name, age, city
4. **Verification** - Verify KYC details
5. **Underwriting** - Evaluate eligibility
6. **Approval** - Generate sanction letter

## Eligibility Criteria

- Credit Score: ≥ 700
- Age: 21-65 years
- Instant Approval: Loan ≤ Pre-approved limit
- With Salary Slip: Loan ≤ 2x Pre-approved limit
- EMI Ratio: ≤ 50% of salary

## Test Customers

| Name | Phone | Credit Score | Pre-approved Limit |
|------|-------|---------------|--------------------|
| Rajesh Kumar | 9876543210 | 750 | ₹5,00,000 |
| Priya Singh | 9876543211 | 800 | ₹4,00,000 |
| Amit Patel | 9876543212 | 720 | ₹6,00,000 |

## Troubleshooting

**Port 5000 already in use?**
\`\`\`bash
# Change port in app.py
app.run(debug=True, port=5001)
\`\`\`

**Groq API Key error?**
- Verify `.env` file exists
- Check API key is correct
- Ensure no extra spaces in `.env`

**CSV files not found?**
- Ensure `data/` folder exists
- Check all CSV files are present

## Next Steps

1. Test with sample customers
2. Try different loan amounts
3. Check dashboard for statistics
4. Download sanction letters
5. Customize for your needs

## Support

Refer to `README.md` for detailed documentation and architecture diagrams.
