"""Colisões entre o boneco e as plataformas (caixas alinhadas aos eixos).

Cada caixa é uma tupla: (x_min, x_max, z_min, z_max, y_topo)
Todas as plataformas começam em y = 0, então só o topo importa.
"""

METADE_BONECO = 0.5      # o boneco é uma caixa de 1 x 2 x 1
TOLERANCIA_DEGRAU = 0.15  # diferença de altura que o boneco "sobe andando"

# plataformas sorteadas (mesmos valores usados em plataforma() no main)
TAMANHO_PLATAFORMA = 10
ALTURA_PLATAFORMA = 2.9

# plataformas de saída/chegada (mesmos valores de plataforma_entrada_saida() em ambiente.py)
LARGURA_PLAT_ES = 10
COMPRIMENTO_PLAT_ES = 20
ALTURA_PLAT_ES = 2.8


def criar_caixas(centros, tamanho_chao):
    """Transforma os centros sorteados + plataformas de saída/chegada em caixas de colisão."""
    caixas = []
    m = TAMANHO_PLATAFORMA / 2
    for (x, y, z) in centros:
        caixas.append((x - m, x + m, z - m, z + m, y + ALTURA_PLATAFORMA))

    c = COMPRIMENTO_PLAT_ES
    # saída (lado -x), onde o jogo começa
    caixas.append((-tamanho_chao, -tamanho_chao + LARGURA_PLAT_ES, -c, c, ALTURA_PLAT_ES))
    # chegada (lado +x), onde o jogo termina
    caixas.append((tamanho_chao - LARGURA_PLAT_ES, tamanho_chao, -c, c, ALTURA_PLAT_ES))
    return caixas


def _sobrepoe(px, pz, caixa):
    x_min, x_max, z_min, z_max, _ = caixa
    return (px + METADE_BONECO > x_min and px - METADE_BONECO < x_max and
            pz + METADE_BONECO > z_min and pz - METADE_BONECO < z_max)


def colide_lateral(px, py, pz, caixas):
    """True se, nessa posição, o boneco bateria na lateral de alguma plataforma
    (ou seja, os pés estão abaixo do topo dela)."""
    for caixa in caixas:
        if _sobrepoe(px, pz, caixa) and py < caixa[4] - TOLERANCIA_DEGRAU:
            return True
    return False


def altura_suporte(px, pz, y_anterior, caixas, piso):
    """Altura da superfície onde o boneco pode pousar agora.
    Só conta plataformas cujo topo estava abaixo (ou na altura) dos pés no frame anterior,
    assim o boneco nunca 'atravessa' o topo caindo e nem é puxado por baixo."""
    melhor = piso
    for caixa in caixas:
        topo = caixa[4]
        if topo > melhor and topo <= y_anterior + TOLERANCIA_DEGRAU and _sobrepoe(px, pz, caixa):
            melhor = topo
    return melhor