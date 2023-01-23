from flask import Flask, render_template, request
from dotenv import load_dotenv
import psycopg2
import os


load_dotenv()

app = Flask(__name__)

url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(url)
    print("Подключение установлено")
    with conn.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS urls (id bigint PRIMARY KEY GENERATED\
                ALWAYS AS IDENTITY, name varchar(255), created_at timestamp)"
        )
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if conn:
        cursor.close()
        conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET", "POST"])
def urls():
    if request.method == "POST":
        email = request.form["url"]
        return render_template("url.html", email=email)
    else:
        return render_template("urls.html")
