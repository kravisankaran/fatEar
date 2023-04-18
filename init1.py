#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
from functools import wraps
import pymysql.cursors
import hashlib, time
from datetime import datetime

#for uploading photo:
from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
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


#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form['password']

    ## need to change varchar limit in order for this to work
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

    lastlogin = time.strftime('%Y-%m-%d')

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s and pwd = %s'
    cursor.execute(query, (username, plaintextPasword))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        update = 'UPDATE user SET lastlogin = %s WHERE username = %s'
        cursor.execute(update, (lastlogin, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    plaintextPasword = request.form['password']

    ## need to change varchar limit in order for this to work
    hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
    fname = request.form['First Name']
    lname = request.form['Last Name']
    nickname = request.form['nickname']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO user VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, plaintextPasword, fname, lname, time.strftime('%Y-%m-%d %H:%M:%S'), nickname))
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

# @app.route('/post', methods=['GET', 'POST'])
# def post():
#     username = session['username']
#     cursor = conn.cursor();
#     blog = request.form['blog']
#     query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
#     cursor.execute(query, (blog, username))
#     conn.commit()
#     cursor.close()
#     return redirect(url_for('home'))

# @app.route('/select_blogger')
# def select_blogger():
#     #check that user is logged in
#     #username = session['username']
#     #should throw exception if username not found
    
#     cursor = conn.cursor();
#     query = 'SELECT DISTINCT username FROM blog'
#     cursor.execute(query)
#     data = cursor.fetchall()
#     cursor.close()
#     return render_template('select_blogger.html', user_list=data)

# @app.route('/show_posts', methods=["GET", "POST"])
# def show_posts():
#     poster = request.args['poster']
#     cursor = conn.cursor()
#     query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
#     cursor.execute(query, poster)
#     data = cursor.fetchall()
#     cursor.close()
#     return render_template('show_posts.html', poster_name=poster, posts=data)


# def allowed_file(filename):
# 	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
# @app.route('/')
# def upload_form():
# 	return render_template('upload.html')

# @app.route('/', methods=['POST'])
# def upload_file():
# 	if request.method == 'POST':
#         # check if the post request has the file part
# 		if 'file' not in request.files:
# 			flash('No file part')
# 			return redirect(request.url)
# 		file = request.files['file']
# 		if file.filename == '':
# 			flash('No file selected for uploading')
# 			return redirect(request.url)
# 		if file and allowed_file(file.filename):
# 			filename = secure_filename(file.filename)
# 			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
# 			flash('File successfully uploaded')
# 			return redirect('/')
# 		else:
# 			flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
# 			return redirect(request.url)




#friend 

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
  return render_template("friend.html", friendRequests=request_data, allFriends = allf_data)

# does not handle duplicated requests yet!
@app.route("/friendUsername", methods=["POST"])
@login_required
def friendUsername():
  if request.form:
    requestData = request.form
    username_friended = requestData["username_friended"]
    username_requester = session["username"]
    if checkUserExist(username_friended):
      request_data = fetchFriendRequests()
      allf_data = fetchFriends()
      if username_friended == username_requester:
        message = "You cannot friend yourself!"
        return render_template("friend.html", message=message, friendRequests=request_data, allFriends = allf_data)
      try:
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
  return render_template("friend.html", friendRequests=request_data, allFriends = allf_data, message=message)

@login_required
@app.route("/accept/<username>", methods=["POST"])
def accept(username):
  username_friended = session["username"]
  username_requester = username
  cursor = conn.cursor()
  query = "UPDATE friend SET acceptStatus = 'accepted', updatedAt = %s WHERE user1 = %s AND user2 = %s"
  cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'),username_friended, username_requester))
  conn.commit()
  cursor.close()

  request_data = fetchFriendRequests()
  allf_data = fetchFriends()
  return render_template("friend.html", friendRequests=request_data, allFriends = allf_data)


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
  return render_template("friend.html", friendRequests=request_data, allFriends = allf_data)


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
        return render_template("friend.html", unfriend_message=message, username=session["username"],friendRequests=request_data, allFriends = allf_data)
      try:
        cursor1 = conn.cursor()
        query = "DELETE FROM friend WHERE (user1=%s AND user2=%s) OR (user2=%s AND user1=%s) AND acceptStatus = 'accepted'"
        cursor1.execute(query, (to_unfriend, currentUser, to_unfriend, currentUser))
        conn.commit()
        cursor1.close()

        #doesn't instantly update, have to refresh 
        message = "Successfully removed friend, refresh to see current friend list" + to_unfriend
      except:
        message = "Failed to unfriend " + to_unfriend
    else:
      message = "user %s does not exist" % (to_unfriend)
      return render_template("friend.html", unfriend_message=message, username=session["username"],friendRequests=request_data, allFriends = allf_data)
  return render_template("friend.html", unfriend_message=message, username=session["username"],friendRequests=request_data, allFriends = allf_data)



        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
