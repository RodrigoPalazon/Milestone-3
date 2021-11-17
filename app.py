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


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/get_products")
def get_products():
    products = list(mongo.db.products.find())
    return render_template("products.html", products=products)
  

@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    products = list(mongo.db.products.find({"$text": {"$search": query}}))
    return render_template("products.html", products=products)


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
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


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


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    products = list(mongo.db.products.find())
    if session["user"]:    
        return render_template("profile.html", username=username, products=products)

    return render_template("login")


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        is_new = "on" if request.form.get("is_new") else "off"
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
        mongo.db.products.insert_one(product)
        flash("Book Successfully Added")
        return redirect(url_for("get_products"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_product.html", categories=categories)


@app.route("/edit_product/<product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if request.method == "POST":
        is_new = "on" if request.form.get("is_new") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "product_name": request.form.get("product_name"),
            "product_description": request.form.get("product_description"),
            "is_new": is_new,
            "release_date": request.form.get("release_date"),
            "created_by": session["user"]
        }
        mongo.db.products.update({"_id": ObjectId(product_id)}, submit)
        flash("Book Successfully Updated")

    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_product.html", product=product, categories=categories)


@app.route("/delete_product/<product_id>")
def delete_product(product_id):
    mongo.db.products.remove({"_id": ObjectId(product_id)})
    flash("Book Successfully Deleted")
    return redirect(url_for("get_products"))


@app.route("/get_categories")    
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))
        
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)




