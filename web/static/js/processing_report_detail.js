/**
 * Processing Report Detail JavaScript
 * Handles opportunity management, pagination, and record interactions
 */

const ProcessingReportJS = {
    // Configuration
    Config: {
        CURRENT_OPPORTUNITIES_PAGE: 1,
        CURRENT_REPORT_FILENAME: null
    },

    // Utility functions
    Utils: {
        /**
         * Standardized error handling
         */
        handleError: function(error, context = 'Operation') {
            console.error(`${context} error:`, error);
            this.showNotification('error', `${context} failed`, error.message || 'An unexpected error occurred');
        },

        /**
         * Show notification using Bootstrap toast
         */
        showNotification: function(type, title, message) {
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                toastContainer.style.zIndex = '9999';
                document.body.appendChild(toastContainer);
            }
            
            const toastId = 'toast-' + Date.now();
            const iconClass = type === 'success' ? 'fa-check-circle text-success' : 'fa-exclamation-triangle text-danger';
            const toastHTML = `
                <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header">
                        <i class="fas ${iconClass} me-2"></i>
                        <strong class="me-auto">${title}</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                    <div class="toast-body">
                        ${message}
                    </div>
                </div>
            `;
            
            toastContainer.insertAdjacentHTML('beforeend', toastHTML);
            const toast = new bootstrap.Toast(document.getElementById(toastId));
            toast.show();
            
            // Remove toast element after it's hidden
            document.getElementById(toastId).addEventListener('hidden.bs.toast', function() {
                this.remove();
            });
        },

        /**
         * Format date for display
         */
        formatDate: function(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleDateString();
        },

        /**
         * Get badge class for stage
         */
        getStageBadgeClass: function(stage) {
            const stageClasses = {
                'New': 'bg-primary',
                'Qualified': 'bg-info',
                'Quote Sent': 'bg-warning text-dark',
                'Proposal': 'bg-secondary',
                'Negotiation': 'bg-warning text-dark',
                'Closed Won': 'bg-success',
                'Closed Lost': 'bg-danger'
            };
            return stageClasses[stage] || 'bg-light text-dark';
        }
    },

    // UI Management
    UI: {
        /**
         * Create the edit opportunity modal HTML
         */
        createEditOpportunityModal: function() {
            // Check if modal already exists
            if (document.getElementById('editOpportunityModal')) {
                return;
            }

            const modalHTML = `
                <div class="modal fade" id="editOpportunityModal" tabindex="-1" aria-labelledby="editOpportunityModalLabel" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="editOpportunityModalLabel">Edit Opportunity</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form id="editOpportunityForm">
                                    <input type="hidden" id="edit-opportunity-id">
                                    <div class="mb-3">
                                        <label for="edit-opportunity-name" class="form-label">RFQ Number</label>
                                        <input type="text" class="form-control" id="edit-opportunity-name" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="edit-opportunity-stage" class="form-label">Stage</label>
                                        <select class="form-select" id="edit-opportunity-stage">
                                            <option value="New">New</option>
                                            <option value="Qualified">Qualified</option>
                                            <option value="Quote Sent">Quote Sent</option>
                                            <option value="Proposal">Proposal</option>
                                            <option value="Negotiation">Negotiation</option>
                                            <option value="Closed Won">Closed Won</option>
                                            <option value="Closed Lost">Closed Lost</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label for="edit-opportunity-amount" class="form-label">Amount</label>
                                        <div class="input-group">
                                            <span class="input-group-text">$</span>
                                            <input type="number" class="form-control" id="edit-opportunity-amount" step="0.01" min="0">
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label for="edit-opportunity-assigned" class="form-label">Assigned To</label>
                                        <input type="text" class="form-control" id="edit-opportunity-assigned">
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" onclick="ProcessingReportJS.Opportunities.saveChanges()">Save Changes</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to document body
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    },

    // Opportunity management
    Opportunities: {
        /**
         * Load opportunities with pagination
         */
        load: function(page = 1) {
            ProcessingReportJS.Config.CURRENT_OPPORTUNITIES_PAGE = page;
            
            fetch(`/api/processing-report/${ProcessingReportJS.Config.CURRENT_REPORT_FILENAME}/opportunities?page=${page}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        ProcessingReportJS.Opportunities.showError(data.error);
                        return;
                    }
                    
                    ProcessingReportJS.Opportunities.renderTable(data);
                })
                .catch(error => {
                    ProcessingReportJS.Utils.handleError(error, 'Loading opportunities');
                    ProcessingReportJS.Opportunities.showError('Failed to load opportunities');
                });
        },

        /**
         * Render opportunities table
         */
        renderTable: function(data) {
            const tbody = document.getElementById('opportunities-tbody');
            const loading = document.getElementById('opportunities-loading');
            const content = document.getElementById('opportunities-content');
            const empty = document.getElementById('opportunities-empty');
            const pagination = document.getElementById('opportunities-pagination');
            
            // Hide loading, show content
            if (loading) loading.style.display = 'none';
            if (content) content.style.display = 'block';
            
            if (data.opportunities.length === 0) {
                if (empty) empty.style.display = 'block';
                const table = document.getElementById('opportunities-table');
                if (table) table.style.display = 'none';
                if (pagination) pagination.style.display = 'none';
                return;
            }
            
            // Show table and populate
            if (empty) empty.style.display = 'none';
            const table = document.getElementById('opportunities-table');
            if (table) table.style.display = 'table';
            
            if (tbody) {
                tbody.innerHTML = data.opportunities.map(opp => `
                    <tr>
                        <td>
                            <a href="/opportunity/${opp.id}" class="text-decoration-none">
                                <strong>${opp.name}</strong>
                            </a>
                        </td>
                        <td>
                            <code class="text-muted">${opp.nsn || 'N/A'}</code>
                        </td>
                        <td>
                            <span class="badge badge-stage ${ProcessingReportJS.Utils.getStageBadgeClass(opp.stage)}">${opp.stage}</span>
                        </td>
                        <td>
                            ${opp.amount ? '$' + parseFloat(opp.amount).toLocaleString() : 'N/A'}
                        </td>
                        <td>
                            ${opp.assigned_to || 'Unassigned'}
                        </td>
                        <td>
                            <small class="text-muted">${ProcessingReportJS.Utils.formatDate(opp.created_at)}</small>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary btn-action me-1" 
                                    onclick="ProcessingReportJS.Opportunities.edit(${opp.id}, '${opp.name}', '${opp.stage}', ${opp.amount || 0}, '${opp.assigned_to || ''}')"
                                    title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger btn-action" 
                                    onclick="ProcessingReportJS.Opportunities.delete(${opp.id}, '${opp.name}')"
                                    title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
            
            // Update pagination
            if (data.total_pages > 1) {
                ProcessingReportJS.Opportunities.updatePagination(data.page, data.total_pages);
                if (pagination) pagination.style.display = 'block';
            } else {
                if (pagination) pagination.style.display = 'none';
            }
        },

        /**
         * Update pagination controls
         */
        updatePagination: function(currentPage, totalPages) {
            const pagination = document.querySelector('#opportunities-pagination .pagination');
            if (!pagination) return;
            
            let paginationHTML = '';
            
            // Previous button
            if (currentPage > 1) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="ProcessingReportJS.Opportunities.load(${currentPage - 1}); return false;">Previous</a>
                    </li>
                `;
            }
            
            // Page numbers
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                paginationHTML += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="ProcessingReportJS.Opportunities.load(${i}); return false;">${i}</a>
                    </li>
                `;
            }
            
            // Next button
            if (currentPage < totalPages) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="ProcessingReportJS.Opportunities.load(${currentPage + 1}); return false;">Next</a>
                    </li>
                `;
            }
            
            pagination.innerHTML = paginationHTML;
        },

        /**
         * Edit opportunity
         */
        edit: function(id, name, stage, amount, assignedTo) {
            document.getElementById('edit-opportunity-id').value = id;
            document.getElementById('edit-opportunity-name').value = name;
            document.getElementById('edit-opportunity-stage').value = stage;
            document.getElementById('edit-opportunity-amount').value = amount || '';
            document.getElementById('edit-opportunity-assigned').value = assignedTo;
            
            const modal = new bootstrap.Modal(document.getElementById('editOpportunityModal'));
            modal.show();
        },

        /**
         * Save opportunity changes
         */
        saveChanges: function() {
            const id = document.getElementById('edit-opportunity-id').value;
            const name = document.getElementById('edit-opportunity-name').value;
            const stage = document.getElementById('edit-opportunity-stage').value;
            const amount = document.getElementById('edit-opportunity-amount').value;
            const assignedTo = document.getElementById('edit-opportunity-assigned').value;
            
            if (!name.trim()) {
                ProcessingReportJS.Utils.showNotification('error', 'Validation Error', 'RFQ Number is required');
                return;
            }
            
            const data = {
                name: name,
                stage: stage,
                amount: amount || null,
                assigned_to: assignedTo || null
            };
            
            fetch(`/api/processing-report/opportunities/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editOpportunityModal'));
                    modal.hide();
                    ProcessingReportJS.Opportunities.load(ProcessingReportJS.Config.CURRENT_OPPORTUNITIES_PAGE);
                    ProcessingReportJS.Utils.showNotification('success', 'Success', 'Opportunity updated successfully');
                } else {
                    ProcessingReportJS.Utils.showNotification('error', 'Error', result.error || 'Failed to update opportunity');
                }
            })
            .catch(error => {
                ProcessingReportJS.Utils.handleError(error, 'Updating opportunity');
            });
        },

        /**
         * Delete opportunity
         */
        delete: function(id, name) {
            if (!confirm(`Are you sure you want to delete the opportunity "${name}"?\n\nThis action cannot be undone and will also delete all related records (contacts, tasks, etc.).`)) {
                return;
            }
            
            fetch(`/api/processing-report/opportunities/${id}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    ProcessingReportJS.Opportunities.load(ProcessingReportJS.Config.CURRENT_OPPORTUNITIES_PAGE);
                    ProcessingReportJS.Utils.showNotification('success', 'Success', 'Opportunity deleted successfully');
                } else {
                    ProcessingReportJS.Utils.showNotification('error', 'Error', result.error || 'Failed to delete opportunity');
                }
            })
            .catch(error => {
                ProcessingReportJS.Utils.handleError(error, 'Deleting opportunity');
            });
        },

        /**
         * Show opportunity error
         */
        showError: function(message) {
            const loading = document.getElementById('opportunities-loading');
            const content = document.getElementById('opportunities-content');
            
            if (loading) loading.style.display = 'none';
            if (content) {
                content.style.display = 'block';
                content.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading opportunities: ${message}
                    </div>
                `;
            }
        }
    },

    // Record viewing
    Records: {
        /**
         * View record details
         */
        view: function(recordType, recordId) {
            if (!recordId || recordId === 'null' || recordId === '') {
                ProcessingReportJS.Utils.showNotification('error', 'Error', 'Record ID not available');
                return;
            }
            
            let url = '';
            switch(recordType) {
                case 'opportunities':
                    url = `/opportunity/${recordId}`;
                    break;
                case 'contacts':
                    url = `/contact/${recordId}`;
                    break;
                case 'accounts':
                    url = `/account/${recordId}`;
                    break;
                case 'products':
                    url = `/product/${recordId}`;
                    break;
                case 'tasks':
                    url = `/tasks/${recordId}`;
                    break;
                case 'qpls':
                    url = `/qpl/${recordId}`;
                    break;
                default:
                    ProcessingReportJS.Utils.showNotification('error', 'Error', `Unknown record type: ${recordType}`);
                    return;
            }
            
            // Open in new tab for better user experience
            window.open(url, '_blank');
        }
    },

    // Initialization
    init: function(reportFilename) {
        ProcessingReportJS.Config.CURRENT_REPORT_FILENAME = reportFilename;
        
        // Create UI components
        ProcessingReportJS.UI.createEditOpportunityModal();
        
        // Load opportunities if the section exists
        if (document.getElementById('opportunities-tbody')) {
            ProcessingReportJS.Opportunities.load();
        }
        
        // Add event delegation for record item double-clicks
        document.addEventListener('dblclick', function(e) {
            const recordItem = e.target.closest('.record-item');
            if (recordItem) {
                const recordType = recordItem.getAttribute('data-record-type');
                const recordId = recordItem.getAttribute('data-record-id');
                if (recordType && recordId) {
                    ProcessingReportJS.Records.view(recordType, recordId);
                }
            }
        });
    }
};

// Global functions for backward compatibility
window.loadOpportunities = (page) => ProcessingReportJS.Opportunities.load(page);
window.editOpportunity = (id, name, stage, amount, assignedTo) => ProcessingReportJS.Opportunities.edit(id, name, stage, amount, assignedTo);
window.saveOpportunityChanges = () => ProcessingReportJS.Opportunities.saveChanges();
window.deleteOpportunity = (id, name) => ProcessingReportJS.Opportunities.delete(id, name);
window.viewRecord = (recordType, recordId) => ProcessingReportJS.Records.view(recordType, recordId);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProcessingReportJS;
}
