document.addEventListener('DOMContentLoaded', function () {
    // Event listener for like buttons
    var likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            likeStory(this.dataset.id);
        });
    });

    // Event listener for dislike buttons
    var dislikeButtons = document.querySelectorAll('.dislike-button');
    dislikeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            dislikeStory(this.dataset.id);
        });
    });
});

// Handle the Like action
function likeStory(storyId) {
    fetch('/like_story', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
            // CSRF token is not included for simplicity
        },
        body: JSON.stringify({ story_id: storyId })
    }).then(response => {
        return response.json();
    }).then(data => {
        if (data.status === 'success') {
            // Update the UI to show the like has been successful
            document.getElementById('like-count-' + storyId).textContent = data.like_count;
            console.log('Liked story with ID:', storyId);
        } else {
            // Handle error
            console.error('Failed to like story with ID:', storyId);
        }
    }).catch(error => {
        // Handle network error
        console.error('Network error:', error);
    });
}

// Handle the Dislike action
function dislikeStory(storyId) {
    fetch('/dislike_story', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
            // CSRF token is not included for simplicity
        },
        body: JSON.stringify({ story_id: storyId })
    }).then(response => {
        return response.json();
    }).then(data => {
        if (data.status === 'success') {
            // Update the UI to show the dislike has been successful
            document.getElementById('dislike-count-' + storyId).textContent = data.dislike_count;
            console.log('Disliked story with ID:', storyId);
        } else {
            // Handle error
            console.error('Failed to dislike story with ID:', storyId);
        }
    }).catch(error => {
        // Handle network error
        console.error('Network error:', error);
    });
}
