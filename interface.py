"""Texto (fonte de pixels própria), menu, HUD e telas.

Em todas as telas y vai de -1 a 1 e x de -aspecto a +aspecto, então nada fica esticado.
"""
import math
import unicodedata
from OpenGL.GL import *

from dificuldade import formatar_tempo

# cada letra tem 5 x 7 pixels: 7 linhas, de cima para baixo, com 5 bits cada
_FONTE = {
    "A": "0E11111F111111", "B": "1E11111E11111E", "C": "0E11101010110E", "D": "1E11111111111E",
    "E": "1F10101E10101F", "F": "1F10101E101010", "G": "0E11101711110F", "H": "1111111F111111",
    "I": "0E04040404040E", "J": "0702020202120C", "K": "11121418141211", "L": "1010101010101F",
    "M": "111B1515111111", "N": "11191513111111", "O": "0E11111111110E", "P": "1E11111E101010",
    "Q": "0E11111115120D", "R": "1E11111E141211", "S": "0F10100E01011E", "T": "1F040404040404",
    "U": "1111111111110E", "V": "11111111110A04", "W": "11111115151B11", "X": "11110A040A1111",
    "Y": "11110A04040404", "Z": "1F01020408101F", "0": "0E11131519110E", "1": "040C040404040E",
    "2": "0E11010204081F", "3": "1F02040201110E", "4": "02060A121F0202", "5": "1F101E0101110E",
    "6": "0608101E11110E", "7": "1F010204080808", "8": "0E11110E11110E", "9": "0E11110F01020C",
    ".": "00000000000C0C", ",": "00000000040408", ":": "000C0C000C0C00", "!": "04040404040004",
    "-": "0000001F000000", "/": "00010204081000", "+": "0004041F040400", ">": "08040201020408",
    "?": "0E110102040004",
}
# acentos: pixels (coluna, linha) acima (linha > 6) ou abaixo (linha < 0) da letra
_ACENTOS = {
    "́": [(2, 8), (3, 9)], "̀": [(2, 8), (1, 9)], "̂": [(1, 8), (2, 9), (3, 8)],
    "̃": [(0, 8), (1, 9), (2, 8.5), (3, 8), (4, 9)], "̧": [(2, -1), (1, -2)],
}
_listas = {}
BRANCO, CINZA = (1.0, 1.0, 1.0), (0.75, 0.75, 0.78)
AMARELO, VERMELHO, VERDE = (1.0, 0.85, 0.3), (1.0, 0.3, 0.25), (0.4, 1.0, 0.5)


def _lista_da_letra(letra):
    if letra in _listas:
        return _listas[letra]
    partes = unicodedata.normalize("NFD", letra)
    linhas = _FONTE.get(partes[0], "")
    pixels = [(c, 6 - l) for l in range(len(linhas) // 2) for c in range(5)
              if int(linhas[2 * l:2 * l + 2], 16) >> (4 - c) & 1]
    for acento in partes[1:]:
        pixels += _ACENTOS.get(acento, [])
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    glBegin(GL_QUADS)
    for x, y in pixels:
        glVertex2f(x, y)
        glVertex2f(x + 1, y)
        glVertex2f(x + 1, y + 1)
        glVertex2f(x, y + 1)
    glEnd()
    glEndList()
    _listas[letra] = lista
    return lista


def largura_texto(s, tam):
    return (len(s) * 6 - 1) * tam / 7


def texto(s, x, y, tam, cor=BRANCO, alfa=1.0, alinhar="centro", sombra=True):
    """tam = altura das letras; (x, y) = base do texto."""
    s = s.upper()
    if alinhar == "centro":
        x -= largura_texto(s, tam) / 2
    elif alinhar == "direita":
        x -= largura_texto(s, tam)
    # as listas são compiladas antes de usar
    listas = [_lista_da_letra(c) for c in s]
    px = tam / 7
    camadas = [((0.0, 0.0, 0.0), 0.6 * alfa, px * 0.8)] if sombra else []
    camadas.append((cor, alfa, 0.0))
    for c, a, desvio in camadas:
        glColor4f(c[0], c[1], c[2], a)
        glPushMatrix()
        glTranslatef(x + desvio, y - desvio, 0.0)
        glScalef(px, px, 1.0)
        for lista in listas:
            glCallList(lista)
            glTranslatef(6.0, 0.0, 0.0)
        glPopMatrix()


def retangulo(x0, y0, x1, y1, cor, alfa):
    glColor4f(cor[0], cor[1], cor[2], alfa)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()


def inicio_2d(aspecto):
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-aspecto, aspecto, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def fim_2d():
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)


# --- telas (entre inicio_2d e fim_2d) ---

_MENU_TOPO, _MENU_PASSO, _MENU_TAM = 0.12, 0.2, 0.085


def opcao_no_ponto(x, y, quantidade):
    """Índice da opção do menu sob o ponto, ou None."""
    for i in range(quantidade):
        base = _MENU_TOPO - i * _MENU_PASSO
        if abs(x) < 0.85 and base - 0.05 < y < base + _MENU_TAM + 0.05:
            return i
    return None


def tela_menu(aspecto, opcoes, escolhida, recordes, tempo):
    retangulo(-aspecto, -1, aspecto, 1, (0.02, 0.04, 0.1), 0.45)
    texto("PAISAGEM OPENGL", 0, 0.58, 0.16, AMARELO)
    texto("PEGUE OS CRISTAIS, FUJA DO MONSTRO E CHEGUE AO PORTAL", 0, 0.43, 0.042, CINZA)

    for i, opcao in enumerate(opcoes):
        y = _MENU_TOPO - i * _MENU_PASSO
        ativa = i == escolhida
        if ativa:
            retangulo(-0.85, y - 0.045, 0.85, y + _MENU_TAM + 0.045, (1.0, 0.8, 0.3),
                      0.2 + 0.06 * math.sin(tempo * 5))
        texto(opcao, 0, y, _MENU_TAM, AMARELO if ativa else BRANCO)
        if opcao in recordes:
            texto("RECORDE " + formatar_tempo(recordes[opcao]), aspecto - 0.1, y + 0.02, 0.042,
                  VERDE, alinhar="direita")

    texto("WASD ANDAR   ESPAÇO PULAR   CLIQUE PEGAR CRISTAL   V CÂMERA   TAB MAPA   N SOM   ESC PAUSA",
          0, -0.82, 0.036, CINZA)
    texto("SETAS OU MOUSE PARA ESCOLHER, ENTER PARA CONFIRMAR", 0, -0.91, 0.036, CINZA)


def tela_carregando(aspecto):
    retangulo(-aspecto, -1, aspecto, 1, (0.02, 0.04, 0.1), 1.0)
    texto("GERANDO O MAPA...", 0, 0, 0.09)


def tela_pausa(aspecto):
    retangulo(-aspecto, -1, aspecto, 1, (0.0, 0.0, 0.0), 0.55)
    texto("PAUSADO", 0, 0.15, 0.16)
    texto("ESC CONTINUAR", 0, -0.1, 0.06, CINZA)
    texto("M VOLTAR AO MENU", 0, -0.24, 0.06, CINZA)


def tela_morte(aspecto):
    retangulo(-aspecto, -1, aspecto, 1, (0.6, 0.0, 0.0), 0.5)
    texto("O MONSTRO PEGOU VOCÊ", 0, 0.05, 0.13)
    texto("SEUS CRISTAIS FORAM MANTIDOS", 0, -0.12, 0.05, CINZA)


def tela_vitoria(aspecto, dificuldade, tempo, mortes, novo_recorde, recorde):
    retangulo(-aspecto, -1, aspecto, 1, (0.0, 0.25, 0.08), 0.6)
    texto("VOCÊ ESCAPOU!", 0, 0.42, 0.17, AMARELO)
    texto("%s   TEMPO %s   MORTES %d" % (dificuldade, formatar_tempo(tempo), mortes), 0, 0.18, 0.07)
    if novo_recorde:
        texto("NOVO RECORDE!", 0, 0.0, 0.09, VERDE)
    else:
        texto("RECORDE " + formatar_tempo(recorde), 0, 0.0, 0.06, CINZA)
    texto("R JOGAR DE NOVO", 0, -0.3, 0.06, BRANCO)
    texto("ENTER VOLTAR AO MENU", 0, -0.44, 0.06, BRANCO)


def mira(aspecto):
    t = 0.02
    glColor4f(1.0, 1.0, 1.0, 0.8)
    glBegin(GL_LINES)
    glVertex2f(-t, 0)
    glVertex2f(t, 0)
    glVertex2f(0, -t)
    glVertex2f(0, t)
    glEnd()


def _vinheta(aspecto, alfa):
    """Bordas vermelhas, mais fortes quanto mais perto o monstro."""
    l = 0.45
    a = aspecto
    glBegin(GL_QUADS)
    for bordas in (((-a, -1), (-a, 1), (-a + l, 1), (-a + l, -1)),
                   ((a, -1), (a, 1), (a - l, 1), (a - l, -1)),
                   ((-a, 1), (a, 1), (a, 1 - l), (-a, 1 - l)),
                   ((-a, -1), (a, -1), (a, -1 + l), (-a, -1 + l))):
        for i, (x, y) in enumerate(bordas):
            glColor4f(0.8, 0.0, 0.0, alfa if i < 2 else 0.0)
            glVertex2f(x, y)
    glEnd()


def hud(aspecto, tempo, mortes, distancia, alerta, perigo, mensagem, alfa_mensagem):
    """alerta: o jogador está sendo perseguido. mensagem: aviso curto no centro."""
    if alerta:
        _vinheta(aspecto, 0.15 + 0.6 * perigo)
        pulso = 0.7 + 0.3 * math.sin(tempo * (6 + 10 * perigo))
        texto("SAIA DA ÁGUA!", 0, 0.55, 0.08, VERMELHO, pulso)
    texto(formatar_tempo(tempo), aspecto - 0.08, 0.88, 0.07, alinhar="direita")
    texto("MORTES %d" % mortes, aspecto - 0.08, 0.78, 0.04, BRANCO, alinhar="direita")
    texto("PORTAL A %d" % distancia, 0, 0.9, 0.045, BRANCO)
    if mensagem and alfa_mensagem > 0:
        meia = largura_texto(mensagem, 0.07) / 2 + 0.06
        retangulo(-meia, 0.26, meia, 0.41, (0.0, 0.0, 0.0), 0.5 * alfa_mensagem)
        texto(mensagem, 0, 0.3, 0.07, AMARELO, alfa_mensagem)
