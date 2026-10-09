// Claims Officer Logic JS

document.addEventListener('DOMContentLoaded', () => {
    loadOfficerDashboard();
    initReviewForm();
});

async function loadOfficerDashboard() {
    const summaryContainer = document.getElementById('officerDashboardStats');
    if (!summaryContainer) return;

    const res = await fetchAPI('/officer/api/dashboard-summary');
    if (res.success && res.data) {
        const d = res.data;
        document.getElementById('statTotalClaims').textContent = d.total_claims;
        document.getElementById('statPendingReview').textContent = d.pending_review;
        document.getElementById('statUnderReview').textContent = d.under_review;
        document.getElementById('statDocRequired').textContent = d.documents_required;
        document.getElementById('statApproved').textContent = d.approved;
        document.getElementById('statRejected').textContent = d.rejected;

        // Render Pending Claims Table
        const tbody = document.getElementById('officerPendingTableBody');
        if (tbody) {
            if (d.recent_pending_claims.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No pending claims awaiting review</td></tr>';
            } else {
                tbody.innerHTML = d.recent_pending_claims.map(c => `
                    <tr>
                        <td class="font-weight-bold"><a href="/officer/claims/${c.id}/review">${c.claim_number}</a></td>
                        <td>${c.customer_name}</td>
                        <td>${c.policy_number} (${c.policy_type_name})</td>
                        <td class="font-weight-bold">₹${parseFloat(c.claim_amount).toLocaleString('en-IN')}</td>
                        <td>${c.claim_date}</td>
                        <td><span class="badge-status badge-${c.status.toLowerCase()}">${c.status.replace('_', ' ')}</span></td>
                        <td>
                            <a href="/officer/claims/${c.id}/review" class="btn btn-sm btn-primary">
                                <i class="fas fa-search-plus me-1"></i> Assess
                            </a>
                        </td>
                    </tr>
                `).join('');
            }
        }
    }
}

function initReviewForm() {
    const form = document.getElementById('claimReviewForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const claimId = document.getElementById('reviewClaimId').value;
        const decision = document.getElementById('reviewDecision').value;
        const remarks = document.getElementById('reviewRemarks').value;

        if (decision === 'REJECTED' && !remarks.strip) {
            if (!remarks.trim()) {
                showToast('Please provide a reason for rejecting this claim.', 'danger');
                return;
            }
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;

        const res = await fetchAPI(`/api/claims/${claimId}/review`, {
            method: 'POST',
            body: { decision, remarks }
        });

        submitBtn.disabled = false;
        if (res.success) {
            showToast(res.message, 'success');
            setTimeout(() => {
                window.location.href = '/officer/pending-claims';
            }, 1000);
        } else {
            showToast(res.message, 'danger');
        }
    });
}
