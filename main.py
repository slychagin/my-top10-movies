from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# The movie data base API (https://www.themoviedb.org/)
MOVIE_DB_API_KEY = "399df4f8dfcef1cc5db8d2a418be9133"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_DETAILS_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/original"

# Create FlaskApp with Bootstrap
app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
Bootstrap(app)

# Create Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top_movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Create table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.Text, nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    movie_rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    movie_review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating.desc()).all()
    for movie in all_movies:
        movie.ranking = all_movies.index(movie) + 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = float(form.movie_rating.data)
        movie_to_update.review = form.movie_review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie_to_update, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def find_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        title = form.movie_title.data
        response = requests.get(url=MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": title})
        response.raise_for_status()
        options = response.json()["results"]
        return render_template("select.html", movies=options)
    return render_template("add.html", form=form)


@app.route("/adding", methods=["GET", "POST"])
def add_movie():
    if request.method == "GET":
        movie_id = request.args.get("id")
        response = requests.get(url=f"{MOVIE_DB_DETAILS_URL}/{movie_id}", params={"api_key": MOVIE_DB_API_KEY})
        response.raise_for_status()
        movie_data = response.json()
        new_movie = Movie(
            title=movie_data["title"],
            year=movie_data["release_date"][0:4],
            description=movie_data["overview"],
            img_url=f"{MOVIE_DB_IMAGE_URL}{movie_data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
