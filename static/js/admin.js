// Admin Operations & Dashboard JS

document.addEventListener('DOMContentLoaded', () => {
    loadAdminDashboard();
    loadUsersTable();
    initCreatePolicyTypeForm();
    initCreateStaffForm();
});

async function loadAdminDashboard() {
    const summaryContainer = document.getElementById('adminDashboardStats');
    if (!summaryContainer) return;

    const res = await fetchAPI('/admin/api/dashboard-summary');
    if (res.success && res.data) {
        const d = res.data;
        document.getElementById('statTotalUsers').textContent = d.total_users;
        document.getElementById('statTotalCustomers').textContent = d.total_customers;
        document.getElementById('statTotalAgents').textContent = d.total_agents;
        document.getElementById('statTotalOfficers').textContent = d.total_officers;
        document.getElementById('statTotalPolicies').textContent = d.total_policies;
        document.getElementById('statActivePolicies').textContent = d.active_policies;
        document.getElementById('statTotalClaims').textContent = d.total_claims;
        document.getElementById('statPendingClaims').textContent = d.pending_claims;
        document.getElementById('statApprovalRate').textContent = d.approval_rate + '%';

        // Render Claims Status Chart
        const claimsCtx = document.getElementById('claimsStatusChart');
        if (claimsCtx && window.Chart) {
            const labels = d.claims_by_status.map(x => x.status.replace('_', ' '));
            const dataCounts = d.claims_by_status.map(x => x.count);

            new Chart(claimsCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: dataCounts,
                        backgroundColor: ['#0369a1', '#f59e0b', '#10b981', '#ef4444', '#6366f1', '#14b8a6']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // Render Policy Types Chart
        const policyCtx = document.getElementById('policiesTypeChart');
        if (policyCtx && window.Chart) {
            const labels = d.policies_by_type.map(x => x.name);
            const dataCounts = d.policies_by_type.map(x => x.count);

            new Chart(policyCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Enrolled Policies',
                        data: dataCounts,
                        backgroundColor: '#2563eb'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1 } }
                    }
                }
            });
        }
    }
}

async function loadUsersTable() {
    const tbody = document.getElementById('adminUsersTableBody');
    if (!tbody) return;

    const res = await fetchAPI('/admin/api/users');
    if (res.success && res.data) {
        tbody.innerHTML = res.data.map(u => `
            <tr>
                <td>#${u.id}</td>
                <td class="font-weight-bold">${u.name}</td>
                <td>${u.email}</td>
                <td>${u.phone}</td>
                <td><span class="badge bg-secondary">${u.role}</span></td>
                <td><span class="badge ${u.status === 'ACTIVE' ? 'bg-success' : 'bg-danger'}">${u.status}</span></td>
                <td>
                    ${u.status === 'ACTIVE' ? 
                        `<button onclick="updateUserStatus(${u.id}, 'SUSPENDED')" class="btn btn-sm btn-outline-danger">Suspend</button>` :
                        `<button onclick="updateUserStatus(${u.id}, 'ACTIVE')" class="btn btn-sm btn-outline-success">Activate</button>`
                    }
                </td>
            </tr>
        `).join('');
    }
}

window.updateUserStatus = async function(userId, newStatus) {
    if (!confirm(`Are you sure you want to change user #${userId} status to ${newStatus}?`)) return;

    const res = await fetchAPI(`/admin/api/users/${userId}/status`, {
        method: 'POST',
        body: { status: newStatus }
    });

    if (res.success) {
        showToast(res.message, 'success');
        loadUsersTable();
    } else {
        showToast(res.message, 'danger');
    }
};

function initCreatePolicyTypeForm() {
    const form = document.getElementById('createPolicyTypeForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('ptName').value;
        const description = document.getElementById('ptDescription').value;
        const coverage = document.getElementById('ptCoverage').value;
        const premium = document.getElementById('ptPremium').value;
        const duration_months = document.getElementById('ptDuration').value;

        const res = await fetchAPI('/admin/api/policy-types', {
            method: 'POST',
            body: { name, description, coverage, premium, duration_months }
        });

        if (res.success) {
            showToast(res.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('createPolicyTypeModal')).hide();
            setTimeout(() => { location.reload(); }, 1000);
        } else {
            showToast(res.message, 'danger');
        }
    });
}

function initCreateStaffForm() {
    const form = document.getElementById('createStaffForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const role = document.getElementById('staffRole').value;
        const name = document.getElementById('staffName').value;
        const email = document.getElementById('staffEmail').value;
        const phone = document.getElementById('staffPhone').value;
        const password = document.getElementById('staffPassword').value;

        const res = await fetchAPI('/admin/api/users/create-staff', {
            method: 'POST',
            body: { role, name, email, phone, password }
        });

        if (res.success) {
            showToast(res.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('createStaffModal')).hide();
            form.reset();
            loadUsersTable();
        } else {
            showToast(res.message, 'danger');
        }
    });
}
