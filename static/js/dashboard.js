/**
 * Hostel Parcel Desk - Master Workbench Console Script
 * Hallmark-compliant interactive layer with full keyboard shortcuts,
 * 8-state feedback, copy utilities, and real-time API integrations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    let allParcels = [];
    let formOptions = { students: [], couriers: [], staff: [] };

    // DOM Elements
    const elements = {
        themeToggleBtn: document.getElementById('themeToggleBtn'),
        statTotalVal: document.getElementById('statTotalVal'),
        statPendingVal: document.getElementById('statPendingVal'),
        statCollectedVal: document.getElementById('statCollectedVal'),
        statOverdueVal: document.getElementById('statOverdueVal'),
        systemStatusText: document.getElementById('systemStatusText'),

        cardPending: document.getElementById('cardPending'),
        cardCollected: document.getElementById('cardCollected'),
        cardOverdue: document.getElementById('cardOverdue'),

        tabButtons: document.querySelectorAll('.tab-btn'),
        tabPanels: document.querySelectorAll('.tab-panel'),

        parcelsTableBody: document.getElementById('parcelsTableBody'),
        searchInput: document.getElementById('searchInput'),
        statusFilter: document.getElementById('statusFilter'),
        blockFilter: document.getElementById('blockFilter'),
        refreshParcelsBtn: document.getElementById('refreshParcelsBtn'),

        registerModal: document.getElementById('registerModal'),
        openRegisterModalBtn: document.getElementById('openRegisterModalBtn'),
        closeRegisterModalBtn: document.getElementById('closeRegisterModalBtn'),
        cancelRegisterBtn: document.getElementById('cancelRegisterBtn'),
        registerParcelForm: document.getElementById('registerParcelForm'),

        regTrackingNo: document.getElementById('regTrackingNo'),
        regStudentSelect: document.getElementById('regStudentSelect'),
        regCourierSelect: document.getElementById('regCourierSelect'),
        regStaffSelect: document.getElementById('regStaffSelect'),
        regShelfLoc: document.getElementById('regShelfLoc'),
        regRemarks: document.getElementById('regRemarks'),

        codeSuccessModal: document.getElementById('codeSuccessModal'),
        successTrackingNo: document.getElementById('successTrackingNo'),
        successPickupCode: document.getElementById('successPickupCode'),
        closeSuccessModalBtn: document.getElementById('closeSuccessModalBtn'),
        copySuccessPinBtn: document.getElementById('copySuccessPinBtn'),

        verifyForm: document.getElementById('verifyForm'),
        verifyParcelSelect: document.getElementById('verifyParcelSelect'),
        verifyParcelPreview: document.getElementById('verifyParcelPreview'),
        prevStudentName: document.getElementById('prevStudentName'),
        prevRegNo: document.getElementById('prevRegNo'),
        prevShelf: document.getElementById('prevShelf'),
        prevArrival: document.getElementById('prevArrival'),
        enteredPinCode: document.getElementById('enteredPinCode'),
        pinRevealToggleBtn: document.getElementById('pinRevealToggleBtn'),
        collectorRegInput: document.getElementById('collectorRegInput'),
        verifyingStaffSelect: document.getElementById('verifyingStaffSelect'),
        verifyRemarksInput: document.getElementById('verifyRemarksInput'),
        submitVerifyBtn: document.getElementById('submitVerifyBtn'),
        verificationFeedbackPanel: document.getElementById('verificationFeedbackPanel'),

        thresholdInput: document.getElementById('thresholdInput'),
        runCursorBtn: document.getElementById('runCursorBtn'),
        sendOverdueRemindersBtn: document.getElementById('sendOverdueRemindersBtn'),
        overdueCountBadge: document.getElementById('overdueCountBadge'),
        overdueSummaryDesc: document.getElementById('overdueSummaryDesc'),
        overdueTableBody: document.getElementById('overdueTableBody'),

        auditListContainer: document.getElementById('auditListContainer'),
        refreshAuditBtn: document.getElementById('refreshAuditBtn'),
        notifListContainer: document.getElementById('notifListContainer'),
        refreshNotifsBtn: document.getElementById('refreshNotifsBtn'),

        toastContainer: document.getElementById('toastContainer')
    };

    // ------------------------------------------------------------------------
    // THEME HANDLING (Dark / Light with local storage persistence)
    // ------------------------------------------------------------------------
    const savedTheme = localStorage.getItem('hpd_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    if (elements.themeToggleBtn) {
        elements.themeToggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('hpd_theme', next);
            // Gate 16: Silent success — user sees the theme switch immediately
        });
    }

    // ------------------------------------------------------------------------
    // WORKBENCH TAB NAVIGATION
    // ------------------------------------------------------------------------
    function switchTab(targetId) {
        elements.tabButtons.forEach(btn => {
            const isMatch = btn.getAttribute('data-target') === targetId;
            btn.classList.toggle('active', isMatch);
            btn.setAttribute('aria-selected', isMatch ? 'true' : 'false');
        });

        elements.tabPanels.forEach(panel => {
            const isMatch = panel.id === targetId;
            panel.classList.toggle('active', isMatch);
        });

        if (targetId === 'tabAudit') {
            loadAuditTrail();
            loadNotifications();
        } else if (targetId === 'tabOverdue') {
            executeCursorReport();
        }
    }

    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            switchTab(targetId);
        });
    });

    // Metric Cards Click-to-Filter shortcuts
    if (elements.cardPending) {
        elements.cardPending.addEventListener('click', () => {
            switchTab('tabInventory');
            if (elements.statusFilter) {
                elements.statusFilter.value = 'PENDING';
                loadParcels();
            }
        });
    }

    if (elements.cardCollected) {
        elements.cardCollected.addEventListener('click', () => {
            switchTab('tabInventory');
            if (elements.statusFilter) {
                elements.statusFilter.value = 'COLLECTED';
                loadParcels();
            }
        });
    }

    if (elements.cardOverdue) {
        elements.cardOverdue.addEventListener('click', () => {
            switchTab('tabOverdue');
        });
    }

    // ------------------------------------------------------------------------
    // KEYBOARD SHORTCUTS ENGINE
    // ------------------------------------------------------------------------
    document.addEventListener('keydown', (e) => {
        const activeTag = (document.activeElement.tagName || '').toLowerCase();
        const isEditing = activeTag === 'input' || activeTag === 'select' || activeTag === 'textarea';

        if (e.key === 'Escape') {
            closeRegisterModal();
            if (elements.codeSuccessModal) elements.codeSuccessModal.classList.remove('open');
            return;
        }

        if (isEditing) return;

        if (e.key === '1') {
            e.preventDefault();
            switchTab('tabInventory');
        } else if (e.key === '2') {
            e.preventDefault();
            switchTab('tabVerify');
        } else if (e.key === '3') {
            e.preventDefault();
            switchTab('tabOverdue');
        } else if (e.key === '4') {
            e.preventDefault();
            switchTab('tabAudit');
        } else if (e.key === '/') {
            e.preventDefault();
            switchTab('tabInventory');
            if (elements.searchInput) elements.searchInput.focus();
        } else if (e.key === 'n' || e.key === 'N') {
            e.preventDefault();
            openRegisterModal();
        }
    });

    // ------------------------------------------------------------------------
    // TOAST NOTIFICATIONS (Reserved strictly for errors & async tasks — Gate 16)
    // ------------------------------------------------------------------------
    function showToast(message, type = 'info', duration = 4000) {
        if (!elements.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconSvg = '';
        if (type === 'success') {
            iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>';
        } else if (type === 'error') {
            iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
        } else {
            iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
        }

        toast.innerHTML = `${iconSvg} <span>${escapeHtml(message)}</span>`;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 250);
        }, duration);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"']/g, m => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[m]);
    }

    // ------------------------------------------------------------------------
    // DATA LOADERS & API CALLS
    // ------------------------------------------------------------------------
    async function loadFormOptions() {
        try {
            const res = await fetch('/api/form-options');
            const data = await res.json();
            if (data.success) {
                formOptions = data;

                // Populate Student Dropdown
                if (elements.regStudentSelect) {
                    elements.regStudentSelect.innerHTML = '<option value="">-- Choose Recipient Student --</option>' +
                        data.students.map(s => `<option value="${s.student_id}">${escapeHtml(s.reg_no)} — ${escapeHtml(s.full_name)} (${escapeHtml(s.hostel_block)}, ${escapeHtml(s.room_no)})</option>`).join('');
                }

                // Populate Courier Dropdown
                if (elements.regCourierSelect) {
                    elements.regCourierSelect.innerHTML = '<option value="">-- Choose Courier Service --</option>' +
                        data.couriers.map(c => `<option value="${c.courier_id}">${escapeHtml(c.company_name)} (${escapeHtml(c.service_type)})</option>`).join('');
                }

                // Populate Staff Dropdowns
                const staffOptions = data.staff.map(st => `<option value="${st.staff_id}">${escapeHtml(st.staff_code)} — ${escapeHtml(st.full_name)} (${escapeHtml(st.staff_role)})</option>`).join('');
                if (elements.regStaffSelect) elements.regStaffSelect.innerHTML = staffOptions;
                if (elements.verifyingStaffSelect) elements.verifyingStaffSelect.innerHTML = staffOptions;
            }
        } catch (err) {
            console.error('Error loading form options:', err);
        }
    }

    async function loadStats() {
        try {
            const res = await fetch('/api/stats');
            const result = await res.json();
            if (result.success) {
                const s = result.data;
                if (elements.statTotalVal) elements.statTotalVal.textContent = s.total;
                if (elements.statPendingVal) elements.statPendingVal.textContent = s.pending;
                if (elements.statCollectedVal) elements.statCollectedVal.textContent = s.collected;
                if (elements.statOverdueVal) elements.statOverdueVal.textContent = s.overdue;
                if (elements.overdueCountBadge) elements.overdueCountBadge.textContent = s.overdue;
            }
        } catch (err) {
            console.error('Error loading stats:', err);
        }
    }

    async function loadParcels() {
        const search = elements.searchInput ? elements.searchInput.value : '';
        const status = elements.statusFilter ? elements.statusFilter.value : 'ALL';
        const block = elements.blockFilter ? elements.blockFilter.value : 'ALL';

        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (status) params.append('status', status);
        if (block) params.append('block', block);

        try {
            if (elements.parcelsTableBody) {
                elements.parcelsTableBody.innerHTML = `
                    <tr>
                        <td colspan="9" class="table-empty">
                            <div class="table-loading-spinner"></div>
                            <span>Fetching parcels from campus database...</span>
                        </td>
                    </tr>
                `;
            }

            const res = await fetch(`/api/parcels?${params.toString()}`);
            const result = await res.json();

            if (result.success) {
                allParcels = result.data;
                renderParcelsTable(allParcels);
                updatePendingSelect(allParcels);
            } else {
                elements.parcelsTableBody.innerHTML = `<tr><td colspan="9" class="table-empty">Error: ${escapeHtml(result.message)}</td></tr>`;
            }
        } catch (err) {
            if (elements.parcelsTableBody) {
                elements.parcelsTableBody.innerHTML = '<tr><td colspan="9" class="table-empty">Failed to load parcels from database.</td></tr>';
            }
            console.error(err);
        }
    }

    function renderParcelsTable(parcels) {
        if (!elements.parcelsTableBody) return;

        if (!parcels || parcels.length === 0) {
            elements.parcelsTableBody.innerHTML = '<tr><td colspan="9" class="table-empty">No packages found matching your criteria.</td></tr>';
            return;
        }

        elements.parcelsTableBody.innerHTML = parcels.map(p => {
            const badgeClass = p.status === 'COLLECTED' ? 'badge-collected' :
                               (p.is_overdue || p.status === 'OVERDUE') ? 'badge-overdue' : 'badge-pending';
            const statusLabel = p.is_overdue && p.status === 'PENDING' ? 'OVERDUE' : p.status;
            
            const actionBtn = p.status === 'PENDING' ? 
                `<button class="btn btn-primary btn-sm quick-verify-btn" data-id="${p.parcel_id}" title="Proceed to Verification Station">Verify</button>` :
                `<span class="badge badge-collected" style="font-size:0.75rem;">Verified</span>`;

            return `
                <tr>
                    <td><strong class="code-val">#${p.parcel_id}</strong></td>
                    <td>
                        <div style="display:flex; align-items:center; gap:6px;">
                            <code class="code-val">${escapeHtml(p.tracking_number)}</code>
                            <button class="btn btn-secondary btn-sm copy-inline-btn" data-copy="${escapeHtml(p.tracking_number)}" title="Copy tracking #" style="height:24px; padding:0 0.35rem; font-size:0.65rem;">Copy</button>
                        </div>
                    </td>
                    <td>
                        <div style="font-weight:600; color:var(--color-ink);">${escapeHtml(p.student_name)}</div>
                        <div style="font-size:0.75rem; color:var(--color-ink-muted); font-family:var(--font-mono);">${escapeHtml(p.reg_no)}</div>
                    </td>
                    <td>
                        <span style="font-weight:500;">${escapeHtml(p.hostel_block)}</span>
                        <span style="color:var(--color-ink-muted); margin:0 3px;">•</span>
                        <span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--color-ink-2);">${escapeHtml(p.room_no)}</span>
                    </td>
                    <td><span style="font-size:0.85rem;">${escapeHtml(p.courier_name)}</span></td>
                    <td><span class="badge badge-shelf">${escapeHtml(p.shelf_location)}</span></td>
                    <td><span class="badge badge-wait">${p.waiting_hours >= 0 ? p.waiting_hours + ' hrs' : 'Just now'}</span></td>
                    <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
                    <td style="text-align: right;">${actionBtn}</td>
                </tr>
            `;
        }).join('');

        // Wire quick-verify buttons
        document.querySelectorAll('.quick-verify-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const pId = e.currentTarget.getAttribute('data-id');
                switchTab('tabVerify');
                if (elements.verifyParcelSelect) {
                    elements.verifyParcelSelect.value = pId;
                    elements.verifyParcelSelect.dispatchEvent(new Event('change'));
                }
                if (elements.enteredPinCode) elements.enteredPinCode.focus();
            });
        });

        // Wire inline copy buttons
        document.querySelectorAll('.copy-inline-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const text = e.currentTarget.getAttribute('data-copy');
                if (text && navigator.clipboard) {
                    navigator.clipboard.writeText(text);
                    const originalText = e.currentTarget.textContent;
                    e.currentTarget.textContent = 'Copied!';
                    setTimeout(() => { e.currentTarget.textContent = originalText; }, 1500);
                }
            });
        });
    }

    function updatePendingSelect(parcels) {
        if (!elements.verifyParcelSelect) return;
        const pending = parcels.filter(p => p.status === 'PENDING');
        elements.verifyParcelSelect.innerHTML = '<option value="">-- Choose Pending Package --</option>' +
            pending.map(p => `<option value="${p.parcel_id}">#${p.parcel_id} — ${escapeHtml(p.tracking_number)} (${escapeHtml(p.student_name)}, ${escapeHtml(p.reg_no)})</option>`).join('');
    }

    // ------------------------------------------------------------------------
    // VERIFY PREVIEW & SELECTION
    // ------------------------------------------------------------------------
    if (elements.verifyParcelSelect) {
        elements.verifyParcelSelect.addEventListener('change', () => {
            const selectedId = parseInt(elements.verifyParcelSelect.value);
            if (!selectedId) {
                if (elements.verifyParcelPreview) elements.verifyParcelPreview.style.display = 'none';
                return;
            }

            const parcel = allParcels.find(p => p.parcel_id === selectedId);
            if (parcel && elements.verifyParcelPreview) {
                if (elements.prevStudentName) elements.prevStudentName.textContent = parcel.student_name;
                if (elements.prevRegNo) elements.prevRegNo.textContent = parcel.reg_no;
                if (elements.prevShelf) elements.prevShelf.textContent = parcel.shelf_location;
                if (elements.prevArrival) elements.prevArrival.textContent = parcel.arrival_time;
                elements.verifyParcelPreview.style.display = 'flex';
            }
        });
    }

    // PIN Reveal Toggle
    if (elements.pinRevealToggleBtn && elements.enteredPinCode) {
        elements.pinRevealToggleBtn.addEventListener('click', () => {
            const isPassword = elements.enteredPinCode.type === 'password';
            elements.enteredPinCode.type = isPassword ? 'text' : 'password';
            elements.pinRevealToggleBtn.setAttribute('title', isPassword ? 'Hide PIN' : 'Show PIN');
        });
    }

    // ------------------------------------------------------------------------
    // REGISTRATION MODAL CONTROLS
    // ------------------------------------------------------------------------
    function openRegisterModal() {
        if (elements.registerModal) {
            elements.registerModal.classList.add('open');
            elements.registerModal.setAttribute('aria-hidden', 'false');
            if (elements.regTrackingNo) elements.regTrackingNo.focus();
        }
    }

    function closeRegisterModal() {
        if (elements.registerModal) {
            elements.registerModal.classList.remove('open');
            elements.registerModal.setAttribute('aria-hidden', 'true');
            if (elements.registerParcelForm) elements.registerParcelForm.reset();
        }
    }

    if (elements.openRegisterModalBtn) elements.openRegisterModalBtn.addEventListener('click', openRegisterModal);
    if (elements.closeRegisterModalBtn) elements.closeRegisterModalBtn.addEventListener('click', closeRegisterModal);
    if (elements.cancelRegisterBtn) elements.cancelRegisterBtn.addEventListener('click', closeRegisterModal);

    // Close on backdrop click
    if (elements.registerModal) {
        elements.registerModal.addEventListener('click', (e) => {
            if (e.target === elements.registerModal) closeRegisterModal();
        });
    }

    if (elements.codeSuccessModal) {
        elements.codeSuccessModal.addEventListener('click', (e) => {
            if (e.target === elements.codeSuccessModal) elements.codeSuccessModal.classList.remove('open');
        });
    }

    if (elements.closeSuccessModalBtn) {
        elements.closeSuccessModalBtn.addEventListener('click', () => {
            if (elements.codeSuccessModal) elements.codeSuccessModal.classList.remove('open');
        });
    }

    // Copy PIN Button in Success Dialog
    if (elements.copySuccessPinBtn && elements.successPickupCode) {
        elements.copySuccessPinBtn.addEventListener('click', () => {
            const pin = elements.successPickupCode.textContent.trim();
            if (pin && navigator.clipboard) {
                navigator.clipboard.writeText(pin);
                elements.copySuccessPinBtn.textContent = 'Copied!';
                setTimeout(() => { elements.copySuccessPinBtn.textContent = 'Copy'; }, 2000);
            }
        });
    }

    // ------------------------------------------------------------------------
    // SUBMIT PARCEL REGISTRATION
    // ------------------------------------------------------------------------
    if (elements.registerParcelForm) {
        elements.registerParcelForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const payload = {
                tracking_number: elements.regTrackingNo.value.trim(),
                student_id: elements.regStudentSelect.value,
                courier_id: elements.regCourierSelect.value,
                staff_id: elements.regStaffSelect.value,
                shelf_location: elements.regShelfLoc.value.trim(),
                remarks: elements.regRemarks.value.trim()
            };

            const submitBtn = document.getElementById('submitRegisterBtn');
            try {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Registering & Dispatching...';
                }

                const res = await fetch('/api/parcels/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await res.json();
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon-svg" aria-hidden="true">
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                            <polyline points="17 21 17 13 7 13 7 21"/>
                            <polyline points="7 3 7 8 15 8"/>
                        </svg>
                        <span>Save & Dispatch Alerts</span>`;
                }

                if (result.success) {
                    closeRegisterModal();
                    // Show PIN dialog directly (Silent success — dialog is the visual confirmation)
                    if (elements.successTrackingNo) elements.successTrackingNo.textContent = result.result.tracking_number;
                    if (elements.successPickupCode) elements.successPickupCode.textContent = result.result.pickup_code;
                    if (elements.codeSuccessModal) elements.codeSuccessModal.classList.add('open');

                    loadStats();
                    loadParcels();
                } else {
                    showToast(result.message, 'error', 6000);
                }
            } catch (err) {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = `<span>Save & Dispatch Alerts</span>`;
                }
                showToast('Network error while registering parcel.', 'error');
                console.error(err);
            }
        });
    }

    // ------------------------------------------------------------------------
    // SUBMIT PICKUP VERIFICATION
    // ------------------------------------------------------------------------
    if (elements.verifyForm) {
        elements.verifyForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const parcelId = elements.verifyParcelSelect.value;
            const enteredCode = elements.enteredPinCode.value.trim();
            const staffId = elements.verifyingStaffSelect.value;
            const collectorReg = elements.collectorRegInput.value.trim();
            const remarks = elements.verifyRemarksInput.value.trim();

            if (!parcelId || !enteredCode) {
                showToast('Please select a package and enter the 6-digit PIN.', 'warning');
                return;
            }

            const btn = elements.submitVerifyBtn;
            try {
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Verifying Handover...';
                }

                const res = await fetch('/api/parcels/verify-pickup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        parcel_id: parcelId,
                        entered_code: enteredCode,
                        staff_id: staffId,
                        collector_reg_no: collectorReg,
                        remarks: remarks
                    })
                });

                const result = await res.json();
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon-svg" aria-hidden="true">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        <span>Validate & Authorize Handover</span>`;
                }

                if (result.success) {
                    // Render certificate right in front of user (Silent success — Gate 16)
                    renderVerificationReceipt(true, result.message, parcelId, enteredCode);
                    elements.verifyForm.reset();
                    if (elements.verifyParcelPreview) elements.verifyParcelPreview.style.display = 'none';
                    loadStats();
                    loadParcels();
                } else {
                    renderVerificationReceipt(false, result.message, parcelId, enteredCode);
                    showToast(result.message, 'error', 6000);
                }
            } catch (err) {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<span>Validate & Authorize Handover</span>`;
                }
                showToast('Error communicating with verification endpoint.', 'error');
                console.error(err);
            }
        });
    }

    function renderVerificationReceipt(isSuccess, message, parcelId, enteredCode) {
        if (!elements.verificationFeedbackPanel) return;
        const parcel = allParcels.find(p => p.parcel_id === parseInt(parcelId));
        const timestamp = new Date().toLocaleString();

        if (isSuccess) {
            elements.verificationFeedbackPanel.innerHTML = `
                <div class="receipt-card">
                    <div class="receipt-status-header">
                        <div class="receipt-icon receipt-icon-success">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                            </svg>
                        </div>
                        <div>
                            <h3 style="color:var(--color-success);">Handover Authenticated</h3>
                            <p>${escapeHtml(message)}</p>
                        </div>
                    </div>
                    <div class="receipt-details-list">
                        <div class="receipt-detail-row">
                            <span class="label">Carrier Tracking:</span>
                            <span class="val code-val">${parcel ? escapeHtml(parcel.tracking_number) : '#' + parcelId}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">Recipient Student:</span>
                            <span class="val">${parcel ? escapeHtml(parcel.student_name + ' (' + parcel.reg_no + ')') : '--'}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">Locker / Shelf Cleared:</span>
                            <span class="val badge badge-shelf">${parcel ? escapeHtml(parcel.shelf_location) : '--'}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">Verification Timestamp:</span>
                            <span class="val">${timestamp}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">Digital Receipts:</span>
                            <span class="val" style="color:var(--color-success); font-weight:600;">Email Confirmation Dispatched</span>
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-block" onclick="document.getElementById('verifyParcelSelect').focus();">
                        Verify Next Delivery
                    </button>
                </div>
            `;
        } else {
            elements.verificationFeedbackPanel.innerHTML = `
                <div class="receipt-card">
                    <div class="receipt-status-header">
                        <div class="receipt-icon receipt-icon-error">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
                            </svg>
                        </div>
                        <div>
                            <h3 style="color:var(--color-danger);">Handover Rejected</h3>
                            <p>${escapeHtml(message)}</p>
                        </div>
                    </div>
                    <div class="receipt-details-list">
                        <div class="receipt-detail-row">
                            <span class="label">Target Package:</span>
                            <span class="val code-val">${parcel ? escapeHtml(parcel.tracking_number) : '#' + parcelId}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">PIN Code Entered:</span>
                            <span class="val" style="font-family:var(--font-mono); color:var(--color-danger);">${escapeHtml(enteredCode)}</span>
                        </div>
                        <div class="receipt-detail-row">
                            <span class="label">Security Rule:</span>
                            <span class="val">Valid 6-digit verification code required for handover</span>
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-block" onclick="document.getElementById('enteredPinCode').focus();">
                        Retry With Correct PIN
                    </button>
                </div>
            `;
        }
    }

    // ------------------------------------------------------------------------
    // OVERDUE RETENTION WATCHDOG & ALERTS
    // ------------------------------------------------------------------------
    async function executeCursorReport() {
        const threshold = elements.thresholdInput ? (elements.thresholdInput.value || 48) : 48;
        try {
            if (elements.overdueTableBody) {
                elements.overdueTableBody.innerHTML = `
                    <tr>
                        <td colspan="9" class="table-empty">
                            <div class="table-loading-spinner"></div>
                            <span>Scanning overdue packages...</span>
                        </td>
                    </tr>
                `;
            }
            const res = await fetch(`/api/reports/overdue?hours=${threshold}`);
            const result = await res.json();

            if (result.success) {
                const list = result.data;
                if (elements.overdueCountBadge) {
                    elements.overdueCountBadge.textContent = list.length;
                }
                if (elements.overdueSummaryDesc) {
                    elements.overdueSummaryDesc.textContent = `Identified ${list.length} packages awaiting pickup for >= ${threshold} hours. Click "Dispatch SMS & Email Reminders" to notify all students.`;
                }

                if (!elements.overdueTableBody) return;

                if (list.length === 0) {
                    elements.overdueTableBody.innerHTML = `<tr><td colspan="9" class="table-empty">No packages currently exceed the ${threshold}-hour retention threshold.</td></tr>`;
                } else {
                    elements.overdueTableBody.innerHTML = list.map(p => `
                        <tr>
                            <td><strong class="code-val">#${p.parcel_id}</strong></td>
                            <td><code class="code-val">${escapeHtml(p.tracking_number)}</code></td>
                            <td><strong style="color:var(--color-ink);">${escapeHtml(p.student_name)}</strong></td>
                            <td><span style="font-family:var(--font-mono);">${escapeHtml(p.reg_no)}</span></td>
                            <td>${escapeHtml(p.hostel_block)} • ${escapeHtml(p.room_no)}</td>
                            <td><span class="badge badge-shelf">${escapeHtml(p.shelf_location)}</span></td>
                            <td><strong style="color:var(--color-danger); font-family:var(--font-mono);">${p.waiting_hours} hrs</strong></td>
                            <td>${escapeHtml(p.courier_name)}</td>
                            <td><span class="badge badge-overdue">OVERDUE</span></td>
                        </tr>
                    `).join('');
                }
            }
        } catch (err) {
            if (elements.overdueTableBody) {
                elements.overdueTableBody.innerHTML = `<tr><td colspan="9" class="table-empty">Failed to load overdue report: ${err}</td></tr>`;
            }
        }
    }

    if (elements.runCursorBtn) {
        elements.runCursorBtn.addEventListener('click', executeCursorReport);
    }

    if (elements.sendOverdueRemindersBtn) {
        elements.sendOverdueRemindersBtn.addEventListener('click', async () => {
            const threshold = elements.thresholdInput ? elements.thresholdInput.value : 48;
            const btn = elements.sendOverdueRemindersBtn;
            btn.disabled = true;
            btn.textContent = 'Dispatching Email Alerts...';

            try {
                const res = await fetch('/api/notifications/send-overdue-reminders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hours: threshold })
                });
                const result = await res.json();
                if (result.success) {
                    showToast(result.message, 'success', 5000);
                    loadNotifications();
                } else {
                    showToast('Failed to send reminders: ' + result.message, 'error');
                }
            } catch (err) {
                showToast('Network error while dispatching alerts.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon-svg" aria-hidden="true">
                        <path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>
                    </svg>
                    <span>Dispatch Email Reminders</span>`;
            }
        });
    }

    // ------------------------------------------------------------------------
    // AUDIT TRAIL & NOTIFICATION LOGS
    // ------------------------------------------------------------------------
    async function loadAuditTrail() {
        if (!elements.auditListContainer) return;
        try {
            elements.auditListContainer.innerHTML = '<div class="table-empty">Loading activity history...</div>';
            const res = await fetch('/api/audit-log');
            const result = await res.json();

            if (result.success && result.data.length > 0) {
                elements.auditListContainer.innerHTML = result.data.map(a => `
                    <div class="audit-item">
                        <div class="audit-meta">
                            <span>Parcel #${a.parcel_id} (${escapeHtml(a.tracking_number)}) • Recipient: ${escapeHtml(a.student_name)}</span>
                            <span>${escapeHtml(a.changed_at)}</span>
                        </div>
                        <div class="audit-transition">
                            <span class="badge badge-${a.old_status.toLowerCase()}">${a.old_status}</span>
                            <span style="color:var(--color-ink-muted);">&rarr;</span>
                            <span class="badge badge-${a.new_status.toLowerCase()}">${a.new_status}</span>
                            <span style="margin-left:auto; font-size:0.75rem; color:var(--color-ink-muted);">${escapeHtml(a.changed_by)}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                elements.auditListContainer.innerHTML = '<div class="table-empty">No status transition records found.</div>';
            }
        } catch (err) {
            elements.auditListContainer.innerHTML = '<div class="table-empty">Failed to load activity logs.</div>';
        }
    }

    async function loadNotifications() {
        if (!elements.notifListContainer) return;
        try {
            elements.notifListContainer.innerHTML = '<div class="table-empty">Loading notifications...</div>';
            const res = await fetch('/api/notifications');
            const result = await res.json();

            if (result.success && result.data.length > 0) {
                elements.notifListContainer.innerHTML = result.data.map(n => {
                    const isSms = (n.channel || '').includes('SMS');
                    const channelBadge = isSms ?
                        '<span class="badge badge-sms">SMS</span>' :
                        '<span class="badge badge-email">EMAIL</span>';
                    const recipient = isSms ? (n.phone_no || '') : (n.student_email || '');

                    return `
                        <div class="notif-item">
                            <div class="notif-header">
                                <span class="notif-type-tag">
                                    ${channelBadge}
                                    <strong style="margin-left:0.35rem; color:var(--color-ink);">${escapeHtml(n.notification_type.replace(/_/g, ' '))}</strong>
                                    ${recipient ? `<span style="color:var(--color-ink-muted); margin-left:0.35rem;">(${escapeHtml(recipient)})</span>` : ''}
                                </span>
                                <span>${escapeHtml(n.sent_at)}</span>
                            </div>
                            <div class="notif-body">${escapeHtml(n.message_body)}</div>
                        </div>
                    `;
                }).join('');
            } else {
                elements.notifListContainer.innerHTML = '<div class="table-empty">No notification records dispatched yet.</div>';
            }
        } catch (err) {
            elements.notifListContainer.innerHTML = '<div class="table-empty">Failed to load notifications.</div>';
        }
    }

    if (elements.refreshAuditBtn) elements.refreshAuditBtn.addEventListener('click', loadAuditTrail);
    if (elements.refreshNotifsBtn) elements.refreshNotifsBtn.addEventListener('click', loadNotifications);

    // ------------------------------------------------------------------------
    // SEARCH & FILTER LISTENERS
    // ------------------------------------------------------------------------
    if (elements.searchInput) elements.searchInput.addEventListener('input', () => loadParcels());
    if (elements.statusFilter) elements.statusFilter.addEventListener('change', () => loadParcels());
    if (elements.blockFilter) elements.blockFilter.addEventListener('change', () => loadParcels());
    if (elements.refreshParcelsBtn) {
        elements.refreshParcelsBtn.addEventListener('click', () => {
            loadStats();
            loadParcels();
        });
    }

    // ------------------------------------------------------------------------
    // INITIALIZATION
    // ------------------------------------------------------------------------
    loadFormOptions();
    loadStats();
    loadParcels();
});
