/**
 * Tasks Module
 * Handles task operations and UI updates
 */

const Tasks = {
    tasks: [],
    currentTaskId: null,

    async loadTasks(statusFilter = '', priorityFilter = '') {
        try {
            UI.showLoading(true);
            const filters = {};
            if (statusFilter) filters.status_filter = statusFilter;
            if (priorityFilter) filters.priority = priorityFilter;

            const response = await API.tasks.list(filters);
            // Normalize task data - backend returns lowercase, UI expects uppercase
            this.tasks = (response.data?.tasks || response.tasks || []).map(task => ({
                ...task,
                status: task.status?.toUpperCase() || 'PENDING',
                priority: task.priority?.toUpperCase() || 'MEDIUM'
            }));
            this.renderTasks();
        } catch (error) {
            console.error('Failed to load tasks:', error);
            UI.showToast(error.message, 'error');
        } finally {
            UI.showLoading(false);
        }
    },

    async searchTasks(query) {
        try {
            UI.showLoading(true);
            const response = await API.tasks.search(query);
            // Normalize task data
            this.tasks = (response.data?.tasks || response.tasks || []).map(task => ({
                ...task,
                status: task.status?.toUpperCase() || 'PENDING',
                priority: task.priority?.toUpperCase() || 'MEDIUM'
            }));
            this.renderTasks();
            UI.showToast(`Found ${this.tasks.length} task(s)`, 'info');
        } catch (error) {
            console.error('Failed to search tasks:', error);
            UI.showToast(error.message, 'error');
            this.loadTasks(); // Fallback to all tasks
        } finally {
            UI.showLoading(false);
        }
    },

    async loadStats() {
        try {
            const response = await API.tasks.getStats();
            const stats = response.data?.statistics || response.statistics || {};

            const totalEl = document.getElementById('totalTasksCount');
            const inProgressEl = document.getElementById('inProgressCount');
            const completedEl = document.getElementById('completedCount');
            const highPriorityEl = document.getElementById('highPriorityCount');

            if (totalEl) totalEl.textContent = stats.total_tasks || 0;
            if (inProgressEl) inProgressEl.textContent = stats.in_progress || 0;
            if (completedEl) completedEl.textContent = stats.completed || 0;
            if (highPriorityEl) highPriorityEl.textContent = stats.high_priority || 0;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },

    async createTask(taskData) {
        try {
            UI.showLoading(true);
            await API.tasks.create(taskData);
            UI.showToast('Task created successfully!', 'success');
            document.getElementById('createTaskForm').reset();
            const createTaskSection = document.getElementById('createTaskSection');
            if (createTaskSection) {
                createTaskSection.classList.add('hidden');
            }
            await this.loadTasks();
            await this.loadStats();
        } catch (error) {
            UI.showToast(error.message || 'Failed to create task', 'error');
            console.error('Create task error:', error);
        } finally {
            UI.showLoading(false);
        }
    },

    async updateTask(taskId, updates) {
        try {
            await API.tasks.update(taskId, updates);
            UI.showToast('Task updated successfully!', 'success');
            await this.loadTasks();
            await this.loadStats();
            this.closeModal();
        } catch (error) {
            UI.showToast(error.message || 'Failed to update task', 'error');
            console.error('Update task error:', error);
        }
    },

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) return;

        try {
            await API.tasks.delete(taskId);
            UI.showToast('Task deleted successfully!', 'success');
            await this.loadTasks();
            await this.loadStats();
            this.closeModal();
        } catch (error) {
            UI.showToast(error.message || 'Failed to delete task', 'error');
            console.error('Delete task error:', error);
        }
    },

    async toggleTaskStatus(taskId) {
        try {
            const task = this.tasks.find(t => t.id === taskId);
            if (!task) return;

            if (task.status === 'COMPLETED') {
                // Uncomplete: set back to PENDING
                await this.updateTask(taskId, { status: 'PENDING' });
            } else {
                // Complete the task using the complete endpoint
                await API.tasks.complete(taskId);
                UI.showToast('Task marked as complete!', 'success');
                await this.loadTasks();
                await this.loadStats();
            }
        } catch (error) {
            console.error('Toggle status error:', error);
            UI.showToast('Failed to update task status', 'error');
        }
    },

    async openModal(taskId) {
        try {
            const response = await API.tasks.get(taskId);
            const task = response.data?.task || response.data || response;
            this.currentTaskId = taskId;
            
            document.getElementById('modalTaskId').value = taskId;
            document.getElementById('modalTaskTitle').value = task.title || '';
            document.getElementById('modalStatus').value = (task.status || 'PENDING').toUpperCase();
            document.getElementById('modalPriority').value = (task.priority || 'MEDIUM').toUpperCase();
            document.getElementById('modalDescription').value = task.description || '';
            
            document.getElementById('taskModal').classList.remove('hidden');
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    closeModal() {
        document.getElementById('taskModal').classList.add('hidden');
        this.currentTaskId = null;
    },

    renderTasks() {
        const tasksList = document.getElementById('tasksList');

        if (this.tasks.length === 0) {
            tasksList.innerHTML = `
                <div class="flex justify-center items-center h-32 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-tasks text-4xl mb-2 opacity-30"></i>
                        <p>No tasks found. Create one to get started!</p>
                    </div>
                </div>
            `;
            return;
        }

        tasksList.innerHTML = this.tasks.map(task => `
            <div class="p-5 border border-gray-200 rounded-xl hover:shadow-lg transition-smooth cursor-pointer group bg-white" onclick="Tasks.openModal('${task.id}')">
                <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-2">
                            <h4 class="font-bold text-gray-900 group-hover:text-blue-600 transition-smooth text-lg truncate">${UI.escapeHtml(task.title)}</h4>
                            ${task.status === 'COMPLETED' ? '<i class="fas fa-check-circle text-green-500"></i>' : ''}
                        </div>
                        ${task.description ? `<p class="text-sm text-gray-600 mt-2 line-clamp-2">${UI.escapeHtml(task.description)}</p>` : ''}
                        <div class="flex items-center gap-3 mt-3 flex-wrap">
                            <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${UI.getPriorityClass(task.priority)}">
                                <i class="fas ${UI.getPriorityIcon(task.priority)}"></i>
                                ${task.priority}
                            </span>
                            <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${UI.getStatusClass(task.status)}">
                                <i class="fas ${UI.getStatusIcon(task.status)}"></i>
                                ${task.status.replace('_', ' ')}
                            </span>
                            ${task.due_date ? `
                                <span class="inline-flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                                    <i class="fas fa-calendar"></i>
                                    ${UI.formatDate(task.due_date)}
                                </span>
                            ` : ''}
                        </div>
                        ${task.tags && task.tags.length > 0 ? `
                            <div class="flex flex-wrap gap-2 mt-3">
                                ${task.tags.map(tag => `
                                    <span class="inline-flex items-center text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-md">
                                        <i class="fas fa-tag mr-1"></i>${UI.escapeHtml(tag)}
                                    </span>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                    <div class="flex flex-col items-end gap-2">
                        <input type="checkbox" ${task.status === 'COMPLETED' ? 'checked' : ''} 
                               onclick="event.stopPropagation(); Tasks.toggleTaskStatus('${task.id}')" 
                               class="w-6 h-6 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-200 cursor-pointer">
                        ${task.created_at ? `
                            <span class="text-xs text-gray-400">${UI.formatDate(task.created_at)}</span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    },

    init() {
        // Form submission
        document.getElementById('createTaskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const taskData = {
                title: document.getElementById('taskTitle').value,
                description: document.getElementById('taskDescription').value,
                priority: document.getElementById('taskPriority').value,
                due_date: document.getElementById('taskDueDate').value || null,
                tags: document.getElementById('taskTags').value.split(',').map(t => t.trim()).filter(t => t)
            };
            this.createTask(taskData);
        });

        // Update task form
        document.getElementById('updateTaskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const updates = {
                title: document.getElementById('modalTaskTitle').value,
                status: document.getElementById('modalStatus').value,
                priority: document.getElementById('modalPriority').value,
                description: document.getElementById('modalDescription').value
            };
            this.updateTask(this.currentTaskId, updates);
        });

        // Status filter
        document.getElementById('taskFilter').addEventListener('change', (e) => {
            const priorityFilter = document.getElementById('priorityFilter').value;
            this.loadTasks(e.target.value, priorityFilter);
        });
    }
};

// Initialize tasks when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Tasks.init();
});
