/**
 * PLASU Examination Management System - Main JavaScript
 * Contains common functionality used across the application
 */

// Global variables
window.PLASU = {
    config: {
        apiBaseUrl: '/api/',
        csrfToken: null,
        dateFormat: 'YYYY-MM-DD',
        timeFormat: 'HH:mm'
    },
    utils: {},
    components: {},
    helpers: {}
};

// Utility functions
PLASU.utils = {
    /**
     * Format date string
     * @param {Date|string} date - Date object or string
     * @param {string} format - Date format
     * @returns {string} Formatted date
     */
    formatDate: function(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        const d = new Date(date);
        if (isNaN(d.getTime())) return date;
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes);
    },

    /**
     * Format file size
     * @param {number} bytes - Size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Show loading spinner
     * @param {string} message - Loading message
     * @param {string} container - Container selector
     */
    showLoading: function(message = 'Loading...', container = 'body') {
        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <div class="loading-text">${message}</div>
            </div>
        `;
        
        const containerEl = document.querySelector(container);
        if (containerEl) {
            containerEl.style.position = 'relative';
            containerEl.appendChild(loader);
        }
    },

    /**
     * Hide loading spinner
     * @param {string} container - Container selector
     */
    hideLoading: function(container = 'body') {
        const containerEl = document.querySelector(container);
        if (containerEl) {
            const loader = containerEl.querySelector('.loading-overlay');
            if (loader) {
                loader.remove();
            }
        }
    },

    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds
     */
    showNotification: function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    },

    /**
     * Confirm dialog
     * @param {string} message - Confirmation message
     * @param {Function} callback - Callback function
     * @param {string} title - Dialog title
     */
    confirmDialog: function(message, callback, title = 'Confirm') {
        if (window.confirm(message)) {
            callback();
        }
    },

    /**
     * Get CSRF token
     * @returns {string} CSRF token
     */
    getCsrfToken: function() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    },

    /**
     * Make AJAX request
     * @param {Object} options - Request options
     * @returns {Promise} Promise object
     */
    ajax: function(options) {
        const defaults = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': PLASU.utils.getCsrfToken()
            }
        };
        
        const config = Object.assign(defaults, options);
        
        return fetch(config.url, config)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('AJAX Error:', error);
                PLASU.utils.showNotification('An error occurred. Please try again.', 'error');
                throw error;
            });
    },

    /**
     * Initialize tooltips
     */
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    /**
     * Initialize popovers
     */
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
};

// Component functions
PLASU.components = {
    /**
     * Initialize data tables
     */
    initDataTables: function() {
        const tables = document.querySelectorAll('.data-table');
        tables.forEach(table => {
            if (typeof $.fn.DataTable !== 'undefined') {
                $(table).DataTable({
                    responsive: true,
                    pageLength: 10,
                    language: {
                        search: "Search:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        paginate: {
                            first: "First",
                            last: "Last",
                            next: "Next",
                            previous: "Previous"
                        }
                    }
                });
            }
        });
    },

    /**
     * Initialize date pickers
     */
    initDatePickers: function() {
        const datePickers = document.querySelectorAll('.date-picker');
        datePickers.forEach(picker => {
            if (typeof flatpickr !== 'undefined') {
                flatpickr(picker, {
                    dateFormat: 'Y-m-d',
                    allowInput: true
                });
            }
        });

        const timePickers = document.querySelectorAll('.time-picker');
        timePickers.forEach(picker => {
            if (typeof flatpickr !== 'undefined') {
                flatpickr(picker, {
                    enableTime: true,
                    noCalendar: true,
                    dateFormat: 'H:i',
                    allowInput: true
                });
            }
        });
    },

    /**
     * Initialize charts
     */
    initCharts: function() {
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(element => {
            const chartType = element.getAttribute('data-chart');
            const chartData = JSON.parse(element.getAttribute('data-chart-data') || '{}');
            
            if (typeof Chart !== 'undefined') {
                const ctx = element.getContext('2d');
                new Chart(ctx, {
                    type: chartType,
                    data: chartData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
        });
    },

    /**
     * Initialize form validation
     */
    initFormValidation: function() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    },

    /**
     * Initialize file uploads
     */
    initFileUploads: function() {
        const fileInputs = document.querySelectorAll('.file-upload');
        fileInputs.forEach(input => {
            input.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const maxSize = 10 * 1024 * 1024; // 10MB
                    if (file.size > maxSize) {
                        PLASU.utils.showNotification('File size must be less than 10MB', 'error');
                        e.target.value = '';
                        return;
                    }
                    
                    // Update file info display
                    const fileInfo = document.querySelector(`#${input.id}-info`);
                    if (fileInfo) {
                        fileInfo.innerHTML = `
                            <div class="alert alert-info">
                                <strong>Selected:</strong> ${file.name}<br>
                                <strong>Size:</strong> ${PLASU.utils.formatFileSize(file.size)}
                            </div>
                        `;
                    }
                }
            });
        });
    },

    /**
     * Initialize search functionality
     */
    initSearch: function() {
        const searchInputs = document.querySelectorAll('.search-input');
        searchInputs.forEach(input => {
            const debouncedSearch = PLASU.utils.debounce(function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const target = input.getAttribute('data-search-target');
                const items = document.querySelectorAll(target);
                
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }, 300);
            
            input.addEventListener('input', debouncedSearch);
        });
    },

    /**
     * Initialize filter functionality
     */
    initFilters: function() {
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', function(e) {
                const filterValue = e.target.value;
                const target = select.getAttribute('data-filter-target');
                const items = document.querySelectorAll(target);
                
                if (filterValue === '') {
                    items.forEach(item => item.style.display = '');
                } else {
                    items.forEach(item => {
                        const filterAttr = item.getAttribute('data-filter-value');
                        if (filterAttr === filterValue) {
                            item.style.display = '';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                }
            });
        });
    }
};

// Helper functions
PLASU.helpers = {
    /**
     * Toggle sidebar
     */
    toggleSidebar: function() {
        const sidebar = document.querySelector('.sidebar');
        const main = document.querySelector('.main-content');
        
        if (sidebar && main) {
            sidebar.classList.toggle('collapsed');
            main.classList.toggle('expanded');
        }
    },

    /**
     * Print page
     */
    printPage: function() {
        window.print();
    },

    /**
     * Export table to CSV
     * @param {string} tableId - Table ID
     * @param {string} filename - Filename
     */
    exportTableToCSV: function(tableId, filename = 'export.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = Array.from(cols).map(col => {
                const text = col.textContent.trim();
                // Escape quotes and wrap in quotes if comma present
                return text.includes(',') ? `"${text.replace(/"/g, '""')}"` : text;
            });
            csv.push(rowData.join(','));
        });
        
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    },

    /**
     * Copy to clipboard
     * @param {string} text - Text to copy
     */
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            PLASU.utils.showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            PLASU.utils.showNotification('Failed to copy text', 'error');
        });
    },

    /**
     * Generate random ID
     * @param {number} length - Length of ID
     * @returns {string} Random ID
     */
    generateId: function(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    PLASU.components.initTooltips();
    PLASU.components.initPopovers();
    PLASU.components.initDatePickers();
    PLASU.components.initCharts();
    PLASU.components.initFormValidation();
    PLASU.components.initFileUploads();
    PLASU.components.initSearch();
    PLASU.components.initFilters();
    
    // Auto-hide notifications
    const notifications = document.querySelectorAll('.alert:not(.alert-permanent)');
    notifications.forEach(notification => {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    });
    
    // Handle form submissions with AJAX
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            PLASU.ajax({
                url: form.getAttribute('action'),
                method: form.getAttribute('method') || 'POST',
                body: formData
            })
            .then(data => {
                if (data.success) {
                    PLASU.utils.showNotification(data.message || 'Operation successful!', 'success');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.reload) {
                        window.location.reload();
                    }
                } else {
                    PLASU.utils.showNotification(data.message || 'Operation failed!', 'error');
                }
            })
            .catch(error => {
                console.error('Form submission error:', error);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
        });
    });
    
    // Handle delete confirmations
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.getAttribute('data-confirm-message') || 'Are you sure you want to delete this item?';
            const url = this.getAttribute('href');
            
            PLASU.utils.confirmDialog(message, function() {
                PLASU.ajax({
                    url: url,
                    method: 'DELETE'
                })
                .then(data => {
                    if (data.success) {
                        PLASU.utils.showNotification(data.message || 'Item deleted successfully!', 'success');
                        if (data.reload) {
                            window.location.reload();
                        }
                    } else {
                        PLASU.utils.showNotification(data.message || 'Failed to delete item!', 'error');
                    }
                });
            });
        });
    });
    
    // Handle auto-save functionality
    const autoSaveInputs = document.querySelectorAll('.auto-save');
    let autoSaveTimeout;
    
    autoSaveInputs.forEach(input => {
        input.addEventListener('change', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                const form = input.closest('form');
                if (form && form.classList.contains('auto-save-form')) {
                    const formData = new FormData(form);
                    PLASU.ajax({
                        url: form.getAttribute('data-save-url') || form.getAttribute('action'),
                        method: 'POST',
                        body: formData
                    })
                    .then(data => {
                        if (data.success) {
                            PLASU.utils.showNotification('Auto-saved!', 'info');
                        }
                    });
                }
            }, 2000);
        });
    });
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    PLASU.utils.showNotification('An unexpected error occurred. Please refresh the page.', 'error');
});

// Export for external use
window.PLASU = PLASU;
