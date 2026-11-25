"""Dificuldades e recordes (melhor tempo de cada uma, salvo em recordes.json)."""
import json
import os

# plataformas: quantidade inicial (o gerador acrescenta até existir caminho)
# especiais: multiplica a chance de plataformas especiais
# monstro: atributos trocados em Monstro
DIFICULDADES = {
    "FÁCIL": {"plataformas": 1800, "especiais": 0.5, "cristais": 3,
              "monstro": {"VEL_APROXIMACAO": 1.8, "VEL_ATAQUE_MIN": 0.5, "VEL_ATAQUE_MAX": 0.7}},
    "MÉDIO": {"plataformas": 500, "especiais": 1.0, "cristais": 5, "monstro": {}},
    "DIFÍCIL": {"plataformas": 500, "especiais": 1.6, "cristais": 7,
                "monstro": {"VEL_APROXIMACAO": 3.2, "VEL_ATAQUE_MIN": 0.7, "VEL_ATAQUE_MAX": 1.1}},
}

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordes.json")


def ler_recordes():
    try:
        with open(ARQUIVO, encoding="utf-8") as arq:
            dados = json.load(arq)
        return {k: float(v) for k, v in dados.items() if k in DIFICULDADES}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def salvar_tempo(nome, tempo):
    """Guarda o tempo se for o melhor. True se bateu o recorde."""
    recordes = ler_recordes()
    if nome in recordes and recordes[nome] <= tempo:
        return False
    recordes[nome] = tempo
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as arq:
            json.dump(recordes, arq, ensure_ascii=False, indent=2)
    except OSError as erro:
        print("Não consegui salvar o recorde:", erro)
    return True


def formatar_tempo(t):
    return "%02d:%04.1f" % divmod(int(t * 10) / 10, 60)
