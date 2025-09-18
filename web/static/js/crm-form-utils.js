/**
 * CRM Form Utilities - Common JavaScript functions for form handling
 */

class CRMFormUtils {
    
    /**
     * Generic API call handler
     */
    static async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            console.log(`Making ${method} request to ${endpoint}`, data);
            const response = await fetch(endpoint, options);
            console.log('Response received:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('Response data:', result);
            return result;
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }
    
    /**
     * Load dropdown options from API
     */
    static async loadDropdownData(selectId, endpoint, valueField = 'id', labelField = 'name', emptyOption = true) {
        try {
            const data = await this.apiCall(endpoint);
            const select = document.getElementById(selectId);
            
            if (!select) {
                console.error(`Select element ${selectId} not found`);
                return;
            }
            
            // Clear existing options
            select.innerHTML = '';
            
            // Add empty option if requested
            if (emptyOption) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = `Select ${select.previousElementSibling.textContent.replace(' *', '')}`;
                select.appendChild(option);
            }
            
            // Add data options
            if (data && Array.isArray(data)) {
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item[valueField];
                    option.textContent = item[labelField];
                    select.appendChild(option);
                });
            }
            
            console.log(`Loaded ${data.length} options for ${selectId}`);
        } catch (error) {
            console.error(`Error loading dropdown data for ${selectId}:`, error);
        }
    }
    
    /**
     * Generic form validation
     */
    static validateForm(formContainer, requiredFields = []) {
        const errors = [];
        
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (!field) {
                errors.push(`Field ${fieldId} not found`);
                return;
            }
            
            const value = field.value.trim();
            if (!value) {
                const label = field.previousElementSibling.textContent.replace(' *', '');
                errors.push(`${label} is required`);
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return errors;
    }
    
    /**
     * Extract form data from container
     */
    static extractFormData(formContainer, fieldMappings = {}) {
        const data = {};
        const inputs = formContainer.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const id = input.id;
            const name = fieldMappings[id] || input.name || id;
            let value = input.value.trim();
            
            // Convert empty strings to null for optional fields
            if (value === '') {
                value = null;
            }
            
            data[name] = value;
        });
        
        return data;
    }
    
    /**
     * Reset form fields
     */
    static resetForm(formContainer, defaultValues = {}) {
        const inputs = formContainer.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const defaultValue = defaultValues[input.id] || '';
            
            if (input.type === 'checkbox') {
                input.checked = defaultValue;
            } else {
                input.value = defaultValue;
            }
            
            // Remove validation classes
            input.classList.remove('is-invalid', 'is-valid');
        });
    }
    
    /**
     * Close modal and reset form
     */
    static closeModal(modalId, formContainerId = null) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
        
        if (formContainerId) {
            const formContainer = document.getElementById(formContainerId);
            if (formContainer) {
                this.resetForm(formContainer);
            }
        }
    }
    
    /**
     * Show success message and optionally reload page
     */
    static showSuccess(message, reload = false) {
        console.log('Success:', message);
        // You could implement toast notifications here
        alert(message);
        
        if (reload) {
            location.reload();
        }
    }
    
    /**
     * Show error message
     */
    static showError(message) {
        console.error('Error:', message);
        alert('Error: ' + message);
    }
}

/**
 * Task-specific form handler
 */
class TaskFormHandler {
    constructor(modalId, formContainerId, opportunityId = null) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.opportunityId = opportunityId;
        this.fieldMappings = {
            taskSubject: 'subject',
            taskPriority: 'priority',
            taskStatus: 'status',
            taskWorkDate: 'work_date',
            taskDueDate: 'due_date',
            taskAssignedTo: 'assigned_to',
            taskOwner: 'owner',
            taskDescription: 'description',
            task_contact_id: 'contact_id',
            task_account_id: 'account_id',
            task_opportunity_id: 'opportunity_id',
            task_quote_id: 'quote_id'
        };
    }
    
    async loadDropdowns() {
        console.log('Loading task form dropdowns...');
        await Promise.all([
            CRMFormUtils.loadDropdownData('task_contact_id', '/api/contacts'),
            CRMFormUtils.loadDropdownData('task_account_id', '/api/accounts'),
            CRMFormUtils.loadDropdownData('task_opportunity_id', '/api/opportunities'),
            CRMFormUtils.loadDropdownData('task_quote_id', '/api/quotes')
        ]);
        
        // Set default opportunity if provided
        if (this.opportunityId) {
            const opportunitySelect = document.getElementById('task_opportunity_id');
            if (opportunitySelect) {
                opportunitySelect.value = this.opportunityId;
            }
        }
    }
    
    async saveTask() {
        console.log('=== SAVING TASK ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['taskSubject']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            // Set default opportunity if creating from opportunity page
            if (this.opportunityId && !formData.opportunity_id) {
                formData.opportunity_id = this.opportunityId;
            }
            
            console.log('Task data:', formData);
            
            // Save via API
            const result = await CRMFormUtils.apiCall('/api/tasks', 'POST', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Task created successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to create task');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving task: ' + error.message);
        }
    }
}

/**
 * Account-specific form handler
 */
class AccountFormHandler {
    constructor(modalId, formContainerId, accountId = null) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.accountId = accountId;
        this.fieldMappings = {
            editAccountName: 'name',
            editAccountType: 'type',
            editCageCode: 'cage',
            editAccountLocation: 'location',
            editWebsite: 'website',
            editEmail: 'email',
            editLinkedIn: 'linkedin',
            editParentCompany: 'parent_co',
            editAccountSummary: 'summary'
        };
    }
    
    async loadAccountData() {
        if (!this.accountId) return;
        
        try {
            const account = await CRMFormUtils.apiCall(`/api/accounts/${this.accountId}`);
            this.populateForm(account);
        } catch (error) {
            console.error('Error loading account data:', error);
        }
    }
    
    populateForm(account) {
        const formContainer = document.getElementById(this.formContainerId);
        if (!formContainer) return;
        
        // Populate form fields with account data
        Object.entries(this.fieldMappings).forEach(([fieldId, apiField]) => {
            const field = document.getElementById(fieldId);
            if (field && account[apiField] !== undefined) {
                field.value = account[apiField] || '';
            }
        });
    }
    
    async loadParentCompanies() {
        await CRMFormUtils.loadDropdownData('editParentCompany', '/api/accounts', 'id', 'name', false);
    }
    
    async saveAccount() {
        console.log('=== SAVING ACCOUNT ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['editAccountName']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            console.log('Account data:', formData);
            
            // Update via API
            const result = await CRMFormUtils.apiCall(`/api/accounts/${this.accountId}`, 'PUT', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Account updated successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to update account');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving account: ' + error.message);
        }
    }
}

/**
 * Contact-specific form handler
 */
class ContactFormHandler {
    constructor(modalId, formContainerId, accountId) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.accountId = accountId;
        this.fieldMappings = {
            contactFirstName: 'first_name',
            contactLastName: 'last_name',
            contactTitle: 'title',
            contactDepartment: 'department',
            contactEmail: 'email',
            contactPhone: 'phone',
            contactMobile: 'mobile',
            contactLinkedIn: 'linkedin',
            contactNotes: 'notes',
            contactAccountId: 'account_id'
        };
    }
    
    async saveContact() {
        console.log('=== SAVING CONTACT ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['contactFirstName', 'contactLastName']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            // Ensure account ID is set
            formData.account_id = this.accountId;
            
            console.log('Contact data:', formData);
            
            // Save via API
            const result = await CRMFormUtils.apiCall('/api/contacts', 'POST', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Contact created successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to create contact');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving contact: ' + error.message);
        }
    }
}

/**
 * Relationship-specific form handler
 */
class RelationshipFormHandler {
    constructor(modalId, formContainerId, accountId, accountType) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.accountId = accountId;
        this.accountType = accountType;
        this.targetType = accountType === 'QPL' ? 'Vendor' : 'QPL';
    }
    
    async loadRelationshipOptions() {
        console.log('Loading relationship options...');
        const endpoint = `/api/accounts/${this.targetType.toLowerCase()}`;
        await CRMFormUtils.loadDropdownData('relationshipAccount', endpoint, 'id', 'name', false);
        
        // Add the "Create New" option back
        const select = document.getElementById('relationshipAccount');
        if (select) {
            const newOption = document.createElement('option');
            newOption.value = 'new';
            newOption.textContent = `+ Create New ${this.targetType}`;
            select.appendChild(newOption);
        }
    }
    
    toggleNewAccountForm() {
        const select = document.getElementById('relationshipAccount');
        const newAccountForm = document.getElementById('newAccountForm');
        
        if (select && newAccountForm) {
            if (select.value === 'new') {
                newAccountForm.style.display = 'block';
            } else {
                newAccountForm.style.display = 'none';
                // Clear new account form
                ['newAccountName', 'newAccountLocation', 'newAccountEmail', 'newAccountCage'].forEach(id => {
                    const field = document.getElementById(id);
                    if (field) field.value = '';
                });
            }
        }
    }
    
    async saveRelationship() {
        console.log('=== SAVING RELATIONSHIP ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            const relationshipAccount = document.getElementById('relationshipAccount').value;
            const notes = document.getElementById('relationshipNotes').value;
            
            let targetAccountId = relationshipAccount;
            
            // If creating new account, create it first
            if (relationshipAccount === 'new') {
                const newAccountData = {
                    name: document.getElementById('newAccountName').value,
                    location: document.getElementById('newAccountLocation').value,
                    email: document.getElementById('newAccountEmail').value,
                    type: this.targetType
                };
                
                const cageField = document.getElementById('newAccountCage');
                if (cageField) {
                    newAccountData.cage = cageField.value;
                }
                
                // Validate new account data
                if (!newAccountData.name.trim()) {
                    CRMFormUtils.showError('Account name is required');
                    return;
                }
                
                const newAccount = await CRMFormUtils.apiCall('/api/accounts', 'POST', newAccountData);
                if (!newAccount.success) {
                    CRMFormUtils.showError('Failed to create new account: ' + (newAccount.message || 'Unknown error'));
                    return;
                }
                targetAccountId = newAccount.account_id;
            }
            
            if (!targetAccountId) {
                CRMFormUtils.showError('Please select an account or create a new one');
                return;
            }
            
            // Create the relationship
            const relationshipData = {
                source_account_id: this.accountId,
                target_account_id: targetAccountId,
                relationship_type: this.accountType === 'QPL' ? 'approved_vendor' : 'qpl_manufacturer',
                notes: notes
            };
            
            console.log('Relationship data:', relationshipData);
            
            const result = await CRMFormUtils.apiCall('/api/account-relationships', 'POST', relationshipData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Relationship created successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to create relationship');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving relationship: ' + error.message);
        }
    }
}

/**
 * Interaction-specific form handler
 */
class InteractionFormHandler {
    constructor(modalId, formContainerId, interactionId = null) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.interactionId = interactionId;
        this.fieldMappings = {
            editInteractionType: 'type',
            editDirection: 'direction',
            editInteractionDate: 'interaction_date',
            editDurationMinutes: 'duration_minutes',
            editStatus: 'status',
            editLocation: 'location',
            editSubject: 'subject',
            editContactId: 'contact_id',
            editOpportunityId: 'opportunity_id',
            editProjectId: 'project_id',
            editDescription: 'description',
            editOutcome: 'outcome'
        };
    }
    
    async loadDropdowns() {
        console.log('Loading interaction form dropdowns...');
        await Promise.all([
            CRMFormUtils.loadDropdownData('editContactId', '/api/contacts'),
            CRMFormUtils.loadDropdownData('editOpportunityId', '/api/opportunities'),
            CRMFormUtils.loadDropdownData('editProjectId', '/api/projects')
        ]);
    }
    
    async loadInteractionData() {
        if (!this.interactionId) return;
        
        try {
            const interaction = await CRMFormUtils.apiCall(`/api/interactions/${this.interactionId}`);
            this.populateForm(interaction);
        } catch (error) {
            console.error('Error loading interaction data:', error);
        }
    }
    
    populateForm(interaction) {
        const formContainer = document.getElementById(this.formContainerId);
        if (!formContainer) return;
        
        // Populate form fields with interaction data
        Object.entries(this.fieldMappings).forEach(([fieldId, apiField]) => {
            const field = document.getElementById(fieldId);
            if (field && interaction[apiField] !== undefined) {
                if (fieldId === 'editInteractionDate' && interaction[apiField]) {
                    // Handle datetime-local format
                    const date = new Date(interaction[apiField]);
                    field.value = date.toISOString().slice(0, 16);
                } else {
                    field.value = interaction[apiField] || '';
                }
            }
        });
    }
    
    async saveInteraction() {
        console.log('=== SAVING INTERACTION ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['editInteractionType', 'editDirection', 'editInteractionDate', 'editSubject']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            console.log('Interaction data:', formData);
            
            // Update via API
            const result = await CRMFormUtils.apiCall(`/api/interactions/${this.interactionId}`, 'PUT', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Interaction updated successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to update interaction');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving interaction: ' + error.message);
        }
    }
}

/**
 * Follow-up-specific form handler
 */
class FollowupFormHandler {
    constructor(modalId, formContainerId, parentInteractionId = null) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.parentInteractionId = parentInteractionId;
        this.fieldMappings = {
            followupType: 'type',
            followupDirection: 'direction',
            followupDate: 'interaction_date',
            followupDurationMinutes: 'duration_minutes',
            followupStatus: 'status',
            followupLocation: 'location',
            followupSubject: 'subject',
            followupContactId: 'contact_id',
            followupOpportunityId: 'opportunity_id',
            followupProjectId: 'project_id',
            followupDescription: 'description'
        };
    }
    
    async loadDropdowns() {
        console.log('Loading follow-up form dropdowns...');
        await Promise.all([
            CRMFormUtils.loadDropdownData('followupContactId', '/api/contacts'),
            CRMFormUtils.loadDropdownData('followupOpportunityId', '/api/opportunities'),
            CRMFormUtils.loadDropdownData('followupProjectId', '/api/projects')
        ]);
    }
    
    async initializeFromParent() {
        if (!this.parentInteractionId) return;
        
        try {
            const parentInteraction = await CRMFormUtils.apiCall(`/api/interactions/${this.parentInteractionId}`);
            
            // Pre-populate some fields based on parent interaction
            document.getElementById('followupContactId').value = parentInteraction.contact_id || '';
            document.getElementById('followupOpportunityId').value = parentInteraction.opportunity_id || '';
            document.getElementById('followupProjectId').value = parentInteraction.project_id || '';
            document.getElementById('followupSubject').value = `Follow-up: ${parentInteraction.subject || ''}`;
            document.getElementById('followupDescription').value = `Follow-up to previous ${parentInteraction.type || 'interaction'} on ${parentInteraction.interaction_date || 'unknown date'}`;
            
            // Set default date to tomorrow
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(9, 0, 0, 0); // 9 AM tomorrow
            document.getElementById('followupDate').value = tomorrow.toISOString().slice(0, 16);
            
        } catch (error) {
            console.error('Error loading parent interaction data:', error);
        }
    }
    
    async saveFollowup() {
        console.log('=== SAVING FOLLOW-UP ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['followupType', 'followupDirection', 'followupDate', 'followupSubject']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            // Add parent interaction reference
            if (this.parentInteractionId) {
                formData.parent_interaction_id = this.parentInteractionId;
            }
            
            console.log('Follow-up data:', formData);
            
            // Create via API
            const result = await CRMFormUtils.apiCall('/api/interactions', 'POST', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Follow-up interaction created successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to create follow-up');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving follow-up: ' + error.message);
        }
    }
}

/**
 * Duplicate interaction form handler
 */
class DuplicateInteractionFormHandler {
    constructor(modalId, formContainerId, sourceInteractionId = null) {
        this.modalId = modalId;
        this.formContainerId = formContainerId;
        this.sourceInteractionId = sourceInteractionId;
        this.fieldMappings = {
            duplicateInteractionType: 'type',
            duplicateDirection: 'direction',
            duplicateInteractionDate: 'interaction_date',
            duplicateDurationMinutes: 'duration_minutes',
            duplicateStatus: 'status',
            duplicateLocation: 'location',
            duplicateSubject: 'subject',
            duplicateContactId: 'contact_id',
            duplicateOpportunityId: 'opportunity_id',
            duplicateProjectId: 'project_id',
            duplicateDescription: 'description'
        };
    }
    
    async loadDropdowns() {
        console.log('Loading duplicate form dropdowns...');
        await Promise.all([
            CRMFormUtils.loadDropdownData('duplicateContactId', '/api/contacts'),
            CRMFormUtils.loadDropdownData('duplicateOpportunityId', '/api/opportunities'),
            CRMFormUtils.loadDropdownData('duplicateProjectId', '/api/projects')
        ]);
    }
    
    async initializeFromSource() {
        if (!this.sourceInteractionId) return;
        
        try {
            const sourceInteraction = await CRMFormUtils.apiCall(`/api/interactions/${this.sourceInteractionId}`);
            
            // Populate form with source data
            Object.entries(this.fieldMappings).forEach(([fieldId, apiField]) => {
                const field = document.getElementById(fieldId);
                if (field && sourceInteraction[apiField] !== undefined) {
                    if (fieldId === 'duplicateInteractionDate') {
                        // Set to current time for duplicates
                        const now = new Date();
                        field.value = now.toISOString().slice(0, 16);
                    } else if (fieldId === 'duplicateSubject') {
                        field.value = `Copy of ${sourceInteraction[apiField] || ''}`;
                    } else {
                        field.value = sourceInteraction[apiField] || '';
                    }
                }
            });
            
        } catch (error) {
            console.error('Error loading source interaction data:', error);
        }
    }
    
    async saveDuplicate() {
        console.log('=== SAVING DUPLICATE INTERACTION ===');
        
        try {
            const formContainer = document.getElementById(this.formContainerId);
            if (!formContainer) {
                throw new Error('Form container not found');
            }
            
            // Validate required fields
            const errors = CRMFormUtils.validateForm(formContainer, ['duplicateInteractionType', 'duplicateDirection', 'duplicateInteractionDate', 'duplicateSubject']);
            if (errors.length > 0) {
                CRMFormUtils.showError(errors.join(', '));
                return;
            }
            
            // Extract form data
            const formData = CRMFormUtils.extractFormData(formContainer, this.fieldMappings);
            
            // Add source interaction reference
            if (this.sourceInteractionId) {
                formData.source_interaction_id = this.sourceInteractionId;
            }
            
            console.log('Duplicate interaction data:', formData);
            
            // Create via API
            const result = await CRMFormUtils.apiCall('/api/interactions', 'POST', formData);
            
            if (result.success) {
                CRMFormUtils.closeModal(this.modalId, this.formContainerId);
                CRMFormUtils.showSuccess('Interaction duplicated successfully', true);
            } else {
                CRMFormUtils.showError(result.message || 'Failed to duplicate interaction');
            }
            
        } catch (error) {
            CRMFormUtils.showError('Error saving duplicate interaction: ' + error.message);
        }
    }
}