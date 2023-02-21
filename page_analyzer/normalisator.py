from urllib.parse import urlsplit


def normalise(form):
    return urlsplit(form).scheme + "://"\
        + urlsplit(form).netloc
