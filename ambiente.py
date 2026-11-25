from OpenGL.GL import *

from texturas import usar, parar, face, faces_caixa


LADRILHO = 25.0   # a neblina pode ser calculada por vértice: faces grandes são divididas


def _face_dividida(a, b, c, d, escala):
    """Retângulo a-b-c-d dividido em ladrilhos (dentro de glBegin(GL_QUADS))."""
    def ponto(u, v):
        return tuple(p + (q - p) * u + (r - p) * v for p, q, r in zip(a, b, d))

    def fracoes(p, q):
        comprimento = sum(abs(i - j) for i, j in zip(p, q))   # lados alinhados aos eixos
        n = max(1, int(round(comprimento / LADRILHO)))
        return [i / n for i in range(n + 1)]

    us, vs = fracoes(a, b), fracoes(a, d)
    for u0, u1 in zip(us, us[1:]):
        for v0, v1 in zip(vs, vs[1:]):
            face(ponto(u0, v0), ponto(u1, v0), ponto(u1, v1), ponto(u0, v1), escala)


def chao(tamanho, altura):
    t = tamanho
    h = altura
    usar("terra")
    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)
    _face_dividida((-t, h, -t), (t, h, -t), (t, h, t), (-t, h, t), 20.0)
    glEnd()
    parar()


def parede(tamanho, altura):
    t = tamanho
    h = altura
    usar("pedra")
    glBegin(GL_QUADS)

    # laterais
    glColor3f(0.85, 0.85, 0.85)
    for z in (-t, t):
        _face_dividida((-t, 0, z), (t, 0, z), (t, h, z), (-t, h, z), 20.0)

    # saída (-t) e entrada (+t), com um vão de 30 x 15 no meio
    glColor3f(1.0, 1.0, 1.0)
    for x in (-t, t):
        _face_dividida((x, 0, -t), (x, 0, -15), (x, h, -15), (x, h, -t), 20.0)
        _face_dividida((x, 0, t), (x, 0, 15), (x, h, 15), (x, h, t), 20.0)
        face((x, 15, -15), (x, 15, 15), (x, h, 15), (x, h, -15), 20.0)

    glEnd()
    parar()


def compilar_agua(tamanho, altura):
    """Superfície da água numa display list.
    (As laterais não são desenhadas: ficariam no mesmo plano dos muros.)"""
    t = tamanho
    h = altura
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    glBegin(GL_QUADS)
    glColor4f(1.0, 1.0, 1.0, 0.8)
    _face_dividida((-t, h, -t), (t, h, -t), (t, h, t), (-t, h, t), 25.0)
    glEnd()
    glEndList()
    return lista


def agua(lista, tempo):
    """Superfície translúcida e em movimento. Desenhar depois do que é opaco."""
    usar("agua")
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # desloca as coordenadas de textura para a água "correr"
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glTranslatef(tempo * 0.03 % 1.0, tempo * 0.02 % 1.0, 0.0)
    glMatrixMode(GL_MODELVIEW)

    glCallList(lista)

    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glDisable(GL_BLEND)
    parar()


def plataforma_entrada_saida(largura_chao):
    largura = 10
    comprimento = 20
    altura = 2.8

    usar("pedra")
    glBegin(GL_QUADS)
    for lado in (1, -1):          # entrada (+x) e saída (-x)
        x0 = lado * largura_chao
        x1 = lado * (largura_chao - largura)
        # topo
        glColor3f(1.0, 1.0, 1.0)
        face((x0, altura, -comprimento), (x0, altura, comprimento),
             (x1, altura, comprimento), (x1, altura, -comprimento))
        # laterais
        glColor3f(0.75, 0.75, 0.75)
        face((x1, 0, -comprimento), (x1, 0, comprimento),
             (x1, altura, comprimento), (x1, altura, -comprimento))
        for z in (-comprimento, comprimento):
            face((x0, 0, z), (x1, 0, z), (x1, altura, z), (x0, altura, z),
                 normal=(0.0, 0.0, 1.0 if z > 0 else -1.0))
    glEnd()
    parar()


def caixa_entrada_saida(largura_chao):
    largura = 10
    comprimento = 20
    altura = 30
    altura_piso = 2.8

    usar("pedra")
    glBegin(GL_QUADS)
    # entrada (+x) com piso roxo e saída (-x) com piso verde
    for lado, cor_piso in ((1, (0.8, 0.35, 1.0)), (-1, (0.35, 1.0, 0.35))):
        x0 = lado * largura_chao
        x1 = lado * (largura_chao + largura)
        # teto
        glColor3f(0.7, 0.7, 0.7)
        face((x1, altura, -comprimento), (x1, altura, comprimento),
             (x0, altura, comprimento), (x0, altura, -comprimento), normal=(0.0, -1.0, 0.0))
        # laterais
        glColor3f(0.85, 0.85, 0.85)
        face((x1, altura_piso, -comprimento), (x1, altura_piso, comprimento),
             (x1, altura, comprimento), (x1, altura, -comprimento))
        for z in (-comprimento, comprimento):
            face((x0, altura_piso, z), (x1, altura_piso, z), (x1, altura, z), (x0, altura, z))
        # piso
        glColor3f(*cor_piso)
        face((x1, altura_piso, -comprimento), (x1, altura_piso, comprimento),
             (x0, altura_piso, comprimento), (x0, altura_piso, -comprimento))
    glEnd()
    parar()


def plataforma(centro, largura, comprimento, altura, cor=(1.0, 1.0, 1.0)):
    (x, y, z) = centro
    l = largura / 2
    c = comprimento / 2
    glBegin(GL_QUADS)
    faces_caixa(x - l, x + l, y, y + altura, z - c, z + c, cor,
                tons=(1.0, 1.0, 1.0))   # quem escurece os lados é a luz
    glEnd()


def compilar_cenario(plataformas, tamanho, altura_chao, altura_muro, tam_plat, altura_plat):
    """plataformas: lista de (centro, cor) das que não se mexem.
    Grava o cenário fixo numa display list: fica na placa de vídeo e é desenhado
    com uma única chamada por frame (glCallList)."""
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    chao(tamanho, altura_chao)
    parede(tamanho, altura_muro)
    caixa_entrada_saida(tamanho)
    plataforma_entrada_saida(tamanho)
    usar("madeira")
    for centro, cor in plataformas:
        plataforma(centro, tam_plat, tam_plat, altura_plat, cor)
    parar()
    glEndList()
    return lista
