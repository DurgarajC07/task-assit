/**
 * Main App Initialization and View Management
 */

// Global view switching
window.switchView = function(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    
    // Stop analytics auto-refresh when leaving analytics view
    if (Analytics.updateInterval) {
        Analytics.stopAutoRefresh();
    }
    
    // Show selected view
    const view = document.getElementById(`${viewName}View`);
    if (view) {
        view.classList.remove('hidden');
        
        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        const menuItem = document.querySelector(`[data-view="${viewName}"]`);
        if (menuItem) menuItem.classList.add('active');
        
        // Load data for specific views
        if (viewName === 'tasks') {
            Tasks.loadTasks();
            Tasks.loadStats();
        } else if (viewName === 'analytics') {
            Analytics.init();
        } else if (viewName === 'dashboard') {
            Dashboard.loadData();
        }
    }
};

// Dashboard Module
const Dashboard = {
    async loadData() {
        try {
            // Load stats
            await Tasks.loadStats();
            
            // Load recent tasks sorted by creation date (newest first)
            const response = await API.tasks.list({ sort_by: 'created_at', sort_order: 'desc' });
            const tasks = (response.data?.tasks || response.tasks || []).map(task => ({
                ...task,
                status: task.status?.toUpperCase() || 'PENDING',
                priority: task.priority?.toUpperCase() || 'MEDIUM'
            }));
            
            // Display recent 5 tasks (already sorted DESC)
            this.renderRecentActivity(tasks.slice(0, 5));
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    },
    
    renderRecentActivity(tasks) {
        const container = document.getElementById('recentActivity');
        if (!container) return;
        
        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-clock text-3xl mb-2 opacity-30"></i>
                    <p class="text-sm">No recent tasks</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = tasks.map(task => `
            <div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-smooth cursor-pointer" onclick="Tasks.openModal('${task.id}')">
                <div class="w-8 h-8 rounded-lg ${UI.getPriorityClass(task.priority)} flex items-center justify-center flex-shrink-0">
                    <i class="fas ${UI.getPriorityIcon(task.priority)}"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="font-semibold text-gray-900 truncate">${UI.escapeHtml(task.title)}</p>
                    <p class="text-xs text-gray-500">${UI.formatDate(task.created_at)}</p>
                </div>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${UI.getStatusClass(task.status)}">
                    ${task.status.replace('_', ' ')}
                </span>
            </div>
        `).join('');
    }
};

// Analytics Module
const Analytics = {
    statusChart: null,
    priorityChart: null,
    updateInterval: null,
    
    async init() {
        try {
            await this.loadData();
            // Setup auto-refresh every 10 seconds for real-time data
            this.startAutoRefresh();
        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    },
    
    async loadData() {
        try {
            const response = await API.tasks.getStats();
            const stats = response.data?.statistics || response.statistics || {};
            
            this.renderStatusChart(stats);
            this.renderPriorityChart(stats);
        } catch (error) {
            console.error('Failed to load analytics data:', error);
        }
    },
    
    startAutoRefresh() {
        // Clear existing interval if any
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        // Refresh every 10 seconds
        this.updateInterval = setInterval(() => this.loadData(), 10000);
    },
    
    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },
    
    renderStatusChart(stats) {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;
        
        if (this.statusChart) {
            this.statusChart.destroy();
        }
        
        this.statusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'In Progress', 'Completed'],
                datasets: [{
                    data: [
                        stats.pending || 0,
                        stats.in_progress || 0,
                        stats.completed || 0
                    ],
                    backgroundColor: [
                        'rgba(156, 163, 175, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(34, 197, 94, 0.8)'
                    ],
                    borderColor: [
                        'rgba(156, 163, 175, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(34, 197, 94, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },
    
    renderPriorityChart(stats) {
        const ctx = document.getElementById('priorityChart');
        if (!ctx) return;
        
        if (this.priorityChart) {
            this.priorityChart.destroy();
        }
        
        this.priorityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Low', 'Medium', 'High', 'Urgent'],
                datasets: [{
                    label: 'Tasks by Priority',
                    data: [
                        stats.low_priority || 0,
                        stats.medium_priority || 0,
                        stats.high_priority || 0,
                        stats.urgent_priority || 0
                    ],
                    backgroundColor: [
                        'rgba(156, 163, 175, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderColor: [
                        'rgba(156, 163, 175, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(251, 146, 60, 1)',
                        'rgba(239, 68, 68, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Setup WebSocket event handlers
    WebSocketManager.on('connected', () => {
        UI.updateStatus('online');
        UI.showToast('Connected to server', 'success');
    });

    WebSocketManager.on('disconnected', () => {
        UI.updateStatus('offline');
    });

    WebSocketManager.on('task_update', (data) => {
        // Update tasks view if visible
        const tasksView = document.getElementById('tasksView');
        if (tasksView && !tasksView.classList.contains('hidden')) {
            Tasks.loadTasks();
            Tasks.loadStats();
        }
        
        // Update dashboard if visible
        const dashboardView = document.getElementById('dashboardView');
        if (dashboardView && !dashboardView.classList.contains('hidden')) {
            Dashboard.loadData();
        }
        
        // Update analytics if visible
        const analyticsView = document.getElementById('analyticsView');
        if (analyticsView && !analyticsView.classList.contains('hidden')) {
            Analytics.loadData();
        }
        
        UI.showToast('Task updated', 'info');
    });

    WebSocketManager.on('chat_response', (data) => {
        // This is handled by Chat module
    });
    
    WebSocketManager.on('error', (error) => {
        console.error('[App] WebSocket error:', error);
    });
    
    WebSocketManager.on('server_error', (error) => {
        console.error('[App] Server error:', error);
        UI.showToast('Server error: ' + (error.message || 'Unknown error'), 'error');
    });

    // Menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.getAttribute('data-view');
            window.switchView(view);
        });
    });

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');
        });
    }

    // Create task button
    const createTaskBtn = document.getElementById('createTaskBtn');
    const createTaskSection = document.getElementById('createTaskSection');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    
    if (createTaskBtn && createTaskSection) {
        createTaskBtn.addEventListener('click', () => {
            createTaskSection.classList.toggle('hidden');
        });
    }
    
    if (cancelTaskBtn && createTaskSection) {
        cancelTaskBtn.addEventListener('click', () => {
            createTaskSection.classList.add('hidden');
            document.getElementById('createTaskForm').reset();
        });
    }

    // Global search
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        let searchTimeout;
        globalSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.trim();
                if (query) {
                    Tasks.searchTasks(query);
                } else {
                    Tasks.loadTasks();
                }
            }, 500);
        });
    }

    // Clear filters
    const clearFilters = document.getElementById('clearFilters');
    if (clearFilters) {
        clearFilters.addEventListener('click', () => {
            document.getElementById('taskFilter').value = '';
            document.getElementById('priorityFilter').value = '';
            Tasks.loadTasks();
        });
    }

    // Priority filter
    const priorityFilter = document.getElementById('priorityFilter');
    if (priorityFilter) {
        priorityFilter.addEventListener('change', (e) => {
            Tasks.loadTasks(document.getElementById('taskFilter').value, e.target.value);
        });
    }

    // Profile button
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            UI.showToast('Profile feature coming soon!', 'info');
        });
    }

    // Auto-refresh stats every 30 seconds (only when logged in)
    setInterval(() => {
        const authContainer = document.getElementById('authContainer');
        if (!authContainer || authContainer.classList.contains('hidden')) {
            // Only refresh when logged in (auth container hidden)
            if (API.getToken()) {
                Tasks.loadStats();
            }
        }
    }, 30000);
});
