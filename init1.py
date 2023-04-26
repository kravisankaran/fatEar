# Import Flask Library
import hashlib
import time
from datetime import datetime
from functools import wraps

import pymysql.cursors

from flask import render_template, request, session, url_for, redirect


# for uploading photo:
from app import app

# from flask import Flask, flash, request, redirect, render_template

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=8889,
                       user='root',
                       password='root',
                       db='FatEar',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return dec


def checkUserExist(username):
    with conn.cursor() as cursor:
        query = "SELECT * FROM user WHERE username = '%s'" % (username)
        cursor.execute(query)
    result = cursor.fetchall()
    return result


def checkPlaylistExists(username, playlistName):
    with conn.cursor() as cursor:
        query = "SELECT * FROM playlist WHERE username = '%s' % (username) and playlistName = '%s' % (playlistName)"
        cursor.execute(query)
    result = cursor.fetchall()
    return result
# def allowed_image(filename):

#     if not "." in filename:
#         return False

#     ext = filename.rsplit(".", 1)[1]

#     if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
#         return True
#     else:
#         return False


# def allowed_image_filesize(filesize):

#     if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
#         return True
#     else:
#         return False


# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form['password']

    ## need to change varchar limit in order for this to work
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

    lastlogin = time.strftime('%Y-%m-%d')

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM user WHERE username = %s and pwd = %s'
    cursor.execute(query, (username, hashedPassword))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        session['username'] = username
        update = 'UPDATE user SET lastlogin = %s WHERE username = %s'
        cursor.execute(update, (lastlogin, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form['password']

    ## need to change varchar limit in order for this to work
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
    fname = request.form['First Name']
    lname = request.form['Last Name']
    nickname = request.form['nickname']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO user VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashedPassword, fname, lname, time.strftime('%Y-%m-%d %H:%M:%S'), nickname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    # query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    # cursor.execute(query, (user))
    # data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user)


def _checkEmptyParams(x):
   if x == "":
      return 0
   else:
      return 1
   
def getSearchQuery(x, song, fname, lname):
    if x['s'] and x['f'] and x['l'] :
        print ('all 3 are present')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where title like %s and a.fname like %s and a.lname like %s", (song,fname,lname)
    elif x['s'] and x['f'] :
        print('song and artist fname present')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where title like %s and a.fname like %s", (song,fname)

    elif x['s'] and x['l']:
        print ('song and artist lname present')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where title like %s and a.lname like %s", (song,lname)

    elif x['f'] and x['l']:
        print('artist fname and lname present')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where a.fname like %s and a.lname like %s", (fname, lname)

    elif x['f']:
        print ('only firstname')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where a.fname like %s", (fname)

    elif x['l']:
        print ('only lastname')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where a.lname like %s", (lname)

    elif x['s']:
        print ('only song')
        return "select s.title, a.fname, a.lname, s.releaseDate from song s natural join artistPerformsSong asp natural join artist a where title like %s", (song)

    else:
       print('nothing was picked')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        print("in post method")
        song = request.form['song']
        artistFName = request.form['artistFName']
        artistLName = request.form['artistLName']
        # album = request.form['album']
        print(song)
        print(artistFName)
        print(artistLName)
        # print(album)
       
        cursor = conn.cursor()
        # song, artistF, artistLast, album
        searchParams = [song, artistFName, artistLName]
        keys = ["s", "f", "l"]
        
        status = list(map(_checkEmptyParams, searchParams))
        parameterMap = {keys[i]: status[i] for i in range(len(keys))}
        print(parameterMap)
        
        song2 = "%" + song + "%"
        artistFName2 = "%" + artistFName + "%"
        artistLName2 = "%" + artistLName + "%"
        #album = "%" + album + "%"
        query = getSearchQuery(parameterMap, song2, artistFName2, artistLName2)
        print(query)
        cursor.execute(query[0], query[1])
        conn.commit()
        data = cursor.fetchall()
        return render_template('search.html', data=data)

    return render_template('search.html')

@app.route('/playlist', methods=['GET', 'POST'])
def addPlaylist():
    if request.method == "POST":
        print("in post method")
        playlistName = request.form['playlist']
        userName = session['username']
        description = request.form['description']
        creationDate = str(datetime.now())
        song = request.form['song']
        
        print(playlistName)
        print(song)
        print(userName)
        print(datetime)
        ##add alert if user, playlist already exists
        cursor = conn.cursor()
        # song, artistF, artistLast, album
        print("Creating new entry in Playlist Table")
        cursor.execute("INSERT INTO playlist (username, playlistName, description, creationDate) VALUES(%s, %s, %s, %s)", (userName, playlistName, description, creationDate))
        cursor.execute("INSERT INTO songsInPlaylist (username, playlistName, songID) VALUES(%s, %s, %s)", (userName, playlistName, song))
        conn.commit()
        cursor.execute("select * from songsInPlaylist")
        data = cursor.fetchall()
        print(data)
        return render_template('playlist.html', data=data)
       
    return render_template('playlist.html')



# friend

@login_required
def fetchFriendRequests():
    cursor = conn.cursor()
    query = "SELECT user2 FROM friend WHERE user1 = '%s' AND acceptStatus = 'pending'" % session["username"]
    cursor.execute(query)
    return cursor.fetchall()


@login_required
def fetchFriends():
    cursor = conn.cursor()
    user = session["username"]
    query = "SELECT user1 as myFriend FROM friend WHERE user2=%s AND acceptStatus = 'accepted' UNION SELECT user2 as myFriend FROM friend WHERE user1=%s AND acceptStatus = 'accepted'"
    cursor.execute(query, (user, user))
    return cursor.fetchall()


@app.route("/friend", methods=["GET"])
@login_required
def friend():
    request_data = fetchFriendRequests()
    allf_data = fetchFriends()
    return render_template("friend.html", friendRequests=request_data, allFriends=allf_data)


# does not handle duplicated requests yet!
@app.route("/friendUser", methods=["POST"])
@login_required
def friendUser():
    if request.form:
        requestData = request.form
        username_friended = requestData["username_friended"]
        username_requester = session["username"]
        if checkUserExist(username_friended):
            request_data = fetchFriendRequests()
            allf_data = fetchFriends()
            if username_friended == username_requester:
                message = "You cannot friend yourself!"
                return render_template("friend.html", message=message, friendRequests=request_data,
                                       allFriends=allf_data)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT acceptStatus FROM friend WHERE (user1 = %s AND user2 = %s) OR (user2 = %s AND user1 = %s)"
                cursor1.execute(statusQuery, (username_friended, username_requester, username_friended, username_requester))
                friendStatus = cursor1.fetchall()
                cursor1.close()
                
                # check if user 1 and 2 are already friends, or if there's already a pending request
                if len(friendStatus) > 0:
                    if friendStatus[0].get("acceptStatus") == "accepted":
                        message = "You are already friends with %s." % (username_friended)
                    elif friendStatus[0].get("acceptStatus") == "pending":
                        message = "There is already a pending friend request between you and %s." % (username_friended)
                else:
                    acceptStatus = 'pending'
                    cursor = conn.cursor()
                    query = "INSERT INTO friend VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, (username_friended, username_requester, acceptStatus, username_requester,
                                        time.strftime('%Y-%m-%d %H:%M:%S'), time.strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    cursor.close()
                    message = "Request sent to %s." % (username_friended)

            except:
                message = "An error has occurred. Please try again."
                return render_template("friend.html", message=message)
        else:
            message = "%s does not exist." % (username_friended)
    return render_template("friend.html", friendRequests=request_data, allFriends=allf_data, message=message)


@login_required
@app.route("/accept/<username>", methods=["POST"])
def accept(username):
    username_friended = session["username"]
    username_requester = username
    cursor = conn.cursor()
    query = "UPDATE friend SET acceptStatus = 'accepted', updatedAt = %s WHERE user1 = %s AND user2 = %s"
    cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), username_friended, username_requester))
    conn.commit()
    cursor.close()

    request_data = fetchFriendRequests()
    allf_data = fetchFriends()
    return render_template("friend.html", friendRequests=request_data, allFriends=allf_data)


@login_required
@app.route("/decline/<username>", methods=["POST"])
def decline(username):
    username_friended = session["username"]
    username_requester = username
    cursor = conn.cursor()
    query = "DELETE FROM friend WHERE user1 = %s AND user2 = %s"
    cursor.execute(query, (username_friended, username_requester))
    conn.commit()
    cursor.close()

    request_data = fetchFriendRequests()
    allf_data = fetchFriends()
    return render_template("friend.html", friendRequests=request_data, allFriends=allf_data)


# does not check if users are actually friends 
@app.route("/unfriend", methods=["POST"])
def unfriend():
    request_data = fetchFriendRequests()
    allf_data = fetchFriends()

    if request.form:
        requestData = request.form
        to_unfriend = requestData["to_unfriend"]
        currentUser = session["username"]

        if checkUserExist(to_unfriend):
            if to_unfriend == currentUser:
                message = "You cannot unfriend yourself!"
                return render_template("friend.html", unfriend_message=message, username=session["username"],
                                       friendRequests=request_data, allFriends=allf_data)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT acceptStatus FROM friend WHERE (user1 = %s AND user2 = %s) OR (user2 = %s AND user1 = %s)"
                cursor1.execute(statusQuery, (currentUser, to_unfriend, currentUser, to_unfriend))
                friendStatus = cursor1.fetchall()
                cursor1.close()
                
                # check if user 1 and 2 are currently friends
                if len(friendStatus) > 0 and friendStatus[0].get("acceptStatus") == "accepted":
                    cursor1 = conn.cursor()
                    query = "DELETE FROM friend WHERE (user1=%s AND user2=%s) OR (user2=%s AND user1=%s) AND acceptStatus = 'accepted'"
                    cursor1.execute(query, (to_unfriend, currentUser, to_unfriend, currentUser))
                    conn.commit()
                    cursor1.close()

                    # doesn't instantly update, have to refresh
                    message = "Successfully removed friend, refresh to see current friend list" 
                else: 
                    message = "You and %s are not friends" % (to_unfriend)
            except:
                message = "Failed to unfriend " + to_unfriend
        else:
            message = "user %s does not exist" % (to_unfriend)
            return render_template("friend.html", unfriend_message=message, username=session["username"],
                                   friendRequests=request_data, allFriends=allf_data)
    return render_template("friend.html", unfriend_message=message, username=session["username"],
                           friendRequests=request_data, allFriends=allf_data)


@login_required
@app.route("/post", methods=["GET"])
def fetchList():
    # Fetch all data from song, album, artist tables
    user_id = session['username']
    cursor = conn.cursor()
    query = " SELECT s.songID,s.title, sIA.albumID, a.artistID, a.fname, a.lname FROM song s JOIN artistPerformsSong aPS on s.songID = aPS.songID JOIN artist a on a.artistID = aPS.artistID JOIN songInAlbum sIA on s.songID = sIA.songID;"
    cursor.execute(query)
    list = cursor.fetchall()
    cursor.close()

    # Error - Review
    error_duplicate_song_review = request.args.get('error_duplicate_song_review')
    error_empty_song_review = request.args.get('error_empty_song_review')
    error_duplicate_album_review = request.args.get('error_duplicate_album_review')
    error_empty_album_review = request.args.get('error_empty_album_review')

    # Error - Rating
    error_duplicate_song_rating = request.args.get('error_duplicate_song_rating')
    error_empty_song_rating = request.args.get('error_empty_song_rating')
    error_duplicate_album_rating = request.args.get('error_duplicate_album_rating')
    error_empty_album_rating = request.args.get('error_empty_album_rating')

    # Error -Fan
    error_fan = request.args.get('error_fan')
    error_artist_id = request.args.get('error_artist_id')

    # Fetch all data from review, rate, fan tables
    review_album_data, review_song_data, rating_album_data, rating_song_data, fan_data = fetchPost()

    return render_template("post.html",
                           list=list,
                           user_id=user_id,
                           error_duplicate_song_review=error_duplicate_song_review,
                           error_empty_song_review=error_empty_song_review,
                           error_duplicate_album_review=error_duplicate_album_review,
                           error_empty_album_review=error_empty_album_review,
                           error_duplicate_song_rating=error_duplicate_song_rating,
                           error_empty_song_rating=error_empty_song_rating,
                           error_duplicate_album_rating=error_duplicate_album_rating,
                           error_empty_album_rating=error_empty_album_rating,
                           error_fan=error_fan,
                           error_artist_id=error_artist_id,
                           review_album_data=review_album_data,
                           review_song_data=review_song_data,
                           rating_album_data=rating_album_data,
                           rating_song_data=rating_song_data,
                           fan_data=fan_data
                           )


def fetchPost():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviewAlbum")
    review_album_data = cursor.fetchall()
    cursor.execute("SELECT * FROM reviewSong")
    review_song_data = cursor.fetchall()
    cursor.execute("SELECT * FROM rateAlbum")
    rating_album_data = cursor.fetchall()
    cursor.execute("SELECT * FROM rateSong")
    rating_song_data = cursor.fetchall()
    cursor.execute("SELECT * FROM userFanOfArtist")
    fan_data = cursor.fetchall()

    cursor.close()
    return review_album_data, review_song_data, rating_album_data, rating_song_data, fan_data


@login_required
@app.route("/reviewAlbum", methods=["POST"])
def review_album():
    cursor = conn.cursor()
    album_id = request.form['album_id']
    review_text = request.form['review_text'].strip()
    user_id = session['username']
    review_date = datetime.now()

    # Check if the input field is empty
    if not review_text:
        return redirect(url_for('fetchList', error_empty_album_review=album_id))

    # Check if the user already posted a review for the album
    check_query = "SELECT * FROM reviewAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(check_query, (album_id, user_id))
    existing_review = cursor.fetchone()
    if existing_review:
        cursor.close()
        return redirect(url_for('fetchList', error_duplicate_album_review=album_id))

    # Save review in the database
    insert_query = "INSERT INTO reviewAlbum (albumID, username, reviewText, reviewDate) VALUES (%s, %s, %s,%s);"
    cursor.execute(insert_query, (album_id, user_id, review_text, review_date))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))  # Redirect back to the list page


@login_required
@app.route("/reviewSong", methods=["POST"])
def review_song():
    cursor = conn.cursor()
    song_id = request.form['song_id']
    review_text = request.form['review_text'].strip()
    user_id = session['username']
    review_date = datetime.now()

    # Check if the input field is empty
    if not review_text:
        return redirect(url_for('fetchList', error_empty_song_review=song_id))

    # Check if the user already posted a review for the song
    check_query = "SELECT * FROM reviewSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_review = cursor.fetchone()
    if existing_review:
        cursor.close()
        return redirect(url_for('fetchList', error_duplicate_song_review=song_id))

    # Save review in the database
    insert_query = "INSERT INTO reviewSong (songID, username, reviewText, reviewDate) VALUES (%s, %s, %s,%s);"
    cursor.execute(insert_query, (song_id, user_id, review_text, review_date))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))


@login_required
@app.route("/rateAlbum", methods=["POST"])
def rate_album():
    cursor = conn.cursor()
    album_id = request.form['album_id']
    rating = int(request.form['rating'])
    user_id = session['username']
    # rate_date = datetime.now()

    # Check if the input field is empty
    if rating == 0:
        return redirect(url_for('fetchList', error_empty_album_rating=album_id))

    # Check if the user already posted a rating for the album
    check_query = "SELECT * FROM rateAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(check_query, (album_id, user_id))
    existing_review = cursor.fetchone()
    if existing_review:
        cursor.close()
        return redirect(url_for('fetchList', error_duplicate_album_rating=album_id))

    # Save rating in the database
    # save_query = "INSERT INTO rateAlbum (albumID, username, stars, ratingDate) VALUES (%s, %s, %s, %s);"
    # cursor.execute(save_query, (album_id, user_id, rating, rate_date))
    save_query = "INSERT INTO rateAlbum (albumID, username, stars) VALUES (%s, %s, %s);"
    cursor.execute(save_query, (album_id, user_id, rating))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))


@login_required
@app.route("/rateSong", methods=["POST"])
def rate_song():
    cursor = conn.cursor()
    song_id = request.form['song_id']
    rating = int(request.form['rating'])
    user_id = session['username']
    rate_date = datetime.now()

    # Check if the input field is empty
    if rating == 0:
        return redirect(url_for('fetchList', error_empty_song_rating=song_id))

    # Check if the user already posted a rating for the song
    check_query = "SELECT * FROM rateSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_review = cursor.fetchone()
    if existing_review:
        cursor.close()
        return redirect(url_for('fetchList', error_duplicate_song_rating=song_id))

    # Save rating in the database
    save_query = "INSERT INTO rateSong (songID, username, stars, ratingDate) VALUES (%s, %s, %s, %s);"
    cursor.execute(save_query, (song_id, user_id, rating, rate_date))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))


@login_required
@app.route("/fanOfArtist", methods=["POST"])
def fan_of_artist():
    cursor = conn.cursor()
    artist_id = request.form['artist_id']
    is_fan = request.form.get('is_fan', 'off') == 'on'
    user_id = session['username']
    error_fan = ""

    # Check if user is already a fan
    check_query = "SELECT * FROM userFanOfArtist WHERE username = %s AND artistID = %s;"
    cursor.execute(check_query, (user_id, artist_id))
    result = cursor.fetchone()

    if is_fan:
        # Insert fan relationship in the database only if not already a fan
        if not result:
            save_query = "INSERT INTO userFanOfArtist (username, artistID) VALUES (%s, %s);"
            cursor.execute(save_query, (user_id, artist_id))
        else:
            error_fan = "You are already a fan of this artist."
    else:
        # Remove fan relationship from the database only if user is a fan
        if result:
            delete_query = "DELETE FROM userFanOfArtist WHERE username = %s AND artistID = %s;"
            cursor.execute(delete_query, (user_id, artist_id))
        else:
            error_fan = "You are not a fan of this artist."

    conn.commit()
    cursor.close()

    if error_fan:
        return redirect(url_for('fetchList', error_fan=error_fan, error_artist_id=artist_id))
    else:
        return redirect(url_for('fetchList'))


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
