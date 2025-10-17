class ChatBot {
    constructor() {
        this.conversationId = this.loadConversationId();
        this.isTyping = false;
        this.conversationState = {
            step: 'greeting',
            data: {}
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateQuickInfo();
        this.addRestartButton();
        
        // Load existing conversation if available
        if (this.conversationId) {
            this.loadExistingConversation();
        }
    }

    loadConversationId() {
        return localStorage.getItem('tata_conversation_id');
    }

    saveConversationId(id) {
        this.conversationId = id;
        localStorage.setItem('tata_conversation_id', id);
    }

    clearConversationId() {
        this.conversationId = null;
        localStorage.removeItem('tata_conversation_id');
    }

    async loadExistingConversation() {
        try {
            const response = await fetch(`/api/conversation/${this.conversationId}`);
            if (response.ok) {
                const conversation = await response.json();
                this.restoreConversation(conversation);
            } else {
                // Conversation not found in memory or CSV, clear stored ID
                this.clearConversationId();
                // Show option to continue or start new
                this.addMessage("Welcome back! It looks like your previous session expired. Would you like to start a new loan application?", 'bot');
            }
        } catch (error) {
            console.error('Error loading existing conversation:', error);
            this.clearConversationId();
            this.addMessage("Welcome back! Starting a fresh loan application session.", 'bot');
        }
    }

    restoreConversation(conversation) {
        const chatMessages = document.getElementById('chatMessages');
        // Clear existing messages
        chatMessages.innerHTML = '';
        
        // Add restart button first
        this.addRestartButton();

        // Check if this is a CSV-restored conversation (minimal messages)
        if (conversation.messages && conversation.messages.length <= 2) {
            // This is likely a CSV restore - create a summary message
            const customerData = conversation.customer_data || {};
            let summaryMessage = "Welcome back! Here's your application summary:\n\n";
            
            if (customerData.name) summaryMessage += `Name: ${customerData.name}\n`;
            if (customerData.age) summaryMessage += `Age: ${customerData.age}\n`;
            if (customerData.city) summaryMessage += `City: ${customerData.city}\n`;
            if (customerData.phone) summaryMessage += `Phone: ${customerData.phone}\n`;
            if (customerData.email) summaryMessage += `Email: ${customerData.email}\n`;
            if (customerData.loan_type) summaryMessage += `Loan Type: ${customerData.loan_type}\n`;
            if (customerData.loan_amount) summaryMessage += `Loan Amount: ₹${customerData.loan_amount.toLocaleString()}\n`;
            if (customerData.monthly_income) summaryMessage += `Monthly Income: ₹${customerData.monthly_income.toLocaleString()}\n`;
            
            summaryMessage += `\nStatus: ${conversation.status}\n\n`;
            
            if (conversation.status === 'completed') {
                summaryMessage += "Your loan has been approved! You can download your sanction letter below.";
                this.addMessage(summaryMessage, 'bot');
                this.showSanctionLetterButton();
            } else if (conversation.status === 'documents_verified') {
                summaryMessage += "Your documents have been verified. Your application is being processed.";
                this.addMessage(summaryMessage, 'bot');
                setTimeout(() => {
                    this.addMessage('🎉 Great news! Your loan application has been approved! Your sanction letter is ready for download.', 'bot');
                    this.showSanctionLetterButton();
                }, 2000);
            } else {
                summaryMessage += "You can continue where you left off. What would you like to do next?";
                this.addMessage(summaryMessage, 'bot');
            }
        } else {
            // Restore full conversation history
            conversation.messages.forEach(msg => {
                this.addMessage(msg.content, msg.role);
            });
        }

        // Update UI with conversation data
        if (conversation.customer_data) {
            this.conversationState.data = conversation.customer_data;
            this.updateQuickInfo(conversation.customer_data);
            
            // Update process steps based on data completeness
            this.updateProcessStepsFromData(conversation.customer_data, conversation.status);
        }
    }

    updateProcessStepsFromData(data, status) {
        if (data.name) this.updateProcessSteps('collect_name');
        if (data.age) this.updateProcessSteps('collect_age');
        if (data.city) this.updateProcessSteps('collect_city');
        if (data.phone) this.updateProcessSteps('collect_phone');
        if (data.email) this.updateProcessSteps('collect_email');
        if (data.loan_type) this.updateProcessSteps('collect_loan_type');
        if (data.loan_amount) this.updateProcessSteps('collect_amount');
        if (data.monthly_income) this.updateProcessSteps('collect_income');
        if (data.documents_verified) this.updateProcessSteps('collect_documents');
        if (status === 'completed') this.updateProcessSteps('generate_sanction');
    }

    addRestartButton() {
        const chatMessages = document.getElementById('chatMessages');
        const restartDiv = document.createElement('div');
        restartDiv.className = 'text-center p-3 border-bottom';
        restartDiv.innerHTML = `
            <button class="btn btn-outline-secondary btn-sm" onclick="chatBot.restartConversation()">
                🔄 Start New Application
            </button>
        `;
        chatMessages.insertBefore(restartDiv, chatMessages.firstChild);
    }

    restartConversation() {
        if (confirm('Are you sure you want to start a new loan application? Your current progress will be saved and you can continue it later from the dashboard.')) {
            // Don't clear the conversation ID immediately - let it be saved first
            const oldConversationId = this.conversationId;
            
            // Clear stored conversation from localStorage only
            localStorage.removeItem('tata_conversation_id');
            this.conversationId = null;
            
            // Reset state
            this.conversationState = {
                step: 'greeting',
                data: {}
            };
            
            // Clear UI
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
            
            // Reset Quick Info
            document.getElementById('applicationStatus').textContent = '-';
            document.getElementById('loanAmount').textContent = '-';
            document.getElementById('creditScore').textContent = '-';
            
            // Re-initialize
            this.init();
            
            // Add welcome message
            this.addMessage("Hello! Welcome to Tata Capital. I'm here to help you with your loan application. To get started, may I have your full name please?", 'bot');
        }
    }

    bindEvents() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const uploadButton = document.getElementById('uploadFileButton');

        // Send message on button click
        sendButton.addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // File upload handler
        if (uploadButton) {
            uploadButton.addEventListener('click', () => this.uploadFile());
        }

        // Auto-resize input
        messageInput.addEventListener('input', this.autoResizeInput);
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message || this.isTyping) return;

        // Clear input
        messageInput.value = '';

        // Add user message to chat
        this.addMessage(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Use relative URLs that work in both development and production
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            const data = await response.json();
            console.log('API Response:', data);

            // Hide typing indicator
            this.hideTypingIndicator();

            if (response.ok) {
                // Store conversation ID
                this.saveConversationId(data.conversation_id);

                // Update conversation state
                if (data.data) {
                    this.conversationState.data = { ...this.conversationState.data, ...data.data };
                }
                if (data.action) {
                    this.conversationState.step = data.action;
                }

                // Add bot response
                this.addMessage(data.response, 'bot');

                // Handle actions
                this.handleAction(data.action, data.data);

                // Update UI
                this.updateQuickInfo(this.conversationState.data);
                this.updateProcessSteps(data.action);
            } else {
                console.error('API Error:', data);
                this.addMessage(data.error || 'Sorry, something went wrong. Please try again.', 'bot', 'error');
            }
        } catch (error) {
            console.error('Network Error:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I cannot connect to the server. Please check your connection and try again.', 'bot', 'error');
        }
    }

    addMessage(content, sender, type = 'normal') {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'error') {
            messageContent.style.backgroundColor = '#f8d7da';
            messageContent.style.color = '#721c24';
            messageContent.style.border = '1px solid #f5c6cb';
        }

        messageContent.textContent = content;
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const chatMessages = document.getElementById('chatMessages');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        const typingDots = document.createElement('div');
        typingDots.className = 'typing-dots';
        typingDots.innerHTML = '<span></span><span></span><span></span>';
        
        typingDiv.appendChild(typingDots);
        chatMessages.appendChild(typingDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    handleAction(action, data) {
        switch (action) {
            case 'collect_name':
                this.updateProcessSteps('qualification');
                break;
            case 'collect_age':
                this.updateProcessSteps('qualification');
                break;
            case 'collect_city':
                this.updateProcessSteps('qualification');
                break;
            case 'collect_phone':
                this.updateProcessSteps('qualification');
                break;
            case 'collect_email':
                this.updateProcessSteps('qualification');
                break;
            case 'collect_loan_type':
                this.updateProcessSteps('personal-details');
                break;
            case 'collect_amount':
                this.updateProcessSteps('personal-details');
                break;
            case 'collect_income':
                this.updateProcessSteps('verification');
                break;
            case 'collect_documents':
                this.updateProcessSteps('verification');
                setTimeout(() => this.showFileUploadModal(), 1000);
                break;
            case 'upload_documents':
                this.showFileUploadModal();
                break;
            case 'process_application':
                this.updateProcessSteps('underwriting');
                break;
            case 'generate_sanction':
                this.updateProcessSteps('approval');
                this.showSanctionLetterButton();
                break;
        }
    }

    updateQuickInfo(data = {}) {
        // Update customer name and status
        if (data.name) {
            document.getElementById('applicationStatus').textContent = 'In Progress';
        }
        
        // Update loan amount
        if (data.loan_amount) {
            document.getElementById('loanAmount').textContent = `₹${parseInt(data.loan_amount).toLocaleString()}`;
        }
        
        // Update credit score based on multiple factors
        if (data.monthly_income && data.age) {
            const income = parseInt(data.monthly_income);
            const age = parseInt(data.age);
            let creditScore = 'Fair';
            
            // Age factor (25-45 is optimal)
            const ageScore = age >= 25 && age <= 45 ? 1 : 0.8;
            
            // Income factor
            let incomeScore = 0.5;
            if (income >= 75000) incomeScore = 1;
            else if (income >= 50000) incomeScore = 0.9;
            else if (income >= 30000) incomeScore = 0.7;
            
            const totalScore = (ageScore + incomeScore) / 2;
            
            if (totalScore >= 0.9) creditScore = 'Excellent';
            else if (totalScore >= 0.75) creditScore = 'Very Good';
            else if (totalScore >= 0.6) creditScore = 'Good';
            
            document.getElementById('creditScore').textContent = creditScore;
        }
        
        // Update progress bar
        const progressSteps = ['name', 'age', 'city', 'phone', 'email', 'loan_type', 'loan_amount', 'monthly_income'];
        const completedSteps = progressSteps.filter(step => data[step]).length;
        const progressPercentage = Math.round((completedSteps / progressSteps.length) * 100);
        
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${progressPercentage}%`;
            progressBar.textContent = `${progressPercentage}%`;
            
            // Update color based on progress
            if (progressPercentage === 100) {
                progressBar.className = 'progress-bar bg-success';
            } else if (progressPercentage >= 50) {
                progressBar.className = 'progress-bar bg-info';
            } else {
                progressBar.className = 'progress-bar bg-warning';
            }
        }
    }

    updateProcessSteps(currentStep) {
        const steps = ['greeting', 'qualification', 'personal-details', 'verification', 'underwriting', 'approval'];
        const currentIndex = steps.indexOf(currentStep);
        
        steps.forEach((step, index) => {
            const stepElement = document.getElementById(`step-${step}`);
            if (stepElement) {
                stepElement.classList.remove('completed', 'active');
                
                if (index < currentIndex) {
                    stepElement.classList.add('completed');
                } else if (index === currentIndex) {
                    stepElement.classList.add('active');
                }
            }
        });
    }

    showFileUploadModal() {
        const modal = new bootstrap.Modal(document.getElementById('fileUploadModal'));
        modal.show();
    }

    async uploadFile() {
        const fileInput = document.getElementById('salarySlipFile');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file to upload.');
            return;
        }

        if (!this.conversationId) {
            alert('Please start a conversation first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('conversation_id', this.conversationId);

        // Show progress
        const progress = document.getElementById('uploadProgress');
        progress.style.display = 'block';
        progress.querySelector('.progress-bar').style.width = '50%';

        try {
            const response = await fetch('/api/upload-salary-slip', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            progress.querySelector('.progress-bar').style.width = '100%';

            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('fileUploadModal'));
                modal.hide();
                progress.style.display = 'none';
                progress.querySelector('.progress-bar').style.width = '0%';
                fileInput.value = '';

                if (response.ok) {
                    this.addMessage('✅ ' + data.message, 'bot');
                    this.updateProcessSteps('underwriting');
                    
                    // Trigger approval process
                    setTimeout(() => {
                        this.addMessage('🎉 Great news! Your loan application has been approved! Your sanction letter is ready for download.', 'bot');
                        this.showSanctionLetterButton();
                    }, 2000);
                } else {
                    this.addMessage('❌ ' + (data.error || 'File upload failed.'), 'bot', 'error');
                }
            }, 500);

        } catch (error) {
            console.error('Error uploading file:', error);
            progress.style.display = 'none';
            alert('File upload failed. Please try again.');
        }
    }

    showSanctionLetterButton() {
        const chatMessages = document.getElementById('chatMessages');
        const buttonDiv = document.createElement('div');
        buttonDiv.className = 'message bot-message';
        buttonDiv.innerHTML = `
            <div class="message-content">
                <p>🎉 Congratulations! Your loan has been approved!</p>
                <button class="btn btn-success btn-sm" onclick="chatBot.downloadSanctionLetter()">
                    📄 Download Sanction Letter
                </button>
            </div>
        `;
        chatMessages.appendChild(buttonDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async downloadSanctionLetter() {
        if (!this.conversationId) {
            alert('No active conversation found.');
            return;
        }

        try {
            const response = await fetch('/api/generate-sanction-letter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: this.conversationId
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sanction-letter.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.addMessage('✅ Sanction letter downloaded successfully!', 'bot');
                this.updateProcessSteps('approval');
            } else {
                const data = await response.json();
                this.addMessage('❌ ' + (data.error || 'Failed to generate sanction letter.'), 'bot', 'error');
            }
        } catch (error) {
            console.error('Error downloading sanction letter:', error);
            this.addMessage('❌ Failed to download sanction letter. Please try again.', 'bot', 'error');
        }
    }

    autoResizeInput(event) {
        const input = event.target;
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new ChatBot();
});
