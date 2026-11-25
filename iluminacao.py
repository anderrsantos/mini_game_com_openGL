"""Luz do sol e sombras de contato."""
import math
from OpenGL.GL import *


def _direcao(elevacao):
    e = math.radians(elevacao)
    return (math.cos(e), math.sin(e), 0.0)


DIRECAO_SOL_CEU = _direcao(15)     # onde o sol aparece no céu (lado da chegada)
# a luz vem de um pouco mais alto, senão os topos das plataformas ficariam escuros
DIRECAO_LUZ = _direcao(38)
LUZ_AMBIENTE = (0.46, 0.47, 0.56, 1.0)   # azulada, do céu
LUZ_SOL = (0.95, 0.76, 0.55, 1.0)        # quente, de fim de tarde

LADOS_SOMBRA = 24


def ligar_luz():
    """Chamar com a matriz da câmera já aplicada."""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, LUZ_AMBIENTE)
    glLightfv(GL_LIGHT0, GL_POSITION, (*DIRECAO_LUZ, 0.0))    # w = 0: direcional
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, LUZ_SOL)
    # glColor passa a ser a cor do material
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)


def desligar_luz():
    glDisable(GL_COLOR_MATERIAL)
    glDisable(GL_LIGHTING)


def sombra(x, y, z, raio, forca):
    """Mancha escura e suave numa superfície horizontal. Mostra onde o jogador vai cair."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.0, 0.0, 0.0, forca)
    glVertex3f(x, y, z)
    glColor4f(0.0, 0.0, 0.0, 0.0)
    for i in range(LADOS_SOMBRA + 1):
        a = 2 * math.pi * i / LADOS_SOMBRA
        glVertex3f(x + raio * math.cos(a), y, z + raio * math.sin(a))
    glEnd()
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
