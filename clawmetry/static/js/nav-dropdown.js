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

// The free Asimov view stays discoverable when the private workbench is absent.
// Its stored-evidence page has no background fetch on the digital dashboard.
//
// When the Physical AI workbench IS installed it owns Asimov 1 outright, as an
// entry in its own Hardware list, so the digital rail must not offer a second
// home for the same robot. The workbench is discovered asynchronously, after
// this handler has already run, so the handoff both clears a link already added
// and blocks a later one.
window.cmPhysicalAiWorkbenchPresent = function () {
  window.CM_PHYSICAL_AI_WORKBENCH = true;
  var existing = document.getElementById('cm-asimov-link');
  if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
};
document.addEventListener('DOMContentLoaded', function () {
  if (window.CLOUD_MODE || window.CM_PHYSICAL_AI_WORKBENCH || document.getElementById('cm-asimov-link')) return;
  var monitoring = document.querySelector('#left-nav .left-nav-section');
  var legacy = document.querySelector('.nav-tabs');
  if (!monitoring && !legacy) return;
  var link = document.createElement('a');
  link.id = 'cm-asimov-link'; link.href = '/asimov';
  link.className = monitoring ? 'left-nav-item' : 'nav-tab';
  link.style.textDecoration = 'none'; link.style.color = 'inherit';
  link.title = 'Inspect stored Asimov robot state and command evidence';
  var label = document.createElement('span');
  label.className = 'left-nav-label'; label.textContent = 'Asimov 1';
  if (monitoring) {
    var icon = document.createElement('span');
    icon.className = 'left-nav-icon'; icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '◇'; link.appendChild(icon);
  }
  link.appendChild(label);
  var nodeActivity = monitoring && monitoring.querySelector('[data-tab="node-activity"]');
  if (nodeActivity) monitoring.insertBefore(link, nodeActivity.nextSibling);
  else (monitoring || legacy).appendChild(link);
});
