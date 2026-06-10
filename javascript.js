// Replace hardcoded array with live data fetch
async function loadLiveMedia() {
    const response = await fetch('https://your-backend-api.com/movies');
    const liveData = await response.json();
    displayCards(liveData);
}
