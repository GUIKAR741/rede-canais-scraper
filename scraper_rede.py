from requests import get
from bs4 import BeautifulSoup as Bs
from collections import namedtuple
from pprint import pprint
from multiprocessing.dummy import Pool
from io import StringIO
from json import dump, load
from funcs import sanitizestring, timeit, tira_num
from pega_link_req import dispatcher


def cria_link_filme(i):
    return f"{link_base}browse-filmes-videos-{i}-title.html"


def cria_link_serie(i):
    return f"{link_base}browse-series-videos-{i}-title.html"


def cria_link_animes(i):
    return f"{link_base}browse-animes-videos-{i}-title.html"


def cria_link_desenhos(i):
    return f"{link_base}browse-desenhos-videos-{i}-title.html"


def percorre_lista(pagina: int = 1, lst: list = None, func=cria_link_filme) -> int:
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
    [(di['nome'].append(' '.join(i.nome
                                 .replace("Lista de Episodios", "")
                                 .replace("Lista de Episodio", "")
                                 .strip()
                                 .split()
                                 )
                        ),
      di['link'].append(i.link.replace(',', '%2C')),
      di['imagem'].append(i.imagem.replace(',', '%2C')))
     for i in sorted(lista, key=lambda litem: litem.nome)]
    salvar_arq(di, nome)


def link_parse(arq: str, tam_pool: int = 10):
    arquivo = ler_arq(arq)
    nome, link, imagem = [*arquivo.keys()][:3]
    arquivo = list(zip(arquivo[nome], arquivo[link], arquivo[imagem]))
    print("Total:", len(arquivo))
    node = Pool(tam_pool)
    espera = node.map_async(dispatcher, arquivo)
    espera.wait()
    di = {"nome": [], "link": [], "imagem": [], 'assistir': []}
    lis = espera.get()
    print("total fim:", len(lis))
    [(di['nome'].append(i[0]), di['link'].append(i[1]), di['imagem'].append(i[2]), di['assistir'].append(i[3]))
     if i else i
     for i in sorted(list(filter(lambda x: x is not None, filter(lambda x: x is not False, lis))),
                     key=lambda litem: litem[0])]
    salvar_arq(di, arq)
    gera_m3u(arq)


def gera_m3u(arq: str):
    df = ler_arq(arq)
    m3u = '#EXTM3U\n'
    for i in range(len(df['nome'])):
        if type(df['assistir'][i]) == str:
            m3u += '#EXTINF:-1 tvg-id="' + df['nome'][i] + '" tvg-name="' \
                   + df['nome'][i] + '" logo="' + df['imagem'][i] + '",' + df['nome'][i] + '\n'
            m3u += df['assistir'][i] + "\n"
        elif type(df['assistir'][i]) == list:
            li = df['assistir'][i]
            nome = ' '.join(df['nome'][i].split())
            tam = 1
            tam_str = len(str(len(li)))
            for k in li:
                chave = [*k.keys()][0]
                if type(k[chave]) == str:
                    m3u += '#EXTINF:-1 tvg-id="' + nome + '" tvg-name="' \
                           + nome + '" logo="' + df['imagem'][i] + '",' + nome + ' ' + \
                           '0' * (tam_str - len(str(tam))) + str(tam) + ' ' + \
                           ' '.join(tira_num(chave).replace('Episodio', ' ').split()) + " " + '\n'
                    m3u += k[chave] + "\n"
                elif type(k[chave]) == dict:
                    nome = ' '.join(nome.replace("Dublado", '').replace('Legendado', '').split())
                    for key, val in k[chave].items():
                        if val:
                            m3u += '#EXTINF:-1 tvg-id="' + nome + '" tvg-name="' \
                                   + nome + '" logo="' + df['imagem'][i] + '",' + \
                                   nome + ' ' + '0' * (tam_str-len(str(tam)))+str(tam) + ' ' + \
                                   ' '.join(tira_num(chave).replace('Episodio', ' ').split()) + ' ' + key + '\n'
                            m3u += val + "\n"
                tam += 1
    arq = open(f'{pasta}/{arq}.m3u', 'w')
    arq.write(m3u)
    arq.close()


with timeit():
    link_base = "https://www.redecanais.click/"
    pasta = "json"
    tupla = namedtuple("molde", "nome link imagem")
    gera_m3u('filmes')
    # pipeline = [
    #     (cria_link_desenhos, "desenhos"),
    #     (cria_link_animes, "animes"),
    #     (cria_link_serie, "series"),
    #     (cria_link_filme, "filmes")
    # ]
    # [scraper_rede(*i) for i in pipeline]
    # pipeline = {
    #     ('filmes', 30),
    #     ('desenhos',),
    #     ('animes',),
    #     ('series',)
    # }
    # [link_parse(*i) for i in pipeline]
