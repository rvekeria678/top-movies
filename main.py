from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import requests, os

#-----Constants-----#
DATABASE_URL = 'sqlite:///movies.db'
TMDB_URL = 'https://api.themoviedb.org/3/search/movie'
TMDB_DETAILS_URL = 'https://api.themoviedb.org/3/movie'
TMDB_IMG_EP = 'https://image.tmdb.org/t/p/w185'
load_dotenv()
#-----Aux-----#
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
class Base(DeclarativeBase):pass
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(model_class=Base)
db.init_app(app)
#-----Models-----#
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String, nullable=False)
    img_url: Mapped[str] = mapped_column(String, nullable=False)
#-----Forms-----#
class EditForm(FlaskForm):
    rating = FloatField(label="Your Rating out of 10 e.g. 7.5",
                          validators=[DataRequired()])
    review = StringField(label="Your Review",
                         validators=[DataRequired()])
    sbmt = SubmitField(label="Done")
class AddForm(FlaskForm):
    movie_title = StringField(label="Movie Title")
    sbmt = SubmitField(label="Add Movie")
#-----Create DB-----#
with app.app_context():
    db.create_all()
#-----Routes-----#
@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    
    rank = len(all_movies)

    for movie in all_movies:
        movie.ranking = rank
        rank -= 1
        db.session.commit()

    return render_template("index.html", movies=all_movies)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    edit_form = EditForm()
    if edit_form.validate_on_submit() and request.method == 'POST':
        movie_id = request.args.get('id')
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.review = edit_form.review.data
        movie_to_update.rating = edit_form.rating.data
        db.session.commit()
        return redirect(url_for("home"))
    
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template('edit.html', movie=movie_selected, form=edit_form)

@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))

@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        return redirect(url_for('select', query=add_form.movie_title.data))
    return render_template('add.html', form=add_form)

@app.route('/select/<query>')
def select(query):
    tmdb_params = {
        "query": query,
        "api_key": os.environ.get('TMDB_API_KEY'),
    }
    response = requests.get(url=TMDB_URL, params=tmdb_params)
    results = response.json()
    return render_template('select.html', data=results)

@app.route('/getfilm')
def get_film():
    q_id = request.args.get('film_id')
    tmdb_params = {
        "api_key": os.environ.get('TMDB_API_KEY')
    }
    response = requests.get(url=f"{TMDB_DETAILS_URL}/{q_id}", params=tmdb_params)
    result = response.json()
    print(result)

    new_movie = Movie(
        id = result['id'],
        title = result['title'],
        year = result['release_date'].split('-')[0],
        description = result['overview'],
        rating = 0,
        ranking = 0,
        review = "None",
        img_url = f"{TMDB_IMG_EP}{result['poster_path']}"
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=result['id']))

#-----Server Driver-----#
if __name__ == '__main__':
    app.run(debug=True)