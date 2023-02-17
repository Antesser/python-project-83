from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages  # noqa(E501)
from dotenv import load_dotenv
from datetime import datetime
from psycopg2.extras import RealDictCursor, NamedTupleCursor
from .validator import validate
from bs4 import BeautifulSoup
import psycopg2
import os
import validators
import requests


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


URL = os.getenv("DATABASE_URL")


with open("database.sql", "r") as init_script:
    table_query = init_script.read()

try:
    conn = psycopg2.connect(URL)
    print("Подключение установлено")
    with conn.cursor() as cursor:
        cursor.execute(table_query)
except (requests.exceptions.ConnectionError(), psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if conn:
        conn.commit()
        conn.close()


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.route("/urls", methods=["GET"])
def urls_get():
    with psycopg2.connect(URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("""SELECT a.id, a.name,
                            b.created_at, b.status_code FROM urls a
                              LEFT JOIN (SELECT date(created_at)
                                  AS created_at, status_code, url_id
                                    FROM url_checks WHERE id IN
                                      (SELECT MAX(id) FROM url_checks
                                        GROUP BY url_id) ORDER BY url_id)
                                          AS b ON a.id=b.url_id
                                            ORDER BY a.id DESC""")
            answer = cursor.fetchall()
            return render_template("urls.html", answer=answer)


@app.route("/urls", methods=["POST"])
def urls_post():
    form = request.form["url"]
    input = validate(form)
    if not validators.url(input):
        flash("Некорректный URL", "danger")
        messages = get_flashed_messages(with_categories=True)
        return render_template("index.html", messages=messages), 422

    current_date = datetime.now()
    with psycopg2.connect(URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT id, name FROM urls WHERE
                                name = %s""", (input,))
            list_of_names = cursor.fetchone()
            if list_of_names:
                id = list_of_names[0]
                flash("Страница уже существует", "warning")
                return redirect(url_for("url_id", id=id))
            else:
                cursor.execute(
                    """INSERT INTO urls (name, created_at)
                                VALUES (%s,%s) RETURNING id""",
                    (input, current_date),
                )
                id = cursor.fetchone()[0]
                flash("Страница успешно добавлена", "success")
                return redirect(url_for("url_id", id=id))


@app.route("/urls/<id>/checks", methods=["POST"])
def url_id_check(id):
    with psycopg2.connect(URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """SELECT name FROM urls WHERE id=%s""",
                (id,),
            )
            url_to_check = cursor.fetchone().get("name")
            try:
                res = requests.get(url_to_check)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                if soup.find(["h1"]) is not None:
                    h1 = ((soup.find(["h1"])).text)
                else:
                    h1 = ""
                if soup.find(["title"]) is not None:
                    title = ((soup.find(["title"])).text)
                else:
                    title = ""
                if soup.find("meta",
                             attrs={"name": "description"}) is not None:
                    description = (soup.find("meta",
                                             attrs={"name": "description"})
                                   .attrs["content"])
                else:
                    description = ""
            except requests.exceptions.RequestException:
                flash("Произошла ошибка при проверке", "danger")
                return redirect(url_for("url_id", id=id))
            cursor.execute(
                """INSERT INTO url_checks (url_id, created_at, status_code, h1,
                        title, description)
                            VALUES (%s,now(),%s,%s,%s,%s)""",
                (id, res.status_code, h1, title, description),
            )
            flash("Страница успешно проверена", "success")
            return redirect(url_for("url_id", id=id))


@app.route("/urls/<id>", methods=["GET"])
def url_id(id):
    messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT name, date(created_at)
                           FROM urls WHERE id = %s""", (id,))
            result_urls = cursor.fetchall()
            cursor.execute("""SELECT id, status_code, date(created_at), h1,
                           title, description FROM url_checks
                            WHERE url_id = %s ORDER BY id DESC""", (id,))
            test_results = cursor.fetchall()
        return render_template("url.html", id=id, result_urls=result_urls,
                               messages=messages, test_results=test_results)
