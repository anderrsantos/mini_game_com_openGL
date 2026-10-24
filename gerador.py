import random

nivel = {"facil": [100, 80, 15], "medio": [200, 150, 20], "dificil": [500, 400, 30]}

def gerar_centros_plataformas(num_plataformas, largura_chao):
    """Gera os centros (x, y, z) sorteados das plataformas de acordo com a dificuldade"""

    
    centros = []

    for _ in range(num_plataformas):
        x = random.uniform(-largura_chao, largura_chao)
        z = random.uniform(-largura_chao, largura_chao)
        centros.append((x, 0, z))

    return centros