from requests import get
from bs4 import BeautifulSoup as Bs
from collections import namedtuple
from pprint import pprint
from multiprocessing.dummy import Pool
from io import StringIO
from json import dump, load
from funcs import sanitizestring, timeit
from pega_link_req import pega_link_req, lst_, pega_eps


def cria_link_filme(i):
    return f"{link_base}browse-filmes-videos-{i}-title.html"


def cria_link_serie(i):
    return f"{link_base}browse-series-videos-{i}-title.html"


def cria_link_animes(i):
    return f"{link_base}browse-animes-videos-{i}-title.html"


def cria_link_desenhos(i):
    return f"{link_base}browse-desenhos-videos-{i}-title.html"


def percorre_lista(pagina: int = 1, lst=None, func=cria_link_filme) -> int:
    if lst is None:
        lst = []
    pprint(func(pagina))
    page = Bs(get(func(pagina)).text, "html.parser")
    filmes = page.find("ul", {'id': 'pm-grid'}).find_all("li")
    for i in filmes:
        info = i.find('a', {"class": "ellipsis"})
        titulo = sanitizestring(info.get("title")).strip()
        link = info.get("href")
        imagem = i.find('img').get('data-echo')
        lst.append(tupla(titulo, link_base + link[2:], imagem))
    return int(page.find("ul", {'class': 'pagination'}).find_all('a')[-2].text)


def salvar_arq(arq: dict, nome: str):
    io = StringIO()
    dump(arq, io)
    json_s = io.getvalue()
    arq = open(f'{pasta}/{nome}.json', 'w')
    arq.write(json_s)
    arq.close()


def ler_arq(nome: str) -> dict:
    return load(open(f'{pasta}/{nome}.json'))


def salva_lista(func=cria_link_filme) -> list:
    lst = []
    ultimo = percorre_lista(lst=lst, func=func)
    li = [i for i in range(2, ultimo + 1)]
    node = Pool(100)
    x = node.map_async(lambda a: percorre_lista(a, lst, func), li)
    x.wait()
    return lst


def scraper_rede(func=cria_link_filme, nome='filmes'):
    lista = salva_lista(func)
    di = {"nome": [], "link": [], "imagem": []}
    [(di['nome'].append(i.nome), di['link'].append(i.link), di['imagem'].append(i.imagem))
     for i in sorted(lista, key=lambda litem: litem.nome)]
    salvar_arq(di, nome)


def link_parse_filme(arq: str = 'filmes', nome_arq: str = 'filmes'):
    arquivo = ler_arq(arq)
    nome, link, imagem = arquivo.keys()
    arquivo = list(zip(arquivo[nome], arquivo[link], arquivo[imagem]))
    node = Pool(100)
    espera = node.map_async(lambda x: pega_link_req(x), arquivo)
    espera.wait()
    lst = lst_()
    pprint(len(lst))
    di = {"nome": [], "link": [], "imagem": []}
    [(di['nome'].append(i[0]), di['link'].append(i[1]), di['imagem'].append(i[2]))
     for i in sorted(lst, key=lambda litem: litem[0])]
    salvar_arq(di, f"{nome_arq}")


def link_parse_eps(arq: str, nome_arq: str):
    arquivo = ler_arq(arq)
    nome, link, imagem = arquivo.keys()
    arquivo = list(zip(arquivo[nome], arquivo[link], arquivo[imagem]))
    lst_().clear()
    node = Pool(10)
    espera = node.map_async(lambda x: pega_eps(x), arquivo)
    espera.wait()
    lst = lst_()
    pprint(len(lst))
    di = {"nome": [], "link": [], "imagem": [], 'episodios': []}
    [(di['nome'].append(i[0]), di['link'].append(i[1]), di['imagem'].append(i[2]), di['episodios'].append(i[3]))
     for i in sorted(lst, key=lambda litem: litem[0])]
    salvar_arq(di, f"{nome_arq}")


def gera_m3u_filmes():
    df = ler_arq("filme")
    m3u = '#EXTM3U\n'
    for i in range(len(df['nome'])):
        m3u += '#EXTINF:-1 tvg-id="' + df['nome'][i] + '" tvg-name="' \
               + df['nome'][i] + '" logo="' + df['imagem'][i] + '",' + df['nome'][i] + '\n'
        m3u += df['link'][i] + "\n"
    arq = open('json/filme.m3u', 'w')
    arq.write(m3u)
    arq.close()


with timeit():
    link_base = "https://www.redecanais.click/"
    pasta = "json"
    tupla = namedtuple("molde", "nome link imagem")
    pipeline = [(cria_link_desenhos, "desenhos"),
                (cria_link_animes, "animes"),
                (cria_link_serie, "series"),
                (cria_link_filme, "filmes")
                ]
    # [scraper_rede(*i) for i in pipeline]
    # link_parse_filme()
    link_parse_eps('animes', 'anime')
