"""Minimapa tipo radar: o jogador fica no centro e "para cima" é para onde ele olha.

Cristais e portal fora do alcance aparecem presos na borda, mostrando a direção.
"""
import math
from OpenGL.GL import *

from colisao import TAMANHO_PLATAFORMA, LARGURA_PLAT_ES, COMPRIMENTO_PLAT_ES
from interface import retangulo, texto
from plataformas import CORES, PASSOS_QUEBRAR
import cristais as _cristais

ALCANCE = 110.0     # unidades do mundo do centro até a borda
MEIO = 0.27         # metade do lado do painel, na tela
MARGEM = 0.06
_M = TAMANHO_PLATAFORMA / 2

# cores mais vivas que as do cenário, que são multiplicadas pela textura
_MADEIRA = (0.72, 0.5, 0.3)


def _cor(tipo_cor):
    return _MADEIRA if tipo_cor == (1.0, 1.0, 1.0) else tipo_cor


def _quad(x0, x1, z0, z1):
    # no mapa o eixo vertical é -z
    glVertex2f(x0, -z0)
    glVertex2f(x1, -z0)
    glVertex2f(x1, -z1)
    glVertex2f(x0, -z1)


def compilar_minimapa(fixas, tamanho):
    """Display list com tudo que não se mexe, em coordenadas do mundo."""
    t = tamanho
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    glBegin(GL_QUADS)
    glColor4f(0.15, 0.32, 0.55, 1.0)                # água
    _quad(-t, t, -t, t)
    glColor4f(0.6, 0.58, 0.55, 1.0)                 # saída e chegada
    _quad(-t, -t + LARGURA_PLAT_ES, -COMPRIMENTO_PLAT_ES, COMPRIMENTO_PLAT_ES)
    _quad(t - LARGURA_PLAT_ES, t, -COMPRIMENTO_PLAT_ES, COMPRIMENTO_PLAT_ES)
    for (x, _, z), cor in fixas:
        glColor4f(*_cor(cor), 1.0)
        _quad(x - _M, x + _M, z - _M, z + _M)
    glEnd()
    glEndList()
    return lista


def _losango(x, y, r):
    glVertex2f(x, y - r)
    glVertex2f(x + r, y)
    glVertex2f(x, y + r)
    glVertex2f(x - r, y)


def desenhar_minimapa(aspecto, lista, partida, pos, rotacao, tamanho, tempo):
    """Chamar entre inicio_2d e fim_2d."""
    cx, cy = aspecto - MARGEM - MEIO, -1 + MARGEM + MEIO
    retangulo(cx - MEIO - 0.012, cy - MEIO - 0.012, cx + MEIO + 0.012, cy + MEIO + 0.012,
              (0.0, 0.0, 0.0), 0.65)
    retangulo(cx - MEIO, cy - MEIO, cx + MEIO, cy + MEIO, (0.08, 0.08, 0.1), 0.9)

    # nada é desenhado fora do painel
    _, _, largura, altura = glGetIntegerv(GL_VIEWPORT)
    px = altura / 2                                 # pixels por unidade de tela
    glEnable(GL_SCISSOR_TEST)
    glScissor(int((cx - MEIO + aspecto) * px), int((cy - MEIO + 1) * px),
              int(2 * MEIO * px), int(2 * MEIO * px))

    escala = MEIO / ALCANCE
    glPushMatrix()
    glTranslatef(cx, cy, 0.0)
    glScalef(escala, escala, 1.0)
    glRotatef(-rotacao, 0.0, 0.0, 1.0)
    glTranslatef(-pos[0], pos[2], 0.0)
    glCallList(lista)

    alcance = ALCANCE * 1.5 + _M                    # até os cantos do quadrado girado
    glBegin(GL_QUADS)
    for i in partida.plataformas.dinamicas:
        p = partida.plataformas.plats[i]
        if abs(p.x - pos[0]) > alcance or abs(p.z - pos[2]) > alcance:
            continue
        if p.contador > PASSOS_QUEBRAR:
            continue                                # quebrada: some do mapa
        glColor4f(*_cor(CORES[p.tipo]), 1.0)
        _quad(p.x - _M, p.x + _M, p.z - _M, p.z + _M)
    glEnd()
    glPopMatrix()

    # --- marcadores: posição na tela calculada aqui, para não girarem nem mudarem de tamanho ---
    ang = math.radians(rotacao)
    seno, cosseno = math.sin(ang), math.cos(ang)

    def no_mapa(x, z, prender):
        dx, dz = x - pos[0], z - pos[2]
        mx = (dx * cosseno - dz * seno) * escala    # direita do jogador
        my = (-dx * seno - dz * cosseno) * escala   # frente do jogador
        borda = MEIO - 0.025
        f = max(abs(mx), abs(my)) / borda
        if f > 1.0:
            if not prender:
                return None
            mx, my = mx / f, my / f
        return cx + mx, cy + my

    glBegin(GL_QUADS)
    for (x, _, z), pego in zip(partida.cristais.posicoes, partida.cristais.coletados):
        if not pego:
            mx, my = no_mapa(x, z, True)
            glColor4f(0.0, 0.0, 0.0, 1.0)
            _losango(mx, my, 0.023)
            glColor4f(*_cristais.COR, 1.0)
            _losango(mx, my, 0.017)

    mx, my = no_mapa(tamanho - LARGURA_PLAT_ES / 2, 0.0, True)
    for r, cor in ((0.022, (0.0, 0.0, 0.0)),
                   (0.016, (0.2, 1.0, 0.4) if partida.cristais.completos else (1.0, 0.2, 0.2))):
        glColor4f(*cor, 1.0)
        glVertex2f(mx - r, my - r)
        glVertex2f(mx + r, my - r)
        glVertex2f(mx + r, my + r)
        glVertex2f(mx - r, my + r)
    glEnd()

    # monstro: só quando está dentro do alcance, pulsando
    monstro = no_mapa(partida.monstro.x, partida.monstro.z, False)
    if monstro:
        r = 0.02 + 0.006 * math.sin(tempo * 8)
        cor = (1.0, 0.1, 0.1) if partida.monstro.perseguindo else (0.7, 0.25, 0.9)
        for raio, c in ((r + 0.006, (0.0, 0.0, 0.0)), (r, cor)):
            glColor4f(*c, 1.0)
            glBegin(GL_TRIANGLE_FAN)
            for k in range(16):
                a = 2 * math.pi * k / 16
                glVertex2f(monstro[0] + raio * math.cos(a), monstro[1] + raio * math.sin(a))
            glEnd()

    # jogador: seta no centro
    glBegin(GL_TRIANGLES)
    for r, c in ((0.034, (0.0, 0.0, 0.0)), (0.024, (1.0, 1.0, 1.0))):
        glColor4f(*c, 1.0)
        glVertex2f(cx, cy + r)
        glVertex2f(cx + r * 0.7, cy - r * 0.8)
        glVertex2f(cx - r * 0.7, cy - r * 0.8)
    glEnd()
    glDisable(GL_SCISSOR_TEST)

    texto("TAB MAPA", cx, cy + MEIO + 0.03, 0.03)
