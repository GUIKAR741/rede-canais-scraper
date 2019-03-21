from re import sub
from unicodedata import normalize, combining
from contextlib import contextmanager
from datetime import datetime


@contextmanager
def timeit():
    start_time = datetime.now()
    yield
    time_elapsed = datetime.now() - start_time
    print(f'Tempo total (hh:mm:ss.ms) {time_elapsed}')


def sanitizestring(palavra):
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    nfkd = normalize('NFKD', palavra)
    palavrasemacento = u"".join([c for c in nfkd if not combining(c)])
    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    return sub('[^a-zA-Z0-9 ]', '', palavrasemacento)


def tira_num(palavra):
    return sub('[^a-zA-Z ]', '', palavra[:int(len(palavra)/2)])+palavra[int(len(palavra)/2):]
