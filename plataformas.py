"""Plataformas especiais: móvel, afunda, quebra e impulso.

As plataformas protegidas (caminho garantido e cristais) são sempre normais, então o mapa
continua tendo solução. As caixas de colisão são atualizadas aqui, na mesma ordem dos centros.
"""
import math
import random
from OpenGL.GL import *

from ambiente import plataforma
from colisao import (TAMANHO_PLATAFORMA, ALTURA_PLATAFORMA, METADE_BONECO, _sobrepoe,
                     colide_lateral)
from texturas import usar, parar

NORMAL, MOVEL, AFUNDA, QUEBRA, IMPULSO = "normal", "movel", "afunda", "quebra", "impulso"
CHANCES = [(MOVEL, 0.12), (AFUNDA, 0.12), (QUEBRA, 0.12), (IMPULSO, 0.06)]

CORES = {NORMAL: (1.0, 1.0, 1.0), MOVEL: (0.45, 0.75, 1.0), AFUNDA: (0.5, 0.75, 0.4),
         QUEBRA: (1.0, 0.45, 0.35), IMPULSO: (1.0, 0.95, 0.3)}

MULT_IMPULSO = 1.5         # multiplica a velocidade do pulo
VEL_MOVEL = 0.08           # velocidade máxima, por passo
PERCURSO_MIN, PERCURSO_MAX = 3.0, 10.0
VEL_AFUNDAR, VEL_SUBIR = 0.02, 0.01
TOPO_AFUNDADA = 1.0        # nível do fundo: em cima dela você já está na água
PASSOS_QUEBRAR = 45        # 0.75 s depois de pisar
PASSOS_VOLTAR = 240        # 4 s quebrada
FOLGA = 1.0                # espaço mínimo entre uma móvel e as outras
DISTANCIA_DESENHO = 450.0  # depois disso a neblina já cobriu tudo

_M = TAMANHO_PLATAFORMA / 2
_CAIXA_VAZIA = (1e9, 1e9, 1e9, 1e9, -1e9)   # não colide com nada


class _Plat:
    def __init__(self, centro):
        self.x0, _, self.z0 = centro
        self.tipo = NORMAL
        self.eixo = 0              # móvel: 0 anda em x, 1 anda em z
        self.percurso = 0.0
        self.fase0 = 0.0
        self.reiniciar()

    def reiniciar(self):
        self.x, self.z = self.x0, self.z0
        self.topo = ALTURA_PLATAFORMA
        self.contador = 0          # quebra: passos desde que foi pisada
        self.fase = self.fase0
        if self.tipo == MOVEL:
            self._posicionar()
        self.x_ant, self.z_ant = self.x, self.z

    def _posicionar(self):
        d = self.percurso * math.sin(self.fase)
        if self.eixo == 0:
            self.x = self.x0 + d
        else:
            self.z = self.z0 + d

    def mover(self):
        self.x_ant, self.z_ant = self.x, self.z
        self.fase += VEL_MOVEL / self.percurso
        self._posicionar()

    def caixa(self):
        if self.contador > PASSOS_QUEBRAR:
            return _CAIXA_VAZIA
        return (self.x - _M, self.x + _M, self.z - _M, self.z + _M, self.topo)


class Plataformas:
    def __init__(self, centros, protegidas, caixas, tamanho_chao):
        """caixas: lista de criar_caixas(); é alterada aqui conforme as plataformas mudam."""
        self.caixas = caixas
        self.tamanho_chao = tamanho_chao
        self.plats = [_Plat(c) for c in centros]
        self.impulso_pronto = False      # o jogador está em cima de uma de impulso?

        ocupado = [p.caixa()[:4] for p in self.plats]
        for i, p in enumerate(self.plats):
            if i in protegidas:
                continue
            sorteio = random.random()
            for tipo, chance in CHANCES:
                if sorteio < chance:
                    if tipo != MOVEL or self._preparar_movel(i, ocupado):
                        p.tipo = tipo
                    break
                sorteio -= chance

        self.dinamicas = [i for i, p in enumerate(self.plats) if p.tipo not in (NORMAL, IMPULSO)]
        self.reiniciar()

    def _preparar_movel(self, i, ocupado):
        """Acha um percurso que não encoste em nenhuma outra. False se não couber."""
        p = self.plats[i]
        limite = self.tamanho_chao - 15 - FOLGA       # longe da saída e da chegada
        for eixo in random.sample((0, 1), 2):
            for percurso in (PERCURSO_MAX, 7.0, 5.0, PERCURSO_MIN):
                ex, ez = (percurso, 0.0) if eixo == 0 else (0.0, percurso)
                a = (p.x0 - _M - ex, p.x0 + _M + ex, p.z0 - _M - ez, p.z0 + _M + ez)
                if max(-a[0], a[1], -a[2], a[3]) > limite:
                    continue
                if all(j == i or a[0] - FOLGA >= b[1] or a[1] + FOLGA <= b[0] or
                       a[2] - FOLGA >= b[3] or a[3] + FOLGA <= b[2]
                       for j, b in enumerate(ocupado)):
                    p.eixo, p.percurso = eixo, percurso
                    p.fase0 = random.uniform(0, 2 * math.pi)
                    ocupado[i] = a          # reserva todo o percurso
                    return True
        return False

    def reiniciar(self):
        self.impulso_pronto = False
        for i, p in enumerate(self.plats):
            p.reiniciar()
            self.caixas[i] = p.caixa()

    def _em_cima(self, i, pos):
        caixa = self.caixas[i]
        return abs(pos[1] - caixa[4]) < 0.05 and _sobrepoe(pos[0], pos[2], caixa)

    def atualizar(self, pos):
        """Um passo. Pode alterar pos: a móvel leva o jogador junto (ou o empurra)."""
        for i in self.dinamicas:
            p = self.plats[i]
            if p.tipo == MOVEL:
                self._passo_movel(i, p, pos)
            elif p.tipo == AFUNDA:
                if self._em_cima(i, pos):
                    p.topo = max(TOPO_AFUNDADA, p.topo - VEL_AFUNDAR)
                elif p.topo < ALTURA_PLATAFORMA:
                    p.topo = min(ALTURA_PLATAFORMA, p.topo + VEL_SUBIR)
                else:
                    continue
                self.caixas[i] = p.caixa()
            else:
                self._passo_quebra(i, p, pos)

        self.impulso_pronto = any(p.tipo == IMPULSO and self._em_cima(i, pos)
                                  for i, p in enumerate(self.plats))

    def _passo_movel(self, i, p, pos):
        em_cima = self._em_cima(i, pos)
        p.mover()
        self.caixas[i] = caixa = p.caixa()
        dentro = _sobrepoe(pos[0], pos[2], caixa) and pos[1] < p.topo - 0.15
        if em_cima or dentro:
            limite = self.tamanho_chao - METADE_BONECO
            x = max(-limite, min(limite, pos[0] + p.x - p.x_ant))
            z = max(-limite, min(limite, pos[2] + p.z - p.z_ant))
            if not colide_lateral(x, pos[1], z, self.caixas):
                pos[0], pos[2] = x, z

    def _passo_quebra(self, i, p, pos):
        if p.contador == 0:
            if self._em_cima(i, pos):
                p.contador = 1
            return
        p.contador += 1
        if p.contador > PASSOS_QUEBRAR + PASSOS_VOLTAR:
            original = (p.x0 - _M, p.x0 + _M, p.z0 - _M, p.z0 + _M, p.topo)
            if _sobrepoe(pos[0], pos[2], original) and pos[1] < p.topo:
                p.contador -= 1          # espera o jogador sair de baixo
            else:
                p.contador = 0
        self.caixas[i] = p.caixa()

    # --- desenho ---

    def compilar(self):
        """Uma display list por tipo, com a plataforma na origem. Chamar com as texturas prontas."""
        self.listas = {}
        for tipo in (MOVEL, AFUNDA, QUEBRA):
            lista = glGenLists(1)
            glNewList(lista, GL_COMPILE)
            plataforma((0.0, 0.0, 0.0), TAMANHO_PLATAFORMA, TAMANHO_PLATAFORMA,
                       ALTURA_PLATAFORMA, CORES[tipo])
            glEndList()
            self.listas[tipo] = lista

    def fixas(self):
        """[(centro, cor)] das que nunca mudam: vão para a display list do cenário."""
        return [((p.x0, 0.0, p.z0), CORES[p.tipo]) for p in self.plats
                if p.tipo in (NORMAL, IMPULSO)]

    def desenhar(self, olho, f):
        """f: fração entre o passo anterior e o atual (0 a 1)."""
        usar("madeira")
        for i in self.dinamicas:
            p = self.plats[i]
            if (p.x - olho[0]) ** 2 + (p.z - olho[2]) ** 2 > DISTANCIA_DESENHO ** 2:
                continue
            x = p.x_ant + (p.x - p.x_ant) * f
            z = p.z_ant + (p.z - p.z_ant) * f
            y = p.topo - ALTURA_PLATAFORMA
            if p.tipo == QUEBRA and p.contador > 0:
                if p.contador <= PASSOS_QUEBRAR:
                    x += 0.12 * math.sin(p.contador * 1.9)      # treme antes de quebrar
                else:
                    y -= 0.15 * (p.contador - PASSOS_QUEBRAR)   # cai
                    if y < -ALTURA_PLATAFORMA:
                        continue
            glPushMatrix()
            glTranslatef(x, y, z)
            glCallList(self.listas[p.tipo])
            glPopMatrix()
        parar()
