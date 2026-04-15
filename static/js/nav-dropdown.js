window.toggleAdvancedTabs = function(e) {
  e.stopPropagation();
  var dd = e.target.closest('.nav-tab-more').querySelector('.advanced-tabs-dropdown');
  if (!dd) return;
  var vis = dd.style.display === 'none' || !dd.style.display;
  document.querySelectorAll('.advanced-tabs-dropdown').forEach(function(d){ d.style.display = 'none'; });
  if (vis) dd.style.display = 'block';
};
window.hideAdvDropdown = function() {
  document.querySelectorAll('.advanced-tabs-dropdown').forEach(function(d){ d.style.display = 'none'; });
};
document.addEventListener('click', function(e) {
  if (!e.target.closest('.nav-tab-more') && !e.target.closest('.advanced-tabs-dropdown')) {
    if (typeof hideAdvDropdown !== 'undefined') hideAdvDropdown();
  }
});
