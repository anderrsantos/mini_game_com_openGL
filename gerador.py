import math
import random
from collections import deque

nivel = {"facil": [80, 80, 15], "medio": [200, 150, 20], "dificil": [500, 400, 30]}

TAM_PLAT = 10          # tamanho das plataformas sorteadas
LARGURA_ES = 10        # largura das plataformas de saída/chegada
COMPRIMENTO_ES = 20    # comprimento (em z) delas

DIST_MIN = 14          # distância mínima entre centros (evita plataformas sobrepostas)
FOLGA_SOLUCAO = 0.9    # a solução só usa pulos de até 90% do alcance máximo


def alcance_pulo(vel_pulo, gravidade, vel_horizontal):
    """Distância horizontal máxima de um pulo (bordas das plataformas no mesmo nível)."""
    return 2 * vel_pulo / gravidade * vel_horizontal


def _gap(a, b):
    """Distância entre as bordas de duas caixas (x_min, x_max, z_min, z_max)."""
    dx = max(0.0, a[0] - b[1], b[0] - a[1])
    dz = max(0.0, a[2] - b[3], b[2] - a[3])
    return math.hypot(dx, dz)


def _sortear_plataformas(plats, quantidade, largura):
    """Sorteia posições totalmente aleatórias pelo mapa (como no gerador original),
    só descartando as que ficariam sobrepostas a outra plataforma."""
    lim = largura - 20
    B = DIST_MIN
    baldes = {}
    for i, (x, _, z) in enumerate(plats):
        baldes.setdefault((int(x // B), int(z // B)), []).append(i)

    adicionadas = 0
    for _ in range(quantidade * 20):
        if adicionadas >= quantidade:
            break
        x = random.uniform(-lim, lim)
        z = random.uniform(-lim, lim)
        bx, bz = int(x // B), int(z // B)
        livre = True
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in baldes.get((bx + dx, bz + dz), ()):
                    if math.hypot(x - plats[j][0], z - plats[j][2]) < DIST_MIN:
                        livre = False
        if livre:
            baldes.setdefault((bx, bz), []).append(len(plats))
            plats.append((x, 0, z))
            adicionadas += 1


def _tem_solucao(plats, largura, alcance):
    """True se dá para ir da saída até a chegada pulando de plataforma em plataforma."""
    return caminho_solucao(plats, largura, alcance) is not None


def vizinhas(plats, i, alcance):
    """Índices das plataformas que dá para alcançar com um pulo a partir da plataforma i."""
    m = TAM_PLAT / 2

    def caixa(p):
        return (p[0] - m, p[0] + m, p[2] - m, p[2] + m)

    a = caixa(plats[i])
    return [j for j in range(len(plats))
            if j != i and _gap(a, caixa(plats[j])) <= FOLGA_SOLUCAO * alcance]


def caminho_solucao(plats, largura, alcance):
    """Índices das plataformas do caminho mais curto (em pulos) até a chegada,
    ou None se não existir caminho."""
    limite = FOLGA_SOLUCAO * alcance
    c = COMPRIMENTO_ES
    m = TAM_PLAT / 2
    saida = (-largura, -largura + LARGURA_ES, -c, c)
    chegada = (largura - LARGURA_ES, largura, -c, c)
    caixas = [(x - m, x + m, z - m, z + m) for (x, _, z) in plats]

    B = limite + TAM_PLAT          # tamanho do balde (busca só nos vizinhos)
    baldes = {}
    for i, (x, _, z) in enumerate(plats):
        baldes.setdefault((int(x // B), int(z // B)), []).append(i)

    # busca em largura; 'origem' guarda de onde veio, para refazer o caminho
    origem = {i: None for i, cx in enumerate(caixas) if _gap(saida, cx) <= limite}
    fila = deque(origem)
    while fila:
        i = fila.popleft()
        if _gap(caixas[i], chegada) <= limite:
            caminho = []
            while i is not None:
                caminho.append(i)
                i = origem[i]
            return caminho[::-1]
        bx, bz = int(plats[i][0] // B), int(plats[i][2] // B)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in baldes.get((bx + dx, bz + dz), ()):
                    if j not in origem and _gap(caixas[i], caixas[j]) <= limite:
                        origem[j] = i
                        fila.append(j)
    return None


def gerar_centros_plataformas(num_plataformas, largura_chao, alcance):
    """Gera os centros (x, y, z) das plataformas, sorteados aleatoriamente pelo mapa inteiro.

    alcance = distância horizontal que um pulo alcança (use alcance_pulo()).
    Começa com num_plataformas; se com isso não existir caminho possível da saída até a
    chegada, vai acrescentando mais plataformas aleatórias até existir.
    """
    plats = []
    _sortear_plataformas(plats, num_plataformas, largura_chao)
    while not _tem_solucao(plats, largura_chao, alcance) and len(plats) < 20000:
        _sortear_plataformas(plats, max(10, len(plats) // 20), largura_chao)
    return plats