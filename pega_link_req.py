"""Faz a resolução dos links."""
from multiprocessing.dummy import Pool
from re import compile as comp

from bs4 import BeautifulSoup as Bs
from requests import RequestException, Session, get
from requests.models import Response

from funcs import sanitizestring


def verifica_link(link_ver):
    """Verifica se o link está funcionando."""
    return req_link(link_ver, stream=True).status_code == 200


def tira_barra(link: str):
    """Tira o ultimo caractere da."""
    if link[-1] == '/':
        return link[:-1]
    return link


def req_link(link, stream: bool = False) -> Response:
    """Faz a requisição do link."""
    try:
        resul = get(link, stream=stream)
    except (Exception, RequestException):
        resul = req_link(link)
    return resul


def parse_bs(texto: str) -> Bs:
    """Transformar texto em objeto beautiful soap."""
    return Bs(texto, 'html.parser')


def pega_link_req(link_tupla: tuple, retorno: bool = True, repeticoes: int = 1,
                  frame: bool = False) -> tuple or bool:
    """Pega o link para assistir da pagina."""
    def req_ses_get(link: str, headers: dict = None) -> Response:
        if headers is None:
            headers = {}
        try:
            resul = ses.get(link, headers=headers)
        except (Exception, RequestException) as ee:
            print(red, 'tá dando erro get', link,
                  link_tupla, ee, type(ee), reset)
            resul = req_ses_get(link)
        return resul

    def req_ses_post(link: str, data: dict = None, headers: dict = None) -> Response:
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        try:
            resul = ses.post(link, data=data, headers=headers)
        except (Exception, RequestException) as ee:
            print(red, 'tá dando erro post', link,
                  link_tupla, ee, type(ee), reset)
            resul = req_ses_post(link)
        return resul

    global cont
    conta = cont
    try:
        if repeticoes >= 10:
            return False
        link_solve = link_tupla[1].replace('https://rede.canais.vip', '')
        # define header e data
        header = {'Referer': ''}
        d = {'data': ''}
        ses = Session()
        # se passar logo o link do frame
        if not frame:
            # request da pagina inicial/link
            req_get = req_ses_get(link_solve)
            if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
                return pega_link_req(link_tupla=link_tupla,
                                     retorno=retorno, repeticoes=(repeticoes+1), frame=frame)
            if req_get.url != link_solve:
                return False
            ifra = parse_bs(req_get.content).find('iframe', {'name': 'Player'})
            if ifra:
                prox = ifra.get('src').replace('hhttps://', 'https://')
            else:
                return False
        else:
            prox = link_solve
        # abre o iframe
        req_get = req_ses_get(prox)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
            return pega_link_req(link_tupla=link_tupla, retorno=retorno,
                                 repeticoes=(repeticoes+1), frame=frame)
        # req_get = ses.get(prox)
        dat = parse_bs(req_get.content)
        # pega o valor do form dentro do iframe
        d['data'] = dat.find('input').get('value')
        # pega o link para madar os dados do form
        prox = "https:" + dat.find('form').get('action') if not \
            ('https' in dat.find('form').get('action')) else dat.find('form').get('action')
        # seta a pagina atual
        header['Referer'] = req_get.url
        # requisicao no form do iframe
        # sleep(1)
        req_post = req_ses_post(prox, data=d, headers=header)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_post.text.lower():
            return pega_link_req(link_tupla=link_tupla, retorno=retorno,
                                 repeticoes=(repeticoes+1), frame=frame)
        dat = parse_bs(req_post.content)
        # pega o link para madar os dados do form
        prox = dat.find('form').get('action')
        # pega o valor do input dentro do form
        d['data'] = dat.find('input').get('value')
        # seta a pagina atual
        header['Referer'] = req_post.url
        # requisicao da pagina de dentro do form do iframe
        req_post = req_ses_post(prox, data=d, headers=header)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_post.text.lower():
            return pega_link_req(link_tupla=link_tupla, retorno=retorno,
                                 repeticoes=(repeticoes+1), frame=frame)
        # Seta pagina atual
        header['Referer'] = req_post.url
        # monta url final
        partido = req_post.url.split('/')
        link_fim = partido[0] + '//' + partido[2]
        # request na pagina final
        req_get = req_ses_get(link_fim, headers=header)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
            return pega_link_req(link_tupla=link_tupla, retorno=retorno,
                                 repeticoes=(repeticoes+1), frame=frame)
        # pega o link do video
        dat = parse_bs(req_get.content)
        link_do_video = dat.find('source').get('src')
        if retorno:
            conta += 1
            print(cont, link_tupla[0], link_tupla[1])
        if verifica_link(link_do_video):
            return (*link_tupla, link_do_video)
        else:
            return False
    except Exception as e:
        print(red, "pega_link_req:", link_tupla,
              '\n', e.__str__(), type(e), reset)
        return pega_link_req(link_tupla=link_tupla, retorno=retorno,
                             repeticoes=(repeticoes+1), frame=frame)


def pega_eps(link_tupla: tuple, conteudo: bytes = b'') -> tuple or bool:
    """Pega os episodios da pagina e passa para pegar o link."""
    global cont
    try:
        if conteudo == b'':
            link_rede = link_tupla[1]
            requisicao_get = req_link(link_rede)
            if requisicao_get.status_code != 200 and requisicao_get.url != link_rede:
                return False
            requisicao_get = requisicao_get.content
        else:
            requisicao_get = conteudo
        req = parse_bs(requisicao_get)
        desc = req.find('div', {'itemprop': 'description'}) \
            if req.find('div', {'itemprop': 'description'}) is not None \
            else req.find(class_=comp("description"))
        base = "https://www.redecanais.click"
        des = desc.find()
        episodios = []
        # pegar itens
        separar = des.prettify().replace('\n', '').split('<br/>')
        for i in separar:
            parse_pag = parse_bs(i)
            if parse_pag.find('a') is not None:
                str_episodio = ' '.join(sanitizestring(parse_pag.text
                                                       .replace('Assistir', '')
                                                       .replace('Dublado', '')
                                                       .replace('Legendado', '')
                                                       )
                                        .strip().split())
                a_tag = parse_pag.find_all('a')
                if len(a_tag) == 1:
                    str_link = tira_barra(base + a_tag[0].get('href').replace("%20", ' ')
                                          .replace('redi/', '').replace('[', '').split()[0])
                else:
                    str_link = {
                        k.text.strip():
                            tira_barra(base + k.get('href').replace("%20", ' ')
                                       .replace('redi/', '')
                                       .replace('[', '')
                                       .split()[0])
                        for k in a_tag
                    }
                ep = {str_episodio: str_link}
                episodios.append(ep)
        no = Pool(5)
        li = no.map_async(altera_link, episodios)
        li.wait()
        episodios.clear()
        for d in li.get():
            if d is not None:
                episodios.append(d)
        cont += 1
        print(cont, link_tupla[0], link_tupla[1])
        return (*link_tupla, episodios)
    except Exception as e:
        print(red, "pega_eps:", link_tupla, '\n', e.__str__(),
              type(e), e.with_traceback(e.__traceback__), reset)


def altera_link(i: dict):
    """Altera o link pegando o link pra assistir."""
    try:
        chave = [*i.keys()][0]
        tipo_link = type(i.get(*i.keys()))
        if tipo_link == str:
            ret = pega_link_req((0, i.get(chave)), retorno=False) if not ('.jpg' in i.get(chave) or
                                                                          'href' in i.get(chave)) \
                else False
            link = ret[-1] if ret else ret
            i[chave] = link
        if tipo_link == dict:
            alt = {}
            for ep, li in i[chave].items():
                ret = pega_link_req((0, li), retorno=False) if not ('.jpg' in li or
                                                                    '<a' in li) else False
                alt[ep] = ret[-1] if ret else ret
            i[chave] = alt
        return i
    except Exception as e:
        print(red, 'Altera Link:', i, '\n', e.__str__(), type(e), reset)


def dispatcher(tupla_link: tuple):
    """Separa para onde cada tupla deve ir."""
    link = tupla_link[1]
    get_req = req_link(link)
    if get_req.status_code == 200 and get_req.url == link:
        req = parse_bs(get_req.content)
        iframe = req.find('iframe', {'name': 'Player'})
        if iframe is not None:
            lin = pega_link_req(link_tupla=(tupla_link[0], iframe.get("src")
                                            .replace('hhttps://', 'https://')),
                                retorno=True, frame=True)
            return (*tupla_link, lin) if lin else False
        else:
            return pega_eps(tupla_link, conteudo=get_req.content)


red = "\033[1;31m"
reset = "\033[0;0m"
cont = 0
