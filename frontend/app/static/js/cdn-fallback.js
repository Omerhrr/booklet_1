window.addEventListener('load', function() {
    var missing = [];
    if (typeof htmx === 'undefined') missing.push('HTMX');
    if (typeof Alpine === 'undefined') missing.push('Alpine.js');
    if (typeof echarts === 'undefined') missing.push('ECharts');

    if (missing.length > 0) {
        var banner = document.createElement('div');
        banner.className = 'fixed top-0 left-0 right-0 bg-yellow-100 border-b border-yellow-300 text-yellow-800 text-center py-2 text-sm z-[9999]';
        banner.textContent = 'Some features may not work. Could not load: ' + missing.join(', ') + '. Please check your internet connection.';
        document.body.prepend(banner);
        setTimeout(function() { banner.style.display = 'none'; }, 10000);
    }
});
