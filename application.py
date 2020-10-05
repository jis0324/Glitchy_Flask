import csv
import io
import logging
import re
import uuid
from datetime import date, datetime
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, Response

application = Flask(__name__)
application.secret_key = '1a2b3c4d5e'
application.config['MYSQL_HOST'] = 'database-freegift.cr4bbmvqlh1t.us-east-2.rds.amazonaws.com'
application.config['MYSQL_USER'] = 'admin'
application.config['MYSQL_PASSWORD'] = 'freegift41GOD'
application.config['MYSQL_DB'] = 'nonothingdb01'

rds_host  = "database-freegift.cr4bbmvqlh1t.us-east-2.rds.amazonaws.com"
name = 'admin'
password = 'freegift41GOD'
db_name = 'nonothingdb01'
reviewcount = 0
logger = logging.getLogger()
logger.setLevel(logging.INFO)
conn = None
today = date.today()
now = datetime.now()
today_day = today.strftime("%m%Y")
today_time = now.strftime("%H%M%S")
print("START....", today_day, today_time)


def get_active_connection(new_conn):
    try:
        if not new_conn or new_conn == None:
            new_conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5,
                               cursorclass=pymysql.cursors.DictCursor)
        return new_conn, new_conn.cursor()
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")


def get_navigation_ids():
    productid = 0
    if 'productid' in session:
        productid = session['productid']
    orderno = 0
    if 'orderno' in session:
        orderno = session['orderno']
    fname = ''
    if 'fname' in session:
        fname = session['fname']
    lname = ''
    if 'lname' in session:
        lname = session['lname']
    email = ''
    if 'email' in session:
        email = session['email']
    userguid = ''
    if 'userguid' in session:
        userguid = session['userguid']
    tel = ''
    if 'tel' in session:
        tel = session['tel']
    return productid, orderno, fname, lname, email, tel, userguid


def setnavigation_ids(productid, orderno, userguid, fname='', lname='', email='', tel=''):
    if productid == -1 and 'productid' in session:
        productid = str(session['productid'])
    elif productid >= 0:
        session['productid'] = productid
    else:
        productid = 0
    if len(str(orderno)) < 16 and 'orderno' in session:
        orderno = str(session['orderno'])
    elif len(str(orderno)) >= 16:
        session['orderno'] = orderno
    else:
        orderno = ''
    if fname == '' and 'fname' in session:
        fname = str(session['fname'])
    else:
        session['fname'] = fname
    if lname == '' and 'lname' in session:
        lname = str(session['lname'])
    else:
        session['lname'] = lname
    if email == '' and 'email' in session:
        email = str(session['email'])
    else:
        session['email'] = email
    if tel == '' and 'tel' in session:
        tel = str(session['tel'])
    else:
        session['tel'] = tel
    if userguid == '' and 'userguid' in session:
        userguid = str(session['userguid'])
    else:
        session['userguid'] = userguid


@application.route('/deleteproduct/<int:productid>', methods=['GET'])
def deleteproduct(productid=0):
    global conn
    if 'loggedin' in session:
        userid = session['id']
        username = str(session['username']).upper()
        info_text = ""
        searchtype = 'Products'
        p_ordernumber = ''
        p_subscribed = ''
        p_startdate = ''
        p_enddate = ''
        if request.method == 'GET':
            conn, od_cursor = get_active_connection(conn)
            productdata = {}
            print("deleteproduct: ", productid)
            if productid > 0:
                od_cursor.execute("SELECT * FROM products WHERE prod_id='" + str(productid) + "'")
                productdata = od_cursor.fetchone()
                od_cursor.execute("DELETE FROM products WHERE prod_id='" + str(productid) + "'")
                conn.commit()
            if productid in session:
                productid = session['productid']
            else:
                productid = 0
            if p_ordernumber in session:
                p_ordernumber = session['p_ordernumber']
            if p_subscribed in session:
                p_subscribed = session['p_subscribed']
            if p_startdate in session:
                p_startdate = session['p_startdate']
            if p_enddate in session:
                p_enddate = session['p_enddate']
            od_cursor.execute("SELECT * FROM amazonorders order by id desc LIMIT 15")
            allorders = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM products order by prod_id desc LIMIT 15")
            allproducts = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM user_reviews order by id desc LIMIT 15")
            allbuyers = od_cursor.fetchall()
            return render_template('admin.html', userid=userid, username=username, searchtype=searchtype, productid=productid, p_ordernumber=p_ordernumber,p_subscribed=p_subscribed,p_startdate=p_startdate, p_enddate=p_enddate, buyerslist=allbuyers, orderslist=allorders, productslist=allproducts, dataproduct=productdata)


@application.route('/editproduct/<int:productid>', methods=['GET', 'POST'])
def editproduct(productid=0):
    global conn
    if 'loggedin' in session:
        userid = session['id']
        username = str(session['username']).upper()
        info_text = ""
        searchtype = 'Products'
        p_ordernumber = ''
        p_subscribed = ''
        p_startdate = ''
        p_enddate = ''
        if request.method == 'POST':
            data = dict(request.form)
            epx_title = ''
            epx_asin = ''
            epx_url = ''
            epx_deleted = '0'
            print("Xeditproduct: ", productid, str(data))
            if 'epx_title' in data:
                epx_title = data['epx_title']
            if 'epx_asin' in data:
                epx_asin = data['epx_asin']
            if 'epx_url' in data:
                epx_url = data['epx_url']
            if 'epx_deleted' in data:
                epx_deleted = data['epx_deleted']
            print("editproduct: ", productid, epx_title)
            conn, od_cursor = get_active_connection(conn)
            if productid > 0:
                if len(str(epx_title)) > 0 or len(str(epx_asin)) > 0 or len(str(epx_url)) > 0 or len(str(epx_deleted)) > 0:
                    up_sql = "UPDATE products set title = '" + str(epx_title) + "', asin = '" + str(epx_asin) + "', image = '" + str(epx_url) + "', is_deleted = '" + str(epx_deleted) + "' WHERE prod_id=" + str(productid)
                    print("editproduct: ", productid, up_sql)
                    od_cursor.execute(up_sql)
                    conn.commit()
                od_cursor.execute("SELECT * FROM products WHERE prod_id='" + str(productid) + "'")
                productdata = od_cursor.fetchone()
            if productid in session:
                productid = session['productid']
            else:
                productid = 0
            if p_ordernumber in session:
                p_ordernumber = session['p_ordernumber']
            if p_subscribed in session:
                p_subscribed = session['p_subscribed']
            if p_startdate in session:
                p_startdate = session['p_startdate']
            if p_enddate in session:
                p_enddate = session['p_enddate']
            od_cursor.execute("SELECT * FROM amazon_orders order by id desc LIMIT 15")
            allorders = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM products order by prod_id desc LIMIT 15")
            allproducts = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM user_reviews order by id desc LIMIT 15")
            allbuyers = od_cursor.fetchall()
            productdata = {}
            return render_template('admin.html', userid=userid, username=username, searchtype=searchtype, productid=productid, p_ordernumber=p_ordernumber,p_subscribed=p_subscribed,p_startdate=p_startdate, p_enddate=p_enddate, buyerslist=allbuyers, orderslist=allorders, productslist=allproducts, dataproduct=productdata)


@application.route('/saveproduct', methods=['POST'])
def saveproduct():
    global conn
    if 'loggedin' in session:
        userid = session['id']
        username = str(session['username']).upper()
        info_text = ""
        searchtype = 'Products'
        p_ordernumber = ''
        p_subscribed = ''
        p_startdate = ''
        p_enddate = ''
        productid = 0
        if request.method == 'POST':
            if productid in session:
                productid = session['productid']
            if p_ordernumber in session:
                p_ordernumber = session['p_ordernumber']
            if p_subscribed in session:
                p_subscribed = session['p_subscribed']
            if p_startdate in session:
                p_startdate = session['p_startdate']
            if p_enddate in session:
                p_enddate = session['p_enddate']
            data = dict(request.form)
            px_title = ''
            px_asin = ''
            px_url = ''
            px_deleted = 0
            if 'px_title' in data:
                px_title = data['px_title']
            if 'px_asin' in data:
                px_asin = data['px_asin']
            if 'px_url' in data:
                px_url = data['px_url']
            if 'px_deleted' in data:
                px_deleted = data['px_deleted']
            print("saveproductX: ", px_title, px_deleted)
            conn, od_cursor = get_active_connection(conn)
            if len(str(px_title)) > 0 and len(str(px_url)) > 0:
                i_sql = "INSERT INTO products (title, asin, image, is_deleted, added_by, added_on) VALUES ('" + str(px_title) + "', '" + str(px_asin) + "', '" + str(px_url) + "', '" + str(px_deleted) + "', '" + str(userid) + "', NOW())"
                od_cursor.execute(i_sql)
                conn.commit()
            od_cursor.execute("SELECT * FROM amazonorders order by id desc LIMIT 15")
            allorders = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM products order by prod_id desc LIMIT 15")
            allproducts = od_cursor.fetchall()
            od_cursor.execute("SELECT * FROM user_reviews order by id desc LIMIT 15")
            allbuyers = od_cursor.fetchall()
            productdata = {}
            if productid > 0:
                od_cursor.execute("SELECT * FROM products WHERE prod_id='" + str(productid) + "'")
                productdata = od_cursor.fetchone()
    return render_template('admin.html', userid=userid, username=username, searchtype=searchtype, productid=productid, p_ordernumber=p_ordernumber,p_subscribed=p_subscribed,p_startdate=p_startdate, p_enddate=p_enddate, buyerslist=allbuyers, orderslist=allorders, productslist=allproducts, dataproduct=productdata)


def save_user_account(fname, lname, email, tel):
    global conn
    theguid = str(uuid.uuid1().hex)
    print("save_user_account1: ", fname, lname, email, tel, theguid)
    conn, cursor = get_active_connection(conn)
    sql_1 = "SELECT count(*) as total FROM user_reviews WHERE Email='" + str(email) + "'  and FName='" + str(fname) + "' and LName='" + str(lname) + "'"
    print("save_user_account2-sql: ", sql_1)
    cursor.execute(sql_1)
    user_data = cursor.fetchone()
    user_data_count = cursor.rowcount
    user_total = 0
    user_code = '0'
    if user_data_count > 0:
        user_total = user_data['total']
        if user_total <= 0:
            conn, cursor = get_active_connection(conn)
            user_code = theguid
            full_name = fname + " " + lname
            sql_2 = "INSERT INTO user_reviews (FName, LName, Buyer_Name, Email, Tel, Code, AmazonOrderId) VALUES ('" + str(fname) + "','" + str(lname) + "', '" + str(full_name) + "', '" + str(email) + "','" + str(tel) + "','" + str(theguid) + "','0')"
            cursor.execute(sql_2)
            conn.commit()
            return user_code
        else:
            sql_3 = "SELECT Code as code FROM user_reviews WHERE Email='" + str(email) + "'  and FName='" + str(fname) + "' and LName='" + str(lname) + "'"
            print("save_user_account3-sql: ", sql_3)
            conn, cursor = get_active_connection(conn)
            cursor.execute(sql_3)
            user_data = cursor.fetchone()
            if cursor.rowcount > 0:
                user_code = user_data['code']
                return user_code
    return user_code


def save_user_address(in_userguid, ship_addr1, ship_addr2, ship_city, ship_state, ship_country, ship_zip):
    global conn
    userguid = str(in_userguid).strip()
    print("save_user_address: ", in_userguid, ship_city, ship_addr1, ship_addr2)
    conn, cursor = get_active_connection(conn)
    sql = "UPDATE user_reviews set ShippingAddress_Line_1='" + str(ship_addr1) + "', ShippingAddress_Line_2='" + str(ship_addr2) + "', ShippingAddress_City='" + str(ship_city) + "', ShippingAddress_StateOrRegion='" + str(ship_state) + "', ShippingAddress_CountryCode='" + str(ship_country) + "', ShippingAddress_PostalCode='" + str(ship_zip) + "' WHERE Code='" + str(userguid) + "'"
    print("save_user_address-sql: ", sql)
    cursor.execute(sql)
    #print(cursor.description)
    conn.commit()
    return userguid


def save_user_reviews(in_userguid, satisfied, buy, comment):
    global conn
    userguid = str(in_userguid).strip()
    print("save_user_reviews: ", in_userguid, satisfied, buy, comment)
    conn, cursor = get_active_connection(conn)
    sql = "UPDATE user_reviews set Satisfied='" + str(satisfied) + "', Buy_Product='" + str(buy) + "', Commentary='" + str(comment) + "' WHERE Code='" + str(userguid) + "'"
    print("save_user_reviews-sql: ", sql)
    cursor.execute(sql)
    conn.commit()
    return userguid


def save_order_number(in_order_no, in_user_guid):
    global conn
    theguid = str(in_user_guid).strip()
    order_no = str(in_order_no).strip()
    msg_text = ''
    print("0save_order_number: ", order_no, theguid)
    if len(str(theguid)) < 16:
        theguid = str(uuid.uuid1().hex)
    status_code = str('')
    order_purchase_days_total = 0
    print("1save_order_number: ", order_no, theguid, status_code)
    conn, cursor = get_active_connection(conn)
    sql_main_total = "SELECT count(*) as total FROM amazonorders WHERE AmazonOrderId='" + str(order_no) + "'"
    print("2xsave_order_number-sql: ", sql_main_total)
    cursor.execute(sql_main_total)
    order_main_data = cursor.fetchone()
    order_main_total = 0
    if cursor.rowcount > 0:
        order_main_total = order_main_data['total']
        if order_main_total <= 0:
            status_code += '|3'
            msg_text += "|Data input error please check order number"
            print("save_order_number: ", order_no, status_code, "Data input error please check order number")
        else:
            sql_purchase_days = "SELECT DATEDIFF(NOW(),PurchaseDate) AS days FROM amazonorders WHERE AmazonOrderId='" + str(order_no) + "';"
            cursor.execute(sql_purchase_days)
            order_purchase_days_data = cursor.fetchone()
            order_count = cursor.rowcount
            if order_count > 0:
                order_purchase_days_total = order_purchase_days_data['days']
                if order_purchase_days_total >= 90:
                    status_code += '|4'
                    msg_text += "|Purchase date more than 90 days"
                    print("save_order_number: ", order_no, status_code, "Purchase date more than 90 days")
                else:
                    status_code += '|1'
                    msg_text += "|Valid order"
                    print("save_order_number: ", order_no, status_code, "Valid order")
    else:
        status_code += '|6'
        msg_text += "|Order Number Not Found In our System"
        print("save_order_number: ", order_no, status_code, "Order Number Not Found In our System")
    sql_is_subscribed = "SELECT COUNT(*) AS total FROM amazonorders WHERE AmazonOrderId='" + str(order_no) + "' AND Is_Subscribed=1;"
    conn, cursor = get_active_connection(conn)
    cursor.execute(sql_is_subscribed)
    order_is_subscribed_data = cursor.fetchone()
    order_subscribed_total = 0
    if cursor.rowcount > 0:
        order_subscribed_total = order_is_subscribed_data['total']
        if order_subscribed_total > 0:
            status_code += '|2'
            msg_text += "|Already Subscribed to the order"
            print("save_order_number: ", order_no, status_code, "Already Subscribed to the order")
    conn, cursor = get_active_connection(conn)
    sql_buyer_email_total = "SELECT count(*) as total FROM amazonorders WHERE AmazonOrderId='" + str(order_no) + "' AND BuyerEmail <> '';"
    cursor.execute(sql_buyer_email_total)
    print("4save_order_number-sql: ", sql_buyer_email_total)
    order_sh_buyer_data = cursor.fetchone()
    order_sh_buyer_total = 0
    order_sh_buyer_dataset = None
    if cursor.rowcount > 0:
        order_sh_buyer_total = order_sh_buyer_data['total']
        if order_sh_buyer_total > 0:
            status_code += '|1'
            msg_text += "|Success"
            print("save_order_number: ", order_no, status_code, "Success: Valid Buyer Email")
            sh_sql = "SELECT usv.FName  as fname, usv.LName  as lname, usv.Email as email, usv.AmazonOrderId as order_id, usv.product_id as prod_id, usv.image, odx.asin as asin, '' AS satisfied,'' AS `describe`,'' AS buy_product, usv.fname  as ship_fname, usv.lname as ship_lname, usv.ShippingAddress_Line_1 AS ship_addr1, usv.ShippingAddress_Line_2 AS ship_addr2, usv.ShippingAddress_City AS ship_city, usv.ShippingAddress_StateOrRegion AS ship_state, usv.ShippingAddress_CountryCode AS ship_country,usv.ShippingAddress_PostalCode AS ship_zip FROM user_reviews usv INNER JOIN amazonorders azd on usv.AmazonOrderId = azd.AmazonOrderId INNER JOIN amazonorderitems odx on azd.AmazonOrderId = odx.AmazonOrderId WHERE azd.AmazonOrderId='" + str(order_no) + "' AND azd.BuyerEmail <> ''"
            cursor.execute(sh_sql)
            order_sh_buyer_dataset = cursor.fetchone()
            print("5save_order_number-sql: ", sh_sql)
    else:
        msg_text += "|No buyer email"
        print("save_order_number: ", order_no, status_code, "No buyer email")
    print("order_purchase_days_total: ", order_purchase_days_total, " status_code: ",  status_code)
    if re.search("1", status_code) and order_purchase_days_total < 7:
        wait_days = 7 - order_purchase_days_total
        msg_text = "Our records indicate that the product was delivered less than " + str(wait_days) + " days ago, and this promotion is only valid if you've been using your No nothing product for at least seven days. If you feel you're receiving this message in error please email freegiftnn@gmail.com, or alternatively please return after " + str(wait_days) + " days of using your new product."
    elif (re.search("1", status_code) or re.search("4", status_code)) and order_purchase_days_total >= 90:
        msg_text = "Sorry, You are not eligible to get one free gift since your purchase date is more than 90 days."
    elif re.search("3", status_code) or re.search("6", status_code):
        msg_text = "We can't seem to validate your order... The order ID you provided does not match any selected product."
    elif re.search("2", status_code):
        msg_text = "This order is already subscribed to this service and has been issued with a free gift"
    else:
        status_code = '|0'
        msg_text = "Thank you. Your subscription is in progress"
        conn, cursor = get_active_connection(conn)
        update_sql = "UPDATE user_reviews SET Code='" + str(theguid) + "' WHERE AmazonOrderId='" + str(order_no) + "';"
        cursor.execute(update_sql)
        conn.commit()
        update_sql = "UPDATE amazonorders SET Code='" + str(theguid) + "' WHERE AmazonOrderId='" + str(order_no) + "';"
        cursor.execute(update_sql)
        conn.commit()
        sql = "update user_reviews set Is_Subscribed=1, Subscribed_On=NOW(), AmazonOrderId='" + str(order_no) + "' WHERE Code='" + str(theguid) + "';"
        cursor.execute(sql)
        conn.commit()
        update_sql = "UPDATE amazonorders SET Is_Subscribed=1 WHERE Code='" + str(theguid) + "';"
        cursor.execute(update_sql)
        print('amazonorders->Is_Subscribed', update_sql)
        conn.commit()
        sql = "UPDATE user_reviews a INNER JOIN amazonorders b ON a.AmazonOrderId = b.AmazonOrderId SET a.ShippingAddress_City = b.ShippingAddress_City, a.ShippingAddress_PostalCode= b.ShippingAddress_PostalCode, a.ShippingAddress_StateOrRegion=b.ShippingAddress_StateOrRegion, a.ShippingAddress_CountryCode=b.ShippingAddress_CountryCode;"
        cursor.execute(sql)
        conn.commit()
    print("last:save_order_number: ", msg_text, " status_code: ",  status_code)
    return status_code, msg_text, theguid, order_sh_buyer_dataset

@application.route('/')
def root():
    return render_template('home.html', productid=0, orderno=0)


@application.route('/', methods=['GET', 'POST'])
def start():
    global conn
    print("freegift start: ")
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM accounts WHERE username = '"+ str(username) + "' AND password = '"+ str(password) + "'")
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            print("loginROOT-username", account['id'])
            return redirect(url_for('admin'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('home.html', msg='')


@application.route('/admin', methods=['GET', 'POST'])
def admin():
    global conn
    if 'loggedin' in session:
        today = date.today()
        today_day = today.strftime("%Y-%m-%d")
        param_ordernumber = '0'
        param_start_date = '0'
        param_end_date = '0'
        productid = 0
        param_subscribed = '2'
        userid = session['id']
        searchtype = "Orders"
        username = str(session['username']).upper()
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM amazonorders order by id desc LIMIT 15")
        allorders = cursor.fetchall()
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM products order by prod_id desc LIMIT 15")
        allproducts = cursor.fetchall()
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM user_reviews order by id desc LIMIT 15")
        allbuyers = cursor.fetchall()
        print("adminROOT-username", session['id'], param_subscribed, param_ordernumber, param_start_date, param_end_date)
        productdata = {}
        return render_template('admin.html', userid=userid, username=username, searchtype=searchtype, productid=productid, p_ordernumber=param_ordernumber,p_subscribed=param_subscribed, p_startdate=param_start_date, p_enddate=param_end_date, orderslist=allorders, buyerslist=allbuyers, productlist=allproducts, dataproduct=productdata)

    return redirect(url_for('login'))


@application.route('/login', methods=['GET', 'POST'])
def login():
    print("login Initial")
    return render_template('index.html', msg='')


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@application.route('/profile')
def profile():
    global conn
    # Check if user is loggedin
    if 'loggedin' in session:
        userid = session['id']
        username = str(session['username']).upper()
        print("profile-username", username)
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM accounts WHERE username = '" + str(username) + "'")
        thisaccount = cursor.fetchone()
        return render_template('profile.html',  account=thisaccount)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@application.route('/register', methods=['GET', 'POST'])
def register():
    global conn
    # Output message if something goes wrong...
    msg = ''
    print("xx request.form", str(request.form))
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        conn, cursor = get_active_connection(conn)
        cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id int(11) NOT NULL AUTO_INCREMENT,username varchar(50) NOT NULL,password varchar(255) NOT NULL,email varchar(100) NOT NULL,creationdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY (id));")
        conn.commit()
        cursor.execute("SELECT * FROM accounts WHERE username = '" + str(username) + "'")
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            conn, cursor = get_active_connection(conn)
            print("registration credentials: ", username, password, email)
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO accounts (username, password, email ) VALUES ('" + str(username) + "', '" + str(password) + "', '" + str(email) + "')")
            conn.commit()
            msg = 'You have successfully registered!'
            conn, cursor = get_active_connection(conn)
            cursor.execute("SELECT * FROM accounts WHERE username = '" + str(username) + "'")
            thisaccount = cursor.fetchone()
            session['id'] = thisaccount['id']
            userid = thisaccount['id']
            print("registered credentials: ", username, password, userid)
            return render_template('login.html', userid=userid, username=username, applicationid=1, dragid=0, editionstate=0, dragmetres=1)

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@application.route('/proceed/<int:productid>/<orderno>/<userguid>', methods=['GET', 'POST'])
def proceed(productid=-1, orderno='', userguid=''):
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    tel = request.form['tel']
    print("proceed: ", fname, lname, email, userguid)
    if len(fname) > 0 and len(lname) > 0 and len(email) > 0:
        userguid = save_user_account(fname, lname, email, tel)
        setnavigation_ids(productid, orderno, userguid, fname, lname, email, tel)
        return render_template('proceed.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid, orderno=orderno)
    else:
        return redirect(url_for('login'))


@application.route('/products/<int:productid>/<orderno>', methods=['GET', 'POST'])
def products(productid=-1, orderno='', userguid=''):
    global conn
    in_productid, in_orderno, fname, lname, email, tel, in_userguid = get_navigation_ids()
    print("productid: ", productid)
    conn, cursor = get_active_connection(conn)
    cursor.execute("SELECT * FROM products WHERE is_deleted='0' ORDER BY prod_id ASC limit 3;")
    allproducts = cursor.fetchall()
    if cursor.rowcount > 0:
        setnavigation_ids(productid, orderno, in_userguid, fname, lname, email, tel)
        return render_template('products.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid,orderno=orderno, products=allproducts)
    return render_template('home.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid, orderno=orderno)


@application.route('/ordernumber/<int:productid>/<orderno>', methods=['GET', 'POST'])
def ordernumber(productid=-1, orderno='', userguid=''):
    global conn
    in_productid, in_orderno, fname, lname, email, tel, in_userguid = get_navigation_ids()
    print("ordernumber-productid: ", productid)
    if productid > 0:
        conn, cursor = get_active_connection(conn)
        cursor.execute("SELECT * FROM products WHERE prod_id='" + str(productid) + "';")
        productdata = cursor.fetchone()
        if cursor.rowcount > 0:
            product_image = productdata['image']
            print("selected-product: ", productid, product_image, in_userguid)
            sql = "UPDATE user_reviews set Image='" + str(product_image) + "', Product_Id='" + str(productid) + "' WHERE Code='" + str(in_userguid) + "'"
            cursor.execute(sql)
            conn.commit()
        setnavigation_ids(productid, orderno, in_userguid, fname, lname, email, tel)
        return render_template('ordernumber.html', fname=fname, lname=lname, email=email,  tel=tel, productid=productid, orderno=orderno)
    return redirect(url_for('login'))

@application.route('/updateorderinfo', methods=['POST'])
def updateorderinfo():
    global conn
    productid, orderno, fname, lname, email, tel, userguid = get_navigation_ids()
    if request.method == 'POST':
        orderid = '0'
        print("0updateorderinfo: ", productid, fname, lname, email, tel, userguid)
        data = dict(request.form)
        if 'orderid' in data:
            orderid = request.form.get('orderid')
        print("1updateorderinfo: ", str(orderid), "len-orderid", len(str(orderid)), str(fname), str(lname), str(email))
        if len(str(orderid)) > 16 and len(str(fname)) > 0 and len(str(lname)) > 0 and len(str(email)) > 0:
            print("2updateorderinfo: ", orderid, fname, lname, email, tel)
            status_code, msg_text, theguid, order_sh_buyer_dataset = save_order_number(str(orderid), str(userguid))
            print("3updateorderinfo: ", status_code, theguid, msg_text, str(order_sh_buyer_dataset))
            if not re.search("0",status_code):
                return render_template('warning.html', productid=productid, orderno=orderid, status_code=status_code, info_text=msg_text)
            else:
                if productid > 0:
                    conn, cursor = get_active_connection(conn)
                    cursor.execute("SELECT * FROM amazonorders WHERE AmazonOrderId='" + str(orderid) + "';")
                    productdata = cursor.fetchone()
                setnavigation_ids(productid, orderno, theguid, fname, lname, email, tel)
                return render_template('satisfied.html', productid=productid, orderno=orderid, product=productdata)
    return redirect(url_for('login'))

@application.route('/savereview', methods=['POST'])
def savereview():
    productid, orderno, fname, lname, email, tel, userguid = get_navigation_ids()
    if request.method == 'POST':
        print("savereview: ", productid, orderno, fname, lname, email, tel, userguid)
        data = dict(request.form)
        selector = ''
        selector1 = ''
        if 'selector' in data:
            selector = request.form.get('selector')
        if 'selector1' in data:
            selector1 = request.form.get('selector1')
        if 'rev_comment' in data:
            rev_comment = request.form.get('rev_comment')
        print("savereview: ", str(selector),str(selector1), str(rev_comment), orderno, userguid)
        if len(str(userguid)) >= 16 and len(str(selector)) > 0 and len(str(selector1)) > 0:
            print("XXsavereview: ", orderno, fname, lname, email, tel)
            session['continue_review_comment'] = rev_comment;
            the_userguid = save_user_reviews(str(userguid), str(selector),str(selector1), str(rev_comment))
            return render_template('continue.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid, orderno=orderno, userguid=userguid, comment=rev_comment, reviewcount=reviewcount, msg_info='')
    return redirect(url_for('login'))

@application.route('/amazonreview')
def amazonreview():
    global reviewcount
    reviewcount += 1
    print("amazonreview", reviewcount)
    return redirect("https://urlgeni.us/amazon/l7Wz")

@application.route('/address/<int:productid>/<orderno>/<userguid>', methods=['GET', 'POST'])
def address(productid=-1, orderno='', userguid='', reviewcomment=''):
    global conn
    in_productid, in_orderno, fname, lname, email, tel, in_userguid = get_navigation_ids()
    print("address-productid: ", in_userguid, "reviewcount: ", reviewcount)
    if reviewcount <=0:
        review_comment = reviewcomment
        msg_info = "Please Share You Experience Before Continuing..."
        if 'continue_review_comment' in session:
            review_comment = session['continue_review_comment'];
        return render_template('continue.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid,
                               orderno=orderno, userguid=userguid, comment=review_comment, reviewcount=reviewcount, msg_info=msg_info)
    conn, cursor = get_active_connection(conn)
    sql = "SELECT * FROM user_reviews WHERE Code='" + str(in_userguid) + "'"
    print("address-productid: ", sql)
    cursor.execute(sql)
    userdata = cursor.fetchone()
    if cursor.rowcount > 0:
        setnavigation_ids(productid, orderno, in_userguid, fname, lname, email, tel)
        print("address-buyername: ", userdata['Buyer_Name'])
        return render_template('address.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid,orderno=orderno, useraccount=userdata)
    return render_template('home.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid, orderno=orderno)

@application.route('/saveaddress', methods=['POST'])
def saveaddress():
    global conn
    productid, orderno, fname, lname, email, tel, userguid = get_navigation_ids()
    if request.method == 'POST':
        print("saveaddress: ", productid, orderno, fname, lname, email, tel, userguid)
        data = dict(request.form)
        selector = ''
        selector1 = ''
        if 'selector' in data:
            selector = request.form.get('selector')
        if 'selector1' in data:
            selector1 = request.form.get('selector1')
        if 'rev_comment' in data:
            rev_comment = request.form.get('rev_comment')
        print("saveaddress: ", str(selector), str(selector1), str(rev_comment), orderno, userguid)
        if len(str(userguid)) >= 16 and len(str(selector)) > 0 and len(str(selector1)) > 0:
            print("saveaddress: ", orderno, fname, lname, email, tel)
            session['continue_review_comment'] = rev_comment;
            the_userguid = save_user_reviews(str(userguid), str(selector), str(selector1), str(rev_comment))
            return render_template('continue.html', fname=fname, lname=lname, email=email, tel=tel, productid=productid,
                                   orderno=orderno, userguid=userguid, comment=rev_comment, reviewcount=reviewcount, msg_info='')
    return redirect(url_for('login'))

@application.route('/updateshipping', methods=['POST'])
def updateshipping():
    global conn
    in_productid, in_orderno, fname, lname, email, tel, in_userguid = get_navigation_ids()
    print("updateshipping-productid: ", in_userguid)
    if request.method == 'POST':
        user_address = '2'
        data = dict(request.form)
        if 'ship_fname' in data:
            ship_fname = request.form.get('ship_fname')
        if 'ship_addr1' in data:
            ship_addr1 = request.form.get('ship_addr1')
        if 'ship_addr2' in data:
            ship_addr2 = request.form.get('ship_addr2')
        if 'ship_city' in data:
            ship_city = request.form.get('ship_city')
        if 'ship_state' in data:
            ship_state = request.form.get('ship_state')
        if 'ship_country' in data:
            ship_country = request.form.get('ship_country')
        if 'ship_zip' in data:
            ship_zip = request.form.get('ship_zip')
        if 'user_address' in data:
            user_address = request.form.get('user_address')
        print("updateshipping-ship_fname: ", ship_fname, ship_addr1, ship_addr2, ship_city, ship_state, ship_country, ship_zip, " address?:", user_address)
        if (len(ship_city) > 0 and len(ship_country) > 0) or (len(user_address) > 0 and user_address == '1'):
            setnavigation_ids(in_productid, in_orderno, in_userguid, fname, lname, email, tel)
            print("updateshipping-buyername: ", ship_city, ship_country)
            the_userguid = save_user_address(in_userguid, ship_addr1, ship_addr2, ship_city, ship_state, ship_country, ship_zip)
            return render_template('home.html', fname=fname, lname=lname, email=email, tel=tel, productid=in_productid,orderno=in_orderno)
    return render_template('home.html', fname=fname, lname=lname, email=email, tel=tel, productid=in_productid, orderno=in_orderno)

@application.route('/searchdata/<int:productid>/<searchtype>/<p_ordernumber>/<p_subscribed>/<p_startdate>/<p_enddate>', methods=['GET', 'POST'])
def searchdata(productid=0, searchtype='Orders', p_ordernumber='0', p_subscribed='2', p_startdate='0', p_enddate='0'):
    global conn
    if not p_ordernumber or len(p_ordernumber) <= 0:
        p_ordernumber = '0'
    if not p_subscribed or len(p_subscribed) <= 0:
        p_subscribed = '2'
    if not p_startdate or len(p_startdate) <= 0:
        p_startdate = '0'
    if not p_enddate or len(p_enddate) <= 0:
        p_enddate = '0'
    searchtype = str(searchtype).strip()
    print("searchdata: ", searchtype)
    session['searchtype'] = searchtype
    if productid > 0:
        session['productid'] = productid
    session['p_ordernumber'] = p_ordernumber
    session['p_subscribed'] = p_subscribed
    session['p_startdate'] = p_startdate
    session['p_enddate'] = p_enddate
    print("1_searchdata param: ", p_ordernumber, p_subscribed, p_startdate, p_enddate)
    order_subscribed = '2'
    order_search = '0'
    start_date = '0'
    end_date = '0'
    file_export = '2'
    allproducts = {}
    productdata = {}
    allbuyers = {}
    allorders = {}
    if 'loggedin' in session :
        userid = session['id']
        username = str(session['username']).upper()
        if request.method == 'POST':
            order_subscribed = '2'
            order_search = '0'
            start_date = '0'
            end_date = '0'
            file_export = '2'
            data = dict(request.form)
            if 'order_search' in data:
                order_search = request.form.get('order_search')
                if len(str(order_search)) > 0:
                    p_ordernumber = order_search
            if 'order_subscribed' in data:
                order_subscribed = request.form.get('order_subscribed')
                order_subscribed = str(order_subscribed).strip()
                if len(str(order_subscribed)) > 0:
                    p_subscribed = order_subscribed
            if 'start_date' in data:
                start_date = request.form.get('start_date')
                if len(str(start_date)) > 0:
                    p_startdate = start_date
            if 'end_date' in data:
                end_date = request.form.get('end_date')
                if len(str(end_date)) > 0:
                    p_enddate = end_date
            if 'file_export' in data:
                file_export = request.form.get('file_export')
            print("1_searchdata form: ", order_search, order_subscribed, start_date, end_date)
        if re.search("Products", searchtype):
            print("products form: ", productid)
            conn, cursor = get_active_connection(conn)
            if productid <= 0:
                rql = "SELECT * FROM products ORDER BY prod_id DESC LIMIT 15;"
                cursor.execute(rql)
                allproducts = cursor.fetchall()
                print("products all: ", productid, str(allproducts))
            if productid > 0:
                rql = "SELECT * FROM products WHERE prod_id='" + str(productid) + "' LIMIT 15;"
                cursor.execute(rql)
                productdata = cursor.fetchone()
                print("products one: ", productid, str(productdata))
        else:
            if len(str(order_subscribed)) <= 0 and len(str(p_subscribed)) > 0:
                order_subscribed = p_subscribed
            if len(str(order_search)) <= 0 and len(str(p_ordernumber)) > 1:
                order_search = p_ordernumber
            if len(str(start_date)) <= 0 and len(str(p_startdate)) > 6:
                start_date = p_startdate
            if len(str(end_date)) <= 0 and len(str(p_enddate)) > 6:
                end_date = p_enddate
            print("2_searchdata param: ", p_ordernumber, p_subscribed, p_startdate, p_enddate)
            if searchtype == 'Orders':
                sql_statement = "SELECT * FROM amazonorders"
            if searchtype == 'Buyers':
                sql_statement = "SELECT * FROM user_reviews"
            order_subscribed_flag = False
            order_search_flag = False
            if str(order_subscribed) != '2' and len(str(order_subscribed)) > 0:
                order_subscribed_flag = True
            if str(order_search) != '0' and len(str(order_search)) > 0:
                order_search_flag = True
            if order_subscribed_flag or order_search_flag or len(str(start_date)) > 6 or len(str(end_date)) > 6:
                sql_statement += " WHERE"
                if order_subscribed_flag:
                    sql_statement += " Is_Subscribed = '" + str(order_subscribed) + "'"
                if order_search_flag:
                    if order_subscribed_flag:
                        sql_statement += " and"
                    sql_statement += " AmazonOrderId like '%" + str(order_search) + "%'"
                if re.search("Buyers", searchtype) and len(str(start_date)) > 6 and len(str(end_date)) > 6:
                    if order_subscribed_flag or order_search_flag:
                        sql_statement += " and"
                    sql_statement += " Subscribed_On BETWEEN '" + str(start_date) + "' and '" + str(end_date) + "'"
                if re.search("Orders", searchtype) and len(str(start_date)) > 6 and len(str(end_date)) > 6:
                    if re.search("Orders", searchtype) or order_subscribed_flag or order_search_flag:
                        sql_statement += " and"
                    sql_statement += " PurchaseDate BETWEEN '" + str(start_date) + "' and '" + str(end_date) + "'"
                sql_statement += " order by id desc LIMIT 15"
                print("searchdata-sql: ", searchtype, order_search_flag, order_subscribed_flag, sql_statement)
                allbuyers = {}
                allorders = {}
                row_count = 0
                conn, cursor = get_active_connection(conn)
                cursor.execute(sql_statement)
                if re.search("Buyers", searchtype):
                    allbuyers = cursor.fetchall()
                    row_count = cursor.rowcount
                if re.search("Orders", searchtype):
                    allorders = cursor.fetchall()
                    row_count = cursor.rowcount
                today = date.today()
                now = datetime.now()
                today_day = today.strftime("%Y-%m-%d")
                today_time = now.strftime("%H%M%S")
                filename = str(searchtype) + "_" + str(today_day) + "_" + str(today_time) + ".csv"
                print("file_export: ", str(file_export), row_count)
                if file_export == '1' and row_count > 0:
                    conn, cursor = get_active_connection(conn)
                    cursor.execute(sql_statement)
                    allbuyers = cursor.fetchall()
                    output = io.StringIO()
                    writer = csv.writer(output)
                    if re.search("Buyers", searchtype):
                        line = ['AmazonOrderId', 'Product_Id', 'Buyer_Name', 'Subscribed_On', 'Email', 'Tel', 'ShippingAddress_Line_1', 'ShippingAddress_Line_2', 'ShippingAddress_City', 'ShippingAddress_PostalCode', 'ShippingAddress_StateOrRegion', 'ShippingAddress_CountryCode', 'Satisfied', 'Buy_Product', 'Commentary']
                        writer.writerow(line)
                        for row in allbuyers:
                            datarow = []
                            for linerow in line:
                                datarow.append("'" + str(row[linerow]) + "', '")
                                print("datarow: ", str(datarow))
                            writer.writerow(datarow)
                        output.seek(0)
                        return Response(output, mimetype="text/csv",
                                        headers={"Content-Disposition": "attachment;filename=" + str(filename)})
                    if re.search("Orders", searchtype):
                        conn, cursor = get_active_connection(conn)
                        cursor.execute(sql_statement)
                        allorders = cursor.fetchall()
                        line = ['AmazonOrderId', 'PurchaseDate', 'BuyerEmail', 'OrderTotal_Amount', 'OrderTotal_CurrencyCode', 'PaymentMethod', 'Is_Subscribed']
                        writer.writerow(line)
                        for row in allorders:
                            datarow = []
                            for linerow in line:
                                datarow.append("'" + str(row[linerow]) + "', '")
                                print("datarow: ", str(datarow))
                            writer.writerow(datarow)
                        output.seek(0)
                        return Response(output, mimetype="text/csv",
                                        headers={"Content-Disposition": "attachment;filename=" + str(filename)})
            return render_template('admin.html', userid=userid, username=username, searchtype=searchtype,
                                               productid=productid, p_ordernumber=p_ordernumber,
                                               p_subscribed=p_subscribed, p_startdate=p_startdate, p_enddate=p_enddate,
                                               buyerslist=allbuyers, orderslist=allorders, productslist=allproducts,
                                               dataproduct=productdata)
    return render_template('admin.html', userid=userid, username=username, searchtype=searchtype,
                                       productid=productid, p_ordernumber=p_ordernumber, p_subscribed=p_subscribed,
                                       p_startdate=p_startdate, p_enddate=p_enddate, buyerslist=allbuyers,
                                       orderslist=allorders, productslist=allproducts, dataproduct=productdata)


if __name__ =='__main__':
    conn, cursor = get_active_connection(conn)
    application.debug = True
    application.run()
