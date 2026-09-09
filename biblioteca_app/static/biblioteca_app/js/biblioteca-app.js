// JavaScript del Sistema de Biblioteca.
// Los comentarios explican los eventos y comportamientos implementados.


document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-table-filter]').forEach(input => {
    const selector = input.getAttribute('data-table-filter');
    const table = document.querySelector(selector);
    if (!table) return;
    const rows = [...table.querySelectorAll('[data-search]')];
    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      rows.forEach(row => {
        row.hidden = Boolean(q) && !row.dataset.search.includes(q);
      });
    });
  });
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      const msg = btn.getAttribute('data-confirm');
      if (!window.confirm(msg)) e.preventDefault();
    });
  });
  const year = new Date().getFullYear();
  document.querySelectorAll('[data-current-year]').forEach(el => el.textContent = year);
});
