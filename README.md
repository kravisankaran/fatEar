# fatEar
Implementation of fatEar application for CS-6083


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
2. Users can see new songs by artists that they are fan of. (new songs: since the user became a fan of)
3. Users can see the total number of new feed item since they last logged-in.