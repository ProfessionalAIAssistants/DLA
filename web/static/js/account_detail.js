// Account Detail JavaScript Utilities
// Centralized API endpoints and utility functions

const AccountDetailJS = {
    // API Configuration
    API: {
        BASE_URL: window.location.origin,
        ENDPOINTS: {
            ACCOUNTS: '/api/accounts',
            CONTACTS: '/api/contacts', 
            QPL: '/api/qpl'
        }
    },

    // Utility Functions
    Utils: {
        /**
         * Show confirmation dialog with consistent styling
         */
        confirmDelete: function(message, item = '') {
            const fullMessage = item ? 
                `Are you sure you want to delete ${item}? This action cannot be undone.` : 
                message;
            return confirm(fullMessage);
        },

        /**
         * Handle API errors consistently
         */
        handleApiError: function(error, context = 'Operation') {
            console.error(`${context} error:`, error);
            const message = error.message || 'An unexpected error occurred';
            alert(`${context} failed: ${message}`);
        },

        /**
         * Make API request with error handling
         */
        apiRequest: async function(url, options = {}) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();
            } catch (error) {
                console.error('API Request failed:', error);
                throw error;
            }
        },

        /**
         * Reload page with success message
         */
        reloadWithMessage: function(message) {
            alert(message);
            window.location.reload();
        }
    },

    // Contact Management
    Contacts: {
        delete: async function(contactId, contactName) {
            if (!AccountDetailJS.Utils.confirmDelete(`contact "${contactName}"`)) {
                return;
            }

            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.CONTACTS}/${contactId}`;
                await AccountDetailJS.Utils.apiRequest(url, { method: 'DELETE' });
                AccountDetailJS.Utils.reloadWithMessage('Contact deleted successfully');
            } catch (error) {
                AccountDetailJS.Utils.handleApiError(error, 'Delete contact');
            }
        },

        initializeDeleteButtons: function() {
            document.querySelectorAll('.delete-contact-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const contactId = this.dataset.contactId;
                    const contactName = this.dataset.contactName;
                    AccountDetailJS.Contacts.delete(contactId, contactName);
                });
            });
        }
    },

    // Account Management
    Accounts: {
        delete: async function(accountId) {
            const message = 'Are you sure you want to delete this account? This will also delete all associated contacts and data. This action cannot be undone.';
            if (!confirm(message)) {
                return;
            }

            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.ACCOUNTS}/${accountId}`;
                await AccountDetailJS.Utils.apiRequest(url, { method: 'DELETE' });
                alert('Account deleted successfully!');
                window.location.href = '/accounts';
            } catch (error) {
                AccountDetailJS.Utils.handleApiError(error, 'Delete account');
            }
        },

        loadForEdit: async function(accountId) {
            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.ACCOUNTS}/${accountId}`;
                const account = await AccountDetailJS.Utils.apiRequest(url);
                
                // Populate form fields with all account data
                const fieldMappings = {
                    'editAccountName': 'name',
                    'editAccountType': 'type', 
                    'editCageCode': 'cage',
                    'editAccountLocation': 'location',
                    'editWebsite': 'website',
                    'editEmail': 'email',
                    'editLinkedIn': 'linkedin',
                    'editParentCompany': 'parent_co',
                    'editAccountSummary': 'summary'
                };
                
                Object.entries(fieldMappings).forEach(([elementId, fieldName]) => {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.value = account[fieldName] || '';
                    }
                });
                
                // Load parent company options
                await AccountDetailJS.Accounts.loadParentCompanyOptions(accountId);
                
                // Store account ID for form submission
                document.getElementById('editAccountForm').dataset.accountId = accountId;
                
                // Show the modal
                new bootstrap.Modal(document.getElementById('editAccountModal')).show();
            } catch (error) {
                AccountDetailJS.Utils.handleApiError(error, 'Load account');
            }
        },

        loadParentCompanyOptions: async function(currentAccountId) {
            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.ACCOUNTS}`;
                const accounts = await AccountDetailJS.Utils.apiRequest(url);
                
                const parentSelect = document.getElementById('editParentCompany');
                if (parentSelect && accounts) {
                    // Clear existing options except the first one
                    parentSelect.innerHTML = '<option value="">No Parent Company</option>';
                    
                    // Add all accounts except the current one as potential parents
                    accounts.forEach(account => {
                        if (account.id != currentAccountId) {
                            const option = document.createElement('option');
                            option.value = account.id;
                            option.textContent = account.name;
                            parentSelect.appendChild(option);
                        }
                    });
                }
            } catch (error) {
                console.warn('Could not load parent company options:', error);
            }
        },

        update: async function(accountId, formData) {
            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.ACCOUNTS}/${accountId}`;
                await AccountDetailJS.Utils.apiRequest(url, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                
                bootstrap.Modal.getInstance(document.getElementById('editAccountModal')).hide();
                AccountDetailJS.Utils.reloadWithMessage('Account updated successfully!');
            } catch (error) {
                AccountDetailJS.Utils.handleApiError(error, 'Update account');
            }
        },

        initializeEditForm: function() {
            const form = document.getElementById('editAccountForm');
            if (!form) return;

            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const accountId = this.dataset.accountId;
                const formData = new FormData(this);
                const data = {};
                
                // Convert FormData to JSON, excluding empty values
                for (let [key, value] of formData.entries()) {
                    if (value.trim() !== '') {
                        data[key] = value.trim();
                    }
                }
                
                AccountDetailJS.Accounts.update(accountId, data);
            });
        }
    },

    // QPL Management
    QPL: {
        delete: async function(qplId) {
            if (!AccountDetailJS.Utils.confirmDelete('remove this product from the QPL')) {
                return;
            }

            try {
                const url = `${AccountDetailJS.API.BASE_URL}${AccountDetailJS.API.ENDPOINTS.QPL}/${qplId}`;
                await AccountDetailJS.Utils.apiRequest(url, { method: 'DELETE' });
                AccountDetailJS.Utils.reloadWithMessage('QPL entry removed successfully!');
            } catch (error) {
                AccountDetailJS.Utils.handleApiError(error, 'Remove QPL entry');
            }
        },

        initializeTable: function() {
            const table = document.getElementById('qplTable');
            if (table && typeof $ !== 'undefined' && $.fn.DataTable) {
                $(table).DataTable({
                    responsive: true,
                    pageLength: 10,
                    order: [[0, 'asc']], // Sort by NSN
                    columnDefs: [
                        { orderable: false, targets: [5] } // Disable sorting for Actions column
                    ]
                });
            }
        }
    },

    // Initialize all functionality
    init: function() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', AccountDetailJS.init);
            return;
        }

        // Initialize all components
        AccountDetailJS.Contacts.initializeDeleteButtons();
        AccountDetailJS.Accounts.initializeEditForm();
        AccountDetailJS.QPL.initializeTable();
    }
};

// Global functions for backward compatibility
window.deleteContact = AccountDetailJS.Contacts.delete;
window.deleteAccount = AccountDetailJS.Accounts.delete;
window.editAccount = AccountDetailJS.Accounts.loadForEdit;
window.deleteQPLEntry = AccountDetailJS.QPL.delete;

// Auto-initialize
AccountDetailJS.init();
