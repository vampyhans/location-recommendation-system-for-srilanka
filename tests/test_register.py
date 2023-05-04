import mysql.connector
from flask import Flask, render_template
import pandas as pd
import pytest
import os
from functools import wraps
import sys

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY

    with app.test_client() as client:
        yield client

def test_index(client):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="#Root69toor",
        database="locations"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT Type, Name, Grade, District, Reviewer_Nationality, Lat, Lon FROM locations")
    myresult = mycursor.fetchall()

    hf = pd.DataFrame(myresult, columns=['Type', 'Name', 'Grade', 'District', 'Reviewer_Nationality', 'Lat', 'Lon'])

    response = client.get('/')
    assert response.status_code == 200
    assert b'Get Recommendations' in response.data
    assert set(hf['Type'].unique().tolist()) == set(['Restaurants'])
    assert set(hf['Grade'].unique().tolist()) == set(['A'])
    assert set(hf['District'].unique().tolist()) == set(['Colombo'])
    assert set(hf['Reviewer_Nationality'].unique().tolist()) == set(['Russia'])
