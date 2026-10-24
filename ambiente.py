import glfw
from OpenGL.GL import *
import math

def chao(tamanho, altura):
    t = tamanho
    h = altura
    glBegin(GL_QUADS)

    # topo
    glColor3f(0.5, 0.35, 0.2)
    glVertex3f(-t, h, -t)
    glVertex3f(t, h, -t)
    glVertex3f(t, h, t)
    glVertex3f(-t, h, t)

    # laterais
    glColor3f(0.35, 0.25, 0.15)
    glVertex3f(-t, 0, -t)
    glVertex3f(t, 0, -t)
    glVertex3f(t, h, -t)
    glVertex3f(-t, h, -t)

    glVertex3f(-t, 0, t)
    glVertex3f(t, 0, t)
    glVertex3f(t, h, t)
    glVertex3f(-t, h, t)

    glVertex3f(-t, 0, -t)
    glVertex3f(-t, 0, t)
    glVertex3f(-t, h, t)
    glVertex3f(-t, h, -t)

    glVertex3f(t, 0, -t)
    glVertex3f(t, 0, t)
    glVertex3f(t, h, t)
    glVertex3f(t, h, -t)

    glEnd()

def parede(tamanho, altura):
    t = tamanho
    h = altura
    glBegin(GL_QUADS)

    # laterais
    glColor3f(0.35, 0.25, 0.15)
    glVertex3f(-t, 0, -t)
    glVertex3f(t, 0, -t)
    glVertex3f(t, h, -t)
    glVertex3f(-t, h, -t)

    glVertex3f(-t, 0, t)
    glVertex3f(t, 0, t)
    glVertex3f(t, h, t)
    glVertex3f(-t, h, t)


    # saida 
    # parte 1
    glVertex3f(-t, 0, -t)
    glVertex3f(-t, 0, - 15)
    glVertex3f(-t, h, - 15)
    glVertex3f(-t, h, -t)
    
    # parte 2
    glVertex3f(-t, 0, t)
    glVertex3f(-t, 0,  15)
    glVertex3f(-t, h,  15)
    glVertex3f(-t, h, t)
    
    glVertex3f(-t, 15, -15)
    glVertex3f(-t, 15,  15)
    glVertex3f(-t, h,  15)
    glVertex3f(-t, h, -15)


    # entrada
    # parte 1
    glVertex3f(t, 0, -t)
    glVertex3f(t, 0, -15)
    glVertex3f(t, h, -15)
    glVertex3f(t, h, -t)
    
    #parte 2
    glVertex3f(t, 0, t)
    glVertex3f(t, 0,  15)
    glVertex3f(t, h,  15)
    glVertex3f(t, h, t)
    
    #parte 3
    glVertex3f(t, 15, - 15)
    glVertex3f(t, 15,  15)
    glVertex3f(t, h,   15)
    glVertex3f(t, h, - 15)
    

    glEnd()
    
def agua(tamanho, altura):
    t = tamanho
    h = altura
    
    glBegin(GL_QUADS)
    
    glColor3f(0.2, 0.4, 0.8)
    
    # topo
    glVertex3f(-t, h, -t)
    glVertex3f(t, h, -t)
    glVertex3f(t, h, t)
    glVertex3f(-t, h, t)

    # laterais
    glVertex3f(-t, 0, -t)
    glVertex3f(t, 0, -t)
    glVertex3f(t, h, -t)
    glVertex3f(-t, h, -t)

    glVertex3f(-t, 0, t)
    glVertex3f(t, 0, t)
    glVertex3f(t, h, t)
    glVertex3f(-t, h, t)

    glVertex3f(-t, 0, -t)
    glVertex3f(-t, 0, t)
    glVertex3f(-t, h, t)
    glVertex3f(-t, h, -t)

    glVertex3f(t, 0, -t)
    glVertex3f(t, 0, t)
    glVertex3f(t, h, t)
    glVertex3f(t, h, -t)
    
    glEnd()
    
def plataforma_entrada_saida(largura_chao):
    largura = 10
    comprimento = 20
    altura = 2.8
    
    glBegin(GL_QUADS)
    glColor3f(0.35, 0.25, 0.15)
    
    # entrada
    #topo
    glVertex3f(largura_chao, altura, - comprimento)
    glVertex3f(largura_chao, altura, comprimento)
    glVertex3f(largura_chao - largura, altura, comprimento)
    glVertex3f(largura_chao - largura, altura, - comprimento)
    
    # laterais
    glVertex3f(largura_chao - largura, 0, - comprimento)
    glVertex3f(largura_chao - largura, 0, comprimento)
    glVertex3f(largura_chao - largura, altura, comprimento)
    glVertex3f(largura_chao - largura, altura, - comprimento)
    
    glVertex3f(largura_chao,  0, - comprimento)
    glVertex3f(largura_chao - largura , 0, - comprimento)
    glVertex3f(largura_chao - largura, altura, - comprimento)
    glVertex3f(largura_chao , altura, - comprimento)
    
    glVertex3f(largura_chao,  0,  comprimento)
    glVertex3f(largura_chao - largura , 0,  comprimento)
    glVertex3f(largura_chao - largura, altura,  comprimento)
    glVertex3f(largura_chao , altura,  comprimento)
    
    
    
    # saida
    # topo
    glVertex3f(-largura_chao, altura, - comprimento)
    glVertex3f(-largura_chao, altura, comprimento)
    glVertex3f(-largura_chao + largura, altura, comprimento)
    glVertex3f(-largura_chao + largura, altura, - comprimento)
    
    # laterais
    glVertex3f(-largura_chao + largura, 0, - comprimento)
    glVertex3f(-largura_chao + largura, 0, comprimento)
    glVertex3f(-largura_chao + largura, altura, comprimento)
    glVertex3f(-largura_chao + largura, altura, - comprimento)
    
    glVertex3f(-largura_chao,  0, - comprimento)
    glVertex3f(-largura_chao + largura , 0, - comprimento)
    glVertex3f(-largura_chao + largura, altura, - comprimento)
    glVertex3f(-largura_chao , altura, - comprimento)
    
    glVertex3f(-largura_chao,  0,  comprimento)
    glVertex3f(-largura_chao + largura , 0,  comprimento)
    glVertex3f(-largura_chao + largura, altura,  comprimento)
    glVertex3f(-largura_chao , altura,  comprimento)
    
    glEnd()
    

def caixa_entrada_saida(largura_chao):
    largura = 10
    comprimento = 20
    altura = 30
    altura_piso = 2.8
    
    glBegin(GL_QUADS)
    glColor3f(0.35, 0.25, 0.15)
    
    # entrada
    #top
    glVertex3f(largura_chao + largura, altura, - comprimento)
    glVertex3f(largura_chao + largura, altura, comprimento)
    glVertex3f(largura_chao , altura, comprimento)
    glVertex3f(largura_chao , altura, - comprimento)
    
    # laterais
    glVertex3f(largura_chao + largura, altura_piso, - comprimento)
    glVertex3f(largura_chao + largura, altura_piso, comprimento)
    glVertex3f(largura_chao + largura, altura, comprimento)
    glVertex3f(largura_chao + largura, altura, - comprimento)
    
    glVertex3f(largura_chao , altura_piso, - comprimento)
    glVertex3f(largura_chao + largura, altura_piso, - comprimento)
    glVertex3f(largura_chao + largura, altura, - comprimento)
    glVertex3f(largura_chao , altura, - comprimento)
    
    glVertex3f(largura_chao , altura_piso,  comprimento)
    glVertex3f(largura_chao + largura, altura_piso,  comprimento)
    glVertex3f(largura_chao + largura, altura,  comprimento)
    glVertex3f(largura_chao , altura,  comprimento)
    
    #bottom
    glColor3f(0.6, 0.2, 0.8)
    glVertex3f(largura_chao + largura, altura_piso, - comprimento)
    glVertex3f(largura_chao + largura, altura_piso, comprimento)
    glVertex3f(largura_chao , altura_piso, comprimento)
    glVertex3f(largura_chao , altura_piso, - comprimento)
        
    
    glColor3f(0.35, 0.25, 0.15)
    # saida 
    #top
    glVertex3f(-largura_chao - largura, altura, - comprimento)
    glVertex3f(-largura_chao - largura, altura, comprimento)
    glVertex3f(-largura_chao , altura, comprimento)
    glVertex3f(-largura_chao , altura, - comprimento)
    
    # laterais
    glVertex3f(-largura_chao - largura, altura_piso, - comprimento)
    glVertex3f(-largura_chao - largura, altura_piso, comprimento)
    glVertex3f(-largura_chao - largura, altura, comprimento)
    glVertex3f(-largura_chao - largura, altura, - comprimento)
    
    glVertex3f(-largura_chao , altura_piso, - comprimento)
    glVertex3f(-largura_chao - largura, altura_piso, - comprimento)
    glVertex3f(-largura_chao - largura, altura, - comprimento)
    glVertex3f(-largura_chao , altura, - comprimento)
    
    glVertex3f(-largura_chao , altura_piso,  comprimento)
    glVertex3f(-largura_chao - largura, altura_piso,  comprimento)
    glVertex3f(-largura_chao - largura, altura,  comprimento)
    glVertex3f(-largura_chao , altura,  comprimento)
    
    
    #bottom
    glColor3f(0.2, 0.7, 0.2)
    glVertex3f(-largura_chao - largura, altura_piso, - comprimento)
    glVertex3f(-largura_chao - largura, altura_piso, comprimento)
    glVertex3f(-largura_chao , altura_piso, comprimento)
    glVertex3f(-largura_chao , altura_piso, - comprimento)
    
    glEnd()

def plataforma(centro, largura, comprimento, altura):
    (x, y, z) = centro
    l = largura / 2
    c = comprimento / 2
    h = altura

    glBegin(GL_QUADS)

    # topo
    glColor3f(0.5, 0.35, 0.2)
    glVertex3f(x - l, y + h, z - c)
    glVertex3f(x + l, y + h, z - c)
    glVertex3f(x + l, y + h, z + c)
    glVertex3f(x - l, y + h, z + c)

    # laterais
    glColor3f(0.35, 0.25, 0.15)
    glVertex3f(x - l, y, z - c)
    glVertex3f(x + l, y, z - c)
    glVertex3f(x + l, y + h, z - c)
    glVertex3f(x - l, y + h, z - c)

    glVertex3f(x - l, y, z + c)
    glVertex3f(x + l, y, z + c)
    glVertex3f(x + l, y + h, z + c)
    glVertex3f(x - l, y + h, z + c)

    glVertex3f(x - l, y, z - c)
    glVertex3f(x - l, y, z + c)
    glVertex3f(x - l, y + h, z + c)
    glVertex3f(x - l, y + h, z - c)

    glVertex3f(x + l, y, z - c)
    glVertex3f(x + l, y, z + c)
    glVertex3f(x + l, y + h, z + c)
    glVertex3f(x + l, y + h, z - c)

    glEnd()
    