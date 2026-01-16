"""
EXTRAORDINARY OPENGL ENGINE v2.1
Advanced Turbine Visualization System
Fixed: Containment Breach Logic & Geometry Synchronization
Added: Real-time Structural Integrity Monitoring Overlay
"""

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF
from PyQt6.QtGui import QVector3D, QColor, QPainter, QFont, QPen, QBrush
from PyQt6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutSolidSphere
import math
import random
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import List
import time


@dataclass
class CFDGridCell:
    """Célula para simulação CFD básica"""
    velocity: QVector3D
    pressure: float
    temperature: float
    turbulence: float


class VortexRing:
    """Anel de vórtice para efeitos de fluxo secundário"""

    def __init__(self, position: QVector3D, strength: float = 1.0):
        self.position = position
        self.strength = strength
        self.radius = 0.5
        self.age = 0.0
        self.max_age = 5.0

    def update(self, dt: float):
        self.age += dt
        self.radius += dt * 0.2
        return self.age < self.max_age


class AdvancedParticle:
    """Partícula com física avançada e detecção de colisão robusta"""

    def __init__(self, particle_id: int):
        self.id = particle_id
        self.position = QVector3D()
        self.velocity = QVector3D()
        self.temperature = 300.0
        self.pressure = 101325.0
        self.mass = 1.0
        self.lifetime = 0.0
        self.max_lifetime = random.uniform(3.0, 8.0)
        self.trail: deque[QVector3D] = deque(maxlen=12)  # Aumentei um pouco o rastro
        self.reset()

    def reset(self):
        """Reinicia partícula na entrada (Intake)"""
        angle = random.uniform(0, 2 * math.pi)
        # Raio inicial seguro (dentro do Intake que tem raio 2.2)
        radius = random.uniform(0.3, 1.8)
        self.position = QVector3D(
            radius * math.cos(angle),
            radius * math.sin(angle),
            -6.0 + random.uniform(-0.5, 0.5)
        )
        self.velocity = QVector3D(0, 0, 1.0)  # Velocidade inicial garantida
        self.temperature = 300.0
        self.pressure = 101325.0
        self.lifetime = 0.0
        self.trail.clear()

    def update(self, dt: float, rpm: float, boundary_function, vortex_rings: List[VortexRing]):
        """Atualiza física da partícula com contenção estrita"""
        self.lifetime += dt
        self.trail.append(QVector3D(self.position))  # Cópia segura

        if self.lifetime > self.max_lifetime:
            self.reset()
            return

        # --- 1. Dinâmica de Fluidos ---
        speed_factor = max(1.0, rpm / 3600.0)

        # Perfil de Velocidade Axial (Baseado na Geometria Real)
        z = self.position.z()

        if z < -3.0:  # Intake
            axial_tgt = 2.0 * speed_factor
        elif z < -1.0:  # Compressor (Ar freia para ganhar pressão)
            axial_tgt = 1.5 * speed_factor
        elif z < 1.0:  # Combustor (Alta pressão, velocidade média)
            axial_tgt = 3.0 * speed_factor
        elif z < 4.0:  # Turbina (Expansão violenta)
            axial_tgt = 6.0 * speed_factor
        else:  # Exaustão
            axial_tgt = 8.0 * speed_factor

        # Suavização da velocidade (Inércia)
        self.velocity.setZ(self.velocity.z() * 0.9 + axial_tgt * 0.1)

        # Rotação (Swirl) induzida pelo eixo
        # O swirl é forte no compressor/turbina e fraco no combustor/exaustão
        swirl_intensity = 0.0
        if -5.0 < z < -1.0:
            swirl_intensity = 0.4  # Compressor
        elif 1.0 < z < 4.0:
            swirl_intensity = 0.3  # Turbina

        rotational_speed = swirl_intensity * speed_factor
        angle = math.atan2(self.position.y(), self.position.x())

        # Vetor tangencial
        tangent = QVector3D(-math.sin(angle), math.cos(angle), 0)

        # Aplica rotação à velocidade atual
        self.velocity += tangent * (rotational_speed * 10.0 * dt)

        # --- 2. Influência de Vórtices (Turbulência) ---
        for vortex in vortex_rings:
            to_vortex = vortex.position - self.position
            dist = to_vortex.length()
            if dist < vortex.radius * 2.5:
                # Turbulência caótica perto dos anéis
                cross = QVector3D.crossProduct(to_vortex.normalized(), QVector3D(0, 0, 1))
                self.velocity += cross * (vortex.strength * dt * 5.0)

        # --- 3. Integração de Posição ---
        self.position += self.velocity * dt

        # --- 4. CONTENÇÃO ESTRITA (Correção do Bug) ---
        # Calcula raio atual
        r_current = math.sqrt(self.position.x() ** 2 + self.position.y() ** 2)
        # Pega o limite exato da geometria naquele ponto Z
        r_max = boundary_function(self.position.z())

        if r_current >= r_max:
            # CORREÇÃO: Boundary Layer Sliding
            # Em vez de refletir (quicar), a partícula desliza na parede
            # Isso evita que ela ganhe energia radial e atravesse no próximo frame

            # 1. Traz de volta para dentro (com margem de segurança)
            correction_factor = (r_max * 0.95) / r_current
            self.position.setX(self.position.x() * correction_factor)
            self.position.setY(self.position.y() * correction_factor)

            # 2. Zera velocidade radial (impede que ela tente sair de novo)
            # Mantém apenas a velocidade Tangencial e Axial
            current_angle = math.atan2(self.position.y(), self.position.x())

            # Projeta velocidade na tangente da parede
            v_axial = self.velocity.z()
            v_tangent_mag = -self.velocity.x() * math.sin(current_angle) + self.velocity.y() * math.cos(current_angle)

            self.velocity.setX(-math.sin(current_angle) * v_tangent_mag)
            self.velocity.setY(math.cos(current_angle) * v_tangent_mag)
            self.velocity.setZ(v_axial)  # Mantém fluxo para frente

        # --- 5. Atualização Térmica ---
        # Mapa de temperatura baseado no Ciclo Brayton
        if z < -3.0:
            self.temperature = 300.0  # Ambiente
        elif z < -1.0:
            self.temperature = 300.0 + ((z + 3.0) / 2.0) * 400.0  # Compressão (esquenta)
        elif z < 1.0:
            self.temperature = 1400.0 + random.uniform(-100, 100)  # Combustão (Pico)
        elif z < 4.0:
            self.temperature = 1400.0 - ((z - 1.0) / 3.0) * 600.0  # Expansão (esfria gerando trabalho)
        else:
            self.temperature = 800.0 * 0.95  # Exaustão

        # Reset se sair pelo final
        if z > 8.0:
            self.reset()


class TurbineOpenGLView(QOpenGLWidget):
    """Motor de visualização 3D avançado para simulação de turbinas"""

    # Sinais
    performanceUpdated = pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Controles de câmera
        self.camera_distance = 14.0
        self.camera_rotation = QVector3D(-20, 45, 0)
        self.camera_target = QVector3D(0, 0, 0)
        self.last_mouse_pos = QPoint()

        # Estado da simulação
        self.rotation_angle = 0.0
        self.current_rpm = 0.0
        self.target_rpm = 0.0
        self.cutaway_mode = True
        self.show_flow = True
        self.show_thermal = True
        self.show_vortices = True

        # Monitoramento
        self.structural_integrity = 100.0
        self.vibration_level = 0.0

        # Sistemas avançados
        self.particles: List[AdvancedParticle] = []
        self.vortex_rings: List[VortexRing] = []

        # Performance tracking
        self.frame_times = deque(maxlen=60)
        self.last_time = time.time()
        self.fps = 60.0

        # Shaders & Texturas
        self.shader_program = None
        self.thermal_gradient_texture = None

        # Desgaste
        self.blade_wear = 0.0
        self.casing_oxidation = 0.0

        # Timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_physics)
        self.update_timer.start(16)

        # Inicializar partículas (Aumentado para realismo)
        self._init_particles(2000)

    def _init_particles(self, count: int):
        self.particles = [AdvancedParticle(i) for i in range(count)]

    def initializeGL(self):
        """Inicialização OpenGL avançada"""
        glClearColor(0.08, 0.09, 0.12, 1.0)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Anti-aliasing de linhas para o wireframe
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        self._setup_advanced_lighting()
        self._compile_shaders()
        self._create_thermal_gradient_texture()

        # Configurar materiais padrão
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 100.0)

    def _setup_advanced_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)

        # Luz Key (Quente/Solar)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [-10.0, 10.0, 10.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.85, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

        # Luz Fill (Azulada/Industrial)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, [10.0, -5.0, -5.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.2, 0.3, 0.5, 1.0])

    def _compile_shaders(self):
        # Shaders mantidos do seu código original (estão ótimos)
        try:
            vertex_shader = """
            #version 330 core
            layout(location = 0) in vec3 position;
            layout(location = 1) in vec3 normal;
            layout(location = 2) in vec2 texCoord;

            out vec3 FragPos;
            out vec3 Normal;
            out vec2 TexCoord;

            uniform mat4 model;
            uniform mat4 view;
            uniform mat4 projection;

            void main() {
                FragPos = vec3(model * vec4(position, 1.0));
                Normal = mat3(transpose(inverse(model))) * normal;
                TexCoord = texCoord;
                gl_Position = projection * view * model * vec4(position, 1.0);
            }
            """

            fragment_shader = """
            #version 330 core
            in vec3 FragPos;
            in vec3 Normal;
            in vec2 TexCoord;

            out vec4 FragColor;

            uniform vec3 viewPos;
            uniform float temperature;
            uniform float wear;

            vec3 getThermalColor(float temp) {
                float t = (temp - 300.0) / 800.0; // Ajustado range
                t = clamp(t, 0.0, 1.0);
                // Heatmap: Blue -> Cyan -> Green -> Yellow -> Red
                if (t < 0.25) return mix(vec3(0.0, 0.2, 0.8), vec3(0.0, 0.8, 0.8), t * 4.0);
                if (t < 0.5) return mix(vec3(0.0, 0.8, 0.8), vec3(0.0, 0.8, 0.0), (t-0.25) * 4.0);
                if (t < 0.75) return mix(vec3(0.0, 0.8, 0.0), vec3(1.0, 0.8, 0.0), (t-0.5) * 4.0);
                return mix(vec3(1.0, 0.8, 0.0), vec3(1.0, 0.2, 0.0), (t-0.75) * 4.0);
            }

            void main() {
                vec3 norm = normalize(Normal);
                vec3 lightDir = normalize(vec3(1.0, 1.0, 1.0));
                float diff = max(dot(norm, lightDir), 0.0);

                // Specular mais metálico
                vec3 viewDir = normalize(viewPos - FragPos);
                vec3 reflectDir = reflect(-lightDir, norm);
                float spec = pow(max(dot(viewDir, reflectDir), 0.0), 64.0);

                vec3 baseColor = getThermalColor(temperature);
                vec3 result = (baseColor * 0.6 + diff * 0.4 * baseColor) + vec3(spec);

                FragColor = vec4(result, 1.0);
            }
            """

            self.shader_program = QOpenGLShaderProgram()
            self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vertex_shader)
            self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fragment_shader)
            self.shader_program.link()
            print("Shaders compiled successfully")
        except Exception as e:
            print(f"Shader error: {e}")
            self.shader_program = None

    def _create_thermal_gradient_texture(self):
        width = 256
        data = np.zeros((width, 4), dtype=np.uint8)
        for i in range(width):
            t = i / width
            # Gradiente industrial (Steel -> Heat)
            if t < 0.5:  # Frio/Morno
                data[i] = [int(100 + t * 100), int(100 + t * 50), int(100), 200]
            else:  # Quente
                data[i] = [int(200 + (t - 0.5) * 110), int(125 - (t - 0.5) * 250), 50, 220]

        self.thermal_gradient_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self.thermal_gradient_texture)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA, width, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def resizeGL(self, w: int, h: int):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / max(h, 1)
        gluPerspective(40.0, aspect, 0.1, 100.0)  # FOV mais cinematográfico
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        self.frame_times.append(dt)
        self.fps = len(self.frame_times) / (sum(self.frame_times) + 1e-6)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        self._setup_camera()
        self._render_scene(dt)

        # 2D Overlay (QPainter) para o monitoramento extra que você pediu
        self._render_overlay_stats()

    def _render_overlay_stats(self):
        """Renderiza dados técnicos sobre a cena OpenGL"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Estilo Técnico
        font = QFont("Consolas", 9)
        painter.setFont(font)

        # Caixa de Monitor CFD
        w = 220
        h = 130
        margin = 10
        rect = QRectF(self.width() - w - margin, margin, w, h)

        painter.setBrush(QBrush(QColor(0, 20, 40, 200)))
        painter.setPen(QPen(QColor(0, 200, 255), 1))
        painter.drawRoundedRect(rect, 5, 5)

        # Texto
        painter.setPen(QColor(200, 220, 255))
        x = int(rect.x() + 10)
        y = int(rect.y() + 20)

        painter.drawText(x, y, "CFD REAL-TIME MONITOR")
        y += 20
        painter.drawText(x, y, f"ACTIVE PARTICLES: {len(self.particles)}")
        y += 15
        painter.drawText(x, y, f"VORTEX RINGS: {len(self.vortex_rings)}")
        y += 15
        painter.drawText(x, y, f"CONTAINMENT: {'STABLE' if self.structural_integrity > 90 else 'CRITICAL'}")

        # Barra de Integridade
        y += 20
        painter.drawText(x, y, "STRUCTURAL INTEGRITY:")
        y += 5
        bar_w = 180
        painter.setBrush(QBrush(QColor(50, 0, 0)))
        painter.drawRect(x, y, bar_w, 8)

        if self.structural_integrity > 80:
            color = QColor(0, 255, 0)
        elif self.structural_integrity > 40:
            color = QColor(255, 200, 0)
        else:
            color = QColor(255, 0, 0)

        painter.setBrush(QBrush(color))
        painter.drawRect(x, y, int(bar_w * (self.structural_integrity / 100.0)), 8)

        painter.end()

    def _setup_camera(self):
        glTranslatef(0, 0, -self.camera_distance)
        glRotatef(self.camera_rotation.x(), 1, 0, 0)
        glRotatef(self.camera_rotation.y(), 0, 1, 0)
        glTranslatef(-self.camera_target.x(), -self.camera_target.y(), -self.camera_target.z())

    def _render_scene(self, dt: float):
        if self.cutaway_mode: self._enable_cutaway_clip()

        # Desenhar Carcaça
        self._draw_advanced_casing()

        if self.cutaway_mode: self._disable_cutaway_clip()

        # Rotor
        glPushMatrix()
        glRotatef(self.rotation_angle, 0, 0, 1)
        self._draw_advanced_rotor()
        glPopMatrix()

        # Fluxo (Partículas)
        if self.show_flow:
            self._draw_advanced_flow(dt)

        # Vórtices
        if self.show_vortices:
            self._draw_vortex_rings()

        # Efeitos Térmicos na Carcaça
        if self.show_thermal:
            self._draw_thermal_gradient()

    def _enable_cutaway_clip(self):
        eqn = [0.0, -1.0, 0.0, 0.0]
        glClipPlane(GL_CLIP_PLANE0, eqn)
        glEnable(GL_CLIP_PLANE0)

    def _disable_cutaway_clip(self):
        glDisable(GL_CLIP_PLANE0)

    def _draw_advanced_casing(self):
        """
        Geometria da Carcaça Sincronizada com Física
        Importante: Os raios aqui definidos batem com _get_boundary_radius
        """
        glEnable(GL_BLEND)
        # Material metálico semi-transparente
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.7, 0.7, 0.8, 0.15])

        quad = gluNewQuadric()

        # 1. Intake Housing (Z: -6 a -3)
        glPushMatrix()
        glTranslatef(0, 0, -6.0)
        # Raio constante 2.2
        gluCylinder(quad, 2.2, 2.2, 3.0, 40, 2)
        # Capa frontal
        gluDisk(quad, 2.0, 2.2, 40, 2)
        glPopMatrix()

        # 2. Compressor Casing (Z: -3 a -1) - Convergente
        glPushMatrix()
        glTranslatef(0, 0, -3.0)
        # Raio 2.2 -> 1.9
        gluCylinder(quad, 2.2, 1.9, 2.0, 40, 2)
        glPopMatrix()

        # 3. Combustor Casing (Z: -1 a 1) - Constante
        glPushMatrix()
        glTranslatef(0, 0, -1.0)
        # Raio 1.9
        gluCylinder(quad, 1.9, 1.9, 2.0, 40, 2)
        glPopMatrix()

        # 4. Turbine Casing (Z: 1 a 4) - Divergente
        glPushMatrix()
        glTranslatef(0, 0, 1.0)
        # Raio 1.9 -> 2.4
        gluCylinder(quad, 1.9, 2.4, 3.0, 40, 2)
        glPopMatrix()

        # 5. Exhaust Casing (Z: 4 a 7) - Divergente
        glPushMatrix()
        glTranslatef(0, 0, 4.0)
        # Raio 2.4 -> 3.0
        gluCylinder(quad, 2.4, 3.0, 3.0, 40, 2)
        glPopMatrix()

        gluDeleteQuadric(quad)
        glDisable(GL_BLEND)

    def _draw_advanced_rotor(self):
        # Eixo Central
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.3, 0.3, 0.35, 1.0])
        quad = gluNewQuadric()
        glPushMatrix()
        glTranslatef(0, 0, -5.5)
        gluCylinder(quad, 0.6, 0.6, 11.0, 32, 2)
        glPopMatrix()

        # Compressor (Z ~ -5 a -1)
        for i in range(10):
            z = -5.0 + i * 0.4
            # Raio diminui de 1.9 para 1.3
            r = 1.9 - (i * 0.06)
            self._draw_compressor_stage(z, r, [0.1, 0.5, 0.9])

        # Combustor (Z ~ 0) - Estático Visual
        glPushMatrix()
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.8, 0.3, 0.1, 1.0])
        glTranslatef(0, 0, -0.5)
        gluCylinder(quad, 1.4, 1.4, 1.0, 32, 2)
        glPopMatrix()

        # Turbina (Z ~ 1 a 3.5)
        for i in range(5):
            z = 1.2 + i * 0.6
            # Raio aumenta de 1.4 para 2.0
            r = 1.4 + (i * 0.12)
            # Cor muda com calor
            heat_col = [0.8, 0.5 - i * 0.1, 0.2]
            self._draw_turbine_stage(z, r, heat_col)

        gluDeleteQuadric(quad)

    def _draw_compressor_stage(self, z, r, color):
        glPushMatrix()
        glTranslatef(0, 0, z)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, color + [1.0])
        quad = gluNewQuadric()

        # Cubo
        gluDisk(quad, 0.6, r * 0.8, 20, 2)

        # Pás
        num_blades = 20
        for i in range(num_blades):
            glPushMatrix()
            glRotatef(i * (360 / num_blades), 0, 0, 1)
            glBegin(GL_TRIANGLES)
            glNormal3f(0, 0, 1)
            glVertex3f(0.6, 0, 0)
            glVertex3f(r, 0.1, 0)
            glVertex3f(r, -0.1, 0)
            glEnd()
            glPopMatrix()
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_turbine_stage(self, z, r, color):
        glPushMatrix()
        glTranslatef(0, 0, z)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, color + [1.0])
        quad = gluNewQuadric()

        gluDisk(quad, 0.6, r * 0.9, 16, 2)

        num_blades = 16
        for i in range(num_blades):
            glPushMatrix()
            glRotatef(i * (360 / num_blades), 0, 0, 1)
            glBegin(GL_QUADS)
            glNormal3f(0, 0, 1)
            glVertex3f(0.6, 0.05, 0)
            glVertex3f(0.6, -0.05, 0)
            glVertex3f(r, -0.1, 0)
            glVertex3f(r, 0.1, 0)
            glEnd()
            glPopMatrix()
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_advanced_flow(self, dt):
        if not self.particles: return
        glDisable(GL_LIGHTING)

        # Desenhar Pontos (Núcleo)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for p in self.particles:
            # Cor baseada em Temperatura
            # Azul(300K) -> Branco(1000K) -> Vermelho(1500K)
            t_factor = (p.temperature - 300) / 1200.0
            if t_factor < 0.3:
                glColor3f(0, t_factor * 3, 1.0)
            elif t_factor < 0.6:
                glColor3f((t_factor - 0.3) * 3, 1.0, 1.0 - (t_factor - 0.3) * 3)
            else:
                glColor3f(1.0, 1.0 - (t_factor - 0.6) * 3, 0)

            glVertex3f(p.position.x(), p.position.y(), p.position.z())
        glEnd()

        # Desenhar Rastros (Trails) - Motion Blur
        glEnable(GL_BLEND)
        glLineWidth(1.0)
        for p in self.particles:
            if len(p.trail) < 2: continue

            # Trail mais transparente
            t_factor = (p.temperature - 300) / 1200.0
            glColor4f(1.0 if t_factor > 0.6 else 0.0, 0.5, 1.0 - t_factor, 0.2)

            glBegin(GL_LINE_STRIP)
            for pos in p.trail:
                glVertex3f(pos.x(), pos.y(), pos.z())
            glEnd()

        glEnable(GL_LIGHTING)

    def _draw_vortex_rings(self):
        if not self.vortex_rings: return
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glColor4f(0.6, 0.9, 1.0, 0.15)  # Vórtices sutis

        for v in self.vortex_rings:
            glPushMatrix()
            glTranslatef(v.position.x(), v.position.y(), v.position.z())
            glutSolidSphere(v.radius, 10, 10)  # Simula volume de gás
            glPopMatrix()
        glEnable(GL_LIGHTING)

    def _draw_thermal_gradient(self):
        # Efeito sutil de calor na carcaça usando textura 1D
        if not self.thermal_gradient_texture: return
        glEnable(GL_TEXTURE_1D)
        glBindTexture(GL_TEXTURE_1D, self.thermal_gradient_texture)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending para "brilho"

        # Cilindro de calor ao redor do combustor
        glBegin(GL_QUAD_STRIP)
        for i in range(20):
            z = -2.0 + i * 0.3  # Zona central
            t = abs(z) / 3.0  # Mapeamento
            glTexCoord1f(t)

            radius = 2.0
            for j in range(13):  # +1 para fechar o loop
                angle = j * (2 * math.pi / 12)
                x = math.cos(angle) * radius
                y = math.sin(angle) * radius
                glVertex3f(x, y, z)
        glEnd()

        glDisable(GL_TEXTURE_1D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _update_physics(self):
        dt = 0.016

        # Suavização do RPM
        if abs(self.current_rpm - self.target_rpm) > 1.0:
            self.current_rpm += (self.target_rpm - self.current_rpm) * 0.05

        self.rotation_angle -= self.current_rpm * 0.1 * dt
        self.rotation_angle %= 360.0

        # Atualiza Partículas
        bound_fn = self._get_boundary_radius
        for p in self.particles:
            p.update(dt, self.current_rpm, bound_fn, self.vortex_rings)

        # Vórtices
        self.vortex_rings = [v for v in self.vortex_rings if v.update(dt)]
        if self.current_rpm > 1000 and random.random() < 0.03:
            z = random.uniform(1.5, 3.5)  # Vórtices na turbina
            self.vortex_rings.append(VortexRing(QVector3D(0, 0, z), 1.0))

        # Integridade Estrutural (Simulação)
        stress = (self.current_rpm / 3600.0)
        self.vibration_level = stress * 2.0 + random.uniform(-0.1, 0.1)
        if self.current_rpm > 4000:  # Overspeed damage
            self.structural_integrity -= dt * 0.1
        elif self.structural_integrity < 100.0:
            self.structural_integrity += dt * 0.05  # Auto-repair (simulado)

        self.update()

    # --- GEOMETRIA MATEMÁTICA ---
    def _get_boundary_radius(self, z: float) -> float:
        """
        Retorna o raio interno EXATO da carcaça no ponto Z.
        Sincronizado com _draw_advanced_casing.
        """
        if z < -6.0:
            return 2.2  # Pré-Intake
        elif z < -3.0:
            return 2.2  # Intake Housing
        elif z < -1.0:  # Compressor (Cone)
            # De -3.0 a -1.0 (Comprimento 2.0)
            # Raio de 2.2 a 1.9
            ratio = (z + 3.0) / 2.0
            return 2.2 - (0.3 * ratio)
        elif z < 1.0:
            return 1.9  # Combustor
        elif z < 4.0:  # Turbine (Cone)
            # De 1.0 a 4.0 (Comprimento 3.0)
            # Raio de 1.9 a 2.4
            ratio = (z - 1.0) / 3.0
            return 1.9 + (0.5 * ratio)
        else:  # Exhaust
            # De 4.0 a ...
            # Raio de 2.4 a 3.0
            ratio = min(1.0, (z - 4.0) / 3.0)
            return 2.4 + (0.6 * ratio)

    # API Pública
    def update_physics(self, rpm: float):
        self.target_rpm = rpm

    def toggle_cutaway(self):
        self.cutaway_mode = not self.cutaway_mode; self.update()

    # Mouse Interaction
    def mousePressEvent(self, e):
        self.last_mouse_pos = e.pos()

        def _compile_shaders(self):
            try:
                # NOTA: O .strip() no final é CRUCIAL para remover espaços em branco
                # antes do #version, que causam erro no macOS.

                vertex_shader_source = """
    #version 330 core
    layout(location = 0) in vec3 position;
    layout(location = 1) in vec3 normal;
    layout(location = 2) in vec2 texCoord;

    out vec3 FragPos;
    out vec3 Normal;
    out vec2 TexCoord;

    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;

    void main() {
        FragPos = vec3(model * vec4(position, 1.0));
        Normal = mat3(transpose(inverse(model))) * normal;
        TexCoord = texCoord;
        gl_Position = projection * view * model * vec4(position, 1.0);
    }
    """.strip()

                fragment_shader_source = """
    #version 330 core
    in vec3 FragPos;
    in vec3 Normal;
    in vec2 TexCoord;

    out vec4 FragColor;

    uniform vec3 viewPos;
    uniform float temperature;
    uniform float wear;

    vec3 getThermalColor(float temp) {
        float t = (temp - 300.0) / 800.0;
        t = clamp(t, 0.0, 1.0);
        if (t < 0.25) return mix(vec3(0.0, 0.2, 0.8), vec3(0.0, 0.8, 0.8), t * 4.0);
        if (t < 0.5) return mix(vec3(0.0, 0.8, 0.8), vec3(0.0, 0.8, 0.0), (t-0.25) * 4.0);
        if (t < 0.75) return mix(vec3(0.0, 0.8, 0.0), vec3(1.0, 0.8, 0.0), (t-0.5) * 4.0);
        return mix(vec3(1.0, 0.8, 0.0), vec3(1.0, 0.2, 0.0), (t-0.75) * 4.0);
    }

    void main() {
        vec3 norm = normalize(Normal);
        vec3 lightDir = normalize(vec3(1.0, 1.0, 1.0));
        float diff = max(dot(norm, lightDir), 0.0);

        vec3 viewDir = normalize(viewPos - FragPos);
        vec3 reflectDir = reflect(-lightDir, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), 64.0);

        vec3 baseColor = getThermalColor(temperature);
        vec3 result = (baseColor * 0.6 + diff * 0.4 * baseColor) + vec3(spec);

        FragColor = vec4(result, 1.0);
    }
    """.strip()

                self.shader_program = QOpenGLShaderProgram()
                # Adiciona os shaders usando as strings limpas
                if not self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex,
                                                                   vertex_shader_source):
                    print(f"Vertex Shader Error: {self.shader_program.log()}")

                if not self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment,
                                                                   fragment_shader_source):
                    print(f"Fragment Shader Error: {self.shader_program.log()}")

                self.shader_program.link()
                print("Shaders compiled successfully")

            except Exception as e:
                print(f"Shader compilation exception: {e}")
                self.shader_program = None
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            delta = e.pos() - self.last_mouse_pos
            self.last_mouse_pos = e.pos()
            self.camera_rotation.setX(self.camera_rotation.x() + delta.y() * 0.5)
            self.camera_rotation.setY(self.camera_rotation.y() + delta.x() * 0.5)
            self.update()

    def wheelEvent(self, e):
        delta = e.angleDelta().y() / 120.0
        self.camera_distance = max(5.0, min(30.0, self.camera_distance - delta))
        self.update()