from flask import Flask, render_template,session,request,flash,logging,url_for,redirect
from flask_mysqldb import MySQL
from wtforms import Form,StringField,PasswordField,TextAreaField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from data import Articles
app=Flask(__name__)
articles1=Articles()

# Here we will configure app to use mysql database for storage of data and user credentials
app.config['MYSQL_HOST']    =   'localhost'
app.config['MYSQL_USER']    =   'root'
app.config['MYSQL_PASSWORD']=   'root'
app.config['MYSQL_CURSORCLASS']  =   'DictCursor'
app.config['MYSQL_DB']          =   'myflaskapp'

#iniializing the database now
mysql=MySQL(app)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute('select * from articles')
    if result > 0:
        articles=cur.fetchall()
        return render_template('articles.html',articlesList=articles)
    
    else:
        msg = "There are No articles!"
        return render_template('articles.html',msg)
    


@app.route('/article/<art_id>')
def article(art_id):


    cur = mysql.connection.cursor()
    result = cur.execute('select * from articles where id = %s',[art_id])
    article=cur.fetchone()
    cur.close()
    return render_template('article.html',article1=article)

class RegisterForm(Form):
    name        = StringField('Name',[validators.Length(min=1, max=50)])
    email       =StringField('Email',[validators.Length(min=1,max=50)])
    username    =StringField('Username',[validators.Length(min=1,max=50)])
    
    
    password    =PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='Your passwords do not match!')])
    confirm     =PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
        form=RegisterForm(request.form)
        

        if request.method == 'POST' and form.validate():
            #The cursor needs to be created to execute the queries on the database
            cur =   mysql.connection.cursor()

            #fetch the form values posted with the request
            name    =   form.name.data
            email   =   form.email.data
            username=   form.username.data
            password=   sha256_crypt.encrypt(str(form.password.data))

            cur.execute("INSERT INTO users(name,email,username,password) values(%s, %s, %s, %s) ",(name,email,username,password))

            mysql.connection.commit()
            cur.close()

            flash('You are now Registered as a User of My Website. Go Bonkers and Log in!',category='success')
            return redirect(url_for('home'))



            #return render_template('register.html')
        return render_template('register.html',form1=form)

#User Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username    =   request.form['username']
        password    =   request.form['password']

        #creating the cursor to fetch the user if exists
        cur =   mysql.connection.cursor()
        result= cur.execute('SELECT * from users where username = %s',[username])
        if result   >   0:
            data    =   cur.fetchone()
            if sha256_crypt.verify(password,data['password']):
                session['logged_in']    =    True
                session['username']     =   username
                flash("You have entered Gaurav's World now!! WELCOME!",category='success')
                return redirect(url_for('dashboard'))
            else:
                error   = 'Invalid User credentials.'
                return render_template('login.html',error=error)
        else:
            error   = 'Invalid User! '
            return render_template('login.html',error=error)
    return render_template('login.html')





#DECORATOR TO CHECK USER LOGGED IN OR NOT
def is_logged_in(f):
        @wraps(f)
        def wrap(*args,**kwargs):
            if 'logged_in' in session:
                return f(*args,**kwargs)
            else:
                flash('Uh.. Ohhh... You are just so UNAUTHORIZED Matey!!!!','danger')
                return redirect(url_for('login'))
        return wrap
#User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out of Gaurav's World! Bye Bye!",category="info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():

    cur = mysql.connection.cursor()
    result = cur.execute('select * from articles')
    if result > 0:
        articles=cur.fetchall()
        return render_template('dashboard.html',articles=articles)
        cur.close()
    
    else:
        msg1 = "There are No articles!"
        return render_template('dashboard.html',msg=msg1)


#Add ARticle Form
class ArticleForm(Form):
    title        = StringField('Title:',[validators.Length(min=1, max=200)])
    body       =TextAreaField('Body:',[validators.Length(min=1)])
    
#Route for adding the article
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)

    if request.method == 'POST':
        title = form.title.data
        body = form.body.data

        #create the cursor
        cur = mysql.connection.cursor()

        cur.execute("insert into articles(title,body,author) values(%s, %s, %s)",(title,body,session['username']))

        mysql.connection.commit()
        cur.close()

        flash('Successfully added one article!',category='success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form1=form)


#Route for editing the article
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    form = ArticleForm(request.form)
    cur = mysql.connection.cursor()
    result= cur.execute("select * from articles where id = %s",[id])
    article1=cur.fetchone()
    form.title.data=article1['title']
    form.body.data= article1['body']
    
    cur.close()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        #create the cursor
        cur = mysql.connection.cursor()

        cur.execute("update articles set title=%s,body=%s where id =%s",(title,body,id))

        mysql.connection.commit()
        cur.close()

        flash('Successfully Updated the article!',category='success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form1=form)


#Deleting the article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    


        

        #create the cursor
        cur = mysql.connection.cursor()

        cur.execute("delete from articles where id=%s",[id])

        mysql.connection.commit()
        cur.close()

        flash('Successfully DELETED one article!',category='success')
        return redirect(url_for('dashboard'))
   
if __name__ == "__main__":
    app.debug=True
    app.secret_key= 'secret123'
    app.run(port=8002)
