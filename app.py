from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import numpy as np
import os
from forms import RegistrationForm, LoginForm
from flask_bcrypt import Bcrypt
from functools import wraps
from mysql.connector.errors import Error
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors
import mysql.connector
import sys
print(sys.path)

app = Flask(__name__)

# Load dataset
# Load dataset from MySQL database

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="#Root69toor",
  database="locations"
)

mycursor = mydb.cursor()

mycursor.execute("SELECT Type, Name, Grade, District, Reviewer_Nationality, Lat, Lon FROM locations")

myresult = mycursor.fetchall()

bcrypt = Bcrypt(app)

df = pd.DataFrame(myresult, columns=['Type', 'Name', 'Grade', 'District', 'Reviewer_Nationality', 'Lat', 'Lon'])

hf = pd.DataFrame(myresult, columns=['Type', 'Name', 'Grade', 'District', 'Reviewer_Nationality', 'Lat', 'Lon'])

# Drop unnecessary columns
df = df[['Type', 'Name', 'Grade', 'District', 'Reviewer_Nationality', 'Lat', 'Lon']]

# Encode categorical variables
le_type = LabelEncoder()
le_type.fit(df['Type'])
df['Type'] = le_type.transform(df['Type'])

le_grade = LabelEncoder()
le_grade.fit(df['Grade'])
df['Grade'] = le_grade.transform(df['Grade'])

le_district = LabelEncoder()
le_district.fit(df['District'])
df['District'] = le_district.transform(df['District'])

le_nationality = LabelEncoder()
le_nationality.fit(df['Reviewer_Nationality'])
df['Reviewer_Nationality'] = le_nationality.transform(df['Reviewer_Nationality'])

# Drop missing values
df = df.dropna()

# Compute user-item matrix
user_item = pd.pivot_table(df, values='Grade', index='Reviewer_Nationality', columns='Name', fill_value=0)

# Train the k-NN model
knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=5)
knn.fit(user_item)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():

    input_types = hf['Type'].unique().tolist()
    input_grades = hf['Grade'].unique().tolist()
    input_districts = hf['District'].unique().tolist()
    reviewer_nationalities = hf['Reviewer_Nationality'].unique().tolist()

    return render_template('get-recommendations.html', input_types=input_types, input_grades=input_grades, input_districts=input_districts, reviewer_nationalities=reviewer_nationalities)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    try:
        if form.validate_on_submit():
            username = form.username.data
            email = form.email.data
            password = form.password.data
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
            mydb.commit()
            mycursor.close()
            return redirect(url_for('index'))
        return render_template('register.html', form=form)
    except Error as e:
        # Handle the exception and display an error message to the user
        return render_template('error.html', error=str(e))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    try:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            mycursor = mydb.cursor()
            mycursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = mycursor.fetchone()
            mycursor.close()
            if user and bcrypt.check_password_hash(user[3], password):
                session['email'] = user[1]
                return redirect(url_for('index'))
            else:
                return render_template('login.html', form=form, error='Invalid email or password')
        return render_template('login.html', form=form)
    except Error as e:
        # Handle the exception and display an error message to the user
        return render_template('error.html', error=str(e))



@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/recommend', methods=['POST'])
@login_required
def recommend():
    try:
        # Get user inputs
        input_type = le_type.transform([request.form['input_type']])[0]
        input_district = le_district.transform([request.form['input_district']])[0]
        input_grade = le_grade.transform([request.form['input_grade']])[0]
        input_nationality = le_nationality.transform([request.form['input_nationality']])[0]

        # Filter DataFrame based on user_item.index
        df_filtered = df.loc[user_item.index]

        # Create user vector
        user_vector = np.zeros(len(df['Name'].unique()))
        valid_rows = (df_filtered['Type'] == input_type) & (df_filtered['District'] == input_district) & (df_filtered['Grade'] == input_grade) & (df_filtered['Reviewer_Nationality'] == input_nationality)
        user_vector[df_filtered.index[valid_rows]] = 1

        # Find similar users using k-NN
        user_vector = user_vector.reshape(1, -1)
        _, user_indices = knn.kneighbors(user_vector)

        # Create a boolean mask to select only valid elements of user_indices
        mask = user_indices < len(user_item)

        # Apply the mask to user_indices
        user_indices = user_indices[mask]

        # Get recommended locations
        rec_indices = np.where(user_item.iloc[user_indices[0]].mean(axis=0) > 0)[0]
        rec_names = user_item.columns[rec_indices][:5].tolist()

        # Get longitudes and latitudes of recommended locations
        rec_lats = df[df['Name'].isin(rec_names)]['Lat'].tolist()
        rec_longs = df[df['Name'].isin(rec_names)]['Lon'].tolist()
        district = hf[df['Name'].isin(rec_names)]['District'].tolist()

        return render_template('recommendations.html', top_rec_names=rec_names, rec_lats=rec_lats[0], rec_longs=rec_longs[0], district=district)

    except Exception as e:
        # Log the exception and return an error message to the user
        print(f"An error occurred: {e}")
        return render_template('error.html', error='An error occurred. Please try again later.')






if __name__ == '__main__':
    app.run(debug=True)
