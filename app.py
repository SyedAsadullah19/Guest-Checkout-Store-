from flask import Flask,redirect,url_for,render_template,request,send_from_directory,session,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os
#Make sure that flask_login and bcrypt are installed
from flask_login import login_user,logout_user,current_user,UserMixin, LoginManager, login_required
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = "sk"

###############################################################################

db = SQLAlchemy()
db.init_app(app)

class AdminUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key= True, autoincrement=True)
    uname = db.Column(db.String ,nullable = False, unique=True )
    password = db.Column(db.String ,nullable = False, unique=True )

class Product(db.Model):
    pid = db.Column(db.Integer, primary_key= True, autoincrement=True)
    pname = db.Column(db.String ,nullable = False, unique=True )
    pimage  = db.Column(db.String ,nullable = False, unique=True)
    price = db.Column(db.Integer, nullable = False)
    qty = db.Column(db.Integer, nullable = False)
    about = db.Column(db.String)

class Order(db.Model, UserMixin):
    oid = db.Column(db.Integer, primary_key= True, autoincrement=True)
    oname = db.Column(db.String ,nullable = False )
    price = db.Column(db.Integer, nullable = False)
    qty = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String ,nullable = False)
    address = db.Column(db.String ,nullable = False)
    phone = db.Column(db.Integer, nullable = False)
    date =  db.Column(db.Date, default=date.today())
    status = db.Column(db.String, default="pending")

with app.app_context():
    db.create_all()   
###############################################################################
#Position all of this after the db and app have been initialised
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='dashboard'
@login_manager.user_loader
def user_loader(user_id):
    return AdminUser.query.get(user_id)


#Home Page 

@app.route('/',methods=['GET','POST'])
def home():
    data = db.session.query(Product).all()
    if 'cart' not in session:
        session['cart']=[]
    if request.method=='POST':
        # Handle POST Request here
        return render_template('index.html',data=data)
    return render_template('index.html',data=data)


# Add to cart
@app.route("/add/user/cart/<int:id>")
def user_ad(id):
    cart = session.get('cart',[])
    L=[]
    L.append(id)
    L.append(1)
    L1=[]
    for i in cart:
        L1.append(i[0])
    if id in L1:
        flash("This product already in cart please choose a different product !!!")
        return redirect(url_for("home"))
    elif id not in L1:
        cart.append(L)
    session['cart']=cart
    print(session['cart'])
    return redirect('/')


#Mycart 
@app.route("/user/cart/")
def user_crt():
    cart=session.get('cart',[])
    prolist=[]
    if (cart):
        for i in cart:
            id = i[0]
            qt = i[1]
            det=db.session.query(Product).filter(Product.pid==id).first()
            name = det.pname
            price = det.price
            qty=det.qty
            l=[id,qt,name,price,qty]
            prolist.append(l)
    count=len(prolist)
    cost=0
    for i in prolist:
        per = i[1]*i[3]
        cost+=per
    return render_template("cart.html", list=prolist, count=count, cost=cost)

#Increase Product
@app.route("/inc/product/<int:id>/<int:qty>")
def inc(id,qty):
    cart = session.get('cart',[])
    data = db.session.query(Product).filter(Product.pid==id).first()
    qtyn =qty+1
    if qtyn>data.qty:
        return redirect(url_for("user_crt"))
    elif qtyn<=data.qty:
        cart = session.get('cart',[])
        for i in range(len(cart)):
            if cart[i][0]==id:
                cart[i][1]=qtyn
                session['cart']=cart
        return redirect(url_for("user_crt"))
    return redirect(url_for("user_crt"))
#Decrease Product 
@app.route("/dec/product/<int:id>/<int:qty>")
def dec(id,qty):
    cart = session.get('cart',[])
    qtyn =qty-1
    if qtyn<0:
        return redirect(url_for("user_crt"))
    elif qtyn>=1:
        cart = session.get('cart',[])
        for i in range(len(cart)):
            if cart[i][0]==id:
                cart[i][1]=qtyn
                session['cart']=cart
        return redirect(url_for("user_crt"))
    return redirect(url_for("user_crt"))

@app.route("/rmv/product/<int:id>/<int:qty>")
def rmv(id,qty):
    cart = session.get('cart',[])
    cart.remove([id,qty])
    session['cart']=cart
    return redirect(url_for("user_crt"))
#Login
@app.route("/user/details/", methods=['GET','POST'])
def user_det():
    if request.method == 'POST':
        if 'cart' in session:
          name= request.form.get("name")
          address= request.form.get("adres")
          phone= request.form.get("phone")
          cart= session.get('cart',[])
          if len(phone)!=10:
              return redirect('/')
          if cart != []:
              for c in cart:
                  id=c[0]
                  pro = db.session.query(Product).filter(Product.pid==id).first()
                  Data = Order(oname=pro.pname,price=pro.price,name=name, qty=c[1],address=address,phone=phone)
                  newqty = pro.qty-c[1]
                  db.session.add(Data)
                  db.session.commit()
                  pro.qty=newqty
                  db.session.commit()
                  cart = session.get('cart',[])
                  cart =[]
                  session['cart']=[]
              return render_template("thanks.html")
          return redirect('/')
    return render_template("details.html")
@app.route("/admin/login", methods=['GET','POST'])
def adminlogin():
    if request.method == 'POST':
        name = request.form.get('name')
        passw = request.form.get('passw')
        query = db.session.query(AdminUser).filter(AdminUser.password==passw).filter(AdminUser.uname==name).first()
        if query:
            login_user(query)
            return redirect('/dashboard/admin')
        return redirect('/')
    return render_template("login.html")

#Admin-Dashboard

@app.route("/dashboard/admin")
@login_required
def dashboard():
    data = db.session.query(Order).all()
    return render_template("admino.html",data=data)

#Update
@app.route("/update/order/admin/<int:id>",methods=['GET','POST'])
@login_required
def upd_or(id):
    data = db.session.query(Order).filter(Order.oid==id).first()
    if request.method=='POST':
        qty = request.form.get('qty')
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        status = request.form.get('status')
        if len(phone)!=10:
            return redirect(url_for('dashboard'))
        data.qty=qty
        data.name=name
        data.address=address
        data.phone=phone
        data.status=status
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("updo.html",data=data)



#Admin-Product 
@app.route("/product/admin")
@login_required
def product_admin():
    data= db.session.query(Product).all()
    return render_template("adminp.html",data=data)

@app.route("/show/<id>")
def imp(id):
    data=db.session.query(Product).filter(Product.pid==id).first()
    filename=data.pimage
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route("/delete/product/<int:id>")
@login_required
def del_pro(id):
    data=db.session.query(Product).filter(Product.pid==id).first()
    filename=data.pimage
    filepath=os.path.join(app.config['UPLOAD_FOLDER'],filename)
    os.remove(filepath)
    db.session.delete(data)
    db.session.commit()
    return redirect("/product/admin")
#Add-Product 
@app.route("/add/product/", methods=['GET','POST'])
@login_required
def ad_pro():
    if request.method=='POST':
        pname=request.form.get('pname')
        pimage=request.files['pimage']
        price=request.form.get('price')
        qty=request.form.get('qty')
        about=request.form.get('about')
        print(pname,price,qty,about)
        if (pimage):
            filename= pimage.filename
            pimage.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            data = Product(pname=pname,pimage=filename,price=price,qty=qty,about=about)
            db.session.add(data)
            db.session.commit()
        return redirect('/product/admin')
    return render_template("adpro.html")

@app.route("/update/product/<id>", methods=['GET','POST'])
@login_required
def up_pro(id):
    data=db.session.query(Product).filter(Product.pid==id).first()
    if request.method=='POST':
        pname=request.form.get('pname')
        price=request.form.get('price')
        qty=request.form.get('qty')
        about=request.form.get('about')
        print(pname,price,qty,about)
        if (data):
         data.pname=pname
         data.price=price
         data.qty=qty
         data.about=about
         db.session.commit()
        return redirect('/product/admin')
    return render_template("updpro.html",product=data)
@app.route("/show/info/<int:id>")
def shif(id):
    data = db.session.query(Product).filter(Product.pid==id).first()
    return render_template("aproduct.html",data=data)
if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(port=5000)