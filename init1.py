# Import Flask Library
import hashlib
import time
from datetime import datetime
from functools import wraps

import pymysql.cursors
from flask import Flask, render_template, request, session, url_for, redirect, jsonify

###Initialize the app from Flask
app = Flask(__name__)
app.secret_key = "secret key"

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
        query = "SELECT * FROM playlist WHERE username = '%s' and playlistName = '%s'" % (username, playlistName)
        cursor.execute(query)
    result = cursor.fetchall()
    print ("result : %s", result)
    return result

def getSongIDFromSong(song):
    with conn.cursor() as cursor:
        query = "SELECT songID FROM song WHERE title like '%s'" % (song)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getAlbumIDFromAlbum(album):
    with conn.cursor() as cursor:
        query = "SELECT albumID FROM album WHERE albumName like '%s'" % (album)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getArtistIDFromArtist(fname, lname):    
    with conn.cursor() as cursor:
        if fname == None and lname != None:
            query = "SELECT artistID FROM artist WHERE lname like '%s'" % (lname)
        elif fname != None and lname == None:
            query = "SELECT artistID FROM artist WHERE fname like '%s'" % (fname)
        else:
            query = "SELECT artistID FROM artist WHERE fname like '%s' and lname like '%s'" % (fname, lname)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getSongIDFromAlbum(albumID):
    with conn.cursor() as cursor:
        query = "SELECT songID FROM songInAlbum WHERE albumID = '%s'" % (albumID)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getSongIDFromArtist(artistID):
    with conn.cursor() as cursor:
        query = "SELECT songID FROM artistPerformsSong WHERE artistID = '%s'" % (artistID)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getSongIDFromGenre(genre):
    with conn.cursor() as cursor:
        query = "SELECT songID FROM songGenre WHERE genre like '%s'" % (genre)
        cursor.execute(query)
    result = cursor.fetchall()
    return result

def getSongIDFromRateSong(songID):
    with conn.cursor() as cursor:
        print(songID)
        query = "SELECT songID FROM rateSong WHERE songID in ({})".format(str(songID)[1:-1])
        cursor.execute(query)
    result = cursor.fetchall()
    #print (result)
    return result

def getSongs():
    with conn.cursor() as cursor:
        query = "SELECT songID FROM song"
        cursor.execute(query)
    result = cursor.fetchall()
    print ("songID", result)
    return result


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
        return render_template('login.html')


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


def getSearchQuery(x, song, fname, lname, album, ratingVal, genre):
    if x['s'] and x['a'] and x['f'] and x['l'] and x['r'] and x['g']:
        print('song, album, fname, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and rat.stars = %s and gen.genre like %s", (
            song, fname, lname, album, ratingVal, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['l'] and x['g']:
        print('song, album, fname, lname, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, lname, album, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['r'] and x['g']:
        print('song, album, fname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            song, fname, ratingVal, album, genre)
    
    elif x['s'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('song, album, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            song, lname, ratingVal, album, genre)
    
    elif x['f'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('fname, album, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            fname, lname, ratingVal, album, genre)
   
    elif x['f'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('fname, song, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre , gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s and rat.stars = %s and title like %s and gen.genre like %s", (
            fname, lname, ratingVal, song, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['l'] and x['r']:
        print('song, album, fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and rat.stars = %s", (
            song, fname, lname, album, ratingVal)

    elif x['s'] and x['f'] and x['l'] and x['a']:
        print('song, fname, lastname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", ( song, fname, lname, album)
 
    elif x['s'] and x['f'] and x['l'] and x['g']:
        print('song, fname, lastname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and get.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", ( song, fname, lname, genre)
 
    elif x['s'] and x['f'] and x['l'] and x['r']:
        print('song, fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and rat.stars = %s", (
            song, fname, lname, ratingVal)

    elif x['s'] and x['f'] and x['a'] and x['r']:
        print('song, fname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and alb.albumName like %s and rat.stars = %s", (
            song, fname, album, ratingVal)

    elif x['s'] and x['f'] and x['a'] and x['g']:
        print('song, fname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, album, genre)

    elif x['s'] and x['f'] and x['r'] and x['g']:
        print('song, fname, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and rat.stars = %s and  gen.genre like %s", (song, fname, ratingVal, genre)

    elif x['s'] and x['l'] and x['a'] and x['r']:
        print('song, lname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s and rat.stars = %s", (
            song, lname, album, ratingVal)

    elif x['s'] and x['l'] and x['a'] and x['g']:
        print('song, lname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, album, genre)

    elif x['s'] and x['l'] and x['r'] and x['g']:
        print('song, lname, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and rat.stars = %s and  gen.genre like %s", (
            song, lname, ratingVal, genre)


    elif x['f'] and x['l'] and x['a'] and x['r']:
        print('fname, lname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and alb.albumName like %s and rat.stars = %s", (
            fname, lname, album, ratingVal)

    elif x['f'] and x['l'] and x['a'] and x['g']:
        print('fname, lname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, album, genre)

    elif x['f'] and x['l'] and x['r'] and x['g']:
        print('fname, lname,  rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and rat.stars = %s and gen.genre like %s ", (
            fname, lname, ratingVal, genre)


    elif x['f'] and x['a'] and x['r'] and x['g']:
        print('fname, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            fname, album, ratingVal, genre)

    elif x['l'] and x['a'] and x['r'] and x['g']:
        print('fname, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.lname like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            lname, album, ratingVal, genre)

    elif x['s'] and x['a'] and x['r'] and x['g']:
        print('song, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            song, album, ratingVal, genre)
 

    elif x['s'] and x['f'] and x['a']:
        print('song, fname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, album)

    elif x['s'] and x['f'] and x['g']:
        print('song, fname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, genre)
   
    elif x['s'] and x['f'] and x['r']:
        print('song, fname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and rat.stars = %s", (
            song, fname, ratingVal)
    
    elif x['s'] and x['f'] and x['l']:
        print('song, artist fname, artist lname are present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.fname like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, lname)

    elif x['s'] and x['l'] and x['a']:
        print('song, lname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, album)

    elif x['s'] and x['l'] and x['r']:
        print('song, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and rat.stars = %s", (
            song, lname, ratingVal)
    
    elif x['s'] and x['l'] and x['g']:
        print('song, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, genre)

    elif x['f'] and x['l'] and x['a']:
        print('fname, lname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, album)
    
    elif x['f'] and x['l'] and x['g']:
        print('fname, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, genre)

    elif x['f'] and x['l'] and x['r']:
        print('fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and rat.stars = %s", (
            fname, lname, ratingVal)

    elif x['a'] and x['l'] and x['r']:
        print('album, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and  a.lname like %s and rat.stars = %s", (
            album, lname, ratingVal)

    elif x['a'] and x['l'] and x['g']:
        print('album, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where alb.albumName like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, lname, genre)
    
    elif x['a'] and x['f'] and x['r']:
        print('album, fname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and a.fname like %s  and rat.stars = %s", (
            album, fname, ratingVal)
    
    elif x['a'] and x['f'] and x['g']:
        print('album, fname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and a.fname like %s  and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, fname, genre)

    elif x['a'] and x['s'] and x['r']:
        print('album, song, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where alb.albumName like %s and title like %s and rat.stars = %s", (
            album, song, ratingVal)

    elif x['a'] and x['s'] and x['g']:
        print('album, song, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where  alb.albumName like %s and title like %s  and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, song, genre)
   
    elif x['a'] and x['g'] and x['r']:
        print('album, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where alb.albumName like %s and gen.genre like %s and rat.stars = %s", (
            album, genre, ratingVal)

    elif x['l'] and x['g'] and x['r']:
        print('lname, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where a.lname like %s and gen.genre like %s and rat.stars = %s", (
            lname, genre, ratingVal)
    
    elif x['f'] and x['g'] and x['r']:
        print('fname, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where a.fname like %s and gen.genre like %s and rat.stars = %s", (
            fname, genre, ratingVal)
   
    elif x['s'] and x['g'] and x['r']:
        print('song, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where title like %s and gen.genre like %s and rat.stars = %s", (
            song, genre, ratingVal)

    elif x['s'] and x['f']:
        print('song and artist fname present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.fname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname)

    elif x['s'] and x['l']:
        print('song and artist lname present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname)

    elif x['f'] and x['l']:
        print('artist fname and lname present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname)

    elif x['f'] and x['a']:
        print('artist fname and album name present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, album)

    elif x['l'] and x['a']:
        print('artist fname and album name present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            lname, album)

    elif x['s'] and x['a']:
        print('song and album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, album)

    elif x['s'] and x['r']:
        print('song and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and rat.stars like %s", (
            song, ratingVal)

    elif x['a'] and x['r']:
        print('album and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where alb.albumName like %s and rat.stars like %s", (
            album, ratingVal)

    elif x['f'] and x['r']:
        print('fname and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and rat.stars like %s", (
            fname, ratingVal)

    elif x['l'] and x['r']:
        print('lname and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s and rat.stars like %s", (
            lname, ratingVal)
    
    elif x['g'] and x['r']:
        print('genre and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where gen.genre like %s and rat.stars like %s", (
            genre, ratingVal)
    
    elif x['s'] and x['g']:
        print('song and genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, genre)

    elif x['f'] and x['g']:
        print('fname and genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, genre)
    
    elif x['l'] and x['g']:
        print('lname and genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            lname, genre)
    
    elif x['a'] and x['g']:
        print('album and genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, genre)
    
    elif x['f']:
        print('only firstname')
        return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            fname)

    elif x['l']:
        print('only lastname')
        return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            lname)

    elif x['s']:
        print('only song')
        return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a   where title like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            song)
    elif x['a']:
        print('only album')
        return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            album)

    elif x['r']:
        print('only rating')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a where rat.stars like %s", (
            ratingVal)

    elif x['g']:
        print('only genre')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a where gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            genre)
    else:
        print('nothing was picked')

def getUpdatedSearchQuery(x, song, fname, lname, album, ratingVal, genre):
    
    if x['s'] and x['a'] and x['f'] and x['l'] and x['r'] and x['g']:
        print('song, album, fname, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and rat.stars = %s and gen.genre like %s", (
            song, fname, lname, album, ratingVal, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['l'] and x['g']:
        print('song, album, fname, lname, genre picked')
        print('checking rating: ', checkIfRatingExistsWithSong(song))
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, lname, album, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['r'] and x['g']:
        print('song, album, fname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            song, fname, ratingVal, album, genre)
    
    elif x['s'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('song, album, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            song, lname, ratingVal, album, genre)
    
    elif x['f'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('fname, album, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s and rat.stars = %s and alb.albumName like %s and gen.genre like %s", (
            fname, lname, ratingVal, album, genre)
   
    elif x['f'] and x['a'] and x['l'] and x['r'] and x['g']:
        print('fname, song, lname, rating, genre picked')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s and rat.stars = %s and title like %s and gen.genre like %s", (
            fname, lname, ratingVal, song, genre)
    
    elif x['s'] and x['a'] and x['f'] and x['l'] and x['r']:
        print('song, album, fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s and rat.stars = %s", (
            song, fname, lname, album, ratingVal)

    elif x['s'] and x['f'] and x['l'] and x['a']:
        print('song, fname, lastname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", ( song, fname, lname, album)
 
    elif x['s'] and x['f'] and x['l'] and x['g']:
        print('song, fname, lastname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and get.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", ( song, fname, lname, genre)
 
    elif x['s'] and x['f'] and x['l'] and x['r']:
        print('song, fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and a.lname like %s and rat.stars = %s", (
            song, fname, lname, ratingVal)

    elif x['s'] and x['f'] and x['a'] and x['r']:
        print('song, fname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and alb.albumName like %s and rat.stars = %s", (
            song, fname, album, ratingVal)

    elif x['s'] and x['f'] and x['a'] and x['g']:
        print('song, fname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, album, genre)

    elif x['s'] and x['f'] and x['r'] and x['g']:
        print('song, fname, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s  and rat.stars = %s and  gen.genre like %s", (song, fname, ratingVal, genre)

    elif x['s'] and x['l'] and x['a'] and x['r']:
        print('song, lname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s and rat.stars = %s", (
            song, lname, album, ratingVal)

    elif x['s'] and x['l'] and x['a'] and x['g']:
        print('song, lname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, album, genre)

    elif x['s'] and x['l'] and x['r'] and x['g']:
        print('song, lname, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and rat.stars = %s and  gen.genre like %s", (
            song, lname, ratingVal, genre)


    elif x['f'] and x['l'] and x['a'] and x['r']:
        print('fname, lname,  album, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and alb.albumName like %s and rat.stars = %s", (
            fname, lname, album, ratingVal)

    elif x['f'] and x['l'] and x['a'] and x['g']:
        print('fname, lname,  album, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, album, genre)

    elif x['f'] and x['l'] and x['r'] and x['g']:
        print('fname, lname,  rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s  and rat.stars = %s and gen.genre like %s ", (
            fname, lname, ratingVal, genre)


    elif x['f'] and x['a'] and x['r'] and x['g']:
        print('fname, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            fname, album, ratingVal, genre)

    elif x['l'] and x['a'] and x['r'] and x['g']:
        print('fname, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.lname like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            lname, album, ratingVal, genre)

    elif x['s'] and x['a'] and x['r'] and x['g']:
        print('song, album, rating, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and alb.albumName like %s  and rat.stars = %s and gen.genre like %s ", (
            song, album, ratingVal, genre)
 

    elif x['s'] and x['f'] and x['a']:
        print('song, fname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, album)

    elif x['s'] and x['f'] and x['g']:
        print('song, fname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, genre)
   
    elif x['s'] and x['f'] and x['r']:
        print('song, fname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.fname like %s and rat.stars = %s", (
            song, fname, ratingVal)
    
    elif x['s'] and x['f'] and x['l']:
        print('song, artist fname, artist lname are present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.fname like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname, lname)

    elif x['s'] and x['l'] and x['a']:
        print('song, lname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s  and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, album)

    elif x['s'] and x['l'] and x['r']:
        print('song, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and rat.stars = %s", (
            song, lname, ratingVal)
    
    elif x['s'] and x['l'] and x['g']:
        print('song, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname, genre)

    elif x['f'] and x['l'] and x['a']:
        print('fname, lname, album present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, album)
    
    elif x['f'] and x['l'] and x['g']:
        print('fname, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname, genre)

    elif x['f'] and x['l'] and x['r']:
        print('fname, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where a.fname like %s and a.lname like %s and rat.stars = %s", (
            fname, lname, ratingVal)

    elif x['a'] and x['l'] and x['r']:
        print('album, lname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and  a.lname like %s and rat.stars = %s", (
            album, lname, ratingVal)

    elif x['a'] and x['l'] and x['g']:
        print('album, lname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where alb.albumName like %s and a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, lname, genre)
    
    elif x['a'] and x['f'] and x['r']:
        print('album, fname, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and a.fname like %s  and rat.stars = %s", (
            album, fname, ratingVal)
    
    elif x['a'] and x['f'] and x['g']:
        print('album, fname, genre present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a  where alb.albumName like %s and a.fname like %s  and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, fname, genre)

    elif x['a'] and x['s'] and x['r']:
        print('album, song, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where alb.albumName like %s and title like %s and rat.stars = %s", (
            album, song, ratingVal)

    elif x['a'] and x['s'] and x['g']:
        print('album, song, genre present')
        if (checkIfRatingExistsWithAlbum(album) and checkIfRatingExistsWithSong(song) and checkIfRatingExistsWithGenre(genre)):
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where  alb.albumName like %s and title like %s  and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, song, genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen  natural join artist a  where  alb.albumName like %s and title like %s  and gen.genre like %s", (
            album, song, genre)
   
    elif x['a'] and x['g'] and x['r']:
        print('album, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where alb.albumName like %s and gen.genre like %s and rat.stars = %s", (
            album, genre, ratingVal)

    elif x['l'] and x['g'] and x['r']:
        print('lname, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where a.lname like %s and gen.genre like %s and rat.stars = %s", (
            lname, genre, ratingVal)
    
    elif x['f'] and x['g'] and x['r']:
        print('fname, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where a.fname like %s and gen.genre like %s and rat.stars = %s", (
            fname, genre, ratingVal)
   
    elif x['s'] and x['g'] and x['r']:
        print('song, genre, rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen  natural join artist a  where title like %s and gen.genre like %s and rat.stars = %s", (
            song, genre, ratingVal)

    elif x['s'] and x['f']:
        print('song and artist fname present')
        if (checkIfRatingExistsWithSong(song) and checkIfRatingExistsWithArtist(fname, None)):
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.fname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, fname)
        else:
             return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a where title like %s and a.fname like %s", (
            song, fname)

    elif x['s'] and x['l']:
        print('song and artist lname present')
        if (checkIfRatingExistsWithSong(song) and checkIfRatingExistsWithArtist(None, lname)):
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, lname)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a  where title like %s and a.lname like %s", (
            song, lname)

    elif x['f'] and x['l']:
        print('artist fname and lname present')
        if (checkIfRatingExistsWithArtist(fname, lname)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, lname)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a where a.fname like %s and a.lname like %s", (
            fname, lname)

    elif x['f'] and x['a']:
        print('artist fname and album name present')
        if (checkIfRatingExistsWithArtist(fname, None) and checkIfRatingExistsWithAlbum(album)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, album)
        else:
             return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a where a.fname like %s and alb.albumName like %s ", (
            fname, album)

    elif x['l'] and x['a']:
        print('artist lname and album name present')
        if (checkIfRatingExistsWithArtist(None, lname) and checkIfRatingExistsWithAlbum(album)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            lname, album)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a where a.lname like %s and alb.albumName like %s", (
            lname, album)

    elif x['s'] and x['a']:
        print('song and album present')
        if (checkIfRatingExistsWithSong(song) and checkIfRatingExistsWithAlbum(album)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, album)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a where title like %s and alb.albumName like %s", (
            song, album)

    elif x['s'] and x['r']:
        print('song and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where title like %s and rat.stars like %s", (
            song, ratingVal)

    elif x['a'] and x['r']:
        print('album and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where alb.albumName like %s and rat.stars like %s", (
            album, ratingVal)

    elif x['f'] and x['r']:
        print('fname and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and rat.stars like %s", (
            fname, ratingVal)

    elif x['l'] and x['r']:
        print('lname and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.lname like %s and rat.stars like %s", (
            lname, ratingVal)
    
    elif x['g'] and x['r']:
        print('genre and rating present')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where gen.genre like %s and rat.stars like %s", (
            genre, ratingVal)
    
    elif x['s'] and x['g']:
        print('song and genre present')
        if (checkIfRatingExistsWithSong(song) and checkIfRatingExistsWithGenre(genre)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where title like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            song, genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a where title like %s and gen.genre like %s", (
            song, genre)

    elif x['f'] and x['g']:
        print('fname and genre present')
        if (checkIfRatingExistsWithArtist(fname, None) and checkIfRatingExistsWithGenre(genre)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.fname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            fname, genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a  where a.fname like %s and gen.genre like %s", (
            fname, genre)
    
    elif x['l'] and x['g']:
        print('lname and genre present')
        if (checkIfRatingExistsWithArtist(None, lname) and checkIfRatingExistsWithGenre(genre)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join artist a where a.lname like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            lname, genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a  where a.lname like %s and gen.genre like %s", (
            lname, genre)
    
    elif x['a'] and x['g']:
        print('album and genre present')
        if (checkIfRatingExistsWithAlbum(album) and checkIfRatingExistsWithGenre(genre)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where alb.albumName like %s and gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            album, genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a  where alb.albumName like %s and gen.genre like %s", (
            album, genre) 
    
    elif x['f']:
        print('only firstname')
        print('checking rating: ', checkIfRatingExistsWithArtist(fname, None))
        if (checkIfRatingExistsWithArtist(fname, None)) :
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.fname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            fname)
        else:
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a  where a.fname like %s ", (
            fname)

    elif x['l']:
        print('only lastname')
        print('checking rating: ', checkIfRatingExistsWithArtist(None, lname))
        if (checkIfRatingExistsWithArtist(None, lname)) :
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where a.lname like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            lname)
        else:
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join artist a  where a.lname like %s ", (
            lname)
    elif x['s']:
        print('only song')
        print('checking rating: ', checkIfRatingExistsWithSong(song))
        if (checkIfRatingExistsWithSong(song)) :
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a   where title like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            song)
        else :
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join songGenre gen natural join artist a  where title like %s", (
            song)

    elif x['a']:
        print('only album')
        print('check rating:', checkIfRatingExistsWithAlbum(album))
        if (checkIfRatingExistsWithAlbum(album)) :
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre, avg(rat.stars) as stars from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a  where alb.albumName like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre ", (
            album)
        else:
            return "select distinct s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb natural join songGenre gen natural join  artist a where alb.albumName like %s", (album)


    elif x['r']:
        print('only rating')
        return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, rat.stars, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a where rat.stars like %s", (
            ratingVal)

    elif x['g']:
        print('only genre')
        print('check rating:', checkIfRatingExistsWithGenre(genre))
        if (checkIfRatingExistsWithGenre(genre)) :
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, avg(rat.stars) as stars, s.songURL, gen.genre  from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join rateSong rat natural join songGenre gen natural join  artist a where gen.genre like %s group by s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre", (
            genre)
        else:
            return "select s.title, a.fname, a.lname, s.releaseDate, alb.albumName, s.songURL, gen.genre from song s natural join artistPerformsSong asp natural join songInAlbum sap natural join album alb NATURAL join songGenre gen natural join  artist a where gen.genre like %s", (
            genre)
    else:
        print('nothing was picked')

def checkIfRatingExistsWithSong(song):
    s = getSongIDFromSong(song)
    print(s)
    if s == None or len(s) == 0:
        return 0
    songID = [d['songID'] for d in s]
    if (len(getSongIDFromRateSong(songID)) <= 0) :
        print(getSongIDFromRateSong(songID))
        return 0
    else:
        print(getSongIDFromRateSong(songID))
        return 1

def checkIfRatingExistsWithAlbum(album):
    a = getAlbumIDFromAlbum(album)
    print(a)
    if a == None or len(a) == 0:
        return 0
    albumID = a[0]['albumID']
    print(albumID)
    s = getSongIDFromAlbum(albumID)
    songID = [d['songID'] for d in s]
    print('songID:', songID)
    if (len(getSongIDFromRateSong(songID)) <= 0) :
        print('No song from the album has ratings')
        print(getSongIDFromRateSong(songID))
        return 0
    else:
        set1 = songID
        print("set1: ", set1)
        set2 = getSongIDFromRateSong(songID)
        l2 = [ d['songID'] for d in set2]
        print("set2: ", set2)
        diff = set(set1) ^ set(l2)
        if (len(diff) != 0) :
            print("Songs without rating", diff)
            return 0
        else:
            print("All songs have a rating")
            return 1
       

def checkIfRatingExistsWithArtist(fname, lname):
    a = getArtistIDFromArtist(fname, lname)
    print(a)
    if a == None or len(a) == 0:
        return 0
    artistID = a[0]['artistID']
    print(artistID)
    s = getSongIDFromArtist(artistID)
    songID = [d['songID'] for d in s]
    print(songID)
    if (len(getSongIDFromRateSong(songID)) <= 0) :
        print('No song by this artist has ratings')
        print(getSongIDFromRateSong(songID))
        return 0
    
    else:
        set1 = songID
        print("set1: ", set1)
        set2 = getSongIDFromRateSong(songID)
        l2 = [ d['songID'] for d in set2]
        print("set2: ", set2)
        diff = set(set1) ^ set(l2)
        if (len(diff) != 0) :
            print("Songs by this artist without rating", diff)
            return 0
        else:
            print("All songs by this artist have a rating")
            return 1

def checkIfRatingExistsWithGenre(genre):
    s = getSongIDFromGenre(genre)
    if s == None or len(s) == 0:
        return 0
    songID = [d['songID'] for d in s]
    print(songID)
    if (len(getSongIDFromRateSong(songID)) <= 0) :
        print('No song in this genre has ratings')
        print(getSongIDFromRateSong(songID))
        return 0
    else:
        set1 = songID
        print("set1: ", set1)
        set2 = getSongIDFromRateSong(songID)
        l2 = [ d['songID'] for d in set2]
        print("set2: ", set2)
        diff = set(set1) ^ set(l2)
        if (len(diff) != 0) :
            print("Songs in this genre that dont have a rating", diff)
            return 0
        else:
            print("All songs in this genre have a rating")
            return 1

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        print("in post method")
        song = request.form['song']
        artistFName = request.form['artistFName']
        artistLName = request.form['artistLName']
        album = request.form['album']
        rating = request.form['rating']
        genre = request.form['genre']

        print(song)
        print(artistFName)
        print(artistLName)
        print(album)
        print(rating)
        print(genre)

        cursor = conn.cursor()
        # song, artistF, artistLast, album
        searchParams = [song, artistFName, artistLName, album, rating, genre]
        keys = ["s", "f", "l", "a", "r", "g"]

        status = list(map(_checkEmptyParams, searchParams))
        parameterMap = {keys[i]: status[i] for i in range(len(keys))}
        print(parameterMap)

        song2 = "%" + song + "%"
        artistFName2 = "%" + artistFName + "%"
        artistLName2 = "%" + artistLName + "%"
        album = "%" + album + "%"
        genre = "%" + genre + "%"
        # if rating is not None:
        #     ratingVal = int(rating)
        query = getUpdatedSearchQuery(parameterMap, song2, artistFName2, artistLName2, album, rating, genre)
        print(query)
        if (query == None or len(query) <=0) :
            message = 'No search params were entered, please refresh and try again!'
            return render_template('search.html', error=message)
        cursor.execute(query[0], query[1])
        conn.commit()
        data = cursor.fetchall()
        if (len(data) <=0) :
            message = 'No valid search results, please refresh and try again!'
            return render_template('search.html', error=message)
        
        return render_template('search.html', data=data)

    return render_template('search.html')

def checkLength(field) :
    l = len(field)
    if l <=0 or l > 50 :
        return 0
    return 1

@app.route('/playlist', methods=['GET', 'POST'])
def addPlaylist():
    if request.method == "GET":
        cursor = conn.cursor()
        cursor.execute("select title from song")
        songs = cursor.fetchall()
        print(songs)
        return render_template('playlist.html', songs=songs)
    if request.method == "POST":
        print("in post method")
        playlistName = request.form['playlist']
        userName = session['username']
        description = request.form['description']
        creationDate = str(datetime.now())
        song = request.form.getlist('song-choice')
        print(playlistName)
        print(userName)
        print(datetime)
        print(song)
        cursor = conn.cursor()
        cursor.execute("select title from song")
        songs = cursor.fetchall()
        if (len(playlistName) <=0  or playlistName is None) :
             print("PlaylistName empty")
             message = 'Playlist name is required. Please refresh page and try again'
             return render_template('playlist.html', error=message, songs=songs)
        if (checkLength(playlistName) != 1) :
             print("PlaylistName exceeds length requirements")
             message = 'Playlist name does not meet requirements should be between 1 and 50 chars. Please refresh page and try again'
             return render_template('playlist.html', error=message, songs=songs)
        if (checkPlaylistExists(userName, playlistName)) :
            message = 'You have already created a playlist with this name. Please refresh page and try again'
            return render_template('playlist.html', error=message, songs=songs)
        
        # song, artistF, artistLast, album
        print("Creating new entry in Playlist Table")
        cursor.execute("INSERT INTO playlist (username, playlistName, description, creationDate) VALUES(%s, %s, %s, %s)", (userName, playlistName, description, creationDate))
        if song != None:
            if len(song) == 0:
                message = 'You have chosen any song yet. Please refresh and try again'
                return render_template('playlist.html', error=message, songs=songs)
            print('box checked')
            for item in song:
                print("Calling method")
                print(getSongIDFromSong(item))
                s = getSongIDFromSong(item)
                songID = s[0]['songID']
                cursor.execute("INSERT INTO songsInPlaylist (username, playlistName, songID) VALUES(%s, %s, %s)", (userName, playlistName, songID))
        
        conn.commit()
        cursor.execute("select title, playlistName, count(playlistName) as total from (select title, playlistName, username, sp.songID from song s join songsInPlaylist sp ON s.songID = sp.songID where username = %s and playlistName = %s) gsp group by playlistName, title order by playlistName", (userName, playlistName))
        data = cursor.fetchall()
        print(data)
        cursor.execute("select title, playlistName, count(playlistName) as total from (select title, playlistName, username, sp.songID from song s join songsInPlaylist sp ON s.songID = sp.songID where username = %s) gsp group by playlistName,title order by playlistName", (userName))
        alldata = cursor.fetchall()
        print(alldata)
        cursor.execute("select playlistName, count(playlistName) as total from (select title, playlistName, username, sp.songID from song s join songsInPlaylist sp ON s.songID = sp.songID where username = %s) gsp group by playlistName order by playlistName", (userName))
        countData = cursor.fetchall()
        print(countData)
        cursor.execute("select title from song")
        songs = cursor.fetchall()
        return render_template('playlist.html', data=data, songs=songs, count=countData, alldata= alldata)
       
    return render_template('playlist.html', data=data, songs=songs, count=countData, alldata=alldata)

     

@app.route('/showplaylist', methods=['GET', 'POST'])
def showplaylist():
    cursor = conn.cursor()
    userName = session['username']
    cursor.execute("select title, playlistName, count(playlistName) as total from (select title, playlistName, username, sp.songID from song s join songsInPlaylist sp ON s.songID = sp.songID where username = %s) gsp group by playlistName,title order by playlistName", (userName))
    alldata = cursor.fetchall()
    print(alldata)
    cursor.execute("select playlistName, count(playlistName) as total from (select title, playlistName, username, sp.songID from song s join songsInPlaylist sp ON s.songID = sp.songID where username = %s) gsp group by playlistName order by count(playlistName)", (userName))
    countData = cursor.fetchall()
    print(countData)

    return render_template('showplaylist.html',count=countData, alldata= alldata)

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


@app.route("/friendUser", methods=["POST"])
@login_required
def friendUser():
    request_data = fetchFriendRequests()
    allf_data = fetchFriends()

    if request.form:
        requestData = request.form
        username_friended = requestData["username_friended"]
        username_requester = session["username"]
        if checkUserExist(username_friended):
            if username_friended == username_requester:
                message = "You cannot friend yourself!"
                return render_template("friend.html", message=message, friendRequests=request_data,
                                       allFriends=allf_data)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT acceptStatus FROM friend WHERE (user1 = %s AND user2 = %s) OR (user2 = %s AND user1 = %s)"
                cursor1.execute(statusQuery,
                                (username_friended, username_requester, username_friended, username_requester))
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
    return render_template("friend.html", message=message, username=session["username"],
                           friendRequests=request_data, allFriends=allf_data)


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


# follow

@login_required
def fetchFollowing():
    cursor = conn.cursor()
    user = session["username"]
    query = "SELECT follows as myFollowing FROM follows WHERE follower=%s"
    cursor.execute(query, (user))
    return cursor.fetchall()


@login_required
def fetchFollower():
    cursor = conn.cursor()
    user = session["username"]
    query = "SELECT follower as myFollower FROM follows WHERE follows=%s"
    cursor.execute(query, (user))
    return cursor.fetchall()


@app.route("/follow", methods=["GET"])
@login_required
def follow():
    allf_data = fetchFollowing()
    followersData = fetchFollower()
    return render_template("follow.html", allFollowing=allf_data, allFollower=followersData)


@app.route("/followUser", methods=["POST"])
@login_required
def followUser():
    allf_data = fetchFollowing()
    followersData = fetchFollower()

    if request.form:
        requestData = request.form
        username_following = requestData["username_following"]
        username_follower = session["username"]
        if checkUserExist(username_following):
            if username_following == username_follower:
                message = "You cannot follow yourself!"
                return render_template("follow.html", message=message, allFollowing=allf_data,
                                       allFollower=followersData)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT follows as myFollowing FROM follows WHERE follower=%s and follows=%s"
                cursor1.execute(statusQuery, (username_follower, username_following))
                followStatus = cursor1.fetchall()
                cursor1.close()

                # check if user already follows the other user
                if len(followStatus) > 0:
                    message = "You are already follow %s." % (username_following)
                else:
                    cursor = conn.cursor()
                    query = "INSERT INTO follows VALUES (%s, %s, %s)"
                    cursor.execute(query, (username_follower, username_following, time.strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    cursor.close()
                    message = "You are now following %s, refresh to see current following list" % (username_following)

            except:
                message = "An error has occurred. Please try again."
                return render_template("follow.html", allFollowing=allf_data, allFollower=followersData,
                                       message=message)
        else:
            message = "%s does not exist." % (username_following)
    return render_template("follow.html", allFollowing=allf_data, allFollower=followersData, message=message)


@app.route("/unfollow", methods=["POST"])
def unfollow():
    allf_data = fetchFollowing()
    followersData = fetchFollower()

    if request.form:
        requestData = request.form
        to_unfollow = requestData["to_unfollow"]
        currentUser = session["username"]

        if checkUserExist(to_unfollow):
            if to_unfollow == currentUser:
                message = "You cannot unfollow yourself!"
                return render_template("follow.html", unfollow_message=message, username=session["username"],
                                       allFollowing=allf_data, allFollower=followersData)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT follows as myFollowing FROM follows WHERE follower=%s and follows=%s"
                cursor1.execute(statusQuery, (currentUser, to_unfollow))
                followStatus = cursor1.fetchall()
                cursor1.close()

                # check if user is currently following the other user
                if len(followStatus) > 0:
                    cursor1 = conn.cursor()
                    query = "DELETE FROM follows WHERE follower=%s and follows=%s"
                    cursor1.execute(query, (currentUser, to_unfollow))
                    conn.commit()
                    cursor1.close()

                    # doesn't instantly update, have to refresh
                    message = "Successfully unfollowed, refresh to see current following list"
                else:
                    message = "You are not following %s" % (to_unfollow)
            except:
                message = "Failed to unfollow " + to_unfollow
        else:
            message = "user %s does not exist" % (to_unfollow)
            return render_template("follow.html", unfollow_message=message, username=session["username"],
                                   allFollowing=allf_data, allFollower=followersData)
    return render_template("follow.html", unfollow_message=message, username=session["username"],
                           allFollowing=allf_data, allFollower=followersData)


@app.route("/removeFollow", methods=["POST"])
def removeFollow():
    allf_data = fetchFollowing()
    followersData = fetchFollower()

    if request.form:
        requestData = request.form
        to_remove = requestData["to_remove"]
        currentUser = session["username"]

        if checkUserExist(to_remove):
            if to_remove == currentUser:
                message = "You cannot remove yourself as a follower!"
                return render_template("follow.html", remove_message=message, username=session["username"],
                                       allFollowing=allf_data, allFollower=followersData)
            try:
                cursor1 = conn.cursor()
                statusQuery = "SELECT follows as myFollowing FROM follows WHERE follows=%s and follower=%s"
                cursor1.execute(statusQuery, (currentUser, to_remove))
                followStatus = cursor1.fetchall()
                cursor1.close()

                # check if the to-be-removed user is currently following the loggedin user
                if len(followStatus) > 0:
                    cursor1 = conn.cursor()
                    query = "DELETE FROM follows WHERE follows=%s and follower=%s"
                    cursor1.execute(query, (currentUser, to_remove))
                    conn.commit()
                    cursor1.close()

                    # doesn't instantly update, have to refresh
                    message = "Successfully removed follower, refresh to see current following list"
                else:
                    message = "%s is not your follower" % (to_remove)
            except:
                message = "Failed to remove " + to_remove
        else:
            message = "user %s does not exist" % (to_remove)
            return render_template("follow.html", remove_message=message, username=session["username"],
                                   allFollowing=allf_data, allFollower=followersData)
    return render_template("follow.html", remove_message=message, username=session["username"],
                           allFollowing=allf_data, allFollower=followersData)


# post

@login_required
@app.route("/post", methods=['GET'])
def fetchList():
    # Fetch all data from song, album, artist tables
    user_id = session['username']
    cursor = conn.cursor()
    query = """
     SELECT s.songID,s.title, sIA.albumID, al.albumName, a.artistID, a.fname, a.lname, 
        CASE 
            WHEN uf.username IS NULL THEN false
            ELSE true
        END as is_fan
        FROM song s 
        JOIN artistPerformsSong aPS on s.songID = aPS.songID 
        JOIN artist a on a.artistID = aPS.artistID 
        JOIN songInAlbum sIA on s.songID = sIA.songID 
        JOIN album al on al.albumID = sIA.albumId
        LEFT JOIN userFanOfArtist uf on uf.artistID = a.artistID and uf.username = %s;
    """
    cursor.execute(query, (user_id))
    list = cursor.fetchall()

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

    # Combine review and rating data to show these two together
    combined_song = []
    combined_album = []

    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM song")
    songs = cursor.fetchall()
    cursor.execute("SELECT * FROM album")
    albums = cursor.fetchall()
    cursor.close()

    total_fans = {}
    total_song_reviews = {}
    total_album_reviews = {}
    average_song_ratings = {}
    average_album_ratings = {}

    for fan in fan_data:
        artist_id = fan['artistID']
        if artist_id in total_fans:
            total_fans[artist_id] += 1
        else:
            total_fans[artist_id] = 1

    for user in users:
        for song in songs:
            song_id = song['songID']
            user_song_data = {'username': user['username'], 'songID': song['songID']}
            song_reviews = [review for review in review_song_data if review['songID'] == song_id]
            total_song_reviews[song_id] = len(song_reviews)

            song_ratings = [rating['stars'] for rating in rating_song_data if rating['songID'] == song_id]
            average_song_ratings[song_id] = "{:.2f}".format(
                sum(song_ratings) / len(song_ratings)) if song_ratings else "0"

            for review in song_reviews:
                if review['username'] == user['username']:
                    user_song_data['review'] = review['reviewText']

            for rating in rating_song_data:
                if rating['songID'] == song_id and rating['username'] == user['username']:
                    user_song_data['rating'] = rating['stars']

            # Only append to combined_song if there's a review or rating
            if 'review' in user_song_data or 'rating' in user_song_data:
                combined_song.append(user_song_data)

        for album in albums:
            album_id = album['albumID']
            user_album_data = {'username': user['username'], 'albumID': album['albumID']}
            album_reviews = [review for review in review_album_data if review['albumID'] == album_id]
            total_album_reviews[album_id] = len(album_reviews)

            album_ratings = [rating['stars'] for rating in rating_album_data if rating['albumID'] == album_id]
            average_album_ratings[album_id] = "{:.2f}".format(
                sum(album_ratings) / len(album_ratings)) if album_ratings else "0"

            for review in album_reviews:
                if review['username'] == user['username']:
                    user_album_data['review'] = review['reviewText']

            for rating in rating_album_data:
                if rating['albumID'] == album_id and rating['username'] == user['username']:
                    user_album_data['rating'] = rating['stars']

            # Only append to combined_album if there's a review or rating
            if 'review' in user_album_data or 'rating' in user_album_data:
                combined_album.append(user_album_data)

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
                           fan_data=fan_data,
                           total_fans=total_fans,
                           combined_song=combined_song,
                           combined_album=combined_album,
                           total_song_reviews=total_song_reviews,
                           total_album_reviews=total_album_reviews,
                           average_song_ratings=average_song_ratings,
                           average_album_ratings=average_album_ratings
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
@app.route("/updateReviewAlbum", methods=["POST"])
def update_review_album():
    try:
        cursor = conn.cursor()
        album_id = request.form['album_id']
        new_review_text = request.form['new_review_text'].strip()
        user_id = session['username']
        review_date = datetime.now()

        # Check if the input field is empty
        if not new_review_text:
            return redirect(url_for('fetchList', error_empty_album_review=album_id))

        # Check if the user has already posted a review for the album
        check_query = "SELECT * FROM reviewAlbum WHERE albumID = %s AND username = %s;"
        cursor.execute(check_query, (album_id, user_id))
        existing_review = cursor.fetchone()
        if not existing_review:
            cursor.close()
            return redirect(url_for('fetchList', error_no_existing_review=album_id))

        # Update review in the database
        update_query = "UPDATE reviewAlbum SET reviewText = %s, reviewDate = %s WHERE albumID = %s AND username = %s;"
        cursor.execute(update_query, (new_review_text, review_date, album_id, user_id))
        conn.commit()
        cursor.close()

        return redirect(url_for('fetchList'))  # Redirect back to the list page
    except Exception as e:
        print(str(e))
        return jsonify(success=False, error=str(e)), 400


@app.route("/deleteReviewAlbum", methods=["POST"])
@login_required
def delete_review_album():
    cursor = conn.cursor()
    user_id = session['username']
    album_id = request.form['album_id']

    # Check if the user has posted a review for the album
    check_query = "SELECT * FROM reviewAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(check_query, (album_id, user_id))
    existing_review = cursor.fetchone()

    if existing_review:
        # Delete the review from the database
        delete_query = "DELETE FROM reviewAlbum WHERE albumID = %s AND username = %s;"
        cursor.execute(delete_query, (album_id, user_id))
        conn.commit()

    cursor.close()

    return jsonify(success=True)  # Return a success response


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
@app.route("/updateReviewSong", methods=["POST"])
def update_review_song():
    cursor = conn.cursor()
    song_id = request.form['song_id']
    new_review_text = request.form['new_review_text'].strip()
    user_id = session['username']
    review_date = datetime.now()

    # Check if the input field is empty
    if not new_review_text:
        return redirect(url_for('fetchList', error_empty_song_review=song_id))

    # Check if the user has already posted a review for the album
    check_query = "SELECT * FROM reviewSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_review = cursor.fetchone()
    if not existing_review:
        cursor.close()
        return redirect(url_for('fetchList', error_no_existing_review=song_id))

    # Update review in the database
    update_query = "UPDATE reviewSong SET reviewText = %s, reviewDate = %s WHERE songID = %s AND username = %s;"
    cursor.execute(update_query, (new_review_text, review_date, song_id, user_id))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))  # Redirect back to the list page


@app.route("/deleteReviewSong", methods=["POST"])
@login_required
def delete_review_song():
    cursor = conn.cursor()
    user_id = session['username']
    song_id = request.form['song_id']

    # Check if the user has posted a review for the album
    check_query = "SELECT * FROM reviewSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_review = cursor.fetchone()

    if existing_review:
        # Delete the review from the database
        delete_query = "DELETE FROM reviewSong WHERE songID = %s AND username = %s;"
        cursor.execute(delete_query, (song_id, user_id))
        conn.commit()

    cursor.close()

    return jsonify(success=True)  # Return a success response


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
@app.route("/updateRateAlbum", methods=["POST"])
def update_rate_album():
    cursor = conn.cursor()
    album_id = request.form['album_id']
    rating = int(request.form['rating'])
    user_id = session['username']

    # Check if the input field is empty
    if rating == 0:
        return redirect(url_for('fetchList', error_empty_album_rating=album_id))

    # Check if the user already posted a rating for the album
    check_query = "SELECT * FROM rateAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(check_query, (album_id, user_id))
    existing_rating = cursor.fetchone()

    if not existing_rating:
        cursor.close()
        return redirect(url_for('fetchList', error_no_existing_rating=album_id))

    # Update rating in the database
    update_query = "UPDATE rateAlbum SET stars = %s WHERE albumID = %s AND username = %s;"
    cursor.execute(update_query, (rating, album_id, user_id))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))


@login_required
@app.route("/deleteRateAlbum", methods=["POST"])
def delete_rate_album():
    cursor = conn.cursor()
    album_id = request.form['album_id']
    user_id = session['username']

    # Check if the user has posted a rating for the album
    check_query = "SELECT * FROM rateAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(check_query, (album_id, user_id))
    existing_rating = cursor.fetchone()

    if not existing_rating:
        cursor.close()
        return redirect(url_for('fetchList', error_no_existing_rating=album_id))

    # Delete rating from the database
    delete_query = "DELETE FROM rateAlbum WHERE albumID = %s AND username = %s;"
    cursor.execute(delete_query, (album_id, user_id))
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
@app.route("/updateRateSong", methods=["POST"])
def update_rate_song():
    cursor = conn.cursor()
    song_id = request.form['song_id']
    rating = int(request.form['rating'])
    user_id = session['username']

    # Check if the input field is empty
    if rating == 0:
        return redirect(url_for('fetchList', error_empty_song_rating=song_id))

    # Check if the user already posted a rating for the song
    check_query = "SELECT * FROM rateSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_rating = cursor.fetchone()

    if not existing_rating:
        cursor.close()
        return redirect(url_for('fetchList', error_no_existing_rating=song_id))

    # Update rating in the database
    update_query = "UPDATE rateSong SET stars = %s WHERE songID = %s AND username = %s;"
    cursor.execute(update_query, (rating, song_id, user_id))
    conn.commit()
    cursor.close()

    return redirect(url_for('fetchList'))


@login_required
@app.route("/deleteRateSong", methods=["POST"])
def delete_rate_song():
    cursor = conn.cursor()
    song_id = request.form['song_id']
    user_id = session['username']

    # Check if the user has posted a rating for the song
    check_query = "SELECT * FROM rateSong WHERE songID = %s AND username = %s;"
    cursor.execute(check_query, (song_id, user_id))
    existing_rating = cursor.fetchone()

    if not existing_rating:
        cursor.close()
        return redirect(url_for('fetchList', error_no_existing_rating=song_id))

    # Delete rating from the database
    delete_query = "DELETE FROM rateSong WHERE songID = %s AND username = %s;"
    cursor.execute(delete_query, (song_id, user_id))
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
    print(result)

    if is_fan:
        # Insert fan relationship in the database only if not already a fan
        if not result:
            save_query = "INSERT INTO userFanOfArtist (username, artistID, fanAt) VALUES (%s, %s, %s);"
            cursor.execute(save_query, (user_id, artist_id, time.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            error_fan = "Please refresh your browser."
    else:
        # Remove fan relationship from the database only if user is a fan
        if result:
            delete_query = "DELETE FROM userFanOfArtist WHERE username = %s AND artistID = %s;"
            cursor.execute(delete_query, (user_id, artist_id))
        else:
            error_fan = "Check the box and click the button."

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
