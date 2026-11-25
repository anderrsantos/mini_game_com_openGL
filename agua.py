"""Água com ondas em GLSL: vértices deslocados, reflexo do céu (Fresnel) e brilho do sol.

Se o shader não compilar, usa a água simples de ambiente.py.
"""
import math
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

from ambiente import agua as agua_simples, compilar_agua
from atmosfera import COR_HORIZONTE, COR_ZENITE, NEBLINA_INICIO, NEBLINA_FIM
from iluminacao import DIRECAO_SOL_CEU
from texturas import usar, parar

CELULA = 5.0      # tamanho de cada quadrado da malha
# ondas: (direção x, direção z, comprimento, amplitude, velocidade angular)
ONDAS = ((0.8, 0.6, 38.0, 0.16, 1.1), (-0.5, 0.87, 24.0, 0.09, 1.6), (0.3, -0.95, 61.0, 0.12, 0.8))

_VERTICE = """
#version 120
uniform float tempo;
uniform vec4 ondas[3];      // k.x, k.z, amplitude, velocidade
varying vec3 mundo;
varying float neblina;
void main() {
    vec4 p = gl_Vertex;
    for (int i = 0; i < 3; i++)
        p.y += ondas[i].z * sin(dot(ondas[i].xy, p.xz) + ondas[i].w * tempo);
    mundo = p.xyz;
    vec4 olho = gl_ModelViewMatrix * p;
    neblina = -olho.z;
    gl_Position = gl_ProjectionMatrix * olho;
}
"""

_FRAGMENTO = """
#version 120
uniform float tempo;
uniform vec4 ondas[3];
uniform vec3 camera, sol, horizonte, zenite;
uniform vec2 limites;       // início e fim da neblina
uniform sampler2D textura;
varying vec3 mundo;
varying float neblina;
void main() {
    // normal = derivada das mesmas ondas do vértice, mais ondinhas só visuais
    vec2 d = vec2(0.0);
    for (int i = 0; i < 3; i++)
        d += ondas[i].xy * ondas[i].z * cos(dot(ondas[i].xy, mundo.xz) + ondas[i].w * tempo);
    float dist = length(camera - mundo);
    float detalhe = 1.0 / (1.0 + dist * 0.012);      // ao longe some, para não cintilar
    d += detalhe * 0.07 * vec2(cos(mundo.x * 1.1 + mundo.z * 0.7 + tempo * 2.1),
                               cos(mundo.z * 1.3 - mundo.x * 0.5 + tempo * 1.7));
    d += detalhe * 0.05 * vec2(cos(mundo.x * 2.3 - mundo.z * 1.9 - tempo * 2.9),
                               cos(mundo.z * 2.7 + mundo.x * 1.3 + tempo * 3.3));
    vec3 n = normalize(vec3(-d.x, 1.0, -d.y));
    vec3 v = normalize(camera - mundo);

    // cor própria: duas camadas da textura correndo em sentidos diferentes
    vec2 uv = mundo.xz / 25.0;
    vec3 base = 0.5 * texture2D(textura, uv + tempo * vec2(0.03, 0.02)).rgb
              + 0.5 * texture2D(textura, uv * 0.63 - tempo * vec2(0.02, 0.027)).rgb;

    // reflexo do céu, mais forte em ângulo rasante (Schlick)
    float fresnel = 0.03 + 0.97 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
    vec3 r = reflect(-v, n);
    vec3 ceu = mix(horizonte, zenite, clamp(r.y * 1.3, 0.0, 1.0));
    vec3 cor = mix(base, ceu, min(fresnel, 0.75));

    // rastro do sol (Blinn-Phong)
    float brilho = pow(max(dot(n, normalize(v + sol)), 0.0), 180.0);
    cor += vec3(1.0, 0.75, 0.45) * brilho * 0.9;

    float f = clamp((limites.y - neblina) / (limites.y - limites.x), 0.0, 1.0);
    float alfa = mix(1.0, clamp(0.78 + fresnel + brilho, 0.0, 1.0), f);
    gl_FragColor = vec4(mix(horizonte, cor, f), alfa);
}
"""


def _uniformes_ondas():
    return [(dx * 2 * math.pi / comp, dz * 2 * math.pi / comp, amp, vel)
            for dx, dz, comp, amp, vel in ONDAS]


class Agua:
    def __init__(self, tamanho, altura):
        self.altura_media = altura
        self.ondas = _uniformes_ondas()
        self.programa = None
        try:
            self.programa = compileProgram(compileShader(_VERTICE, GL_VERTEX_SHADER),
                                           compileShader(_FRAGMENTO, GL_FRAGMENT_SHADER))
        except Exception as erro:      # sem suporte a GLSL: segue com a água simples
            print("Água sem shader:", str(erro)[:200])
            self.lista = compilar_agua(tamanho, altura)
            return

        self.lista = self._malha(tamanho, altura)
        self.loc = {nome: glGetUniformLocation(self.programa, nome) for nome in
                    ("tempo", "ondas", "camera", "sol", "horizonte", "zenite", "limites", "textura")}
        glUseProgram(self.programa)
        glUniform4fv(self.loc["ondas"], 3, [c for onda in self.ondas for c in onda])
        glUniform3f(self.loc["sol"], *DIRECAO_SOL_CEU)
        glUniform3f(self.loc["horizonte"], *COR_HORIZONTE)
        glUniform3f(self.loc["zenite"], *COR_ZENITE)
        glUniform2f(self.loc["limites"], NEBLINA_INICIO, NEBLINA_FIM)
        glUniform1i(self.loc["textura"], 0)
        glUseProgram(0)

    def _malha(self, tamanho, altura):
        n = int(2 * tamanho / CELULA)
        pos = [-tamanho + i * CELULA for i in range(n + 1)]
        lista = glGenLists(1)
        glNewList(lista, GL_COMPILE)
        for x0, x1 in zip(pos, pos[1:]):
            glBegin(GL_TRIANGLE_STRIP)
            for z in pos:
                glVertex3f(x0, altura, z)
                glVertex3f(x1, altura, z)
            glEnd()
        glEndList()
        return lista

    def altura(self, x, z, tempo):
        """Altura da superfície naquele ponto (a mesma conta do shader)."""
        if self.programa is None:
            return self.altura_media
        return self.altura_media + sum(a * math.sin(kx * x + kz * z + w * tempo)
                                       for kx, kz, a, w in self.ondas)

    def desenhar(self, tempo, camera):
        """camera: posição da câmera no mundo. Desenhar depois do que é opaco."""
        if self.programa is None:
            agua_simples(self.lista, tempo)
            return
        usar("agua")
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self.programa)
        glUniform1f(self.loc["tempo"], tempo)
        glUniform3f(self.loc["camera"], *camera)
        glCallList(self.lista)
        glUseProgram(0)
        glDisable(GL_BLEND)
        parar()
