from flask import Flask, redirect, render_template, request, send_from_directory
from pip._vendor import requests
import sqlite3
import os.path
from os import path
from datetime import datetime
from find_sds.find_sds import find_sds

URL = "https://commonchemistry.cas.org/api/search?"


# Configure Flask
app = Flask(__name__)

# Configure database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "chem.db")
db = sqlite3.connect(db_path) 

def get_stock(chemical):
    ''' Gets stock count for chemical in question'''
    
    with sqlite3.connect(db_path) as db:
        
        # Get unit required to analyse stock for chemical, fetch all converts from object to list     
        units = db.execute(f"SELECT unit FROM orders WHERE chemical = ? GROUP BY unit", (chemical,)).fetchall()
        # If no units found from database, assumption made that stock = 0 as no matching chemical in database
        if units == []:
            return "Chemical Not Found"       
        unit = units[0][0]
        
        # If units = mL, or L, retrive associated numbers and add together (accounting for unit conversion)
        if unit == "mL" or unit == "L":
            
            # If chemical still on buy request form but not purchased, do not add to total stock
            mL = db.execute("SELECT SUM(amount) FROM orders WHERE chemical = ? AND unit = 'mL' AND NOT purchase_time = 'None' ", (chemical,)).fetchall()[0][0]
            L = db.execute("SELECT SUM(amount) FROM orders WHERE chemical = ? AND unit = 'L' AND NOT purchase_time = 'None' ", (chemical,)).fetchall()[0][0]
            
            # Get total volume of chemical accounting for ML or L == None
            if mL == None:
                total = f"{L} L"
            elif L == None:
                total = f"{(mL/1000)} L"  
            else:
                total = f"{(mL/1000) + L} L"
            
            return total
        
        else:
            # If chemical still on buy request form but not purchased, do not add to total stock. Fetchall converts from object to list
            mg = db.execute("SELECT SUM(amount) FROM orders WHERE chemical = ? AND unit = 'mg' AND NOT purchase_time = 'None' ", (chemical,)).fetchall()[0][0]
            g = db.execute("SELECT SUM(amount) FROM orders WHERE chemical = ? AND unit = 'g' AND NOT purchase_time = 'None' ", (chemical,)).fetchall()[0][0]
            Kg = db.execute("SELECT SUM(amount) FROM orders WHERE chemical = ? AND unit = 'Kg' AND NOT purchase_time = 'None' ", (chemical,)).fetchall()[0][0]
            
            # Make list of above variables
            units = [mg, g, Kg]
            num_total = 0
            
            # if unit has value, add to total value
            if mg != None:
                num_total += mg /1000
            if g != None:
                num_total += g
            if Kg != None:
                num_total += Kg *1000
            
            total = f"{num_total} g"
            return total


def find_cas(chemical):
    '''Return CAS number from function'''
    parameters = {
            'q' : chemical, 
            'size' : '1',
            'offset': '0'}
    # Make API call and save data
    response_api = requests.get(url = URL, params = parameters)
    response_api.raise_for_status()
    data = response_api.json()
    if data["count"] == 0:
        return 0
    # Return CAS (RN) number
    return(data["results"][0]['rn'])


    
@app.route("/")
def index():
    return redirect("/cas_database")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        # Check input added to chemical search, if yes continue with query
        if not request.form.get("chemical"):
            return render_template("error.html", message = "Please Ensure You Input Chemical Name")
        chemical = request.form.get("chemical")
        
        # API call to get CAS number from chemical name
        cas_number = find_cas(chemical)
        if cas_number == 0:
            return render_template("error.html", message = "Chemical Not Found")
        # Show details of search result
        return render_template("search_details.html", chemical = chemical.title(), cas_number = cas_number)

@app.route("/search_details", methods=["GET", "POST"])
def search_details():
    if request.method == "GET":
        return redirect("/cas_database")
    else:
        # add chemical/ CAS to database
        chemical = request.form.get("chemical")
        cas_number = request.form.get("cas_number")
        
        # strip decimals from time, (first convert to str)
        now = datetime.now()
        s = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        time = s[:16]
        
        with sqlite3.connect(db_path) as db:
            # Retrieve chemicals currently in database
            chem_list = (db.execute("SELECT * FROM Chemicals")).fetchall()
            print(chem_list)
            in_database = False       
        
            # Loop through names, if chemical found in database, in_database = True
            for chem in chem_list:
                if chemical == chem[0]:
                    in_database = True
                    return render_template("error.html", message = "Chemical Already in Database")
            
            # Loop through cas, if chemical found in database, in_database = True 
            # (for if someone trys to add same chemical under a different name)
            for chem in chem_list:
                if cas_number == chem[1]:
                    name = chem[0]
                    in_database = True
                    return render_template("error.html", message = f"Chemical Already in Database Under '{name}'")
                    
            if not in_database:
                data = [chemical, cas_number, time]
                db.execute("INSERT INTO Chemicals (name, cas, time) VALUES(?, ?, ?)", data)
        return redirect("/cas_database")
    
@app.route('/cas_database')
def cas_database():
    
    # Show results from database, ordered with most recent at top
    with sqlite3.connect(db_path) as db:
        data = db.execute("SELECT * FROM Chemicals ORDER BY time DESC")
        return render_template("cas_database.html", chemicals = data)

@app.route('/buy', methods=["GET", "POST"])
def buy():
    if request.method == "GET":
        with sqlite3.connect(db_path) as db:
            chemicals = db.execute("SELECT name from Chemicals ORDER BY name ASC")
        return render_template("buy.html", chemicals=chemicals)
    else:
        
        # If any data missing return error
        if not request.form.get("chemical") or not request.form.get("amount") or not request.form.get("unit") or not request.form.get("priority"):
            return render_template("error.html", message = "Please Ensure All Relevant Purchase Data is Added")
        
        # Add form values to variables
        chemical = request.form.get("chemical").title()
        amount = request.form.get("amount")
        unit = request.form.get("unit")
        priority = request.form.get("priority").title()
        
        # Strip decimals from time, (first convert to str)
        now = datetime.now()
        s = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        time = s[:16]
        
        # Add buy order to database
        with sqlite3.connect(db_path) as db:
            data = (chemical, amount, unit, time, priority)
            db.execute("INSERT INTO orders (chemical, amount, unit, time, priority) VALUES (?, ?, ?, ?, ?)", data)
        return redirect("/purchase_database")
        
        
@app.route('/purchase_database')
def purchase_database():
    
    # Show results from database, ordered with most recent at top
    with sqlite3.connect(db_path) as db:
        data = db.execute("SELECT * FROM orders WHERE amount > 0 ORDER BY time DESC")
        return render_template("purchase_database.html", orders = data)
    
@app.route('/purchase', methods = (["GET", "POST"]))
def purchase():
    if request.method == "POST":
        
        # Get data about purchase from posted form
        chemical = request.form.get("chemical") 
        amount = request.form.get("amount")
        unit = request.form.get("unit")
        date = request.form.get("date")
        
        # Get current time 
        now = datetime.now()
        s = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        time = s[:16]
        
        # Add purchase time to database
        with sqlite3.connect(db_path) as db:
            db_data = [time, chemical, amount, unit, date]
            db.execute("UPDATE orders SET purchase_time = ? WHERE chemical = ? AND amount = ? AND unit = ? AND time = ?", db_data)
            data = db.execute("SELECT * FROM orders WHERE amount > 0 ORDER BY time DESC")
            return render_template("purchase_database.html", orders = data)

@app.route('/sds', methods = ["GET", "POST"])
def sds():
    if request.method == "GET":
        return render_template("sds.html")
    else:
        # Ensure cas number was submitted
        if not request.form.get("cas"):
            return render_template("error.html", message = "Please Ensure You Input a Valid CAS Number")
        
        # Call find SDS function from Sub Module
        filepath = "/Users/joelpaull/cs50/CS50/final_project/find_sds/find_sds/SDS"
        cas = request.form.get("cas")
        
        # Ensure cas number is not letters
        if cas.isalpha():
            return render_template("error.html", message = "Please Enter a Numerical CAS Number")
        find_sds.find_sds([cas])
        
        # Check in pdf location to see if SDS has been found, return pdf if found, error if not found
        if path.exists(f"{filepath}/{cas}-SDS.pdf"):
            return send_from_directory(filepath, (cas + "-SDS.pdf"))
        else:
            return render_template("error.html", message = "SDS Not Found. Please Check CAS Number")
    
    
@app.route('/stock', methods = ["GET", "POST"])
def stock():
    
    if request.method == "GET":
        with sqlite3.connect(db_path) as db:
            chemicals = db.execute("SELECT name from Chemicals ORDER BY name ASC")
        return render_template("stock.html", chemicals=chemicals)
    else:     
        # Check if chemical input added to form
        if not request.form.get("chemical"):
            return render_template("error.html", message = "Please Input Chemical Name")
        
        # Check if name is numerical
        if request.form.get("chemical").isnumeric():
            return render_template("error.html", message = "Chemical Name Cannot Be Numerical")
        
        # Check total stock of chemical from form
        chemical = request.form.get("chemical").title()
        total = get_stock(chemical)
        
        with sqlite3.connect(db_path) as db:
            chemical_list = db.execute("SELECT name from Chemicals ORDER BY name ASC")
            
        return render_template("stock_details.html", chemical=chemical, total=total, chemicals=chemical_list, chemical_1 = chemical_list)

@app.route("/stock_removal", methods = ["GET", "POST"])
def remove():
    # Check that all variables are supplied in form
    if not request.form.get("chemical") or not request.form.get("amount") or not request.form.get("unit"):
        return render_template("error.html", message = "Please Input All Values To Remove Item")
    
    # Minus chemical from database
    chemical = request.form.get("chemical").title()
    amount = int(request.form.get("amount"))
    unit = request.form.get("unit")

    # Strip decimals from time, (first convert to str)
    now = datetime.now()
    s = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    time = s[:16]

    # When adding data to database amount * -1 removes amount from stock counting algorithm
    with sqlite3.connect(db_path) as db:
        data = (chemical, amount * -1, unit, time, "-", time)
        
        # Retrieve all chemicals in current database, fetch all converts to str
        chem_list = (db.execute("SELECT name FROM Chemicals")).fetchall()
        
        in_database = False       
        
        # Loop through if chemical found in database, in_database = True
        for chem in chem_list:
            if chemical == chem[0]:
                in_database = True
                
                # Get current stock in database, removing with .strip()
                current_stock = float(get_stock(chemical).strip("g").strip("L").strip())
           
                # Account for unit conversaions (work in g or L)
                if unit == "Kg":
                    current_stock = current_stock * 1000
                elif unit == "mL" or unit == "mg":
                    current_stock = current_stock * 1000

                # If current stock is greater than removal amount, then proceed with removal
                if current_stock >= float(amount):
                    db.execute("INSERT INTO orders (chemical, amount, unit, time, priority, purchase_time) VALUES (?, ?, ?, ?, ?, ?)", data)
                else:
                    return render_template("error.html", message = f"Not Enough {chemical} in Stock to Remove {amount} {unit}")
    
    # If not found in database return error
    if not in_database:
        return render_template("error.html", message = "Chemical Not Found in Current Stock")
    
    # Get new stock count and show stock details
    total = get_stock(chemical)
    return render_template("stock_details.html", chemical=chemical, total = total)
    
@app.route("/removal_data")
def removal_data():
    # Show removal results from database, ordered with most recent at top
    with sqlite3.connect(db_path) as db:
        data = db.execute("SELECT * FROM orders WHERE amount < 0 ORDER BY time DESC")
        return render_template("stock_removal.html", orders = data)

    
        