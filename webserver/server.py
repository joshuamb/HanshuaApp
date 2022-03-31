#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, flash

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jm5325"
DB_PASSWORD = "0414200011231998"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name varchar(15)
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None


@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args

  if not session.get('logged_in'):
      return render_template('login.html')

  else:  
      #
      # example of a database query
      #
      cursor = g.conn.execute("SELECT first_name FROM users WHERE first_name IS NOT NULL")
      names = []
      for result in cursor:
          names.append(result['first_name'])  # can also be accessed using result[0]
      cursor.close()

      #
      # Flask uses Jinja templates, which is an extension to HTML where you can
      # pass data to a template and dynamically generate HTML based on the data
      # (you can think of it as simple PHP)
      # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
      #
      # You can see an example template in templates/index.html
      #
      # context are the variables that are passed to the template.
      # for example, "data" key in the context variable defined below will be 
      # accessible as a variable in index.html:
      #
      #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
      #     <div>{{data}}</div>
      #     
      #     # creates a <div> tag for each element in data
      #     # will print: 
      #     #
      #     #   <div>grace hopper</div>
      #     #   <div>alan turing</div>
      #     #   <div>ada lovelace</div>
      #     #
      #     {% for n in data %}
      #     <div>{{n}}</div>
      #      {% endfor %}
      #
      context = dict(data = names)


      #
      # render_template looks in the templates/ folder for files.
      # for example, the below file reads template/index.html
      #
      return render_template("index.html", first_name = session.get('first_name'))

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/portfolio')
def portfolio():
    if not session.get('logged_in'):
        return render_template('login.html')
    
    cursor1 = g.conn.execute("SELECT * FROM possesses_skills WHERE user_id = %s", session.get('user_id'))
    cursor2 = g.conn.execute("SELECT * FROM experienced_experiences WHERE user_id = %s ORDER BY start", session.get('user_id'))
    cursor3 = g.conn.execute("SELECT * FROM earned_degrees WHERE user_id = %s", session.get('user_id'))
    skills = cursor1.fetchall(); experiences = cursor2.fetchall(); education = cursor3.fetchall()
    cursor1.close(); cursor2.close(); cursor3.close()

    usercursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", session.get('user_id'))
    userdata = usercursor.fetchone()
    usercursor.close()

    return render_template("portfolio.html", skills=skills, experiences=experiences, education=education, userdata = userdata)

@app.route('/get_my_resume')
def get_my_resume():
    if not session.get('logged_in'):
        return render_template('login.html')
    
    cursor1 = g.conn.execute("SELECT * FROM possesses_skills WHERE user_id = %s", session.get('user_id'))
    cursor2 = g.conn.execute("SELECT * FROM experienced_experiences WHERE user_id = %s ORDER BY start", session.get('user_id'))
    cursor3 = g.conn.execute("SELECT * FROM earned_degrees WHERE user_id = %s", session.get('user_id'))
    skills = cursor1.fetchall(); experiences = cursor2.fetchall(); education = cursor3.fetchall()
    cursor1.close(); cursor2.close(); cursor3.close()

    usercursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", session.get('user_id'))
    userdata = usercursor.fetchone()
    usercursor.close()

    return render_template("get_my_resume.html", skills=skills, experiences=experiences, education=education, userdata=userdata)

@app.route('/contact_book')
def contact_book():
    if not session.get('logged_in'):
        return render_template('login.html')

    #TODO check this SQL
    cursor = g.conn.execute("SELECT c.title, c.full_name, j.job_id, c.email, j.company, j.title AS jobtitle, j.job_id "
                            "FROM connection_with_contact_entry AS c JOIN work_at AS w on c.contact_id=w.contact_id "
                            "JOIN jobs AS j ON w.job_id=j.job_id WHERE user_id = %s",
                            session.get('user_id'))
    
    contacts = cursor.fetchall()
    cursor.close()
    
    job_cursor = g.conn.execute("SELECT job_id,title,company FROM jobs ORDER BY company")
    all_jobs = job_cursor.fetchall()
    job_cursor.close()

    return render_template("contact_book.html", contacts=contacts, all_jobs=all_jobs)

@app.route('/account_profile')
def account_profile():
    if not session.get('logged_in'):
        return render_template('login.html')

    cursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", session.get('user_id'))
    userdata = cursor.fetchone()
    cursor.close()

    return render_template("account_profile.html", userdata=userdata)


@app.route('/jobs')
def jobs():
    if not session.get('logged_in'):
        return render_template('login.html')
    

    cursor = g.conn.execute("SELECT * FROM jobs ORDER BY deadline ASC")
    job_ids = []
    companies = []
    titles = []
    descriptions = []
    cities = []
    states = []
    deadlines = []
    for result in cursor:
        job_ids.append(result['job_id'])
        companies.append(result['company'])
        titles.append(result['title'])
        descriptions.append(result['description'])
        cities.append(result['city'])
        states.append(result['state'])
        deadlines.append(result['deadline'])
    cursor.close()

    context = dict(job_ids = job_ids, companies=companies, titles=titles, descriptions=descriptions, cities=cities, states=states, deadlines=deadlines)

    return render_template("jobs.html", **context)


@app.route('/my_jobs')
def my_jobs():
    if not session.get('logged_in'):
        return render_template('login.html')
    

    cursor = g.conn.execute("SELECT * FROM jobs NATURAL JOIN interested_in NATURAL JOIN users WHERE user_id = 2 ORDER BY deadline ASC")
    job_ids = []
    companies = []
    titles = []
    descriptions = []
    cities = []
    states = []
    deadlines = []
    for result in cursor:
        job_ids.append(result['job_id'])
        companies.append(result['company'])
        titles.append(result['title'])
        descriptions.append(result['description'])
        cities.append(result['city'])
        states.append(result['state'])
        deadlines.append(result['deadline'])
    cursor.close()

    context = dict(job_ids = job_ids, companies=companies, titles=titles, descriptions=descriptions, cities=cities, states=states, deadlines=deadlines)

    return render_template("my_jobs.html", **context)



@app.route('/job_description',methods = ['POST'])
def result():
   if request.method == 'POST':
      result = request.form
      job_id = result['job_id']
      print "description requested for job_id " + job_id
      
      cursor = g.conn.execute("SELECT * FROM jobs WHERE job_id = %s", job_id)
      result = cursor.fetchone()
      cursor.close() 
      

      return render_template("job_description.html",result = result)


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')

@app.route('/modify_portfolio', methods=['POST'])
def modify_portfolio():
    sql_cmds = {'addskill':          'INSERT INTO possesses_skills VALUES (:user_id,:skill)',
                'deleteskill':       'DELETE FROM possesses_skills WHERE skill=:skill AND user_id=:user_id',
                'add_education':     'INSERT INTO earned_degrees VALUES (:user_id,:subject,:level)',
                'delete_education':  'DELETE FROM earned_degrees WHERE (user_id,level,subject)=(:user_id,:level,:subject)',
                'delete_experience': 'DELETE FROM experienced_experiences WHERE ex_id=:ex_id',
                'add_experience':    ('INSERT INTO '
                                      'experienced_experiences(user_id,start,stop,title,description,location,institution,category) '
                                      'VALUES(:user_id,:start,:stop,:title,:description,:location,:institution,:category)'
                                     ),
                'add_contact':       'INSERT INTO connection_with_contact_entry(user_id,full_name,email,title) '
                                     'VALUES(:user_id,:full_name,:email,:title); '

             }
    
    whichform = request.form['whichform']
    cmd = sql_cmds[whichform]
    
    try:
        g.conn.execute(text(cmd), dict(request.form.to_dict(), user_id = session.get('user_id')))
        flash('Successfully Modified Portfolio!', 'success')

    except Exception as e:
        print "uh oh, error with database"
        import traceback; traceback.print_exc()
        flash('Failed to modify portfolio!', 'error')
        flash(e.message, 'warning')

    return redirect('/portfolio')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cursor = g.conn.execute("SELECT * FROM users WHERE email = %s", email)
    if cursor.rowcount == 1:
        user = cursor.fetchone()
        print "logged user in"

        session['logged_in'] = True
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        session['user_id'] = user['user_id']
        return index()

    else:
        print "failed login attempt"
        return index()

   # if request.form['password'] == 'password' and request.form['email'] == 'admin':
   #     session['logged_in'] = True
   #     session['first_name'] = 'Josh'
   #     session['user_id'] = 1
   #     return index()
   # else:
   #     flash('wrong password!')
   #     return index()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return index()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.secret_key = os.urandom(12)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
