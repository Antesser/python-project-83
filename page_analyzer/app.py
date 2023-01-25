from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages  # noqa(E501)
from dotenv import load_dotenv
from datetime import datetime
from psycopg2.extras import RealDictCursor
from urllib.parse import urlsplit
import psycopg2
import os
import validators


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


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
    messages = get_flashed_messages(with_categories=True)
    print(messages)
    return render_template("index.html", messages=messages)


@app.route("/urls", methods=["GET", "POST"])
def urls():
    if request.method == "GET":
        with psycopg2.connect(url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM urls")
                list_of_urls = cursor.fetchall()
                return render_template("urls.html", list_of_urls=list_of_urls)
    elif request.method == "POST":
        form = request.form["url"]
        input = urlsplit(form).scheme + "://"\
            + urlsplit(form).netloc
        if validators.url(input):
            current_date = datetime.now()
            with psycopg2.connect(url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, name FROM urls WHERE\
                                      name = %s", (input,))
                    list_of_names = cursor.fetchall()
                    if list_of_names:
                        for i in list_of_names:
                            id = i[0]
                            flash("Страница уже существует", "warning")
                            return redirect(url_for("url_id", id=id))
                    else:
                        cursor.execute(
                            "INSERT INTO urls (name, created_at)\
                                        VALUES (%s,%s)",
                            (input, current_date),
                        )
                        cursor.execute(
                            "SELECT id FROM urls WHERE created_at = %s",
                            (current_date,)
                        )
                        id = cursor.fetchone()[0]
                        flash("Страница успешно добавлена", "success")
                        return redirect(url_for("url_id", id=id))
        else:
            flash("Некорректный URL", "error")
            return redirect(url_for("index"))


@app.route("/urls/<id>", methods=["GET", "POST"])
def url_id(id):
    messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT name, created_at FROM urls WHERE id = %s",
                           (id,))
            result_urls = cursor.fetchall()
            for i in result_urls:
                fetched_url = i.get("name")
                date = i.get("created_at").strftime("%Y-%m-%d")
        return render_template("url.html", url=fetched_url, date=date, id=id,
                               messages=messages)
