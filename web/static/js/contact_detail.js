// Contact Detail JavaScript Utilities
// Centralized API endpoints and utility functions

const ContactDetailJS = {
    // API Configuration
    API: {
        BASE_URL: window.location.origin,
        ENDPOINTS: {
            CONTACTS: '/api/contacts',
            INTERACTIONS: '/api/interactions',
            OPPORTUNITIES: '/api/opportunities',
            PROJECTS: '/api/projects'
        }
    },

    // Configuration
    Config: {
        CONTACT_ID: null // Will be set by template
    },

    // Utility Functions
    Utils: {
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
        },

        /**
         * Set current datetime in datetime-local input
         */
        setCurrentDateTime: function(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                const now = new Date();
                now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                element.value = now.toISOString().slice(0, 16);
            }
        },

        /**
         * Add double-click navigation to table rows
         */
        addDoubleClickNavigation: function(selector, urlPattern) {
            document.querySelectorAll(selector).forEach(row => {
                row.addEventListener('dblclick', function() {
                    const id = this.dataset.opportunityId || this.dataset.interactionId;
                    if (id) {
                        window.location.href = urlPattern.replace('{id}', id);
                    }
                });
                
                // Add hover effect
                row.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#f8f9fa';
                });
                
                row.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '';
                });
            });
        }
    },

    // Contact Management
    Contacts: {
        loadData: async function() {
            if (!ContactDetailJS.Config.CONTACT_ID) {
                throw new Error('Contact ID not set');
            }

            try {
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.CONTACTS}/${ContactDetailJS.Config.CONTACT_ID}`;
                const contact = await ContactDetailJS.Utils.apiRequest(url);
                
                if (contact.error) {
                    throw new Error(contact.error);
                }
                
                // Populate edit modal fields
                const fieldMappings = {
                    'first_name': 'editFirstName',
                    'last_name': 'editLastName', 
                    'email': 'editEmail',
                    'phone': 'editPhone',
                    'title': 'editTitle',
                    'department': 'editDepartment',
                    'description': 'editDescription'
                };
                
                Object.keys(fieldMappings).forEach(field => {
                    const element = document.getElementById(fieldMappings[field]);
                    if (element) {
                        element.value = contact[field] || '';
                    }
                });

                // Handle account selection
                const accountSelect = document.getElementById('editAccountId');
                if (contact.account_id && accountSelect) {
                    accountSelect.value = contact.account_id;
                    document.getElementById('editAccountOptionExisting').checked = true;
                } else {
                    document.getElementById('editAccountOptionNone').checked = true;
                }
                
                return contact;
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Load contact');
                throw error;
            }
        },

        update: async function(formData) {
            if (!ContactDetailJS.Config.CONTACT_ID) {
                throw new Error('Contact ID not set');
            }

            try {
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.CONTACTS}/${ContactDetailJS.Config.CONTACT_ID}`;
                await ContactDetailJS.Utils.apiRequest(url, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('editContactModal'));
                if (modal) modal.hide();
                
                ContactDetailJS.Utils.reloadWithMessage('Contact updated successfully');
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Update contact');
            }
        },

        initializeEditForm: function() {
            const form = document.getElementById('editContactForm');
            if (!form) return;

            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = {};
                
                // Convert FormData to JSON
                formData.forEach((value, key) => {
                    if (value.trim() !== '') {
                        data[key] = value.trim();
                    }
                });
                
                ContactDetailJS.Contacts.submitEditForm(data);
            });
        },

        loadAccountsForEdit: async function() {
            try {
                const url = `${ContactDetailJS.API.BASE_URL}/api/accounts`;
                const response = await ContactDetailJS.Utils.apiRequest(url);
                
                const select = document.getElementById('editAccountId');
                if (select) {
                    select.innerHTML = '<option value="">Select an account...</option>';
                    
                    // Handle different API response formats
                    let accounts = [];
                    if (response.success && response.accounts) {
                        accounts = response.accounts;
                    } else if (Array.isArray(response)) {
                        accounts = response;
                    }
                    
                    accounts.forEach(account => {
                        const option = document.createElement('option');
                        option.value = account.id;
                        option.textContent = account.name;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading accounts:', error);
            }
        },

        initializeAccountRadioHandlers: function() {
            const radios = document.querySelectorAll('input[name="accountOption"]');
            const existingSection = document.getElementById('editExistingAccountSection');
            const newSection = document.getElementById('editNewAccountSection');
            const newAccountName = document.getElementById('editNewAccountName');

            radios.forEach(radio => {
                radio.addEventListener('change', function() {
                    if (this.value === 'existing') {
                        existingSection.classList.remove('d-none');
                        newSection.classList.add('d-none');
                        newAccountName.removeAttribute('required');
                    } else if (this.value === 'new') {
                        existingSection.classList.add('d-none');
                        newSection.classList.remove('d-none');
                        newAccountName.setAttribute('required', 'required');
                    } else { // none
                        existingSection.classList.add('d-none');
                        newSection.classList.add('d-none');
                        newAccountName.removeAttribute('required');
                    }
                });
            });

            // Set initial state
            const checkedRadio = document.querySelector('input[name="accountOption"]:checked');
            if (checkedRadio) {
                checkedRadio.dispatchEvent(new Event('change'));
            }
        },

        submitEditForm: async function(formData) {
            try {
                const accountOption = formData.accountOption;
                let finalData = { ...formData };

                // Remove account option fields from final data
                delete finalData.accountOption;
                delete finalData.new_account_name;
                delete finalData.new_account_type;
                delete finalData.new_account_industry;
                delete finalData.new_account_website;
                delete finalData.new_account_description;

                // Handle account assignment
                if (accountOption === 'new' && formData.new_account_name) {
                    // Create new account first
                    const newAccountData = {
                        name: formData.new_account_name,
                        type: formData.new_account_type || 'Customer',
                        industry: formData.new_account_industry || '',
                        website: formData.new_account_website || '',
                        description: formData.new_account_description || ''
                    };

                    const accountUrl = `${ContactDetailJS.API.BASE_URL}/api/create_account`;
                    const accountResponse = await ContactDetailJS.Utils.apiRequest(accountUrl, {
                        method: 'POST',
                        body: JSON.stringify(newAccountData)
                    });

                    if (accountResponse.success && accountResponse.account_id) {
                        finalData.account_id = accountResponse.account_id;
                    }
                } else if (accountOption === 'existing' && formData.account_id) {
                    finalData.account_id = formData.account_id;
                } else if (accountOption === 'none') {
                    finalData.account_id = null;
                }

                // Update the contact
                await ContactDetailJS.Contacts.update(finalData);
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Save contact');
            }
        }
    },

    // Account Assignment
    Accounts: {
        loadAccounts: async function() {
            try {
                const url = `${ContactDetailJS.API.BASE_URL}/api/accounts`;
                const response = await ContactDetailJS.Utils.apiRequest(url);
                
                const select = document.getElementById('accountSelect');
                if (select) {
                    select.innerHTML = '<option value="">Select Account</option>';
                    
                    response.accounts.forEach(account => {
                        const option = document.createElement('option');
                        option.value = account.id;
                        option.textContent = `${account.name} (${account.type})`;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading accounts:', error);
                const select = document.getElementById('accountSelect');
                if (select) {
                    select.innerHTML = '<option value="">Error loading accounts</option>';
                }
            }
        },

        assignExisting: async function(accountId) {
            try {
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.CONTACTS}/${ContactDetailJS.Config.CONTACT_ID}`;
                await ContactDetailJS.Utils.apiRequest(url, {
                    method: 'PUT',
                    body: JSON.stringify({ account_id: accountId })
                });
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('assignAccountModal'));
                if (modal) modal.hide();
                
                ContactDetailJS.Utils.reloadWithMessage('Account assigned successfully');
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Assign account');
            }
        },

        createAndAssign: async function(accountData) {
            try {
                // First create the account
                const createUrl = `${ContactDetailJS.API.BASE_URL}/api/create_account`;
                const createResponse = await ContactDetailJS.Utils.apiRequest(createUrl, {
                    method: 'POST',
                    body: JSON.stringify(accountData)
                });
                
                const accountId = createResponse.account_id || createResponse.id;
                
                // Then assign it to the contact
                await ContactDetailJS.Accounts.assignExisting(accountId);
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Create and assign account');
            }
        },

        initializeForm: function() {
            const form = document.getElementById('assignAccountForm');
            if (!form) return;

            // Handle radio button changes
            const radios = form.querySelectorAll('input[name="assignmentType"]');
            radios.forEach(radio => {
                radio.addEventListener('change', function() {
                    const existingSection = document.getElementById('existingAccountSection');
                    const newSection = document.getElementById('newAccountSection');
                    const accountSelect = document.getElementById('accountSelect');
                    const newAccountName = document.getElementById('newAccountName');
                    const newAccountType = document.getElementById('newAccountType');
                    
                    if (this.value === 'existing') {
                        existingSection.style.display = 'block';
                        newSection.style.display = 'none';
                        accountSelect.required = true;
                        newAccountName.required = false;
                        newAccountType.required = false;
                    } else {
                        existingSection.style.display = 'none';
                        newSection.style.display = 'block';
                        accountSelect.required = false;
                        newAccountName.required = true;
                        newAccountType.required = true;
                    }
                });
            });

            // Handle form submission
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const assignmentType = formData.get('assignmentType');
                
                if (assignmentType === 'existing') {
                    const accountId = formData.get('account_id');
                    if (accountId) {
                        ContactDetailJS.Accounts.assignExisting(accountId);
                    }
                } else {
                    const accountData = {
                        name: formData.get('name'),
                        type: formData.get('type'),
                        email: formData.get('email') || '',
                        website: formData.get('website') || '',
                        location: formData.get('location') || ''
                    };
                    ContactDetailJS.Accounts.createAndAssign(accountData);
                }
            });
        }
    },
    Interactions: {
        add: async function(formData) {
            try {
                // Ensure contact_id is set
                formData.contact_id = ContactDetailJS.Config.CONTACT_ID;
                
                // Map form field names to database field names
                if (formData.message) {
                    formData.description = formData.message;
                    delete formData.message;
                }
                
                // Map interaction_date to date for API compatibility
                if (formData.interaction_date !== undefined) {
                    formData.date = formData.interaction_date;
                    delete formData.interaction_date;
                }
                
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.INTERACTIONS}`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('addInteractionModal'));
                if (modal) modal.hide();
                
                // Reset form
                document.getElementById('addInteractionForm').reset();
                ContactDetailJS.Utils.setCurrentDateTime('interactionDate');
                document.getElementById('interactionStatus').value = 'Completed';
                
                ContactDetailJS.Utils.reloadWithMessage('Interaction added successfully');
            } catch (error) {
                ContactDetailJS.Utils.handleApiError(error, 'Add interaction');
            }
        },

        loadOpportunities: async function() {
            try {
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.OPPORTUNITIES}`;
                
                const opportunities = await fetch(url).then(response => response.json());
                
                const select = document.getElementById('interactionOpportunity');
                
                if (select) {
                    select.innerHTML = '<option value="">Select Opportunity</option>';
                    
                    opportunities.forEach(opp => {
                        const option = document.createElement('option');
                        option.value = opp.id;
                        option.textContent = `${opp.name} - ${opp.nsn || 'No NSN'}`;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading opportunities:', error);
            }
        },

        loadProjects: async function() {
            try {
                const url = `${ContactDetailJS.API.BASE_URL}${ContactDetailJS.API.ENDPOINTS.PROJECTS}`;
                const projects = await fetch(url).then(response => response.json());
                
                const select = document.getElementById('interactionProject');
                if (select) {
                    select.innerHTML = '<option value="">Select Project</option>';
                    
                    projects.forEach(project => {
                        const option = document.createElement('option');
                        option.value = project.id;
                        option.textContent = project.name || `Project ${project.id}`;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading projects:', error);
            }
        },

        initializeForm: function() {
            const form = document.getElementById('addInteractionForm');
            if (!form) return;

            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = {};
                
                // Convert FormData to JSON with special handling for required fields
                formData.forEach((value, key) => {
                    // Always include interaction_date even if empty - it will be handled by the server
                    if (key === 'interaction_date') {
                        data[key] = value; // Don't trim datetime values
                    } else if (value && value.trim() !== '') {
                        data[key] = value.trim();
                    }
                });
                
                ContactDetailJS.Interactions.add(data);
            });
        }
    },

    // Modal Management
    Modals: {
        initializeEditContact: function() {
            const modal = document.getElementById('editContactModal');
            if (!modal) return;

            modal.addEventListener('show.bs.modal', async function() {
                try {
                    await ContactDetailJS.Contacts.loadData();
                    await ContactDetailJS.Contacts.loadAccountsForEdit();
                    ContactDetailJS.Contacts.initializeAccountRadioHandlers();
                } catch (error) {
                    // Error already handled in loadData
                }
            });
        },

        initializeAddInteraction: function() {
            const modal = document.getElementById('addInteractionModal');
            if (!modal) return;

            modal.addEventListener('show.bs.modal', function() {
                // Set current date/time as default
                ContactDetailJS.Utils.setCurrentDateTime('interactionDate');
                
                // Set default status to Completed
                const statusField = document.getElementById('interactionStatus');
                if (statusField) statusField.value = 'Completed';
                
                // Load opportunities and projects
                ContactDetailJS.Interactions.loadOpportunities();
                ContactDetailJS.Interactions.loadProjects();
            });
        },

        initializeAssignAccount: function() {
            const modal = document.getElementById('assignAccountModal');
            if (!modal) return;

            modal.addEventListener('show.bs.modal', function() {
                // Load accounts for selection
                ContactDetailJS.Accounts.loadAccounts();
                
                // Reset form to default state
                const existingRadio = document.getElementById('existingAccount');
                if (existingRadio) {
                    existingRadio.checked = true;
                    existingRadio.dispatchEvent(new Event('change'));
                }
            });
        }
    },

    // Navigation
    Navigation: {
        initializeTableNavigation: function() {
            // Add double-click functionality to opportunity rows
            ContactDetailJS.Utils.addDoubleClickNavigation(
                '.opportunity-row', 
                '/opportunity/{id}'
            );
            
            // Add double-click functionality to interaction rows
            ContactDetailJS.Utils.addDoubleClickNavigation(
                '.interaction-row', 
                '/interactions/{id}'
            );
        }
    },

    // Initialize all functionality
    init: function(contactId) {
        // Set contact ID
        ContactDetailJS.Config.CONTACT_ID = contactId;
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => ContactDetailJS.init(contactId));
            return;
        }
        
        // Initialize all components
        ContactDetailJS.Contacts.initializeEditForm();
        ContactDetailJS.Interactions.initializeForm();
        ContactDetailJS.Accounts.initializeForm();
        ContactDetailJS.Modals.initializeEditContact();
        ContactDetailJS.Modals.initializeAddInteraction();
        ContactDetailJS.Modals.initializeAssignAccount();
        ContactDetailJS.Navigation.initializeTableNavigation();
    }
};

// Global functions for backward compatibility
window.loadContactData = () => ContactDetailJS.Contacts.loadData();
window.saveContactChanges = () => {
    const form = document.getElementById('editContactForm');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.addInteraction = () => {
    const form = document.getElementById('addInteractionForm');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.loadOpportunitiesForInteraction = () => ContactDetailJS.Interactions.loadOpportunities();
window.loadProjectsForInteraction = () => ContactDetailJS.Interactions.loadProjects();
window.viewOpportunity = (id) => window.location.href = `/opportunity/${id}`;
window.editOpportunity = (id) => window.location.href = `/opportunity/${id}?edit=true`;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContactDetailJS;
}
