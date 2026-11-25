"""Cristais a coletar (clique) e portal da chegada, que abre com todos eles."""
import math
import random
from OpenGL.GL import *

from colisao import ALTURA_PLATAFORMA, ALTURA_PLAT_ES
from gerador import caminho_solucao, vizinhas

ALCANCE_COLETA = 6.0       # distância horizontal
ALTURA_COLETA = 5.0        # diferença de altura
ALTURA_FEIXE = 60.0
COR = (0.3, 1.0, 0.9)


def escolher_lugares(centros, tamanho_chao, alcance, quantidade):
    """Retorna (índices das plataformas com cristal, índices protegidos).
    Cada cristal fica a um pulo do caminho garantido, então sempre dá para pegar todos."""
    caminho = caminho_solucao(centros, tamanho_chao, alcance) or []
    protegidas = set(caminho)
    lugares = []
    quantidade = min(quantidade, len(caminho))
    for k in range(quantidade):
        no = caminho[int((k + 0.5) * len(caminho) / quantidade)]
        opcoes = [j for j in vizinhas(centros, no, alcance)
                  if j not in caminho and j not in lugares]
        lugares.append(random.choice(opcoes) if opcoes else no)
    protegidas.update(lugares)
    return lugares, protegidas


class Cristais:
    def __init__(self, posicoes):
        self.posicoes = [(x, ALTURA_PLATAFORMA + 2.0, z) for (x, _, z) in posicoes]
        self.reiniciar()

    def reiniciar(self):
        self.coletados = [False] * len(self.posicoes)

    @property
    def completos(self):
        return all(self.coletados)

    def coletar(self, pos):
        """Pega o cristal que estiver ao alcance. True se pegou."""
        for i, (x, y, z) in enumerate(self.posicoes):
            if (not self.coletados[i] and math.hypot(pos[0] - x, pos[2] - z) < ALCANCE_COLETA
                    and abs(pos[1] + 1.0 - y) < ALTURA_COLETA):
                self.coletados[i] = True
                return True
        return False

    def _octaedro(self):
        r, h = 0.7, 1.2
        base = [(r, 0, 0), (0, 0, r), (-r, 0, 0), (0, 0, -r)]
        glBegin(GL_TRIANGLES)
        for i in range(4):
            a, b = base[i], base[(i + 1) % 4]
            for topo, brilho in ((h, 1.0 - 0.12 * i), (-h, 0.7 - 0.1 * i)):
                glColor3f(*[c * brilho for c in COR])
                glVertex3f(*a)
                glVertex3f(*b)
                glVertex3f(0, topo, 0)
        glEnd()

    def desenhar(self, tempo):
        for i, (x, y, z) in enumerate(self.posicoes):
            if not self.coletados[i]:
                glPushMatrix()
                glTranslatef(x, y + 0.3 * math.sin(tempo * 2 + i), z)
                glRotatef(tempo * 90 % 360, 0.0, 1.0, 0.0)
                self._octaedro()
                glPopMatrix()

    def desenhar_luzes(self, olho, tamanho_chao, tempo):
        """Feixes de luz e portal. Translúcidos: depois da água, sem neblina."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glBegin(GL_QUADS)
        for i, (x, y, z) in enumerate(self.posicoes):
            if self.coletados[i]:
                continue
            # faixa vertical sempre virada para a câmera
            dx, dz = x - olho[0], z - olho[2]
            d = math.hypot(dx, dz) or 1.0
            larg = 0.6 + d * 0.004              # de longe continua visível
            lx, lz = -dz / d * larg, dx / d * larg
            forca = 0.55 * min(1.0, d / 60)     # de perto fica suave, não ofusca
            for lado in (-1, 1):
                for px, py, alfa in ((0, y, forca), (lado, y, 0.0),
                                     (lado, y + ALTURA_FEIXE, 0.0), (0, y + ALTURA_FEIXE, 0.0)):
                    glColor4f(COR[0], COR[1], COR[2], alfa)
                    glVertex3f(x + lx * px, py, z + lz * px)
        glEnd()

        # portal no vão da chegada: vermelho = fechado, verde = aberto
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        x = tamanho_chao - 0.1
        cor = (0.1, 1.0, 0.4) if self.completos else (1.0, 0.1, 0.1)
        glColor4f(cor[0], cor[1], cor[2], 0.5 + 0.15 * math.sin(tempo * 3))
        glBegin(GL_QUADS)
        glVertex3f(x, ALTURA_PLAT_ES, -15)
        glVertex3f(x, ALTURA_PLAT_ES, 15)
        glVertex3f(x, 15, 15)
        glVertex3f(x, 15, -15)
        glEnd()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

    def desenhar_hud(self, aspecto, piscar):
        """Losangos no canto superior esquerdo (chamar em modo 2D).
        piscar: os que faltam piscam em vermelho (chegou ao portal sem todos)."""
        h = 0.04
        l = h * 0.6
        total = sum(self.coletados)
        for i in range(len(self.coletados)):
            cx, cy = -aspecto + 0.08 + i * 2.8 * l, 0.92
            if i < total:
                glColor4f(COR[0], COR[1], COR[2], 1.0)
            elif piscar:
                glColor4f(1.0, 0.15, 0.1, 0.95)
            else:
                glColor4f(0.0, 0.0, 0.0, 0.4)
            glBegin(GL_QUADS)
            glVertex2f(cx, cy - h)
            glVertex2f(cx + l, cy)
            glVertex2f(cx, cy + h)
            glVertex2f(cx - l, cy)
            glEnd()
