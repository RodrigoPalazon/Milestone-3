import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


# render home template
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


# display books from db
@app.route("/get_products")
def get_products():
    productsList = list(mongo.db.products.find())
    return render_template("products.html", products=productsList)
  

# search for a book in db using text query
@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    productsList = list(mongo.db.products.find({"$text": {"$search": query}}))
    return render_template("products.html", products=productsList)


# user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "type": "user"
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        session["type"] = "user"
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")

# user log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    session["type"] = existing_user["type"]
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "home"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# users profile page
@app.route("/profile", methods=["GET", "POST"])
def profile():
    # grab the session user's username from db
    if "user" in session:  
        loggedUser = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        productsList = list(mongo.db.products.find())
        return render_template("profile.html", username=loggedUser, products=productsList)

    return render_template("login.html")


# user log out
@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


#add book to db
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        is_new = "on" if request.form.get("is_new") else "off"
         # retrieve book info from form
        product = {
            "category_name": request.form.get("category_name"),
            "product_name": request.form.get("product_name"),
            "image_url": request.form.get("image_url"),
            "sales_store_url": request.form.get("sales_store_url"),
            "product_description": request.form.get("product_description"),
            "is_new": is_new,
            "release_date": request.form.get("release_date"),
            "created_by": session["user"]
        }
        # insert new book into db
        mongo.db.products.insert_one(product)
        flash("Book Successfully Added")
        return redirect(url_for("get_products"))

    categoriesList = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_product.html", categories=categoriesList)


# edit book review
@app.route("/edit_product/<product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if request.method == "POST":
        is_new = "on" if request.form.get("is_new") else "off"
        # retrieve book info from db
        product = {
            "category_name": request.form.get("category_name"),
            "product_name": request.form.get("product_name"),
            "image_url": request.form.get("image_url"),
            "sales_store_url": request.form.get("sales_store_url"),
            "product_description": request.form.get("product_description"),
            "is_new": is_new,
            "release_date": request.form.get("release_date"),
            "created_by": session["user"]
        }
        # update book info
        mongo.db.products.update({"_id": ObjectId(product_id)}, product)
        flash("Book Successfully Updated")
        return redirect(url_for("get_products"))

    productList = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    categoriesList = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_product.html", product=productList, categories=categoriesList)


# delete book review
@app.route("/delete_product/<product_id>")
def delete_product(product_id):
    mongo.db.products.remove({"_id": ObjectId(product_id)})
    flash("Book Successfully Deleted")
    return redirect(url_for("get_products"))


# admin to manage categories in db
@app.route("/get_categories")    
def get_categories():
    if session["type"] == "admin":
        categoriesList = list(mongo.db.categories.find().sort("category_name", 1))
        return render_template("categories.html", categories=categoriesList)

    return redirect(url_for("home"))


# admin to add category to categories' list db
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if session["type"] == "admin":
        if request.method == "POST":
            category = {
                "category_name": request.form.get("category_name")
            }
            mongo.db.categories.insert_one(category)
            flash("New Category Added")
            return redirect(url_for("get_categories"))

        return render_template("add_category.html")

    return redirect(url_for("home"))


# edit currently existing category in db
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if session["type"] == "admin":
        if request.method == "POST":
            submit = {
                "category_name": request.form.get("category_name")
            }
            mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
            flash("Category Successfully Updated")
            return redirect(url_for("get_categories"))
            
        category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
        return render_template("edit_category.html", category=category)

    return redirect(url_for("home"))


# delete genre from db
@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    if session["type"] == "admin":
        mongo.db.categories.remove({"_id": ObjectId(category_id)})
        flash("Category Successfully Deleted")
        return redirect(url_for("get_categories"))
    
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)




