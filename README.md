# Paisagem OpenGL

Mini game 3D em Python e OpenGL, feito para a disciplina de Computação Gráfica.

Pule de plataforma em plataforma, pegue os cristais para abrir o portal e chegue ao outro lado
do mapa. Se cair na água, o monstro vem atrás de você.

**Autores:** Anderson Rodrigues dos Santos e Frank Leite

## Como executar

Testado com Python 3.8 no Linux. É preciso ter uma placa de vídeo com suporte a OpenGL.

```bash
python3 -m pip install glfw PyOpenGL
python3 -m pip install pygame      # opcional: só para o som
python3 main.py
```

Sem o `pygame`, o jogo funciona normalmente, mudo. Texturas e sons são gerados por código:
não há arquivos de imagem nem de áudio.

## Controles

| Tecla | Ação |
|---|---|
| W A S D | Andar |
| Mouse | Olhar |
| Espaço | Pular |
| Clique esquerdo | Pegar o cristal próximo |
| V | Alternar primeira e terceira pessoa |
| Tab | Mostrar ou esconder o minimapa |
| N | Ligar ou desligar o som |
| Esc | Pausar (M, na pausa, volta ao menu) |

No menu: setas ou mouse para escolher, Enter ou clique para confirmar.

## Como jogar

- O sol fica na direção da chegada, e feixes de luz marcam os cristais.
- O portal fica vermelho até todos os cristais serem coletados; depois, verde.
- Ao morrer, você volta ao início e mantém os cristais. O cronômetro continua.
- O melhor tempo de cada dificuldade é salvo em `recordes.json`.

| Plataforma | Cor | Efeito |
|---|---|---|
| Normal | Madeira | Nenhum |
| Móvel | Azul | Vai e volta, levando o jogador |
| Afunda | Verde | Desce até a água enquanto você está em cima |
| Quebra | Vermelha | Cai 0,75 s depois de pisada e volta após 4 s |
| Impulso | Amarela | O pulo sai com 1,5x a velocidade |

O mapa é sorteado a cada partida. Uma busca em largura garante um caminho até a chegada, só com
plataformas normais, e cada cristal fica nele ou a um pulo de distância.

## Técnicas de Computação Gráfica

| Técnica | Onde |
|---|---|
| Transformações e câmera em primeira e terceira pessoa, projeção em perspectiva | `main.py` |
| Texturas procedurais (ruído), mipmaps e coordenadas pela posição no mundo | `texturas.py` |
| Iluminação direcional com normais por face | `iluminacao.py`, `texturas.py` |
| Sombras de contato (manchas sob o jogador e o monstro) | `iluminacao.py` |
| Shaders GLSL: ondas por vértice, Fresnel e Blinn-Phong por pixel | `agua.py` |
| Céu em cúpula, nuvens com transparência e neblina linear | `atmosfera.py` |
| Transparência e mistura aditiva (água, feixes, portal) | `agua.py`, `cristais.py` |
| Display lists para o cenário fixo | `ambiente.py`, `plataformas.py` |
| Projeção ortográfica para a interface e fonte própria de pixels | `interface.py` |
| Minimapa com recorte (scissor test) | `minimapa.py` |
| Física em passo fixo com interpolação do movimento | `main.py` |

## Organização

| Arquivo | Conteúdo |
|---|---|
| `main.py` | Laço principal, câmera, movimento e estados do jogo |
| `ambiente.py` | Geometria do cenário |
| `gerador.py` | Sorteio das plataformas e garantia de caminho |
| `colisao.py` | Colisão com caixas alinhadas aos eixos |
| `plataformas.py` | Plataformas especiais |
| `cristais.py` | Cristais, portal e contador na tela |
| `monstro.py` | Comportamento e desenho do monstro |
| `agua.py`, `atmosfera.py`, `iluminacao.py`, `texturas.py` | Visual |
| `interface.py`, `minimapa.py` | Menu, HUD, telas e minimapa |
| `dificuldade.py` | Dificuldades e recordes |
| `som.py` | Síntese e reprodução dos sons |
