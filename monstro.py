import math
import random
from OpenGL.GL import *

from texturas import usar, parar, faces_caixa


def _caixa(x0, x1, y0, y1, z0, z1, cor):
    """Desenha uma caixa colorida, com tons diferentes por face para dar volume."""
    glBegin(GL_QUADS)
    faces_caixa(x0, x1, y0, y1, z0, z1, cor, tons=(1.0, 1.0, 1.0), escala=3.0)
    glEnd()


class Monstro:
    TAMANHO = 3.0
    VEL_PASSEIO = 0.15       # velocidade andando pelo mapa
    # perseguição (o jogador anda a 0.5): de longe ele avança rápido para criar tensão;
    # de perto desacelera e vai ganhando velocidade, dando tempo de escapar
    VEL_APROXIMACAO = 2.7
    DIST_ATAQUE = 60.0
    VEL_ATAQUE_MIN, VEL_ATAQUE_MAX = 0.6, 0.9
    ACELERACAO = 0.002       # por passo (60 por segundo)
    RAIO_CAPTURA = 2.0       # distância horizontal para pegar o jogador
    RAIO_PASSEIO = 120       # quão longe ele escolhe o próximo ponto de passeio

    def __init__(self, limite, y_base, longe_de=None):
        self.limite = limite - 10
        self.y = y_base
        self.reposicionar(longe_de)

    def reposicionar(self, longe_de=None, distancia_min=200):
        """Coloca o monstro num ponto aleatório (longe de 'longe_de', se informado)."""
        while True:
            x = random.uniform(-self.limite, self.limite)
            z = random.uniform(-self.limite, self.limite)
            if longe_de is None or math.hypot(x - longe_de[0], z - longe_de[2]) >= distancia_min:
                break
        self.x, self.z = x, z
        self.rotacao = 0.0
        self.perseguindo = False
        self.vel_ataque = self.VEL_ATAQUE_MIN
        self._novo_destino()

    def _novo_destino(self):
        r = self.RAIO_PASSEIO
        dx = max(-self.limite, min(self.limite, self.x + random.uniform(-r, r)))
        dz = max(-self.limite, min(self.limite, self.z + random.uniform(-r, r)))
        self.destino = (dx, dz)

    def _ir_para(self, tx, tz, vel):
        """Anda em direção ao ponto. Retorna True se chegou."""
        dx, dz = tx - self.x, tz - self.z
        dist = math.hypot(dx, dz)
        if dist <= vel:
            self.x, self.z = tx, tz
            return True
        self.x += dx / dist * vel
        self.z += dz / dist * vel
        # a "frente" do monstro é o lado -z (igual ao boneco)
        self.rotacao = math.degrees(math.atan2(-dx, -dz))
        return False

    def atualizar(self, alvo, perseguindo):
        """alvo = posição [x, y, z] do jogador. perseguindo = jogador está na água?"""
        self.perseguindo = perseguindo
        if perseguindo:
            if self.distancia(alvo) > self.DIST_ATAQUE:
                vel = self.VEL_APROXIMACAO
            else:
                vel = self.vel_ataque
                self.vel_ataque = min(self.VEL_ATAQUE_MAX, self.vel_ataque + self.ACELERACAO)
            self._ir_para(alvo[0], alvo[2], vel)
        else:
            self.vel_ataque = self.VEL_ATAQUE_MIN
            if self._ir_para(self.destino[0], self.destino[1], self.VEL_PASSEIO):
                self._novo_destino()

    def distancia(self, pos):
        """Distância horizontal até pos [x, y, z]."""
        return math.hypot(pos[0] - self.x, pos[2] - self.z)

    def tocou(self, pos):
        """True se o monstro encostou no jogador (pulando bem alto dá pra escapar por cima)."""
        return (self.distancia(pos) < self.RAIO_CAPTURA and
                pos[1] < self.y + self.TAMANHO)

    def desenhar(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotacao, 0.0, 1.0, 0.0)

        t = self.TAMANHO / 2
        if self.perseguindo:
            corpo, olho = (0.6, 0.05, 0.05), (1.0, 1.0, 1.0)
        else:
            corpo, olho = (0.3, 0.1, 0.4), (1.0, 0.9, 0.1)

        usar("escamas")
        _caixa(-t, t, 0, self.TAMANHO, -t, t, corpo)
        # espinhos no topo
        for ex in (-1.0, 0.0, 1.0):
            _caixa(ex - 0.25, ex + 0.25, self.TAMANHO, self.TAMANHO + 0.8, -0.25, 0.25, corpo)
        parar()
        # olhos (lado -z)
        _caixa(-1.0, -0.4, 2.0, 2.5, -t - 0.1, -t, olho)
        _caixa(0.4, 1.0, 2.0, 2.5, -t - 0.1, -t, olho)
        # boca / dentes
        _caixa(-0.8, 0.8, 0.9, 1.4, -t - 0.1, -t, (0.95, 0.95, 0.95))

        glPopMatrix()