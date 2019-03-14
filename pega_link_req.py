from requests import Session, get
from bs4 import BeautifulSoup as Bs, NavigableString
from funcs import sanitizestring
from re import compile
from multiprocessing.dummy import Pool


def verifica_link(link_ver):
    return get(link_ver, stream=True).status_code == 200


def parse_bs(texto: str) -> Bs:
    return Bs(texto, 'html.parser')


def pega_link_req(link_tupla: tuple, retorno: bool = False):
    if not retorno:
        print(link_tupla)
    link_solve = link_tupla[1]
    # define header e data
    header = {'Referer': ''}
    data = {'data': ''}
    ses = Session()
    # request da pagina inicial/link
    req_get = ses.get(link_solve)
    prox = parse_bs(req_get.content).find('iframe', {'name': 'Player'}).get('src')
    # abre o iframe
    req_get = ses.get(prox)
    dat = parse_bs(req_get.content)
    # pega o valor do form dentro do iframe
    data['data'] = dat.find('input').get('value')
    # pega o link para madar os dados do form
    prox = "https:" + dat.find('form').get('action') if not ('https' in dat.find('form').get('action')) else \
        dat.find('form').get('action')
    # seta a pagina atual
    header['Referer'] = req_get.url
    # requisicao no form do iframe
    req_post = ses.post(prox, data=data, headers=header)
    dat = parse_bs(req_post.content)
    # pega o link para madar os dados do form
    prox = dat.find('form').get('action')
    # pega o valor do input dentro do form
    data['data'] = dat.find('input').get('value')
    # seta a pagina atual
    header['Referer'] = req_post.url
    # requisicao da pagina de dentro do form do iframe
    req_post = ses.post(prox, data=data, headers=header)
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
    req_get = ses.get(link_fim, headers=header)
    # pega o link do video
    link_do_video = parse_bs(req_get.content).find('source').get('src')
    if not retorno:
        if verifica_link(link_do_video):
            lst.append((link_tupla[0], link_do_video, link_tupla[2]))
    else:
        return link_do_video if verifica_link(link_do_video) else False


def pega_eps(link_tupla: tuple):
    from requests.models import Response
    from requests import RequestException

    def req_link(link) -> Response:
        try:
            resul = get(link)
        except (Exception, RequestException):
            resul = req_link(link)
        return resul

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
                        # print(' '.join(sanitizestring(parse_pag.text.replace('Assistir', '').replace('Dublado', '')
                        #                               .replace('Legendado', '')).strip().split()),
                        #       base + parse_pag.find('a').get('href').replace("%20", ' ').replace('[', '').split()[0])
                        str_episodio = ' '.join(sanitizestring(parse_pag.text.replace('Assistir', '')
                                                               .replace('Dublado', '').replace('Legendado', ''))
                                                .strip().split())
                        # print(parse_pag.find_all('a'))
                        a_tag = parse_pag.find_all('a')
                        if len(a_tag) == 1:
                            str_link = base + a_tag[0].get('href').replace("%20", ' ') \
                                .replace('[', '').split()[0]
                        else:
                            str_link = {
                                k.text.strip(): base + k.get('href').replace("%20", ' ').replace('[', '').split()[0]
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
# pega_eps((0, 'https://www.redecanais.click/fate-stay-night-dublado-lista-completa-de-episodios_f80dba774.html'))
# from pprint import pprint
#
# pprint(lst)
