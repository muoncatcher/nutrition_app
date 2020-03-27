from flask import Flask, jsonify, request, g, render_template, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True  
app.config['SECRET_KEY'] = 'Thisisasecret!' 


#SQLITE3 database helper functions- should go at the top
from database import connect_db, get_db

@app.teardown_appcontext  
def close_db(error): 
    if hasattr(g, 'sqlite_db'): 
        g.sqlite_db.close()
        
          
@app.route('/', methods=['GET','POST'])
def index():
    db = get_db()
    
    if request.method == 'POST':
        date = request.form['date'] #the format of this depends on the browser. But for chrome, it is %Y-%m-%d
        dt = datetime.strptime(date,'%Y-%m-%d') 
        database_date= datetime.strftime(dt,'%Y%m%d')
        db.execute('insert into log_date (entry_date) values (?)',[database_date])
        db.commit()
    
    cur = db.execute('''select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories 
                     from log_date 
                     join food_date on food_date.log_date_id = log_date.id 
                     join food on food.id = food_date.food_id group by log_date.id order by log_date.entry_date desc''')
    results = cur.fetchall()
    #since we want pretty dates, and cannot modify results directly (it is a SQLITE3 list), we will copy them into a new list.
    date_results = []
    for i in results:
        single_date = {}
        single_date['entry_date'] = i['entry_date']
        single_date['protein'] = i['protein']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']
        d = datetime.strptime(str(i['entry_date']),'%Y%m%d')
        single_date['pretty_date'] = datetime.strftime(d,'%B %d, %Y')
        date_results.append(single_date)
    
    return render_template("home.html", results = date_results)

@app.route('/view/<date>',methods=['GET','POST'])
def view(date):
    db = get_db()
    cur=db.execute('select id, entry_date from log_date where entry_date = ?',[date])
    date_result=cur.fetchone()
    
#    return (str(request.method))
    if request.method == 'POST':
        db.execute('insert into food_date (food_id,log_date_id) values (?,?)', [request.form['food-select'], date_result['id']] )
        db.commit()
        #        return '<h2>The food item added is #{}</h2>'.format(request.form['food-select']) #the name we give is the value of the 
    
    d = str(date_result['entry_date'])  #comes back as an int e.g. 20200302, so convert to str
#    return '<h2>The date is {}</h2>'.format(result['entry_date'])
    pretty_date = datetime.strftime(datetime.strptime(d,'%Y%m%d'),'%B %d, %Y')
#    return pretty_date

    food_cur = db.execute('select id, name from food')    
    food_results = food_cur.fetchall()
    
    log_cur = db.execute('''select food.name, food.protein, food.carbohydrates, food.fat, food.calories 
                         from log_date 
                         join food_date on food_date.log_date_id = log_date.id 
                         join food on food.id = food_date.food_id 
                         where log_date.entry_date = ?''',[date])
    log_results= log_cur.fetchall()
    totals = {}  #faster to perform the addition in python than doing another SQL query
    totals['protein']=0
    totals['carbohydrates']=0
    totals['fat']=0
    totals['calories']=0
                
    for food in log_results:
        totals['protein'] += food['protein']
        totals['carbohydrates'] += food['carbohydrates']
        totals['fat'] += food['fat']
        totals['calories'] += food['calories']
    
    return render_template("day.html", pretty_date=pretty_date, entry_date=date_result['entry_date'],\
                           food_results=food_results,log_results=log_results,totals=totals)

@app.route('/food', methods=['GET','POST'])
def food():
    db = get_db()
    
    if request.method == 'POST':
        name = request.form['food-name']
        protein = request.form['protein']
        carbohydrates = request.form['carbohydrates']
        fat = request.form['fat']
        calories = 4*int(protein)+4*int(carbohydrates)+9*int(fat)
        
        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?,?,?,?,?)', \
                   [name, int(protein), int(carbohydrates), int(fat), calories])
        db.commit()
        
#        return '<h2>Name {}, Protein {}, Carbs {}, Fat {}</h2>'.format(name, protein, carbohydrates,fat)
    
    cur = db.execute('select name, protein, carbohydrates, fat, calories from food')
    results = cur.fetchall()
    
    return render_template("add_food.html",results=results)

if __name__ == "__main__":
    app.run(debug=True)