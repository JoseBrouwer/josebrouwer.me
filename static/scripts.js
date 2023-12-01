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

    //Event listener for delete buttons
    var deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            deleteStory(this.dataset.id);
        });
    });

    //Event listener for deleting a user
    document.querySelector('.container.my-5').addEventListener('click', function (event) {
        // Check if the clicked element has the class 'delete-user-button'
        if (event.target.classList.contains('delete-user-button')) {
            var userEmail = event.target.getAttribute('data-email');
            deleteUser(userEmail);
        }
    });

    //Event listener for deleting a news item
    var deleteNewsButtons = document.querySelectorAll('.delete-news-button');
    deleteNewsButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var newsId = this.getAttribute('data-id');
            deleteNewsItem(newsId);
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

// Handle the Delete action
function deleteStory(storyId) {
    fetch('/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ story_id: storyId })
    }).then(response => {
        return response.json();
    }).then(data => {
        if (data.status === 'success') {
            // Remove the story card from the UI or refresh the page
            document.querySelector('.custom-card[data-id="' + storyId + '"]').remove();
            console.log('Deleted story with ID:', storyId);
        } else {
            // Handle error
            console.error('Failed to delete like/dislike for story with ID:', storyId);
        }
    }).catch(error => {
        // Handle network error
        console.error('Network error:', error);
    });
}

function deleteUser(userEmail) {
    if (confirm("Are you sure you want to delete this user and all their data?")) {
        fetch('/delete_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: userEmail })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    //location.reload();  // Reload after a delay
                    showAlert('User successfully deleted. Reloading in 5 seconds...', 'success');  // Show success alert
                    setTimeout(function () {
                        location.reload();  // Reload after a delay
                    }, 3000);  //3 seconds
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error deleting user', 'danger');  // Show error alert
            });
    }
}

function showAlert(message, type) {
    var alertPlaceholder = document.getElementById('alert-placeholder');
    var alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alert.role = 'alert';
    alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    alertPlaceholder.appendChild(alert);

    // Optional: remove the alert after a few seconds
    setTimeout(function () {
        alert.remove();
    }, 5000);
}

function deleteNewsItem(newsId) {
    if (confirm("Are you sure you want to delete this news item?")) {
        fetch('/delete_news_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ news_id: newsId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Remove the news item from the UI or refresh the page
                    showAlert('News Item successfully deleted. Reloading in 3 seconds...', 'success');
                    setTimeout(function () {
                        location.reload();  // Reload after a delay
                    }, 3000);  //3 seconds
                    console.log('Deleted news item with ID:', newsId);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error deleting news item', 'danger');  // Show error alert
            });
    }
}