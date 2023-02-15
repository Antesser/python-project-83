from urllib.parse import urlsplit


def validate(form):
    return urlsplit(form).scheme + "://"\
        + urlsplit(form).netloc
