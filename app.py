from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'faraz'
app.config['MYSQL_PASSWORD'] =  'password'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = '5612eac0a71cc680a6fcad8b'

#Initialize MySQL
mysql = MySQL(app)


#Articles = Articles()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


#creating articles
@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)
    #close connection
    cur.close()



@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id= %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)
    

class RegisterForm(Form):
    name = StringField('Name', validators=[Length(min=1, max=50)])
    username = StringField('Username', validators=[Length(min=4, max=30)])
    email = StringField('Email', validators=[Length(min=6, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create Cursor
        cur = mysql.connection.cursor()

        # Executing the Query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('home'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # Get from fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #authenticated
                session['logged_in'] = True
                session['username'] = username
                flash('You are logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Username not Found'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not Found'
            return render_template('login.html', error=error)
    
    return render_template('login.html')


#check if the user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap



#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You have logged out', 'success')
    return redirect(url_for('login'))



#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()



#Article form class
class ArticleForm(Form):
    title = StringField('Title', validators=[Length(min=1, max=200)])
    body = TextAreaField('Body', validators=[Length(min=1), DataRequired()])


#Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #commit to DB
        mysql.connection.commit()

        #close the connection
        cur.close()

        flash('Article created', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_article.html', form=form)


#Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    #get user by the id
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    article = cur.fetchone()

    #create the form
    form = ArticleForm(request.form)

    #poplulate the article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        
        #commit to DB
        mysql.connection.commit()

        #close the connection
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True) 