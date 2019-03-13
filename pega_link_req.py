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
    try:
        print(link_tupla)
        link_rede = link_tupla[1]
        requisicao_get = get(link_rede)
        if requisicao_get.status_code==200 and requisicao_get.url==link_rede:
            req = parse_bs(requisicao_get.content)
            iframe = req.find('iframe', {'name': 'Player'})
            if iframe is not None:
                lin = pega_link_req((0, link_rede), True)
                if lin:
                    lst.append((*link_tupla, lin))
            else:
                desc = req.find('div', {'itemprop': 'description'}) if req.find('div', {'itemprop': 'description'}) is not None \
                    else req.find(class_=compile("description"))
                temps = {}
                base = "https://www.redecanais.click"
                tematu = ''
                des = desc.find()
                mod = {}
                ini = 1
                nome = ''
                # pegar itens
                for i in des:
                    if type(i) == NavigableString:
                        nome += sanitizestring(str(i)).strip()
                        mod[nome] = {}
                    else:
                        if 'span' in map(lambda x: x.name, i.contents) or i.name == 'span':
                            tematu = i.text.strip()
                            temps[tematu] = []
                        if ('episódio' in i.text.lower() or i.name == 'strong') and \
                                (not ('assistir' in i.text.lower())) and i.text.strip()!='':
                            nome = i.text
                        t=i.find_all()
                        t.append(i)
                        if 'a' in map(lambda x: x.name, t):
                            i=list(filter(lambda x: x.name=='a', t))[0]
                            # print(i)
                            if i.name != 'a':
                                li = list(filter(lambda y: y[0] == 'a', map(lambda x: (x.name, x), i.contents)))[0]
                                a, i = li
                            # print(mod)
                            if not (nome in mod.keys()):
                                mod[nome] = {}
                            mod[nome][i.text] = base + i.get('href').replace("%20", ' ').split()[0]
                            if tematu == '':
                                tematu = str(ini) + " Temporada"
                                temps[tematu] = []
                            temps[str(tematu)].append(dict(mod))
                # remover itens vazios
                itens_excluir = []
                for i in temps.keys():
                    for j in range(len(temps[i])):
                        for k in temps[i][j]:
                            if temps[i][j][k] == {}:
                                itens_excluir.append((i, j, k))
                for i in itens_excluir:
                    del (temps[i[0]][i[1]][i[2]])
                ###
                # Organizar Itens
                for temporada in temps.keys():
                    eps = []
                    dic = {}
                    print(list(enumerate(temps[temporada])))
                    for num, ep in (enumerate(temps[temporada])):
                        abc = ([(e[0], e[1]) for e in ep.items()][0])
                        dic[abc[0]] = []
                        eps.append(abc)
                    no = Pool(5)
                    li = no.map_async(lambda x: altera_link(x, link_tupla), eps)
                    li.wait()
                    for d in li.get():
                        if d is not None:
                            dic[d[0]].append(d[1])
                    temps[temporada] = dic
                lst.append((*link_tupla, temps))
    except Exception as e:
        RED = "\033[1;31m"
        RESET = "\033[0;0m"
        print(RED, link_tupla, e.__str__(), RESET)


def altera_link(i, tupl: tuple):
    try:
        # dic={str(i[0]): []}
        link = pega_link_req((0, i[1][[*i[1].keys()][0]]), retorno=True)
        if link:
            i[1][[*i[1].keys()][0]] = link
            # dic[i[0]].append(i[1])
            return i
    except Exception as e:
        RED = "\033[1;31m"
        RESET = "\033[0;0m"
        print(RED, tupl, i, e.__str__(), RESET)


def lst_() -> list:
    return lst


lst = []
dicio_compart = {}
# pega_eps((0, 'https://www.redecanais.click/009-1-lista-completa-de-episodios-video_493213c32.html'))
pega_eps((0, 'https://www.redecanais.click/battle-programmer-shirase-legendado-lista-completa-de-episodios-video_66047b9c6.html'))
# pega_eps((0, 'https://www.redecanais.click/aishiteruze-baby-legendado-lista-completa-de-episodios-video_136601d9d.html'))
print(lst)
