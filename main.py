import glfw
from OpenGL.GL import *
import math

from ambiente import *
from gerador import *

posicao = [0.0, 1.0, 0.0]   
velocidade_y = 0.0
rotacao = 0.0               
ultimo_x = None
item = False
pulou = False
pausado = False

TAMANHO_CHAO = 500   
ALTURA_CHAO = 1
SENSIBILIDADE = 0.15

ALTURA_MURO = 30


def boneco():
    glPushMatrix()
    glTranslatef(posicao[0], posicao[1], posicao[2])
    glRotatef(rotacao, 0.0, 1.0, 0.0)   # gira o boneco

    glBegin(GL_QUADS)

    # FRENTE (lado -z): vermelha, mostra para onde ele olha
    glColor3f(0.9, 0.2, 0.2)
    glVertex3f(-0.5, 0, -0.5)
    glVertex3f(0.5, 0, -0.5)
    glVertex3f(0.5, 2, -0.5)
    glVertex3f(-0.5, 2, -0.5)

    # trás
    glColor3f(0.9, 0.7, 0.5)
    glVertex3f(-0.5, 0, 0.5)
    glVertex3f(0.5, 0, 0.5)
    glVertex3f(0.5, 2, 0.5)
    glVertex3f(-0.5, 2, 0.5)

    # topo
    glColor3f(1.0, 0.9, 0.7)
    glVertex3f(-0.5, 2, -0.5)
    glVertex3f(0.5, 2, -0.5)
    glVertex3f(0.5, 2, 0.5)
    glVertex3f(-0.5, 2, 0.5)

    # laterais
    glColor3f(0.8, 0.6, 0.4)
    glVertex3f(-0.5, 0, -0.5)
    glVertex3f(-0.5, 0, 0.5)
    glVertex3f(-0.5, 2, 0.5)
    glVertex3f(-0.5, 2, -0.5)

    glVertex3f(0.5, 0, -0.5)
    glVertex3f(0.5, 0, 0.5)
    glVertex3f(0.5, 2, 0.5)
    glVertex3f(0.5, 2, -0.5)

    glEnd()
    glPopMatrix()
    

def tela_pausa():
    """Escurece a tela e desenha o símbolo de pausa."""
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # fundo escuro
    glColor4f(0.0, 0.0, 0.0, 0.55)
    glBegin(GL_QUADS)
    glVertex2f(-1, -1)
    glVertex2f(1, -1)
    glVertex2f(1, 1)
    glVertex2f(-1, 1)
    glEnd()

    # símbolo de pausa (duas barras)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(-0.15, -0.2)
    glVertex2f(-0.05, -0.2)
    glVertex2f(-0.05, 0.2)
    glVertex2f(-0.15, 0.2)

    glVertex2f(0.05, -0.2)
    glVertex2f(0.15, -0.2)
    glVertex2f(0.15, 0.2)
    glVertex2f(0.05, 0.2)
    glEnd()

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

def alternar_pausa(window):
    global pausado, ultimo_x
    pausado = not pausado
    if pausado:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        glfw.set_window_title(window, "Paisagem OpenGL - PAUSADO")
    else:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
        glfw.set_window_title(window, "Paisagem OpenGL")
        ultimo_x = None   # evita um "pulo" na rotação ao voltar

def tecla_callback(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        alternar_pausa(window)

def mouse_movimento(window, x, y):
    """Mouse para a direita -> boneco olha para a direita."""
    global rotacao, ultimo_x
    if pausado:
        return
    if ultimo_x is None:
        ultimo_x = x
    dx = x - ultimo_x
    ultimo_x = x
    rotacao -= dx * SENSIBILIDADE

def teclado_movimentacao(window):
    global velocidade_y, pulou

    vel = 0.5
    ang = math.radians(rotacao)
    # direção que o boneco está olhando e o lado direito dele
    frente_x, frente_z = -math.sin(ang), -math.cos(ang)
    direita_x, direita_z = math.cos(ang), -math.sin(ang)

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        posicao[0] += frente_x * vel
        posicao[2] += frente_z * vel
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        posicao[0] -= frente_x * vel
        posicao[2] -= frente_z * vel
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        posicao[0] -= direita_x * vel
        posicao[2] -= direita_z * vel
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        posicao[0] += direita_x * vel
        posicao[2] += direita_z * vel

    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS and not pulou:
        velocidade_y = 4
        pulou = True

    # gravidade
    velocidade_y -= 0.1
    posicao[1] += velocidade_y

    # colisão com o topo do chão
    
    if posicao[1] <= ALTURA_CHAO:
        posicao[1] = ALTURA_CHAO
        velocidade_y = 0.0
        pulou = False
    
    """
    # não deixa sair do chão
    limite = TAMANHO_CHAO - 0.5
    posicao[0] = max(-limite, min(limite, posicao[0]))
    posicao[2] = max(-limite, min(limite, posicao[2]))

    """
def mouse_item(window, mouse, action, mods):
    global item
    if pausado or action != glfw.PRESS:
        return

    if mouse == glfw.MOUSE_BUTTON_LEFT and item == False:
        item = True
        print("Pegou o item!")

    elif mouse == glfw.MOUSE_BUTTON_LEFT and item == True:
        item = False
        print("Soltou o item!")

def camera_movimentacao():
    # câmera SEMPRE atrás do boneco, olhando na direção dele
    glTranslatef(0.0, -3.0, -12.0)               # afasta e sobe a câmera
    glRotatef(25, 1.0, 0.0, 0.0)                 # inclina olhando pra baixo
    glRotatef(-rotacao, 0.0, 1.0, 0.0)           # gira junto com o boneco
    glTranslatef(-posicao[0], -posicao[1], -posicao[2])  # segue o boneco

def main():
    if not glfw.init():
        return

    window = glfw.create_window(GL_MAX,GL_MAX, "Paisagem OpenGL", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)  # prende o mouse
    glfw.set_mouse_button_callback(window, mouse_item)
    glfw.set_cursor_pos_callback(window, mouse_movimento)
    glfw.set_key_callback(window, tecla_callback)

    glEnable(GL_DEPTH_TEST)
    
    global posicao  # posição inicial do boneco
    
    posicao = [TAMANHO_CHAO/2, ALTURA_CHAO, TAMANHO_CHAO/2]  # posição inicial do boneco
    
    centros_plataformas = gerar_centros_plataformas(500, TAMANHO_CHAO)  # gera as plataformas de acordo com a dificuldade


    while not glfw.window_should_close(window):
        glfw.poll_events()

        if not pausado:
            teclado_movimentacao(window)

        glClearColor(0.5, 0.8, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # projeção em perspectiva
        largura, altura = glfw.get_framebuffer_size(window)
        glViewport(0, 0, largura, altura)
        aspecto = largura / max(altura, 1)
        near, far = 0.1, 500.0
        topo = near * math.tan(math.radians(30))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-topo * aspecto, topo * aspecto, -topo, topo, near, far)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        camera_movimentacao()
        
        
        chao(TAMANHO_CHAO, ALTURA_CHAO)
        parede(TAMANHO_CHAO, 50)
        agua(TAMANHO_CHAO, ALTURA_CHAO+ 1.0)
        caixa_entrada_saida(TAMANHO_CHAO)
        plataforma_entrada_saida(TAMANHO_CHAO)
        
        for centro in centros_plataformas:
            plataforma(centro, 10, 10, 2.9)
        
        
        
        boneco()

        if pausado:
            tela_pausa()

        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()