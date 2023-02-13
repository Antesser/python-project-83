from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages  # noqa(E501)
from dotenv import load_dotenv
from datetime import datetime
from psycopg2.extras import RealDictCursor, NamedTupleCursor
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from itertools import zip_longest
import psycopg2
import os
import validators
import requests


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


URL = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(URL)
    print("Подключение установлено")
    with conn.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS urls (id bigint PRIMARY KEY GENERATED
                ALWAYS AS IDENTITY, name varchar(255), created_at timestamp)"""
        )
except (requests.exceptions.ConnectionError(), psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if conn:
        conn.commit()
        conn.close()


try:
    conn = psycopg2.connect(URL)
    print("Подключение установлено")
    with conn.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS url_checks (id bigint PRIMARY KEY
                GENERATED ALWAYS AS IDENTITY,
                    url_id bigint,
                        status_code integer, h1 varchar(255),
                            title varchar(255), description varchar(255),
                                created_at timestamp)"""
        )
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
    answer = []
    with psycopg2.connect(URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("SELECT id, name FROM urls ORDER BY id")
            list_of_urls = cursor.fetchall()
            cursor.execute("""SELECT date(created_at), status_code
                           FROM url_checks WHERE id IN (SELECT MAX(id)
                           FROM url_checks GROUP BY url_id)
                           ORDER BY url_id""")
            list_of_test_dates = cursor.fetchall()
            result = list(zip_longest(list_of_urls, list_of_test_dates,
                                      fillvalue=()))
            for i, j in result:
                answer.append(i+j)
            return render_template("urls.html", answer=answer[::-1])


def validate(form):
    return urlsplit(form).scheme + "://"\
        + urlsplit(form).netloc


@app.route("/urls", methods=["POST"])
def urls_post():
    form = request.form["url"]
    input = validate(form)
    if not validators.url(input):
        flash("Некорректный URL", "error")
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
    h1 = ""
    title = ""
    description = ""
    current_date = datetime.now()
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
                print("soup", soup)
                try:
                    h1 = ((soup.find(["h1"])).text).strip()
                except AttributeError:
                    h1 = ""
                try:
                    title = ((soup.find(["title"])).text).strip()
                except AttributeError:
                    title = ""
                try:
                    description = (soup.find(
                        "meta",
                        {"name": "description"}).attrs["content"]).strip()
                except AttributeError:
                    description = ""
            except requests.exceptions.RequestException:
                flash("Произошла ошибка при проверке")
                return redirect(url_for("url_id", id=id))
            cursor.execute(
                """INSERT INTO url_checks (url_id, created_at, status_code, h1,
                        title, description)
                            VALUES (%s,%s,%s,%s,%s,%s)""",
                (id, current_date, res.status_code, h1, title, description),
            )
            flash("Страница успешно проверена", "success")
            return redirect(url_for("url_id", id=id))


@app.route("/urls/<id>", methods=["GET"])
def url_id(id):
    messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT name, created_at FROM urls WHERE id = %s",
                           (id,))
            result_urls = cursor.fetchone()
            fetched_url = result_urls.get("name")
            date = result_urls.get("created_at").strftime("%Y-%m-%d")
            cursor.execute("""SELECT id, status_code, created_at, h1,
                           title, description FROM url_checks
                            WHERE url_id = %s ORDER BY id DESC""", (id,))
            test_results = cursor.fetchall()
            for i in test_results:
                i["created_at"] = i.get("created_at").strftime("%Y-%m-%d")
        return render_template("url.html", url=fetched_url, date=date, id=id,
                               messages=messages, test_results=test_results)
