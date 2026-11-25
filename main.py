import glfw
from OpenGL.GL import *
import math

from ambiente import *
from atmosfera import COR_HORIZONTE, compilar_ceu, desenhar_ceu, ligar_neblina, desligar_neblina
from texturas import carregar_texturas, usar, parar, face
from gerador import *
from colisao import *
from monstro import Monstro
from plataformas import Plataformas, MULT_IMPULSO
from cristais import Cristais, escolher_lugares
from dificuldade import DIFICULDADES, ler_recordes, salvar_tempo
import interface as ui
import som
from minimapa import compilar_minimapa, desenhar_minimapa

TAMANHO_CHAO = 500
ALTURA_CHAO = 1
ALTURA_AGUA = ALTURA_CHAO + 1
SENSIBILIDADE = 0.15

ALTURA_MURO = 30

# câmera em primeira pessoa
ALTURA_OLHOS = 4     # o boneco tem 2 de altura
LIMITE_PITCH = 89.0    # não deixa a câmera virar de cabeça para baixo

# física (valores por passo; são sempre 60 passos por segundo, em qualquer monitor)
PASSO = 1 / 60
VEL = 0.5
VEL_PULO = 1.8
GRAVIDADE = 0.1

# o boneco nasce na plataforma de saída (-x), olhando para a chegada (+x)
PONTO_INICIAL = [-TAMANHO_CHAO + LARGURA_PLAT_ES / 2, ALTURA_PLAT_ES, 0.0]
ROTACAO_INICIAL = -90.0

# efeitos de câmera
BALANCO_ALTURA = 0.15
TREMOR_DISTANCIA = 60.0    # o tremor começa quando o monstro chega a essa distância
TREMOR_MAX = 0.12

posicao = list(PONTO_INICIAL)
pos_anterior = list(PONTO_INICIAL)   # posição no passo anterior
pos_visual = list(PONTO_INICIAL)     # posição desenhada (entre a anterior e a atual)
fase_passo = 0.0
forca_passo = 0.0          # 0 = parado, 1 = andando (varia aos poucos)
velocidade_y = 0.0
rotacao = ROTACAO_INICIAL
inclinacao = 0.0           # positivo = olhando para cima
primeira_pessoa = True     # a tecla V alterna a câmera
ultimo_x = None
ultimo_y = None
estado = "menu"            # "menu", "jogando", "morreu" ou "venceu"
partida = None             # Partida em andamento
pedido = None              # dificuldade escolhida: o laço principal cria a partida
opcao_menu = 1
mapa_visivel = True        # a tecla TAB alterna o minimapa
mensagem, mensagem_fim = "", 0.0
tempo_jogo = 0.0           # relógio das animações: para na pausa
pulou = False
pausado = False
no_agua = False   


def boneco():
    glPushMatrix()
    glTranslatef(pos_visual[0], pos_visual[1], pos_visual[2])
    glRotatef(rotacao,0.0, 1.0, 0.0)   # gira o boneco

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


def mouse_movimento(window, x, y):
    """Mouse para a direita -> olha para a direita; para cima -> olha para cima."""
    global rotacao, inclinacao, ultimo_x, ultimo_y, opcao_menu
    if estado == "menu":
        i = ui.opcao_no_ponto(*ponto_na_tela(window, x, y), len(OPCOES))
        if i is not None and i != opcao_menu:
            opcao_menu = i
            som.tocar("menu")
        return
    if pausado or estado == "venceu":
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


def teclado_movimentacao(window, caixas, impulso=False):
    global velocidade_y, pulou, no_agua, fase_passo, forca_passo

    x_anterior, z_anterior = posicao[0], posicao[2]
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

    # na diagonal o vetor fica maior: volta para a velocidade normal
    modulo = math.hypot(dx, dz)
    if modulo > VEL:
        dx, dz = dx * VEL / modulo, dz * VEL / modulo

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
        velocidade_y = VEL_PULO * (MULT_IMPULSO if impulso else 1.0)
        pulou = True
        som.tocar("impulso" if impulso else "pulo")

    # --- gravidade + pouso (chão ou topo de plataforma) ---
    y_anterior = posicao[1]
    velocidade_y -= GRAVIDADE
    y_novo = y_anterior + velocidade_y

    if velocidade_y <= 0:   # só pousa quando está caindo
        suporte = altura_suporte(posicao[0], posicao[2], y_anterior, caixas, ALTURA_CHAO)
        if y_novo <= suporte:
            caiu = velocidade_y < -0.4
            if suporte == ALTURA_CHAO and (caiu or not no_agua):
                som.tocar("mergulho")
            elif caiu:
                som.tocar("pouso")
            y_novo = suporte
            velocidade_y = 0.0
            pulou = False
            # se pousou no fundo (e não numa plataforma), está dentro da água
            no_agua = (suporte == ALTURA_CHAO)

    posicao[1] = y_novo

    # --- balanço da câmera: só quando anda de verdade e está apoiado ---
    andou = math.hypot(posicao[0] - x_anterior, posicao[2] - z_anterior)
    alvo = 1.0 if andou > 0.01 and velocidade_y == 0.0 else 0.0
    forca_passo += (alvo - forca_passo) * 0.15
    ciclo = int(fase_passo / (2 * math.pi))
    fase_passo += andou * 0.5
    if alvo and int(fase_passo / (2 * math.pi)) != ciclo:   # um passo por balanço
        som.tocar("passo_agua" if no_agua else "passo")


def chegou():
    """Chegou quando está parado em cima da plataforma de chegada (+x)."""
    return (not pulou and
            posicao[0] >= TAMANHO_CHAO - LARGURA_PLAT_ES and
            posicao[1] >= ALTURA_PLAT_ES - 0.01)


def reiniciar(monstro, plataformas):
    global velocidade_y, pulou, no_agua, rotacao, inclinacao, ultimo_x, ultimo_y
    global fase_passo, forca_passo
    posicao[:] = PONTO_INICIAL
    pos_anterior[:] = PONTO_INICIAL
    pos_visual[:] = PONTO_INICIAL
    fase_passo = forca_passo = 0.0
    velocidade_y = 0.0
    pulou = False
    no_agua = False
    rotacao = ROTACAO_INICIAL
    inclinacao = 0.0
    ultimo_x = None
    ultimo_y = None
    monstro.reposicionar(longe_de=posicao)
    plataformas.reiniciar()


def camera_rotacao():
    """Só a orientação da câmera (usada também pelo céu)."""
    if primeira_pessoa:
        glRotatef(-inclinacao, 1.0, 0.0, 0.0)
    else:
        glRotatef(25, 1.0, 0.0, 0.0)             # inclina olhando pra baixo
    glRotatef(-rotacao, 0.0, 1.0, 0.0)           # gira junto com o boneco


def camera_movimentacao(tempo, perigo):
    """perigo: 0 (monstro longe) a 1 (monstro encostando), controla o tremor."""
    tremor = TREMOR_MAX * perigo * perigo
    glTranslatef(tremor * math.sin(tempo * 47), tremor * math.sin(tempo * 61 + 1), 0.0)

    if primeira_pessoa:
        # nos olhos do boneco: inversa da orientação e da posição da cabeça
        camera_rotacao()
        balanco = BALANCO_ALTURA * forca_passo * math.sin(fase_passo)
        glTranslatef(-pos_visual[0], -(pos_visual[1] + ALTURA_OLHOS + balanco), -pos_visual[2])
    else:
        # terceira pessoa: câmera atrás do boneco, olhando na direção dele
        glTranslatef(0.0, -3.0, -12.0)           # afasta e sobe a câmera
        camera_rotacao()
        glTranslatef(-pos_visual[0], -pos_visual[1], -pos_visual[2])  # segue o boneco




class Partida:
    """Um mapa sorteado, com o monstro, os cristais e as estatísticas."""

    def __init__(self, dificuldade):
        cfg = DIFICULDADES[dificuldade]
        self.dificuldade = dificuldade
        self.passos = 0            # passos de física jogados: é o cronômetro
        self.mortes = 0
        self.novo_recorde = False
        self.recorde = 0.0

        alcance = alcance_pulo(VEL_PULO, GRAVIDADE, VEL)
        centros = gerar_centros_plataformas(cfg["plataformas"], TAMANHO_CHAO, alcance)
        self.caixas = criar_caixas(centros, TAMANHO_CHAO)   # caixas de colisão

        # cristais e caminho garantido ficam em plataformas normais; o resto pode ser especial
        lugares, protegidas = escolher_lugares(centros, TAMANHO_CHAO, alcance, cfg["cristais"])
        self.cristais = Cristais([centros[i] for i in lugares])
        self.plataformas = Plataformas(centros, protegidas, self.caixas, TAMANHO_CHAO,
                                       cfg["especiais"])
        self.plataformas.compilar()
        self.cenario = compilar_cenario(self.plataformas.fixas(), TAMANHO_CHAO, ALTURA_CHAO, 50,
                                        TAMANHO_PLATAFORMA, ALTURA_PLATAFORMA)

        self.minimapa = compilar_minimapa(self.plataformas.fixas(), TAMANHO_CHAO)

        self.monstro = Monstro(TAMANHO_CHAO, ALTURA_CHAO, longe_de=PONTO_INICIAL)
        for atributo, valor in cfg["monstro"].items():
            setattr(self.monstro, atributo, valor)
        reiniciar(self.monstro, self.plataformas)

    @property
    def tempo(self):
        return self.passos * PASSO

    def apagar(self):
        """Libera as display lists da placa de vídeo."""
        glDeleteLists(self.cenario, 1)
        glDeleteLists(self.minimapa, 1)
        self.plataformas.apagar_listas()


OPCOES = list(DIFICULDADES) + ["SAIR"]


def avisar(s, segundos=2.5):
    global mensagem, mensagem_fim
    mensagem, mensagem_fim = s, tempo_jogo + segundos


def ponto_na_tela(window, x, y):
    """Converte a posição do mouse para as coordenadas da interface."""
    largura, altura = glfw.get_window_size(window)
    altura = max(altura, 1)
    return (2 * x - largura) / altura, 1 - 2 * y / altura


def mudar_estado(window, novo):
    global estado, pausado, ultimo_x, ultimo_y
    estado = novo
    pausado = False
    ultimo_x = ultimo_y = None      # evita um "pulo" na rotação ao voltar
    livre = novo in ("menu", "venceu")
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL if livre else glfw.CURSOR_DISABLED)


def alternar_pausa(window):
    global pausado, ultimo_x, ultimo_y
    pausado = not pausado
    ultimo_x = ultimo_y = None
    glfw.set_input_mode(window, glfw.CURSOR,
                        glfw.CURSOR_NORMAL if pausado else glfw.CURSOR_DISABLED)


def confirmar_menu(window):
    global pedido
    if OPCOES[opcao_menu] == "SAIR":
        glfw.set_window_should_close(window, True)
    else:
        pedido = OPCOES[opcao_menu]
        som.tocar("confirma")


def tecla_callback(window, key, scancode, action, mods):
    global primeira_pessoa, opcao_menu, pedido, mapa_visivel
    if action != glfw.PRESS:
        return

    if key == glfw.KEY_N:
        avisar("SOM DESLIGADO" if som.alternar_mudo() else "SOM LIGADO", 1.5)
        return

    confirma = key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER)
    if estado == "menu":
        if key in (glfw.KEY_UP, glfw.KEY_W):
            opcao_menu = (opcao_menu - 1) % len(OPCOES)
            som.tocar("menu")
        elif key in (glfw.KEY_DOWN, glfw.KEY_S):
            opcao_menu = (opcao_menu + 1) % len(OPCOES)
            som.tocar("menu")
        elif confirma:
            confirmar_menu(window)
        elif key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
    elif estado == "venceu":
        if key == glfw.KEY_R:
            pedido = partida.dificuldade
        elif confirma or key == glfw.KEY_ESCAPE:
            mudar_estado(window, "menu")
    elif key == glfw.KEY_ESCAPE:
        alternar_pausa(window)
    elif key == glfw.KEY_M and pausado:
        mudar_estado(window, "menu")
    elif key == glfw.KEY_V and not pausado:
        primeira_pessoa = not primeira_pessoa
    elif key == glfw.KEY_TAB and not pausado:
        mapa_visivel = not mapa_visivel


def mouse_clique(window, botao, action, mods):
    """Menu: escolhe a opção. Jogo: pega o cristal que estiver perto."""
    if botao != glfw.MOUSE_BUTTON_LEFT or action != glfw.PRESS:
        return

    if estado == "menu":
        if ui.opcao_no_ponto(*ponto_na_tela(window, *glfw.get_cursor_pos(window)),
                             len(OPCOES)) is not None:
            confirmar_menu(window)
    elif estado == "jogando" and not pausado:
        cristais = partida.cristais
        if cristais.coletar(posicao):
            if cristais.completos:
                avisar("O PORTAL ABRIU!", 4.0)
                som.tocar("portal")
            else:
                avisar("CRISTAL %d DE %d" % (sum(cristais.coletados), len(cristais.coletados)))
                som.tocar("cristal")


def passo_jogo(window):
    """Um passo de física (1/60 s)."""
    p = partida
    p.passos += 1
    pos_anterior[:] = posicao
    p.plataformas.atualizar(posicao)
    teclado_movimentacao(window, p.caixas, p.plataformas.impulso_pronto)
    p.monstro.atualizar(posicao, no_agua)

    if no_agua and p.monstro.tocou(posicao):
        p.mortes += 1
        som.tocar("morte")
        mudar_estado(window, "morreu")
    elif chegou():
        if p.cristais.completos:
            som.tocar("vitoria")
            p.novo_recorde = salvar_tempo(p.dificuldade, p.tempo)
            p.recorde = ler_recordes().get(p.dificuldade, p.tempo)
            mudar_estado(window, "venceu")
        else:
            faltam = p.cristais.coletados.count(False)
            avisar("FALTA 1 CRISTAL" if faltam == 1 else "FALTAM %d CRISTAIS" % faltam, 0.5)


def projecao(window):
    """Limpa a tela e aplica a perspectiva. Retorna o aspecto da janela."""
    glClearColor(*COR_HORIZONTE, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    largura, altura = glfw.get_framebuffer_size(window)
    glViewport(0, 0, largura, altura)
    aspecto = max(largura, 1) / max(altura, 1)
    near, far = 0.1, 500.0
    topo = near * math.tan(math.radians(30))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-topo * aspecto, topo * aspecto, -topo, topo, near, far)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    return aspecto


def desenhar_menu(window, ceu, lista_agua, recordes):
    aspecto = projecao(window)
    glRotatef(tempo_jogo * 3 % 360, 0.0, 1.0, 0.0)    # paisagem girando devagar
    desenhar_ceu(ceu, tempo_jogo)
    ligar_neblina()
    glTranslatef(0.0, -12.0, 0.0)
    agua(lista_agua, tempo_jogo)
    desligar_neblina()

    ui.inicio_2d(aspecto)
    ui.tela_menu(aspecto, OPCOES, opcao_menu, recordes, tempo_jogo)
    ui.fim_2d()


def perigo_atual():
    """0 (monstro longe ou calmo) a 1 (encostando)."""
    if estado != "jogando" or not partida.monstro.perseguindo:
        return 0.0
    return max(0.0, 1.0 - partida.monstro.distancia(posicao) / TREMOR_DISTANCIA)


def desenhar_jogo(window, ceu, lista_agua, f):
    """f: fração entre o passo anterior e o atual."""
    p = partida
    perigo = perigo_atual()

    aspecto = projecao(window)
    camera_rotacao()
    desenhar_ceu(ceu, tempo_jogo)

    glLoadIdentity()
    camera_movimentacao(tempo_jogo, perigo)
    ligar_neblina()
    glCallList(p.cenario)   # chão, muros e plataformas fixas
    p.plataformas.desenhar(pos_visual, f)
    p.cristais.desenhar(tempo_jogo)
    p.monstro.desenhar()
    if not primeira_pessoa:   # em primeira pessoa a câmera está dentro dele
        boneco()
    agua(lista_agua, tempo_jogo)   # translúcida: depois do que é opaco
    desligar_neblina()
    p.cristais.desenhar_luzes(pos_visual, TAMANHO_CHAO, tempo_jogo)

    ui.inicio_2d(aspecto)
    if estado == "venceu":
        ui.tela_vitoria(aspecto, p.dificuldade, p.tempo, p.mortes, p.novo_recorde, p.recorde)
    else:
        p.cristais.desenhar_hud(aspecto, piscar=chegou() and not p.cristais.completos
                                and tempo_jogo % 0.6 < 0.3)
        distancia = max(0, TAMANHO_CHAO - LARGURA_PLAT_ES - posicao[0])
        alerta = estado == "jogando" and no_agua
        ui.hud(aspecto, p.tempo, p.mortes, distancia, alerta, perigo,
               mensagem, min(1.0, (mensagem_fim - tempo_jogo) * 2))
        if mapa_visivel:
            desenhar_minimapa(aspecto, p.minimapa, p, pos_visual, rotacao, TAMANHO_CHAO, tempo_jogo)
        if estado == "morreu":
            ui.tela_morte(aspecto)
        if pausado:
            ui.tela_pausa(aspecto)
        elif primeira_pessoa and estado == "jogando":
            ui.mira(aspecto)
    ui.fim_2d()


def main():
    global partida, pedido, tempo_jogo, mensagem
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
    glfw.set_mouse_button_callback(window, mouse_clique)
    glfw.set_cursor_pos_callback(window, mouse_movimento)
    glfw.set_key_callback(window, tecla_callback)

    glEnable(GL_DEPTH_TEST)
    carregar_texturas()
    som.iniciar()
    lista_agua = compilar_agua(TAMANHO_CHAO, ALTURA_AGUA)
    ceu = compilar_ceu()

    recordes = ler_recordes()
    acumulado = 0.0         # tempo ainda não simulado pela física
    tempo_morto = 0.0
    f = 1.0                 # fração entre o passo anterior e o atual
    ultimo_tempo = glfw.get_time()

    while not glfw.window_should_close(window):
        glfw.poll_events()

        if pedido:
            aspecto = projecao(window)
            ui.inicio_2d(aspecto)
            ui.tela_carregando(aspecto)
            ui.fim_2d()
            glfw.swap_buffers(window)
            if partida:
                partida.apagar()
            partida = Partida(pedido)
            pedido = None
            acumulado = 0.0
            mensagem = ""
            mudar_estado(window, "jogando")
            ultimo_tempo = glfw.get_time()

        agora = glfw.get_time()
        # limite: depois de uma travada, não simula tudo de uma vez
        dt = min(agora - ultimo_tempo, 0.1)
        ultimo_tempo = agora

        if not pausado:
            tempo_jogo += dt

        if estado == "jogando" and not pausado:
            acumulado += dt
            # física em passos fixos: mesma velocidade em 60, 144 Hz...
            while acumulado >= PASSO and estado == "jogando":
                acumulado -= PASSO
                passo_jogo(window)
            if estado == "venceu":
                recordes = ler_recordes()
            tempo_morto = 0.0
            if estado == "jogando" and no_agua:
                som.coracao(perigo_atual(), dt)
            # desenha entre o passo anterior e o atual, para o movimento ficar suave
            f = acumulado / PASSO if estado == "jogando" else 1.0
            for i in range(3):
                pos_visual[i] = pos_anterior[i] + (posicao[i] - pos_anterior[i]) * f
        elif estado == "morreu" and not pausado:
            # mostra a tela por 2.5s e recomeça no mesmo mapa, com os cristais já pegos
            tempo_morto += dt
            if tempo_morto > 2.5:
                reiniciar(partida.monstro, partida.plataformas)
                acumulado = 0.0
                mudar_estado(window, "jogando")

        if estado == "menu":
            desenhar_menu(window, ceu, lista_agua, recordes)
        else:
            desenhar_jogo(window, ceu, lista_agua, f)
        glfw.swap_buffers(window)

    som.encerrar()
    glfw.terminate()


if __name__ == "__main__":
    main()
