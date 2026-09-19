document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle'); // inside drawer: closes it
    const sidebarOpenBtn = document.getElementById('sidebarOpenBtn'); // in top bar: opens it

    function syncSidebar(open) {
        if (!sidebar) return;
        sidebar.classList.toggle('open', open);
        if (sidebarToggle) const isEnglish = document.documentElement.lang === 'en';
        sidebarToggle.setAttribute('aria-label', isEnglish
            ? (open ? 'Close menu' : 'Open menu')
            : (open ? 'مینو بند کریں' : 'مینو کھولیں'));
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            syncSidebar(!sidebar.classList.contains('open'));
        });
    }
    if (sidebarOpenBtn) {
        sidebarOpenBtn.addEventListener('click', function() {
            syncSidebar(true);
        });
    }
    // Tap outside the drawer (on the page content) closes it.
    document.addEventListener('click', function(e) {
        if (sidebar && sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            !(sidebarOpenBtn && sidebarOpenBtn.contains(e.target)) &&
            !(sidebarToggle && sidebarToggle.contains(e.target))) {
            syncSidebar(false);
        }
    });

    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});
