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


def pega_link_req(link_tupla: tuple, retorno: bool = True) -> tuple or bool:
    def req_ses_get(link: str, headers: dict = None) -> Response:
        if headers is None:
            headers = {}
        try:
            resul = ses.get(link, headers=headers)
        except (Exception, RequestException) as ee:
            print(red, 'tá dando erro get', link, link_tupla, ee, type(ee), reset)
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
            print(red, 'tá dando erro post', link, link_tupla, ee, type(ee), reset)
            resul = req_ses_post(link)
        return resul

    try:
        # if not retorno:
        #     print(link_tupla)
        link_solve = link_tupla[1]
        # define header e data
        header = {'Referer': ''}
        d = {'data': ''}
        ses = Session()
        # request da pagina inicial/link
        req_get = req_ses_get(link_solve)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
            return pega_link_req(link_tupla, retorno)
        if req_get.url != link_solve:
            return False
        ifra = parse_bs(req_get.content).find('iframe', {'name': 'Player'})
        if ifra:
            prox = ifra.get('src').replace('hhttps://', 'https://')
        else:
            return False
        # abre o iframe
        req_get = req_ses_get(prox)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
            return pega_link_req(link_tupla, retorno)
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
        # sleep(1)
        req_post = req_ses_post(prox, data=d, headers=header)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_post.text.lower():
            return pega_link_req(link_tupla, retorno)
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
            return pega_link_req(link_tupla, retorno)
        # Seta pagina atual
        header['Referer'] = req_post.url
        # monta url final
        partido = req_post.url.split('/')
        link_fim = partido[0] + '//' + partido[2]
        # request na pagina final
        req_get = req_ses_get(link_fim, headers=header)
        if '404 - Arquivo ou diretório não encontrado.'.lower() in req_get.text.lower():
            return pega_link_req(link_tupla, retorno)
        # pega o link do video
        dat = parse_bs(req_get.content)
        link_do_video = dat.find('source').get('src')
        if retorno:
            global cont
            cont += 1
            print(cont, link_tupla[0], link_tupla[1])
        if verifica_link(link_do_video):
            return (*link_tupla, link_do_video)
        else:
            return False
    except Exception as e:
        print(red, "pega_link_req:", link_tupla, '\n', e.__str__(), type(e), reset)
        return pega_link_req(link_tupla, retorno)


def pega_eps(link_tupla: tuple) -> tuple or bool:
    try:
        link_rede = link_tupla[1]
        requisicao_get = req_link(link_rede)
        if requisicao_get.status_code == 200 and requisicao_get.url == link_rede:
            req = parse_bs(requisicao_get.content)
            iframe = req.find('iframe', {'name': 'Player'})
            if iframe is not None:
                lin = pega_link_req((0, link_rede), True)
                return (*link_tupla, lin) if lin else False
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
                no = Pool()
                li = no.map_async(altera_link, episodios)
                li.wait()
                episodios.clear()
                for d in li.get():
                    if d is not None:
                        episodios.append(d)
                global cont
                cont += 1
                print(cont, link_tupla[0], link_tupla[1])
                return (*link_tupla, episodios)
    except Exception as e:
        print(red, "pega_eps:", link_tupla, '\n', e.__str__(), type(e), e.with_traceback(e.__traceback__), reset)


def altera_link(i: dict):
    try:
        chave = [*i.keys()][0]
        tipo_link = type(i.get(*i.keys()))
        if tipo_link == str:
            link = pega_link_req((0, i.get(chave)), retorno=False)[-1] if not ('.jpg' in i.get(chave)) else False
            i[chave] = link
        if tipo_link == dict:
            alt = {ep: pega_link_req((0, li), retorno=False)[-1] if not ('.jpg' in i.get(chave)) else False
                   for ep, li in i[chave].items()}
            i[chave] = alt
        return i
    except Exception as e:
        print(red, 'Altera Link:', i, '\n', e.__str__(), type(e), reset)


def dispatcher(tupla_link: tuple):
    link = tupla_link[1]
    get = req_link(link)
    if get.status_code == 200 and get.url == link:
        req = parse_bs(get.content)
        iframe = req.find('iframe', {'name': 'Player'})
        if iframe is not None:
            lin = pega_link_req((0, iframe.get("src")), True)
            return (*tupla_link, lin) if lin else False
        else:
            return pega_eps(tupla_link)


red = "\033[1;31m"
reset = "\033[0;0m"
cont = 0
# pega_eps((0, 'https://www.redecanais.click/009-1-lista-completa-de-episodios-video_493213c32.html'))
# pega_eps((0, 'https://www.redecanais.click/battle-programmer-shirase-legendado-lista-'
#             'completa-de-episodios-video_66047b9c6.html'))
# pega_eps((0, 'https://www.redecanais.click/aishiteruze-baby-legendado-lista-completa-'
#              'de-episodios-video_136601d9d.html'))
# print(pega_eps((0, 'https://www.redecanais.click/gungrave-legendado-lista-completa-de-episodios-video_9643748b0.html')))
# pega_eps((0, 'https://www.redecanais.click/ultimate-homem-aranha-dublado'
#              '-lista-completa-de-episodios-video_490ba9c0a.html'))
# from pprint import pprint

# pprint(lst)
