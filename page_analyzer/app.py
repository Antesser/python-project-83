from flask import request, Flask


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return 'Hello, POST!'
    return 'Hello, GET!'
