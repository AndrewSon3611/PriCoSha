#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import sys
#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    cursor = conn.cursor();
    query = "SELECT item_id, email_post, post_time, item_name, file_path FROM contentitem WHERE (is_pub = 1 AND (post_time >= NOW() - INTERVAL 1 DAY)) ORDER BY post_time DESC";
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', posts = data)


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
    email = request.form['email']
    password = hashlib.sha256(bytes(request.form['password'],"utf-8")).hexdigest()#password is hashed

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s and password = %s'
    cursor.execute(query, (email, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['email'] = email
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    fname = request.form['fname']
    lname = request.form['lname'] #grabs information from the forms
    email = request.form['email']
    password = hashlib.sha256(bytes(request.form['password'],"utf-8")).hexdigest()#password is hashed
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, password, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/post', methods=['GET', 'POST'])
def post():
    user = session['email']
    cursor = conn.cursor();
    item_id = request.form['item_id']
    item_name = request.form['item_name']
    file_path = request.form['file_path']
    privacy = request.form['is_pub']
    privacyBool = 1
    if(privacy == 'Yes'):
        privacyBool = 0
    query = 'INSERT INTO contentitem (item_id, email_post, item_name, post_time, file_path, is_pub) VALUES(%s, %s, %s, NOW(), %s, %s)'
    cursor.execute(query, (item_id, user, item_name, file_path, privacyBool))
    if(privacyBool == 1):
        fg_name = request.form['fg_name']
        ins = 'INSERT INTO share (owner_email, fg_name, item_Id) Values(%s, %s, %s)'
        cursor.execute(ins, (user, fg_name, item_id))
        conn.commit()
    cursor.close()
    return redirect(url_for('home'))



@app.route('/home')
def home():
    user = session['email']
    cursor = conn.cursor();
    query = "SELECT item_id, email_post, post_time, item_name, file_path FROM contentitem WHERE (is_pub = 0 AND (post_time >= NOW() - INTERVAL 1 DAY)) ORDER BY post_time DESC";
    cursor.execute(query)
    data = cursor.fetchall()
    query = "SELECT * FROM belong WHERE email = %s"
    cursor.execute(query,(user))
    group = cursor.fetchall()
    cursor.close()
    return render_template('home.html', email = user, posts = data, friendgroup = group)


@app.route('/createfg')
def createfg():
    return render_template('createfg.html')

@app.route('/friendgroup', methods = ['GET', 'POST'])
def friendgroup():
    user = session['email']
    fg_name = request.form['fg_name']
    description = request.form['description']
    cursor = conn.cursor()
    query = 'SELECT fg_name, owner_email FROM friendgroup WHERE fg_name = %s AND owner_email = %s'
    cursor.execute(query, (fg_name, user))
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This friend group already exists"
        return render_template('createfg.html', error = error)
    else:
        ins = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (user, fg_name, description))
        conn.commit()
        ins = 'INSERT INTO belong Values(%s, %s, %s)'
        cursor.execute(ins, (user, user, fg_name))
        conn.commit()
        cursor.close()
        return redirect(url_for('createfg'))




@app.route('/findfriend', methods = ['GET', 'POST'])
def findfriend():
    user = session['email']
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    fg_name = request.form['fg_name']
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE fname = %s AND lname = %s AND email = %s'
    cursor.execute(query, (fname, lname, email))
    ins = 'INSERT INTO belong VALUES(%s, %s, %s)'
    cursor.execute(ins, (email, user, fg_name))
    conn.commit()
    cursor.close()
    return redirect(url_for('createfg'))

@app.route('/tagfriend', methods = ['GET', 'POST'])
def tagfriend():
    user = session['email']
    item_id = request.form['item_id']
    email_tagged = request.form['email_tagged']
    status = "False"
    cursor = conn.cursor()
    ins = 'INSERT INTO tag VALUES(%s,%s,%s,%s, NOW())'
    cursor.execute(ins, (email_tagged, user, item_id, status))
    conn.commit()
    cursor.close()
    return redirect(url_for('managetag'))



@app.route('/managetag')
def managetag():
    user = session['email']
    cursor = conn.cursor();
    query = 'SELECT * FROM tag WHERE email_tagged = %s'
    cursor.execute(query, (user))
    tags = cursor.fetchall()
    cursor.close()
    return render_template('managetag.html', tags = tags)


@app.route('/acceptTag', methods=['GET', 'POST'])
def acceptTag():
    user = session['email']
    email_tagger = request.form['email_tagger']
    id_num = request.form['item_id']
    cursor = conn.cursor();
    query = 'UPDATE Tag SET status = "True" WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
    cursor.execute(query, (user, email_tagger, id_num))
    conn.commit()
    cursor.close()
    return redirect('/managetag')

@app.route('/declineTag', methods=['GET', 'POST'])
def declineTag():
    user = session['email']
    email_tagger = request.form['email_tagger']
    id_num =request.form['item_id']
    cursor = conn.cursor();
    query = 'DELETE FROM Tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
    cursor.execute(query, (user, email_tagger, id_num))
    conn.commit()
    cursor.close()
    return redirect('/managetag')



@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
