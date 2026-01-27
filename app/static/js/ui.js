/**
 * UI Module
 * Handles UI utilities and common functions
 */

const UI = {
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        
        const bgColor = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        }[type] || 'bg-blue-500';

        const icon = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }[type] || 'info-circle';

        toast.className = `glass toast ${bgColor} text-white px-4 py-3 rounded-lg shadow-elevated pointer-events-auto`;
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas fa-${icon}"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    /**
     * Show/hide loading overlay
     */
    showLoading(show = true) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    },

    /**
     * Get priority badge class
     */
    getPriorityClass(priority) {
        const classes = {
            'LOW': 'bg-gray-100 text-gray-700',
            'MEDIUM': 'bg-blue-100 text-blue-700',
            'HIGH': 'bg-orange-100 text-orange-700',
            'URGENT': 'bg-red-100 text-red-700'
        };
        return classes[priority] || classes['MEDIUM'];
    },

    /**
     * Get priority icon
     */
    getPriorityIcon(priority) {
        const icons = {
            'LOW': 'fa-arrow-down',
            'MEDIUM': 'fa-minus',
            'HIGH': 'fa-arrow-up',
            'URGENT': 'fa-exclamation-circle'
        };
        return icons[priority] || icons['MEDIUM'];
    },

    /**
     * Get status badge class
     */
    getStatusClass(status) {
        const classes = {
            'PENDING': 'bg-gray-100 text-gray-700',
            'IN_PROGRESS': 'bg-blue-100 text-blue-700',
            'COMPLETED': 'bg-green-100 text-green-700'
        };
        return classes[status] || classes['PENDING'];
    },

    /**
     * Get status icon
     */
    getStatusIcon(status) {
        const icons = {
            'PENDING': 'fa-clock',
            'IN_PROGRESS': 'fa-spinner',
            'COMPLETED': 'fa-check-circle'
        };
        return icons[status] || icons['PENDING'];
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Update connection status indicator
     */
    updateStatus(status) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');

        if (status === 'online') {
            statusDot.classList.remove('bg-gray-400');
            statusDot.classList.add('bg-green-500', 'pulse-light');
            statusText.textContent = 'Online';
        } else {
            statusDot.classList.remove('bg-green-500', 'pulse-light');
            statusDot.classList.add('bg-gray-400');
            statusText.textContent = 'Offline';
        }
    },

    /**
     * Format date
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
    }
};

// Global window functions for onclick handlers
window.closeTaskModal = () => {
    Tasks.closeModal();
};

window.deleteTask = () => {
    if (Tasks.currentTaskId) {
        Tasks.deleteTask(Tasks.currentTaskId);
    }
};

window.openTaskModal = (taskId) => {
    Tasks.openModal(taskId);
};
