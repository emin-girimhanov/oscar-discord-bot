document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-email]').forEach(link => {
    const email = atob(link.dataset.email); // Base64
    link.href = 'mailto:' + email;
    link.textContent = email;
  });
});
