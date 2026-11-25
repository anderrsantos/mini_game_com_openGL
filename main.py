import glfw
from OpenGL.GL import *
import math

from ambiente import *
from texturas import carregar_texturas, usar, parar, face
from gerador import *
from colisao import *
from monstro import Monstro

TAMANHO_CHAO = 500
ALTURA_CHAO = 1
ALTURA_AGUA = ALTURA_CHAO + 1
SENSIBILIDADE = 0.15

ALTURA_MURO = 30

# câmera em primeira pessoa
ALTURA_OLHOS = 4     # o boneco tem 2 de altura
LIMITE_PITCH = 89.0    # não deixa a câmera virar de cabeça para baixo

# física
VEL = 0.5
VEL_PULO = 1.8
GRAVIDADE = 0.1

# o boneco nasce na plataforma de saída (-x), olhando para a chegada (+x)
PONTO_INICIAL = [-TAMANHO_CHAO + LARGURA_PLAT_ES / 2, ALTURA_PLAT_ES, 0.0]
ROTACAO_INICIAL = -90.0

posicao = list(PONTO_INICIAL)
velocidade_y = 0.0
rotacao = ROTACAO_INICIAL
inclinacao = 0.0           # positivo = olhando para cima
primeira_pessoa = True     # a tecla V alterna a câmera
ultimo_x = None
ultimo_y = None
item = False
pulou = False
pausado = False
no_agua = False   


def boneco():
    glPushMatrix()
    glTranslatef(posicao[0], posicao[1], posicao[2])
    glRotatef(rotacao, 0.0, 1.0, 0.0)   # gira o boneco

    usar("tecido")
    glBegin(GL_QUADS)

    # FRENTE (lado -z): vermelha, mostra para onde ele olha
    glColor3f(0.9, 0.2, 0.2)
    face((-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 2, -0.5), (-0.5, 2, -0.5), 2.0)

    # trás
    glColor3f(0.9, 0.7, 0.5)
    face((-0.5, 0, 0.5), (0.5, 0, 0.5), (0.5, 2, 0.5), (-0.5, 2, 0.5), 2.0)

    # topo
    glColor3f(1.0, 0.9, 0.7)
    face((-0.5, 2, -0.5), (0.5, 2, -0.5), (0.5, 2, 0.5), (-0.5, 2, 0.5), 2.0)

    # laterais
    glColor3f(0.8, 0.6, 0.4)
    for x in (-0.5, 0.5):
        face((x, 0, -0.5), (x, 0, 0.5), (x, 2, 0.5), (x, 2, -0.5), 2.0)

    glEnd()
    parar()
    glPopMatrix()


def _tela_2d_inicio():
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def _tela_2d_fim():
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)


def _fundo(r, g, b, a):
    glColor4f(r, g, b, a)
    glBegin(GL_QUADS)
    glVertex2f(-1, -1)
    glVertex2f(1, -1)
    glVertex2f(1, 1)
    glVertex2f(-1, 1)
    glEnd()


def tela_pausa():
    """Escurece a tela e desenha o símbolo de pausa."""
    _tela_2d_inicio()
    _fundo(0.0, 0.0, 0.0, 0.55)

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

    _tela_2d_fim()


def mira(aspecto):
    """Pequena cruz no centro da tela (só em primeira pessoa)."""
    t = 0.02
    _tela_2d_inicio()
    glColor4f(1.0, 1.0, 1.0, 0.8)
    glBegin(GL_LINES)
    glVertex2f(-t / aspecto, 0)
    glVertex2f(t / aspecto, 0)
    glVertex2f(0, -t)
    glVertex2f(0, t)
    glEnd()
    _tela_2d_fim()


def tela_resultado(cor):
    """Tinge a tela de vermelho (morreu) ou verde (venceu)."""
    _tela_2d_inicio()
    _fundo(cor[0], cor[1], cor[2], 0.5)
    _tela_2d_fim()


def alternar_pausa(window):
    global pausado, ultimo_x, ultimo_y
    pausado = not pausado
    if pausado:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        glfw.set_window_title(window, "Paisagem OpenGL - PAUSADO")
    else:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
        glfw.set_window_title(window, "Paisagem OpenGL")
        ultimo_x = None   # evita um "pulo" na rotação ao voltar
        ultimo_y = None


def tecla_callback(window, key, scancode, action, mods):
    global primeira_pessoa
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        alternar_pausa(window)
    elif key == glfw.KEY_V and action == glfw.PRESS and not pausado:
        primeira_pessoa = not primeira_pessoa


def mouse_movimento(window, x, y):
    """Mouse para a direita -> olha para a direita; para cima -> olha para cima."""
    global rotacao, inclinacao, ultimo_x, ultimo_y
    if pausado:
        return
    if ultimo_x is None:
        ultimo_x = x
        ultimo_y = y
    dx = x - ultimo_x
    dy = y - ultimo_y
    ultimo_x = x
    ultimo_y = y
    rotacao -= dx * SENSIBILIDADE

    if primeira_pessoa:
        # no GLFW o y cresce para baixo
        inclinacao -= dy * SENSIBILIDADE
        inclinacao = max(-LIMITE_PITCH, min(LIMITE_PITCH, inclinacao))


def teclado_movimentacao(window, caixas):
    global velocidade_y, pulou, no_agua

    ang = math.radians(rotacao)
    # direção que o boneco está olhando e o lado direito dele
    frente_x, frente_z = -math.sin(ang), -math.cos(ang)
    direita_x, direita_z = math.cos(ang), -math.sin(ang)

    dx = dz = 0.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        dx += frente_x * VEL
        dz += frente_z * VEL
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        dx -= frente_x * VEL
        dz -= frente_z * VEL
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        dx -= direita_x * VEL
        dz -= direita_z * VEL
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        dx += direita_x * VEL
        dz += direita_z * VEL

    # --- movimento horizontal com colisão (um eixo por vez, assim ele "desliza" na parede) ---
    limite = TAMANHO_CHAO - METADE_BONECO   # não deixa sair do mapa

    novo_x = max(-limite, min(limite, posicao[0] + dx))
    if not colide_lateral(novo_x, posicao[1], posicao[2], caixas):
        posicao[0] = novo_x

    novo_z = max(-limite, min(limite, posicao[2] + dz))
    if not colide_lateral(posicao[0], posicao[1], novo_z, caixas):
        posicao[2] = novo_z

    # --- pulo ---
    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS and not pulou:
        velocidade_y = VEL_PULO
        pulou = True

    # --- gravidade + pouso (chão ou topo de plataforma) ---
    y_anterior = posicao[1]
    velocidade_y -= GRAVIDADE
    y_novo = y_anterior + velocidade_y

    if velocidade_y <= 0:   # só pousa quando está caindo
        suporte = altura_suporte(posicao[0], posicao[2], y_anterior, caixas, ALTURA_CHAO)
        if y_novo <= suporte:
            y_novo = suporte
            velocidade_y = 0.0
            pulou = False
            # se pousou no fundo (e não numa plataforma), está dentro da água
            no_agua = (suporte == ALTURA_CHAO)

    posicao[1] = y_novo


def chegou():
    """Chegou quando está parado em cima da plataforma de chegada (+x)."""
    return (not pulou and
            posicao[0] >= TAMANHO_CHAO - LARGURA_PLAT_ES and
            posicao[1] >= ALTURA_PLAT_ES - 0.01)


def reiniciar(monstro):
    global velocidade_y, pulou, no_agua, rotacao, inclinacao, ultimo_x, ultimo_y
    posicao[:] = PONTO_INICIAL
    velocidade_y = 0.0
    pulou = False
    no_agua = False
    rotacao = ROTACAO_INICIAL
    inclinacao = 0.0
    ultimo_x = None
    ultimo_y = None
    monstro.reposicionar(longe_de=posicao)


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
    if primeira_pessoa:
        # nos olhos do boneco: inversa da orientação e da posição da cabeça
        glRotatef(-inclinacao, 1.0, 0.0, 0.0)
        glRotatef(-rotacao, 0.0, 1.0, 0.0)
        glTranslatef(-posicao[0], -(posicao[1] + ALTURA_OLHOS), -posicao[2])
        return

    # terceira pessoa: câmera atrás do boneco, olhando na direção dele
    glTranslatef(0.0, -3.0, -12.0)               # afasta e sobe a câmera
    glRotatef(25, 1.0, 0.0, 0.0)                 # inclina olhando pra baixo
    glRotatef(-rotacao, 0.0, 1.0, 0.0)           # gira junto com o boneco
    glTranslatef(-posicao[0], -posicao[1], -posicao[2])  # segue o boneco


def main():
    if not glfw.init():
        return

    # abre a janela maximizada (1280x720 é o tamanho ao restaurar)
    glfw.window_hint(glfw.MAXIMIZED, glfw.TRUE)
    window = glfw.create_window(1280, 720, "Paisagem OpenGL", None, None)
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

    alcance = alcance_pulo(VEL_PULO, GRAVIDADE, VEL)
    centros_plataformas = gerar_centros_plataformas(500, TAMANHO_CHAO, alcance)
    caixas = criar_caixas(centros_plataformas, TAMANHO_CHAO)   # caixas de colisão

    carregar_texturas()
    cenario = compilar_cenario(centros_plataformas, TAMANHO_CHAO, ALTURA_CHAO, 50,
                               TAMANHO_PLATAFORMA, ALTURA_PLATAFORMA)
    tempo_agua = 0.0        # só avança fora da pausa
    ultimo_tempo = glfw.get_time()

    monstro = Monstro(TAMANHO_CHAO, ALTURA_CHAO, longe_de=posicao)
    reiniciar(monstro)

    estado = "jogando"      # "jogando", "morreu" ou "venceu"
    tempo_fim = 0.0

    while not glfw.window_should_close(window):
        glfw.poll_events()

        agora = glfw.get_time()
        if not pausado:
            tempo_agua += agora - ultimo_tempo
        ultimo_tempo = agora

        if not pausado:
            if estado == "jogando":
                teclado_movimentacao(window, caixas)
                monstro.atualizar(posicao, no_agua)

                if no_agua and monstro.tocou(posicao):
                    estado = "morreu"
                    tempo_fim = glfw.get_time()
                    glfw.set_window_title(window, "Paisagem OpenGL - O MONSTRO PEGOU VOCÊ!")
                    print("Você morreu! O monstro te pegou na água.")
                elif chegou():
                    estado = "venceu"
                    tempo_fim = glfw.get_time()
                    glfw.set_window_title(window, "Paisagem OpenGL - VOCÊ VENCEU!")
                    print("Você chegou ao final! Parabéns!")
            else:
                # mostra o resultado por 2.5s e recomeça
                if glfw.get_time() - tempo_fim > 2.5:
                    reiniciar(monstro)
                    estado = "jogando"
                    glfw.set_window_title(window, "Paisagem OpenGL")

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

        glCallList(cenario)   # chão, muros e plataformas

        monstro.desenhar()
        if not primeira_pessoa:   # em primeira pessoa a câmera está dentro dele
            boneco()

        agua(TAMANHO_CHAO, ALTURA_AGUA, tempo_agua)   # translúcida: depois do que é opaco

        if primeira_pessoa and estado == "jogando" and not pausado:
            mira(aspecto)

        if estado == "morreu":
            tela_resultado((0.8, 0.0, 0.0))
        elif estado == "venceu":
            tela_resultado((0.0, 0.7, 0.1))
        elif pausado:
            tela_pausa()

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()