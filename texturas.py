"""Texturas do jogo, geradas por código (não precisa de arquivos de imagem).

Uso: carregar_texturas() uma vez, depois de criar o contexto OpenGL.
Para desenhar: usar("madeira") ... glBegin/glEnd ... parar()
A cor do glColor multiplica a textura (GL_MODULATE); branco mostra a cor original.
"""
import random
from OpenGL.GL import *

TAM = 128          # lado das imagens (potência de 2)
_ids = {}


def _ruido(semente, celulas_x, celulas_y):
    """Ruído suave que se repete nas bordas (sem emendas). Valores de 0 a 1."""
    rnd = random.Random(semente)   # gerador próprio: não afeta o sorteio do mapa
    grade = [[rnd.random() for _ in range(celulas_x)] for _ in range(celulas_y)]

    def valor(x, y):
        fx, fy = x * celulas_x / TAM, y * celulas_y / TAM
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        x0, x1 = ix % celulas_x, (ix + 1) % celulas_x
        y0, y1 = iy % celulas_y, (iy + 1) % celulas_y
        a = grade[y0][x0] * (1 - tx) + grade[y0][x1] * tx
        b = grade[y1][x0] * (1 - tx) + grade[y1][x1] * tx
        return a * (1 - ty) + b * ty
    return valor


def _tons(cor, f):
    return tuple(c * f for c in cor)


def _madeira():
    veios, manchas = _ruido(1, 4, 64), _ruido(2, 4, 4)
    tabua = TAM // 4

    def cor(x, y):
        if y % tabua < 2:                       # fresta entre as tábuas
            return (55, 33, 17)
        f = 0.65 + 0.3 * veios(x, y) + 0.2 * manchas(x, y) + 0.05 * (y // tabua % 2)
        return _tons((165, 108, 60), f)
    return cor


def _pedra():
    grao, manchas = _ruido(3, 64, 64), _ruido(4, 8, 8)
    alt, larg = TAM // 8, TAM // 4

    def cor(x, y):
        fila = y // alt
        xt = (x + (larg // 2 if fila % 2 else 0)) % TAM
        if y % alt < 2 or xt % larg < 2:        # argamassa
            return _tons((95, 88, 80), 0.8 + 0.3 * grao(x, y))
        bloco = (fila * 7 + xt // larg * 13) % 5 / 25
        return _tons((150, 135, 118), 0.6 + 0.2 * grao(x, y) + 0.2 * manchas(x, y) + bloco)
    return cor


def _terra():
    grao, manchas = _ruido(5, 64, 64), _ruido(6, 8, 8)
    return lambda x, y: _tons((150, 115, 72), 0.55 + 0.3 * grao(x, y) + 0.35 * manchas(x, y))


def _agua():
    ondas, finas = _ruido(7, 8, 8), _ruido(8, 24, 24)

    def cor(x, y):
        n = 0.65 * ondas(x, y) + 0.35 * finas(x, y)
        brilho = max(0.0, 1 - abs(n - 0.5) * 14)      # linhas claras de reflexo
        return (30 + 45 * n + 70 * brilho, 85 + 60 * n + 60 * brilho, 165 + 50 * n + 35 * brilho)
    return cor


def _escamas():
    grao = _ruido(9, 32, 32)
    r = TAM // 8

    def cor(x, y):
        fila = y // r
        dx = (x + (r // 2 if fila % 2 else 0)) % r - r / 2
        dy = y % r
        d = (dx * dx + dy * dy) ** 0.5 / r
        return _tons((255, 255, 255), 0.95 - 0.45 * min(d, 1.0) + 0.1 * grao(x, y) - 0.05)
    return cor


def _tecido():
    grao = _ruido(10, 64, 64)
    return lambda x, y: _tons((255, 255, 255),
                              0.72 + 0.15 * ((x // 4 + y // 4) % 2) + 0.13 * grao(x, y))


_GERADORES = {"madeira": _madeira, "pedra": _pedra, "terra": _terra,
              "agua": _agua, "escamas": _escamas, "tecido": _tecido}


def _enviar(cor):
    dados = bytearray()
    for y in range(TAM):
        for x in range(TAM):
            for c in cor(x, y):
                dados.append(max(0, min(255, int(c))))

    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    # mipmaps: evitam que a textura "cintile" ao longe
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, TAM, TAM, 0, GL_RGB, GL_UNSIGNED_BYTE, bytes(dados))
    return tid


def carregar_texturas():
    for nome, gerador in _GERADORES.items():
        _ids[nome] = _enviar(gerador())
    glBindTexture(GL_TEXTURE_2D, 0)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)


def usar(nome):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, _ids[nome])


def parar():
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)


def face(a, b, c, d, escala=10.0):
    """Um quadrado (dentro de glBegin(GL_QUADS)). As coordenadas de textura vêm da própria
    posição: a imagem se repete a cada 'escala' unidades, sem esticar."""
    pontos = (a, b, c, d)
    if a[1] == b[1] == c[1] == d[1]:
        u, v = 0, 2        # horizontal (topo/fundo): x e z
    elif a[0] == b[0] == c[0] == d[0]:
        u, v = 2, 1        # parede em x: z e y
    else:
        u, v = 0, 1        # parede em z: x e y
    for p in pontos:
        glTexCoord2f(p[u] / escala, p[v] / escala)
        glVertex3f(*p)


def faces_caixa(x0, x1, y0, y1, z0, z1, cor, tons=(1.0, 1.0, 0.8), escala=10.0):
    """Frente/trás, topo e laterais de uma caixa. tons = (frente e trás, topo, laterais)."""
    def pintar(f):
        glColor3f(*[min(c * f, 1.0) for c in cor])

    pintar(tons[0])
    for z in (z0, z1):
        face((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), escala)
    pintar(tons[1])
    face((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1), escala)
    pintar(tons[2])
    for x in (x0, x1):
        face((x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0), escala)
