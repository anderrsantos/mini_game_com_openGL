"""Sons do jogo, sintetizados por código (não precisa de arquivos de áudio).

Usa o pygame só para tocar (pip install pygame). Sem ele, ou sem placa de som,
o jogo funciona normalmente, mudo.
"""
import array
import math
import os
import random

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
try:
    import pygame.mixer as _mixer
except ImportError:
    _mixer = None

TAXA = 22050
VOLUMES = {"passo": 0.25, "passo_agua": 0.3, "pulo": 0.3, "impulso": 0.45, "pouso": 0.45,
           "mergulho": 0.7, "cristal": 0.5, "portal": 0.6, "quebra": 0.5, "estalo": 0.5,
           "morte": 0.8, "vitoria": 0.6, "coracao": 0.9, "menu": 0.25, "confirma": 0.4}
VOLUME_MAR = 0.18

_sons = {}
_canal_mar = None
_mudo = False
_ate_batida = 0.0       # segundos até a próxima batida do coração


# --- síntese: cada função devolve amostras de -1 a 1 ---

def _amostras(duracao, f):
    """f(t, p): t em segundos, p de 0 a 1 ao longo do som."""
    n = int(duracao * TAXA)
    return [f(i / TAXA, i / n) for i in range(n)]


def _seno(freq, t):
    return math.sin(2 * math.pi * freq * t)


def _varredura(f0, f1, duracao, decai):
    """Nota que desliza de f0 para f1."""
    return _amostras(duracao, lambda t, p: math.exp(-decai * p) * min(1.0, p * 30) *
                     _seno(f0 + (f1 - f0) * p / 2, t))


def _ruido(duracao, suavidade, envelope, semente=1):
    """Ruído filtrado: suavidade perto de 0 = grave e abafado, 1 = chiado."""
    rnd = random.Random(semente)      # não afeta o sorteio do mapa
    v = 0.0
    saida = []
    n = int(duracao * TAXA)
    for i in range(n):
        v += (rnd.uniform(-1, 1) - v) * suavidade
        saida.append(v * envelope(i / n))
    pico = max(abs(a) for a in saida) or 1.0
    return [a / pico for a in saida]


def _notas(frequencias, passo, duracao):
    """Sequência de notas com brilho de sino."""
    total = [0.0] * int((passo * (len(frequencias) - 1) + duracao) * TAXA)
    for k, freq in enumerate(frequencias):
        ini = int(k * passo * TAXA)
        nota = _amostras(duracao, lambda t, p: math.exp(-5 * p) * min(1.0, p * 60) * (1 - p) *
                         (_seno(freq, t) + 0.4 * _seno(2 * freq, t) + 0.15 * _seno(3 * freq, t)))
        for i, a in enumerate(nota):
            if ini + i < len(total):
                total[ini + i] += a
    return total


def _somar(*partes):
    saida = [0.0] * max(len(p) for p in partes)
    for p in partes:
        for i, a in enumerate(p):
            saida[i] += a
    return saida


def _batida():
    def tum(atraso, forca):
        n = [0.0] * int(atraso * TAXA)
        return n + [forca * a for a in _varredura(75, 35, 0.16, 4)]
    return _somar(tum(0.0, 1.0), tum(0.17, 0.7))


def _mar():
    """Ondas em laço: o começo e o fim têm o mesmo volume e são emendados."""
    dur, emenda = 5.0, 0.5
    bruto = _ruido(dur + emenda, 0.05,
                   lambda p: 0.65 + 0.35 * math.sin(2 * math.pi * p * (dur + emenda) / dur), 7)
    n, m = int(dur * TAXA), int(emenda * TAXA)
    return [bruto[i] * (i / m) + bruto[n + i] * (1 - i / m) if i < m else bruto[i]
            for i in range(n)]


def _criar():
    cai = lambda k: (lambda p: math.exp(-k * p) * (1 - p) * min(1.0, p * 40))
    return {
        "passo": _ruido(0.09, 0.25, cai(6), 2),
        "passo_agua": _ruido(0.2, 0.4, cai(4), 3),
        "pulo": _varredura(220, 520, 0.18, 3),
        "impulso": _somar(_varredura(200, 1100, 0.4, 2), _varredura(300, 1650, 0.4, 3)),
        "pouso": _somar(_ruido(0.14, 0.15, cai(6), 4), _varredura(140, 70, 0.14, 4)),
        "mergulho": _somar(_ruido(0.7, 0.35, cai(4), 5), _varredura(300, 80, 0.25, 3)),
        "cristal": _notas((988, 1319, 1976), 0.08, 0.5),
        "portal": _notas((392, 523, 659, 784, 1047), 0.12, 0.9),
        "estalo": _ruido(0.12, 0.6, cai(9), 6),
        "quebra": _ruido(0.45, 0.2, cai(4), 8),
        "morte": _somar(_varredura(160, 30, 1.0, 2), _ruido(1.0, 0.08, cai(3), 9)),
        "vitoria": _notas((523, 659, 784, 1047, 784, 1047, 1319), 0.14, 1.0),
        "coracao": _batida(),
        "menu": _varredura(500, 560, 0.06, 3),
        "confirma": _notas((523, 784), 0.07, 0.3),
        "mar": _mar(),
    }


def _para_bytes(amostras):
    pico = max(1.0, max(abs(a) for a in amostras))
    return array.array("h", [int(a / pico * 32000) for a in amostras]).tobytes()


# --- uso no jogo ---

def iniciar():
    """Prepara os sons. False (com aviso no terminal) se não der para tocar."""
    global _canal_mar
    if _mixer is None:
        print("Sem som: instale o pygame com  pip install pygame")
        return False
    try:
        # allowedchanges=0: o dispositivo se adapta ao formato das nossas amostras
        _mixer.init(TAXA, -16, 1, 512, allowedchanges=0)
        _mixer.set_num_channels(16)
        _mixer.set_reserved(1)                  # canal 0: só o mar
        for nome, amostras in _criar().items():
            _sons[nome] = _mixer.Sound(buffer=_para_bytes(amostras))
            _sons[nome].set_volume(VOLUMES.get(nome, 1.0))
        _canal_mar = _mixer.Channel(0)
        _canal_mar.play(_sons["mar"], loops=-1)
        _canal_mar.set_volume(VOLUME_MAR)
    except Exception as erro:     # sem placa de som, por exemplo: segue mudo
        print("Sem som:", erro)
        _sons.clear()
        _canal_mar = None
        return False
    return True


def tocar(nome):
    if _sons and not _mudo:
        _sons[nome].play()


def alternar_mudo():
    """Retorna True se ficou mudo."""
    global _mudo
    _mudo = not _mudo
    if _canal_mar:
        _canal_mar.set_volume(0.0 if _mudo else VOLUME_MAR)
    if _mudo and _sons:
        for nome, som in _sons.items():
            if nome != "mar":
                som.stop()
    return _mudo


def coracao(perigo, dt):
    """Chamar a cada quadro em que o monstro persegue. Bate mais rápido e mais forte de perto."""
    global _ate_batida
    _ate_batida -= dt
    if _ate_batida <= 0:
        _ate_batida = 1.0 - 0.6 * perigo
        if _sons:
            _sons["coracao"].set_volume(VOLUMES["coracao"] * (0.4 + 0.6 * perigo))
        tocar("coracao")


def encerrar():
    if _sons:
        _sons.clear()
        _mixer.quit()
