// ========================================================
// THE GRAND HORIZON LUXURY HOTEL MANAGEMENT SYSTEM
// Main JavaScript Controller
// ========================================================

document.addEventListener('DOMContentLoaded', function () {
    // 1. Theme Toggle (Dark / Light)
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const currentTheme = localStorage.getItem('hms_theme') || 'dark';

    if (currentTheme === 'light') {
        document.body.classList.add('light-mode');
        if (themeToggleBtn) {
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        }
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            document.body.classList.toggle('light-mode');
            const isLight = document.body.classList.contains('light-mode');
            localStorage.setItem('hms_theme', isLight ? 'light' : 'dark');
            themeToggleBtn.innerHTML = isLight 
                ? '<i class="fa-solid fa-moon"></i>' 
                : '<i class="fa-solid fa-sun text-warning"></i>';
        });
    }

    // 2. Sidebar Mobile Toggle
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // 3. Initialize DataTables
    if (window.$ && $.fn.DataTable) {
        $('.datatable').DataTable({
            responsive: true,
            pageLength: 10,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search records..."
            }
        });
    }

    // 4. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // 5. Poll for unread notifications
    function loadNotifications() {
        const notifBadge = document.getElementById('notif-badge');
        const notifList = document.getElementById('notif-dropdown-list');
        if (!notifBadge || !notifList) return;

        fetch('/api/notifications/unread')
            .then(res => res.json())
            .then(data => {
                if (data.length > 0) {
                    notifBadge.textContent = data.length;
                    notifBadge.classList.remove('d-none');
                    notifList.innerHTML = data.map(n => `
                        <div class="p-2 border-bottom border-secondary border-opacity-25">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong class="small text-gold">${n.title}</strong>
                                <span class="badge bg-secondary" style="font-size: 0.65rem;">${n.time_ago}</span>
                            </div>
                            <p class="small text-muted mb-1">${n.message}</p>
                            ${n.link ? `<a href="${n.link}" class="btn btn-sm btn-link p-0 text-gold" style="font-size: 0.75rem;">View</a>` : ''}
                        </div>
                    `).join('');
                } else {
                    notifBadge.classList.add('d-none');
                    notifList.innerHTML = '<div class="p-3 text-center text-muted small">No new notifications</div>';
                }
            })
            .catch(() => {});
    }

    loadNotifications();
    setInterval(loadNotifications, 30000);
});

// POS Cart Management
window.posCart = {
    items: [],
    addItem: function (id, name, price) {
        const existing = this.items.find(i => i.id === id);
        if (existing) {
            existing.qty += 1;
        } else {
            this.items.push({ id: id, name: name, price: parseFloat(price), qty: 1 });
        }
        this.render();
    },
    updateQty: function (id, delta) {
        const item = this.items.find(i => i.id === id);
        if (item) {
            item.qty += delta;
            if (item.qty <= 0) {
                this.items = this.items.filter(i => i.id !== id);
            }
        }
        this.render();
    },
    removeItem: function (id) {
        this.items = this.items.filter(i => i.id !== id);
        this.render();
    },
    clear: function () {
        this.items = [];
        this.render();
    },
    render: function () {
        const container = document.getElementById('pos-cart-items');
        const subtotalEl = document.getElementById('pos-subtotal');
        const taxEl = document.getElementById('pos-tax');
        const totalEl = document.getElementById('pos-total');
        const hiddenInput = document.getElementById('pos-items-json');
        const checkoutBtn = document.getElementById('pos-submit-btn');

        if (!container) return;

        if (this.items.length === 0) {
            container.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">Cart is empty. Select items from the menu.</td></tr>';
            if (subtotalEl) subtotalEl.textContent = '$0.00';
            if (taxEl) taxEl.textContent = '$0.00';
            if (totalEl) totalEl.textContent = '$0.00';
            if (hiddenInput) hiddenInput.value = '';
            if (checkoutBtn) checkoutBtn.disabled = true;
            return;
        }

        let subtotal = 0;
        container.innerHTML = this.items.map(item => {
            const itemTotal = item.price * item.qty;
            subtotal += itemTotal;
            return `
                <tr>
                    <td>
                        <div class="fw-semibold">${item.name}</div>
                        <small class="text-muted">$${item.price.toFixed(2)}</small>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-secondary" onclick="posCart.updateQty(${item.id}, -1)">-</button>
                            <span class="btn btn-outline-secondary disabled text-light">${item.qty}</span>
                            <button type="button" class="btn btn-outline-secondary" onclick="posCart.updateQty(${item.id}, 1)">+</button>
                        </div>
                    </td>
                    <td class="text-end fw-bold">$${itemTotal.toFixed(2)}</td>
                    <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="posCart.removeItem(${item.id})">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        const tax = subtotal * 0.05;
        const total = subtotal + tax;

        if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        if (taxEl) taxEl.textContent = `$${tax.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
        if (hiddenInput) hiddenInput.value = JSON.stringify(this.items);
        if (checkoutBtn) checkoutBtn.disabled = false;
    }
};
