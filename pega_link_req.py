from requests import Session, get
from bs4 import BeautifulSoup as Bs
from funcs import sanitizestring
from re import compile
from multiprocessing.dummy import Pool
from requests.models import Response
from requests import RequestException


def verifica_link(link_ver):
    return req_link(link_ver, stream=True).status_code == 200


def tira_barra(link: str):
    if link[-1] == '/':
        return link[:-1]
    return link


def req_link(link, stream: bool = False) -> Response:
    try:
        resul = get(link, stream=stream)
    except (Exception, RequestException):
        resul = req_link(link)
    return resul


def parse_bs(texto: str) -> Bs:
    return Bs(texto, 'html.parser')


def pega_link_req(link_tupla: tuple, retorno: bool = False):
    def req_ses_get(link: str, headers: dict = None) -> Response:
        if headers is None:
            headers = {}
        try:
            resul = ses.get(link, headers=headers)
        except (Exception, RequestException):
            resul = req_ses_get(link)
        return resul

    def req_ses_post(link: str, data: dict = None, headers: dict = None) -> Response:
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        try:
            resul = ses.post(link, data=data, headers=headers)
        except (Exception, RequestException):
            resul = req_ses_post(link)
        return resul

    try:
        if not retorno:
            print(link_tupla)
        link_solve = link_tupla[1]
        # define header e data
        header = {'Referer': ''}
        d = {'data': ''}
        ses = Session()
        # request da pagina inicial/link
        req_get = req_ses_get(link_solve)
        # req_get = ses.get(link_solve)
        if req_get.url != link_solve:
            return False
        ifra = parse_bs(req_get.content).find('iframe', {'name': 'Player'})
        if ifra:
            prox = ifra.get('src').replace('hhttps://', 'https://')
        else:
            return False
        # abre o iframe
        req_get = req_ses_get(prox)
        # req_get = ses.get(prox)
        dat = parse_bs(req_get.content)
        # pega o valor do form dentro do iframe
        d['data'] = dat.find('input').get('value')
        # pega o link para madar os dados do form
        prox = "https:" + dat.find('form').get('action') if not ('https' in dat.find('form').get('action')) else \
            dat.find('form').get('action')
        # seta a pagina atual
        header['Referer'] = req_get.url
        # requisicao no form do iframe
        req_post = req_ses_post(prox, data=d, headers=header)
        # req_post = ses.post(prox, data=data, headers=header)
        dat = parse_bs(req_post.content)
        # pega o link para madar os dados do form
        prox = dat.find('form').get('action')
        # pega o valor do input dentro do form
        d['data'] = dat.find('input').get('value')
        # seta a pagina atual
        header['Referer'] = req_post.url
        # requisicao da pagina de dentro do form do iframe
        req_post = req_ses_post(prox, data=d, headers=header)
        # req_post = ses.post(prox, data=data, headers=header)
        # dat = parse_bs(req_post.content)
        # prox = dat.find('form').get('action')
        # data['data'] = dat.find('input').get('value')
        # Seta pagina atual
        header['Referer'] = req_post.url
        # monta url final
        partido = req_post.url.split('/')
        link_fim = partido[0] + '//' + partido[2]
        # form do form do form do iframe
        # req_post = ses.post(prox, data=data, headers=header)
        # header['Referer'] = req_post.url
        # location
        # req_get = ses.get("https://social.agenciasocializar.com", headers=header)
        # header['Referer'] = req_get.url
        # request na pagina final
        req_get = req_ses_get(link_fim, headers=header)
        # req_get = ses.get(link_fim, headers=header)
        # pega o link do video
        link_do_video = parse_bs(req_get.content).find('source').get('src')
        if not retorno:
            if verifica_link(link_do_video):
                lst.append((link_tupla[0], link_do_video, link_tupla[2]))
        else:
            return link_do_video if verifica_link(link_do_video) else False
    except Exception as e:
        red = "\033[1;31m"
        reset = "\033[0;0m"
        print(red, "pega_link_req:", link_tupla, '\n', e.__str__(), type(e), e.with_traceback(e.__traceback__), reset)
        if not retorno:
            pega_link_req(link_tupla, retorno)
        else:
            return pega_link_req(link_tupla, retorno)


def pega_eps(link_tupla: tuple):
    try:
        print(link_tupla)
        link_rede = link_tupla[1]
        requisicao_get = req_link(link_rede)
        if requisicao_get.status_code == 200 and requisicao_get.url == link_rede:
            req = parse_bs(requisicao_get.content)
            iframe = req.find('iframe', {'name': 'Player'})
            if iframe is not None:
                lin = pega_link_req((0, link_rede), True)
                if lin:
                    lst.append((*link_tupla, lin))
            else:
                desc = req.find('div', {'itemprop': 'description'}) \
                    if req.find('div', {'itemprop': 'description'}) is not None \
                    else req.find(class_=compile("description"))
                base = "https://www.redecanais.click"
                des = desc.find()
                episodios = []
                # pegar itens
                separar = des.prettify().replace('\n', '').split('<br/>')
                for i in separar:
                    parse_pag = parse_bs(i)
                    if parse_pag.find('a') is not None:
                        str_episodio = ' '.join(sanitizestring(parse_pag.text.replace('Assistir', '')
                                                               .replace('Dublado', '').replace('Legendado', ''))
                                                .strip().split())
                        a_tag = parse_pag.find_all('a')
                        if len(a_tag) == 1:
                            str_link = tira_barra(base + a_tag[0].get('href').replace("%20", ' ') \
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
                no = Pool(10)
                li = no.map_async(altera_link, episodios)
                li.wait()
                episodios.clear()
                for d in li.get():
                    if d is not None:
                        episodios.append(d)
                lst.append((*link_tupla, episodios))
    except Exception as e:
        red = "\033[1;31m"
        reset = "\033[0;0m"
        print(red, "pega_eps:", link_tupla, '\n', e.__str__(), type(e), e.with_traceback(e.__traceback__), reset)


def altera_link(i: dict):
    try:
        chave = [*i.keys()][0]
        tipo_link = type(i.get(*i.keys()))
        if tipo_link == str:
            link = pega_link_req((0, i.get(chave)), retorno=True)
            i[chave] = link
        if tipo_link == dict:
            alt = {ep: pega_link_req((0, li), retorno=True) for ep, li in i[chave].items()}
            i[chave] = alt
        return i
    except Exception as e:
        red = "\033[1;31m"
        reset = "\033[0;0m"
        print(red, 'Altera Link:', i, '\n', e.__str__(), type(e), e.with_traceback(e.__traceback__), reset)


def lst_() -> list:
    return lst


lst = []
# pega_eps((0, 'https://www.redecanais.click/009-1-lista-completa-de-episodios-video_493213c32.html'))
# pega_eps((0, 'https://www.redecanais.click/battle-programmer-shirase-legendado-lista-'
#             'completa-de-episodios-video_66047b9c6.html'))
# pega_eps((0, 'https://www.redecanais.click/aishiteruze-baby-legendado-lista-completa-'
#              'de-episodios-video_136601d9d.html'))
# pega_eps((0, 'https://www.redecanais.click/digimon-adventure-02-dublado-lista-de-episodios_5e47fd18e.html'))
# pega_eps((0, 'https://www.redecanais.click/ultimate-homem-aranha-dublado-lista-completa-de-episodios-video_490ba9c0a.html'))
# from pprint import pprint
#
# pprint(lst)
