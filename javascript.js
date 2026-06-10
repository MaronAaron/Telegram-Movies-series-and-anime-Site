// Dynamically fetch the live file updated by your Telegram bot
async function loadLiveMedia() {
    try {
        // Points directly to your Render server's local json endpoint
        const response = await fetch('/movies.json');
        mediaData = await response.json(); 
        displayCards(mediaData);
    } catch (error) {
        console.error("Error loading movie feed:", error);
        document.getElementById('noResults').classList.remove('hidden');
    }
}
