// Customer Dashboard & Operations JS with Razorpay Payment Integration

document.addEventListener('DOMContentLoaded', () => {
    loadCustomerDashboard();
    initSubmitClaimForm();
    initPurchasePolicy();
});

async function loadCustomerDashboard() {
    const summaryContainer = document.getElementById('customerDashboardStats');
    if (!summaryContainer) return;

    const res = await fetchAPI('/customer/api/dashboard-summary');
    if (res.success && res.data) {
        const d = res.data;
        document.getElementById('statActivePolicies').textContent = d.active_policies;
        document.getElementById('statTotalClaims').textContent = d.total_claims;
        document.getElementById('statPendingClaims').textContent = d.pending_claims;
        document.getElementById('statApprovedClaims').textContent = d.approved_claims;
        document.getElementById('statOpenTickets').textContent = d.open_tickets;

        // Render Recent Claims Table
        const tbody = document.getElementById('recentClaimsTableBody');
        if (tbody) {
            if (d.recent_claims.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No recent claims found</td></tr>';
            } else {
                tbody.innerHTML = d.recent_claims.map(c => `
                    <tr>
                        <td class="font-weight-bold"><a href="/customer/claims/${c.id}">${c.claim_number}</a></td>
                        <td>${c.policy_number}</td>
                        <td>${c.reason}</td>
                        <td class="font-weight-bold">₹${parseFloat(c.claim_amount).toLocaleString('en-IN')}</td>
                        <td><span class="badge-status badge-${c.status.toLowerCase()}">${c.status.replace('_', ' ')}</span></td>
                        <td><a href="/customer/claims/${c.id}" class="btn btn-sm btn-outline-primary">View</a></td>
                    </tr>
                `).join('');
            }
        }
    }
}

function initSubmitClaimForm() {
    const form = document.getElementById('submitClaimForm');
    if (!form) return;

    // Populate Customer Policies Dropdown
    fetchAPI('/api/policies').then(res => {
        const select = document.getElementById('policySelect');
        if (select && res.success && res.data) {
            const activePolicies = res.data.filter(p => p.status === 'ACTIVE');
            if (activePolicies.length === 0) {
                select.innerHTML = '<option value="">No active policies available</option>';
            } else {
                select.innerHTML = '<option value="">-- Select Active Policy --</option>' +
                    activePolicies.map(p => `<option value="${p.id}">${p.policy_number} - ${p.policy_type_name} (Max: ₹${parseFloat(p.coverage_amount).toLocaleString('en-IN')})</option>`).join('');
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        const res = await fetchAPI('/api/claims/submit', {
            method: 'POST',
            body: formData
        });

        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Claim';

        if (res.success) {
            showToast(res.message, 'success');
            setTimeout(() => {
                window.location.href = '/customer/claims';
            }, 1200);
        } else {
            showToast(res.message, 'danger');
        }
    });
}

function initPurchasePolicy() {
    window.purchasePolicyModal = function(policyTypeId, policyName, premium, coverage) {
        document.getElementById('modalPolicyTypeId').value = policyTypeId;
        document.getElementById('modalPolicyName').textContent = policyName;
        document.getElementById('modalPolicyPremium').textContent = '₹' + parseFloat(premium).toLocaleString('en-IN');
        document.getElementById('modalPolicyCoverage').textContent = '₹' + parseFloat(coverage).toLocaleString('en-IN');
        
        const modal = new bootstrap.Modal(document.getElementById('purchasePolicyModal'));
        modal.show();
    };

    const confirmBtn = document.getElementById('confirmPurchaseBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async () => {
            const policyTypeId = document.getElementById('modalPolicyTypeId').value;
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Initializing Razorpay...';

            // Step 1: Create Razorpay Order on Server
            const orderRes = await fetchAPI('/api/policies/create-payment-order', {
                method: 'POST',
                body: { policy_type_id: policyTypeId }
            });

            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Pay via Razorpay & Issue Policy';

            if (!orderRes.success) {
                showToast(orderRes.message, 'danger');
                return;
            }

            const data = orderRes.data;
            bootstrap.Modal.getInstance(document.getElementById('purchasePolicyModal')).hide();

            // Step 2: Launch Official Razorpay Checkout Modal
            const options = {
                "key": data.key_id,
                "amount": data.amount,
                "currency": data.currency,
                "name": "ClaimKaro Insurance",
                "description": `${data.policy_name} Annual Policy Premium`,
                "order_id": data.order_id,
                "handler": async function (response) {
                    // Step 3: Verify Payment Signature on Backend
                    showToast('Payment received! Verifying transaction...', 'info');

                    const verifyRes = await fetchAPI('/api/policies/verify-payment', {
                        method: 'POST',
                        body: {
                            policy_type_id: policyTypeId,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        }
                    });

                    if (verifyRes.success) {
                        showToast(verifyRes.message, 'success');
                        setTimeout(() => {
                            window.location.href = '/customer/policies';
                        }, 1200);
                    } else {
                        showToast(verifyRes.message, 'danger');
                    }
                },
                "prefill": {
                    "name": data.user_name,
                    "email": data.user_email,
                    "contact": data.user_phone
                },
                "theme": {
                    "color": "#2563eb"
                }
            };

            const rzp1 = new Razorpay(options);
            rzp1.on('payment.failed', function (response){
                showToast(`Payment failed: ${response.error.description}`, 'danger');
            });
            rzp1.open();
        });
    }
}
