from OpenGL.GL import *

from texturas import usar, parar, face, faces_caixa


def chao(tamanho, altura):
    t = tamanho
    h = altura
    usar("terra")
    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)
    face((-t, h, -t), (t, h, -t), (t, h, t), (-t, h, t), 20.0)
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
        face((-t, 0, z), (t, 0, z), (t, h, z), (-t, h, z), 20.0)

    # saída (-t) e entrada (+t), com um vão de 30 x 15 no meio
    glColor3f(1.0, 1.0, 1.0)
    for x in (-t, t):
        face((x, 0, -t), (x, 0, -15), (x, h, -15), (x, h, -t), 20.0)
        face((x, 0, t), (x, 0, 15), (x, h, 15), (x, h, t), 20.0)
        face((x, 15, -15), (x, 15, 15), (x, h, 15), (x, h, -15), 20.0)

    glEnd()
    parar()


def agua(tamanho, altura, tempo):
    """Superfície translúcida e em movimento. Desenhar depois do que é opaco.
    (As laterais não são desenhadas: ficariam no mesmo plano dos muros.)"""
    t = tamanho
    h = altura
    usar("agua")
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # desloca as coordenadas de textura para a água "correr"
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glTranslatef(tempo * 0.03 % 1.0, tempo * 0.02 % 1.0, 0.0)
    glMatrixMode(GL_MODELVIEW)

    glBegin(GL_QUADS)
    glColor4f(1.0, 1.0, 1.0, 0.8)
    face((-t, h, -t), (t, h, -t), (t, h, t), (-t, h, t), 25.0)
    glEnd()

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
            face((x0, 0, z), (x1, 0, z), (x1, altura, z), (x0, altura, z))
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
             (x0, altura, comprimento), (x0, altura, -comprimento))
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


def plataforma(centro, largura, comprimento, altura):
    (x, y, z) = centro
    l = largura / 2
    c = comprimento / 2
    glBegin(GL_QUADS)
    faces_caixa(x - l, x + l, y, y + altura, z - c, z + c, (1.0, 1.0, 1.0),
                tons=(0.75, 1.0, 0.65))
    glEnd()


def compilar_cenario(centros, tamanho, altura_chao, altura_muro, tam_plat, altura_plat):
    """Grava o cenário fixo numa display list: fica na placa de vídeo e é desenhado
    com uma única chamada por frame (glCallList)."""
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    chao(tamanho, altura_chao)
    parede(tamanho, altura_muro)
    caixa_entrada_saida(tamanho)
    plataforma_entrada_saida(tamanho)
    usar("madeira")
    for centro in centros:
        plataforma(centro, tam_plat, tam_plat, altura_plat)
    parar()
    glEndList()
    return lista
