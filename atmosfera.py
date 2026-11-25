"""Céu de pôr do sol (cúpula, sol e nuvens) e neblina."""
import math
from OpenGL.GL import *

from texturas import usar, parar

COR_HORIZONTE = (0.93, 0.72, 0.56)   # também é a cor da neblina e do fundo
COR_ZENITE = (0.18, 0.34, 0.62)
NEBLINA_INICIO, NEBLINA_FIM = 90.0, 440.0   # termina antes do far (500): esconde o corte

RAIO = 100.0
SETORES = 32
# alturas (graus) dos anéis da cúpula
ANEIS = (-12, 0, 6, 14, 24, 38, 55, 75, 90)


def _direcao(elevacao, azimute):
    e, a = math.radians(elevacao), math.radians(azimute)
    return (RAIO * math.cos(e) * math.cos(a), RAIO * math.sin(e), RAIO * math.cos(e) * math.sin(a))


def _cor_ceu(elevacao):
    # abaixo de 6 graus o céu tem exatamente a cor da neblina, sem emenda com o cenário
    f = max(0.0, min(1.0, (elevacao - 6) / 60)) ** 0.7
    return [h + (z - h) * f for h, z in zip(COR_HORIZONTE, COR_ZENITE)]


def _cupula():
    glBegin(GL_QUADS)
    for e0, e1 in zip(ANEIS, ANEIS[1:]):
        for s in range(SETORES):
            a0, a1 = s * 360 / SETORES, (s + 1) * 360 / SETORES
            for e, a in ((e0, a0), (e0, a1), (e1, a1), (e1, a0)):
                glColor3f(*_cor_ceu(e))
                glVertex3f(*_direcao(e, a))
    glEnd()


def _disco(raio, cor, alfa_centro, alfa_borda, elevacao=15):
    """Disco no lado +x, a direção da chegada: o sol serve de guia."""
    cx, cy, _ = _direcao(elevacao, 0)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(cor[0], cor[1], cor[2], alfa_centro)
    glVertex3f(cx, cy, 0.0)
    glColor4f(cor[0], cor[1], cor[2], alfa_borda)
    for i in range(33):
        a = 2 * math.pi * i / 32
        # disco num plano perpendicular à direção do sol
        sobe = raio * math.sin(a)
        e = math.radians(elevacao)
        glVertex3f(cx - sobe * math.sin(e), cy + sobe * math.cos(e), raio * math.cos(a))
    glEnd()


def _nuvens():
    glBegin(GL_QUADS)
    for e0, e1 in zip(ANEIS[2:-1], ANEIS[3:]):
        for s in range(SETORES):
            a0, a1 = s * 360 / SETORES, (s + 1) * 360 / SETORES
            for e, a in ((e0, a0), (e0, a1), (e1, a1), (e1, a0)):
                x, y, z = _direcao(e, a)
                # some perto do horizonte, onde a textura ficaria espremida
                glColor4f(1.0, 0.9, 0.84, max(0.0, min(1.0, (e - 6) / 20)) * 0.85)
                glTexCoord2f(x / y * 0.3, z / y * 0.3)
                glVertex3f(x, y, z)
    glEnd()


def compilar_ceu():
    """Retorna (lista da cúpula com o sol, lista das nuvens)."""
    ceu = glGenLists(1)
    glNewList(ceu, GL_COMPILE)
    _cupula()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)         # brilho: soma com o céu
    _disco(32, (1.0, 0.6, 0.3), 0.45, 0.0)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    _disco(5, (1.0, 0.95, 0.8), 1.0, 1.0)
    glDisable(GL_BLEND)
    glEndList()

    nuvens = glGenLists(1)
    glNewList(nuvens, GL_COMPILE)
    _nuvens()
    glEndList()
    return ceu, nuvens


def desenhar_ceu(listas, tempo):
    """Chamar só com a rotação da câmera aplicada (sem translação): o céu fica 'no infinito'."""
    glDisable(GL_FOG)
    glDisable(GL_DEPTH_TEST)
    glCallList(listas[0])

    usar("nuvens")
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glTranslatef(tempo * 0.004 % 1.0, tempo * 0.002 % 1.0, 0.0)
    glCallList(listas[1])
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glDisable(GL_BLEND)
    parar()
    glEnable(GL_DEPTH_TEST)


def ligar_neblina():
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, (*COR_HORIZONTE, 1.0))
    glFogf(GL_FOG_START, NEBLINA_INICIO)
    glFogf(GL_FOG_END, NEBLINA_FIM)
    glHint(GL_FOG_HINT, GL_NICEST)


def desligar_neblina():
    glDisable(GL_FOG)
