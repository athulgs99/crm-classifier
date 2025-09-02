// Additional JavaScript functionality

function showHistory() {
    // This would show a modal or navigate to history page
    alert('History feature - to be implemented');
}

function showStats() {
    // This would show detailed statistics
    alert('Statistics feature - to be implemented');
}

// Utility functions
function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}
