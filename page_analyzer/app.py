from flask import request, Flask


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def app():
    if request.method == 'POST':
        return 'Hello, POST!'
    return 'Hello, GET!'
