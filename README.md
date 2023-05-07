# fatEar

Implementation of fatEar application for CS-6083

## Authors
- Claudia Shao
- Hansaem Park
- Kumud Ravisankaran 

## Built With

- Framework: Flask
- Database: MySQL
- Hosting: Local server
- Libraries: Bootstrap, jQuery
- Project management tool: Git

## Getting Started

- PyMySql, Flask should be installed.
- The MySQL connection variable is in init1.py file.

```commandline
flask --app init1 run
```

## Search page (/search)

### Features:

1. Users can search the database
    - by song,
      and/or
    - by artist name
        - (by first name or last name or both),
          and/or
    - by album name
      and/or
    - by a rating threshold (rating of a song)
      and/or
    - by genre
2. The more parameters we specify - the more specific the search will be.
3. Search is based on a fuzzy text match for string fields and a rating threshold for stars
4. If a song has been rated more than once - an average rating will be returned in the results
5. Search results will contain rating information only if ratings are present for songs matching the parameters

### Error Handling:

1. If no search parameters are specified
2. If nothing matches the search parameters

## Show Playlist page (/showplaylist)

### Features:

1. Users can see all the playlists they have created since the beginning

## Add Playlist page (/playlist)

### Features:

1. Users can create a new playlist using this page
2. They can add a playlist name, choose songs from the database and add a description for their playlist
3. Songs they add for a new playlist shall be displayed in the bottom of the screen once its inserted

### Error Handling:

1. User can make only one playlist with the same name
2. User must choose at least one song
3. User must have a playlist name

## Post page (/post)

### Features:

1. Users can post review or rating on song/album.
2. Users can see the number of reviews on song/album
3. Users can see the average ratings on song/album.
4. Users can become or no longer become a fan of artists.
5. Users can see the number of fans of the artists.
6. User can edit/delete only their review or rating on song/album (colored in blue).

### Error Handling:

1. When a user post review or rating on song/album already existed, error message is displayed.
2. When a user try to post with blank field, error message is displayed.
3. When a user edit rating on song/album with default value (Rate Song), error message is popped up.

## Feed page (/feed)

### Features:

1. Users can see reviews or ratings on song/album posted by friends, followers or friend & follower since they last
   logged-in.
2. Users can see new songs by artists that they are fan of. (new songs: since the user last logged-in)
3. Users can see the total number of new feed item since they last logged-in.

### Error Handling:

1. Users can see indication if they have no followers nor friends.
2. Users can see indication if they have followers or friends but they haven't updated any posts(reviews/ratings on
   songs/albums).
3. Users can see indication if they are not fan of any artists.
4. Users can see indication if they are a fan of some artists but they haven't released any new songs yet since the user
   became a fan of them.

## Register/Login

### Features:

1. Users can create an account by filling in Username, password(hashed before inserting into the database for more security), first/last name, and nickname
2. Once the account has been created, the user will be redirected to the login page
3. User can input their username and password to log into FatEar
4. lastlogin time is perserved as a milestone during a logged-in session and updated when user logs out

### Error Handling:

1. Multiple users cannot register with the same username, error message will be displayed.
2. Users cannot leave any field blank on the registration page, error message will be displayed.
3. Users cannot leave any field blank on the login page, error message will be displayed.

## Friend

### Features:

1. Users can send friend request to another user
2. Users can see a list of friends they currently have
3. Users can unfriend another user
4. Users can see friend requests sent to them, and decide whether to accept or decline

### Error Handling:

1. Users cannot friend/unfriend themselves, error message will be displayed.
2. Users cannot friend another user that is already their friend, or send friend requests twice, error message will be displayed.
3. Users cannot remove a user who is not their friend, error message will be displayed.
4. Users cannot friend a username that doesn't exist, error message will be displayed.

## Follow

### Features:

1. Users can follow another user
2. Users can see a list of followers they currently have, and a list of users they are following
3. Users can unfollow another user, or remove a follower

### Error Handling:

1. Users cannot follow/unfollow themselves, error message will be displayed.
2. Users cannot follow another user they are already following, error message will be displayed.
3. Users cannot remove a follower who is not their follower, error message will be displayed.
4. Users cannot unfollow a user who they are not following, error message will be displayed.
5. Users cannot follow/unfollow a username that doesn't exist, error message will be displayed.



