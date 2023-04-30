// ALBUM RATING
$(document).ready(function () {
    $('button.album-rating-edit').click(function () {
        var ratingCell = $(this).parent().prev(); // Gets the previous div of the buttons div
        var rating = ratingCell.children('.star').length; // Count the number of stars (children with class star of the rating div)

        console.log(rating); // ok
        // Hide the Edit and Delete buttons
        $(this).hide();
        $(this).next('.album-rating-delete').hide();

        // Replace the rating with a dropdown (select) menu
        var selectHTML = `

            <select class="form-select" id="editRating" name="rating" aria-label="Default select example" style="margin-top: 0.5rem">
                  <option ${rating === 0 ? 'selected' : ''} value="0">Rate Album</option>
                  <option ${rating === 1 ? 'selected' : ''} value="1">1</option>
                  <option ${rating === 2 ? 'selected' : ''} value="2">2</option>
                  <option ${rating === 3 ? 'selected' : ''} value="3">3</option>
                  <option ${rating === 4 ? 'selected' : ''} value="4">4</option>
                  <option ${rating === 5 ? 'selected' : ''} value="5">5</option>
            </select>

           <button type="button" class="save-edit btn btn-link text-primary" style="padding: 0">Save</button>
    `;
        ratingCell.html(selectHTML);
    });

    $(document).on('click', '.save-edit', function () {
        var ratingCell = $(this).prev();
        var newRating = ratingCell.val(); // Get the new rating from the select menu
        console.log(newRating); // ok

        var oldRatingDiv = $(this).parent().prevAll('div').first(); // Gets the previous div of the parent div
        var oldRating = oldRatingDiv.children('.star').length; // Count the number of stars (children with class star of the old rating div)

        // Check if the rating has changed
        if (newRating === oldRating) {
            // If the rating is the same, restore the original state
            var starHTML = Array(parseInt(oldRating) + 1).join('<span style="font-size: 1em; color: gold;" class="star">&starf;</span>');
            ratingCell.parent().html(starHTML);
        } else if (newRating === '0') {
            alert('Please select a rating for the album!');

        } else {
            // If the rating has changed, send the AJAX request to update the rating
            var album_id = $(this).closest('.card').find('.hidden-album-id').first().val();
            console.log(album_id);
            var user_id = $('body').data('user-id'); // get the user id;
            console.log("userId ", user_id);

            $.ajax({
                url: "/updateRateAlbum",
                type: "POST",
                data: {
                    'album_id': album_id,
                    'rating': newRating,
                    'user_id': user_id
                },
                success: function () {
                    if (newRating === 0) {
                        alert("Please select a rating for the album!");
                    } else {
                        var starHTML = Array(parseInt(newRating) + 1).join('<span style="font-size: 1em; color: gold;" class="star">&starf;</span>');
                        ratingCell.parent().html(starHTML);
                        alert('Successfully updated!');
                    }
                    // On success, update the display of the rating
                    location.reload();

                },
                error: function () {
                    alert('There was an error updating the rating.');
                    location.reload();
                }
            });


        }
    });
});