from flask import Flask,render_template,redirect,session,url_for,request,flash
from wtforms import Form
from wtforms import TextAreaField,StringField,PasswordField,validators
from passlib.hash import sha256_crypt
from flaskext.mysql import MySQL
from functools import wraps
app = Flask(__name__)
mysql = MySQL()

#Configuration for using MySQL
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'myflaskapp'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_CURSORCLASS']='DictCursor'

mysql.init_app(app)


#Articles fetcher helper
def get_articles():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute('select * from articles')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

#The first route for the home page is added below

@app.route('/')
def home():
    return render_template("home.html")


#About Page
@app.route('/about')
def about():
    return render_template('about.html')


#RegisterForm Class
class RegisterForm(Form):
    name=StringField('Name:',[validators.Length(min=1,max=200)])
    username=StringField('Username:',[validators.Length(min=1,max=50)])
    email=StringField('Email:',[validators.Length(min=1,max=200)])
    password=PasswordField('Password:',[validators.DataRequired(),validators.EqualTo('confirm',message="Uh oh... Passwords do not match Mate! Retry!")])
    confirm=PasswordField('Confirm:',validators=None)


#User Registration
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name  = form.name.data
        email= form.email.data
        username=form.username.data
        password = sha256_crypt.hash(str(form.password.data))


        #creating the cursor
        conn=mysql.connect()
        cur = conn.cursor()
        cur.execute('insert into users(name,email,username,password) values(%s, %s, %s, %s)',(name,email,username,password))
        conn.commit()
        #print "came here with ",name
        
        cur.close()
        flash('Account for '+name+" with the username "+username+" created successfully",category="success")
        return redirect(url_for('login'))
    return render_template('register.html',form1=form)



#User Login
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        username=request.form['username']
        password_candidate= request.form['password']
        conn=mysql.connect()
        cur = conn.cursor()
        result=cur.execute('select * from users where username=%s',[username])
        if result > 0:
            data=cur.fetchone()
            password=data[4]
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username']=username
                flash("Successful login!",category='success')
                return redirect(url_for('dashboard'))
            else:
                error1="Wrong password user!"
                return render_template('login.html',error=error1)
        else:
            error2 = "User does not exist"
            return render_template('login.html',error=error2)
    return render_template('login.html')

#User logout
@app.route('/logout')
def logout():
    session.clear()
    msg1="You have successfully logged out!"
    flash(msg1,category="info")
    return redirect(url_for('login'))

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in'  in session:
            return f(*args,**kwargs)
        else:
            flash("You need to be logged in Matey! You do not belong in here!",category="danger")
            return redirect(url_for('login'))
    return wrap
        

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #We will try to fetch all the articles here
    data = get_articles()
    app.logger.info('The length is '+str(len(data)))
    if len(data) > 0:
        return render_template('dashboard.html',articles=data)
    else:
        return render_template('dashboard.html')

    





#ArtcleAdd Form
class ArticleForm(Form):
    title=StringField('Title:',[validators.Length(min=1,max=200)])
    body=TextAreaField('Body:',[validators.Length(min=1)])

#Article adding
@app.route('/add_article',methods=["GET","POST"])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method == "POST":
        title= form.title.data
        body= form.body.data

        conn=mysql.connect()
        cur = conn.cursor()

        cur.execute('insert into articles(title,body,author) values(%s, %s, %s)',(title,body,session['username']))
        conn.commit()
        cur.close()
        flash("Successfully added one article!",category="success")
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form1=form)
    

#Delete Article
@app.route('/delete_article/<string:id>',methods=["POST"])
@is_logged_in
def delete_article(id):
    if request.method=="POST":
        con=mysql.connect()
        cur=con.cursor()
        cur.execute('delete from articles where id=%s',[id])
        con.commit()
        cur.close()
        con.close()
        flash("Successful deletion!",category='success')
        return redirect(url_for('dashboard'))
#Article editing
@app.route('/edit_article/<string:id>',methods=["GET","POST"])
@is_logged_in
def edit_article(id):
    form = ArticleForm(request.form)
    con=mysql.connect()
    cur=con.cursor()
   
    result=cur.execute("select * from articles where id=%s",[id])
    data=cur.fetchone()
    form.title.data=data[1]
    form.body.data=data[2]
    if request.method == "POST":
        title=request.form['title']
        body=request.form['body']
        cur=con.cursor()
        cur.execute('update articles set title=%s,body=%s where id= %s',(title,body,id))
        con.commit()
        cur.close()
        flash("Edit successful!",category="success")
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form1=form)
    

#List all articles on click of link
@app.route('/articles')
def articles():
    data=get_articles()
    return render_template('articles.html',articles=data)

#List One article details
@app.route('/article/<string:id>')
def article(id):
    cur=mysql.connect().cursor()
    result=cur.execute('select * from articles where id = %s',[id])
    data=cur.fetchone()
    cur.close()

    return render_template('article.html',article=data)
if __name__ == '__main__':
    app.secret_key='richgem2326'
    app.run(port=8002,debug=True)
