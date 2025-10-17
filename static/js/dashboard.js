// Dashboard functionality

class Dashboard {
    constructor() {
        this.init();
    }

    init() {
        this.loadDashboardStats();
        this.refreshInterval = setInterval(() => {
            this.loadDashboardStats();
        }, 30000); // Refresh every 30 seconds
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/dashboard-stats');
            const data = await response.json();

            if (response.ok) {
                this.updateStatsCards(data);
                this.updateConversationsTable(data.conversations);
            } else {
                console.error('Failed to load dashboard stats:', data.error);
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    updateStatsCards(data) {
        document.getElementById('totalConversations').textContent = data.total_conversations;
        document.getElementById('activeConversations').textContent = data.active_conversations;
        document.getElementById('completedLoans').textContent = data.completed_loans;
        document.getElementById('pendingVerification').textContent = data.pending_verification;
    }

    updateConversationsTable(conversations) {
        const tbody = document.getElementById('conversationsTable');
        tbody.innerHTML = '';

        if (conversations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No conversations found</td></tr>';
            return;
        }

        conversations.forEach(conv => {
            const row = document.createElement('tr');
            
            // Format timestamp
            const timestamp = new Date(conv.timestamp).toLocaleString();
            
            // Status badge
            const statusBadge = this.getStatusBadge(conv.status);
            
            row.innerHTML = `
                <td>${conv.id.substring(0, 8)}...</td>
                <td>${conv.customer_name}</td>
                <td>₹${parseInt(conv.loan_amount || 0).toLocaleString()}</td>
                <td>${statusBadge}</td>
                <td>${timestamp}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.viewConversation('${conv.id}')">
                        View
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }

    getStatusBadge(status) {
        const statusMap = {
            'active': '<span class="badge bg-primary">Active</span>',
            'documents_verified': '<span class="badge bg-info">Documents Verified</span>',
            'completed': '<span class="badge bg-success">Completed</span>',
            'rejected': '<span class="badge bg-danger">Rejected</span>',
            'pending_verification': '<span class="badge bg-warning">Pending Verification</span>'
        };
        
        return statusMap[status] || '<span class="badge bg-secondary">Unknown</span>';
    }

    async viewConversation(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}`);
            const data = await response.json();

            if (response.ok) {
                this.showConversationModal(data);
            } else {
                alert('Failed to load conversation details: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            alert('Failed to load conversation details.');
        }
    }

    showConversationModal(conversation) {
        const modal = new bootstrap.Modal(document.getElementById('conversationModal'));
        const detailsDiv = document.getElementById('conversationDetails');
        
        // Customer Data - handle both formats
        const customerData = conversation.customer_data || {};
        
        let customerInfo = `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0">Customer Information</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Name:</strong> ${customerData.name || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>Age:</strong> ${customerData.age || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>City:</strong> ${customerData.city || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>Phone:</strong> ${customerData.phone || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>Email:</strong> ${customerData.email || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>Loan Type:</strong> ${customerData.loan_type || 'Not provided'}
                        </div>
                        <div class="col-md-6">
                            <strong>Loan Amount:</strong> ₹${parseInt(customerData.loan_amount || 0).toLocaleString()}
                        </div>
                        <div class="col-md-6">
                            <strong>Monthly Income:</strong> ₹${parseInt(customerData.monthly_income || 0).toLocaleString()}
                        </div>
                        <div class="col-md-6">
                            <strong>Status:</strong> ${this.getStatusBadge(conversation.status)}
                        </div>
                        <div class="col-md-6">
                            <strong>Employer:</strong> ${customerData.employer || 'Not provided'}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Messages - handle cases where messages might be minimal
        let messagesHtml = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Conversation History</h6>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.continueConversation('${conversation.id || conversation.conversation_id}')">
                        Continue Conversation
                    </button>
                </div>
                <div class="card-body" style="max-height: 400px; overflow-y: auto;">
        `;

        if (conversation.messages && conversation.messages.length > 0) {
            conversation.messages.forEach(msg => {
                const timestamp = new Date(msg.timestamp).toLocaleString();
                const messageClass = msg.role === 'user' ? 'bg-primary text-white' : 'bg-light';
                const alignClass = msg.role === 'user' ? 'ms-auto' : 'me-auto';
                
                messagesHtml += `
                    <div class="message-item mb-2 ${alignClass}" style="max-width: 80%;">
                        <div class="p-2 rounded ${messageClass}">
                            <strong>${msg.role === 'user' ? 'Customer' : 'Bot'}:</strong> ${msg.content}
                            <div class="small opacity-75">${timestamp}</div>
                        </div>
                    </div>
                `;
            });
        } else {
            messagesHtml += `
                <div class="text-center text-muted">
                    <p>This conversation was restored from saved data.</p>
                    <p>Click "Continue Conversation" to resume the chat.</p>
                </div>
            `;
        }

        messagesHtml += `
                </div>
            </div>
        `;

        detailsDiv.innerHTML = customerInfo + messagesHtml;
        modal.show();
    }

    continueConversation(conversationId) {
        // Store the conversation ID in localStorage
        localStorage.setItem('tata_conversation_id', conversationId);
        
        // Navigate to chatbot page
        window.location.href = '/';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
