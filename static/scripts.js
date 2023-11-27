document.addEventListener('DOMContentLoaded', function () {
    // Event listener for like buttons
    var likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            handleStoryInteraction(this.dataset.id, true);  // true for like
        });
    });

    // Event listener for dislike buttons
    var dislikeButtons = document.querySelectorAll('.dislike-button');
    dislikeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            handleStoryInteraction(this.dataset.id, false);  // false for dislike
        });
    });
});

// Handle both Like and Dislike actions
function handleStoryInteraction(storyId, isLike) {
    var url = isLike ? '/like_story' : '/dislike_story';

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ story_id: storyId })
    }).then(response => {
        return response.json();
    }).then(data => {
        if (data.status === 'success') {
            // Update the UI to show the new counts
            document.getElementById('like-count-' + storyId).textContent = data.like_count;
            document.getElementById('dislike-count-' + storyId).textContent = data.dislike_count;
            console.log((isLike ? 'Liked' : 'Disliked') + ' story with ID:', storyId);
        } else {
            // Handle error
            console.error('Failed to ' + (isLike ? 'like' : 'dislike') + ' story with ID:', storyId);
        }
    }).catch(error => {
        // Handle network error
        console.error('Network error:', error);
    });
}
