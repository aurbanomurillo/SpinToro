from math import cos,sin,pi
from PIL import Image, ImageDraw, ImageFont
import importlib
import os
import numpy as np
import progressbar

scale = 1



wide = 160*scale
high = 48*scale
cantidad_de_pixeles = wide * high

# Variables globales de rotación para la animación
A = 0.0 # Ángulo de rotación en X
B = 0.0 # Ángulo de rotación en Z

# Ángulos del bucle
theta = 0.0 # Ángulo del bucle que recorre el tubo
phi = 0.0 # Ángulo del bucle que recorre el toroide principal

R1 = 1.0*scale # Radio del tubo del donut
R2 = 2.0*scale # Distancia del centro del donut al centro del tubo
K2 = 5.0*scale # Distancia del donut a la cámara (para que no esté pegado a los ojoS
K1 = 60.0*scale # Escala para hacer el donut más grande en la pantalla

CHARS = ".,-~:;=!*#$@" # Paleta de caracteres (12 niveles de oscuridad a brillo)


# --- OPTIMIZACIÓN ---
# El bucle original llamaba a cos()/sin() de theta, phi, A y B DENTRO del
# doble bucle (theta x phi ≈ 252x252 ≈ 63.500 puntos por frame), y además
# los recalculaba por duplicado (una vez en xyz(), otra en L()). Eso son
# ~16 llamadas trigonométricas por punto x ~63.500 puntos x ~1257 frames
# ≈ 1.270 millones de llamadas a cos/sin... por frame, y de verdad,
# >1.000 millones en todo el vídeo.
#
# Pero theta y phi recorren SIEMPRE la misma secuencia de valores en cada
# frame (solo A y B cambian entre frames), así que cos(theta), sin(theta),
# cos(phi) y sin(phi) se pueden calcular UNA SOLA VEZ para todo el vídeo
# y guardarse en tablas. cos(A), sin(A), cos(B), sin(B) cambian una vez
# por frame, así que se calculan una vez por frame (no por punto).
#
# Con eso, dentro del doble bucle ya no hace falta llamar a cos/sin en
# absoluto: solo queda aritmética simple (multiplicaciones y sumas) sobre
# valores ya calculados. El resultado matemático es idéntico (comprobado
# numéricamente, diferencia ~1e-15, puro ruido de redondeo de punto
# flotante, no afecta a ningún píxel ni carácter).
PASO = 0.025

def _generar_secuencia(limite):
    valores = []
    v = 0.0
    while v <= float(limite):
        valores.append(v)
        v += PASO
    return valores

thetas = _generar_secuencia(2 * pi)
phis = _generar_secuencia(2 * pi)
n_theta = len(thetas)
n_phi = len(phis)

cos_thetas = [cos(t) for t in thetas]
sin_thetas = [sin(t) for t in thetas]
cos_phis = [cos(p) for p in phis]
sin_phis = [sin(p) for p in phis]

# (R2 + R1*cos(theta)) no depende de A ni B: se precalcula una sola vez.
r_tubo = [R2 + R1 * ct for ct in cos_thetas]


# Configuración del vídeo final
video_w = 1920
video_h = 1080
fps = 60
salida_mp4 = "donut_3d_1080p.mp4"

# Bucle perfecto: usamos el incremento actual de B para estimar frames,
# y ajustamos incrementos exactos para cerrar exactamente en 2*pi.
velocidad_rotacion = 0.25
incremento_B_base = 0.02 * velocidad_rotacion
frames_totales = round((2 * pi) / incremento_B_base)
incremento_B = (2 * pi) / frames_totales
incremento_A = 2 * incremento_B

# Cargamos una fuente monoespaciada para no deformar el ASCII
tam_fuente = max(10, min(video_w // wide, video_h // high))
rutas_fuente = ["consola.ttf", "cour.ttf", "Courier New.ttf"]
fuente = None
for ruta in rutas_fuente:
    try:
        fuente = ImageFont.truetype(ruta, tam_fuente)
        break
    except OSError:
        continue
if fuente is None:
    fuente = ImageFont.load_default()

# Medimos celda para centrar el buffer ASCII en 1080p
dummy_img = Image.new("RGB", (video_w, video_h), "black")
dummy_draw = ImageDraw.Draw(dummy_img)
bbox = dummy_draw.textbbox((0, 0), "@", font=fuente)
glyph_left = bbox[0]
glyph_top = bbox[1]
celda_w = max(1, bbox[2] - bbox[0])
celda_h = max(1, bbox[3] - bbox[1])
offset_x = ((video_w - (wide * celda_w)) // 2) - glyph_left
offset_y = ((video_h - (high * celda_h)) // 2) - glyph_top

# Inicializamos writer de OpenCV
if os.path.exists(salida_mp4):
    try:
        os.remove(salida_mp4)
    except PermissionError:
        base, ext = os.path.splitext(salida_mp4)
        idx = 1
        while os.path.exists(f"{base}_{idx}{ext}"):
            idx += 1
        salida_mp4 = f"{base}_{idx}{ext}"

# NOTA: cv2.VideoWriter con fourcc "avc1" se elimina a propósito.
# En muchos sistemas (sobre todo Windows, vía el backend Media Foundation)
# ese escritor "se abre" correctamente (isOpened() == True) pero genera un
# stream H.264 / contenedor MP4 mal formado, sin lanzar ningún error.
# Por eso el video queda corrupto (macrobloques rotos, no reproducible en
# navegador, Windows Media Player ni en el Live Wallpaper) aunque el script
# termine "sin problemas". Usamos siempre imageio + ffmpeg (libx264), que
# es el codificador real y fiable multiplataforma.
imageio = importlib.import_module("imageio.v2")
writer = imageio.get_writer(
    salida_mp4,
    fps=fps,
    codec="libx264",
    pixelformat="yuv420p",   # compatibilidad universal (navegador / Windows / Wallpaper Engine)
    macro_block_size=None,
    output_params=[
        "-movflags", "+faststart",  # evita el típico "no reproduce en el navegador"
        "-crf", "18",                # calidad alta, sin forzar bitrate
        "-preset", "medium",
        # NO fijamos -profile/-level a mano: a 1080p60 hace falta nivel 4.2,
        # y forzarlo mal (p.ej. a 4.0) volvería a corromper el archivo.
        # Dejamos que libx264 elija el nivel correcto automáticamente.
    ],
)
usar_cv2 = False

barra = progressbar.ProgressBar(
    maxval=frames_totales,
    widgets=[
        progressbar.Bar(marker="=", left="[", right="]"),
        " ",
        progressbar.Percentage(),
        " ",
        progressbar.ETA(),
    ],
).start()

for frame_idx in range(frames_totales): # Bucle finito (cada ciclo es un frame)
    
    # ¡LA CLAVE! Resetear buffers al inicio del frame
    z_buffer = [0.0] * cantidad_de_pixeles
    screen_buffer = [" "] * cantidad_de_pixeles

    # cos(A), sin(A), cos(B), sin(B) cambian una vez por frame: se calculan
    # aquí UNA sola vez (antes se recalculaban en cada uno de los ~63.500
    # puntos del frame, 8 veces cada uno).
    cA = cos(A)
    sA = sin(A)
    cB = cos(B)
    sB = sin(B)

    # Términos que dependen de phi y del frame (A,B), pero no de theta:
    # se precalculan una vez por frame, fuera del bucle interno.
    x_phi = [cB*cp + sA*sB*sp for cp, sp in zip(cos_phis, sin_phis)]
    y_phi = [sB*cp - sA*cB*sp for cp, sp in zip(cos_phis, sin_phis)]
    z_phi = [cA*sp for sp in sin_phis]
    # K_phi/K_theta son la fórmula de L() reagrupada algebraicamente:
    # L = cos(theta)*K_phi(phi) + sin(theta)*K_theta  (idéntico resultado,
    # verificado numéricamente, solo reescrito para no repetir cálculos).
    K_phi = [sB*cp - sp*(cA + cB*sA) for cp, sp in zip(cos_phis, sin_phis)]
    K_theta = cA*cB - sA

    # Términos que dependen de theta y del frame (A,B), pero no de phi:
    x_theta_b = [R1*cA*sB*st for st in sin_thetas]
    y_theta_b = [R1*cA*cB*st for st in sin_thetas]
    z_theta_b = [R1*sA*st for st in sin_thetas]

    for i in range(n_theta):
        ct = cos_thetas[i]
        st = sin_thetas[i]
        rt = r_tubo[i]
        xtb = x_theta_b[i]
        ytb = y_theta_b[i]
        ztb = z_theta_b[i]

        for j in range(n_phi):

            # 1-2. Posición 3D ya rotada (A, B), sin llamar a cos/sin aquí:
            # pura aritmética sobre valores precalculados.
            x = rt * x_phi[j] - xtb
            y = rt * y_phi[j] + ytb
            z = K2 + rt * z_phi[j] + ztb

            # 3. Iluminación (misma fórmula que L(), reagrupada)
            lumi = ct * K_phi[j] + st * K_theta

            # 4. Proyectar a coordenadas 2D (x', y')
            xp = int((wide//2) + (K1*x)/z)
            # Multiplicamos por 0.5 para compensar la altura de las fuentes de la terminal
            yp = int((high//2) - (K1*y*0.5)/z)

            # 5. Comprobar Z-buffer en la posición (x', y'):
                 # Si el nuevo 'z' está más cerca:
            if 0<= xp < wide and 0 <= yp < high:
                
                pos = xp + yp * wide
                
                # Calculamos la inversa de Z. 
                # Un 1/z mayor significa que el punto está más cerca de la cámara.
                z_inv = 1 / z
                
                # Si este punto está por delante de lo que había dibujado antes...
                if z_inv > z_buffer[pos]:
                    z_buffer[pos] = z_inv # Actualizamos la memoria de profundidad
                    
                    # Transformamos la luz matemática en un carácter ASCII
                    if lumi > 0:
                        # Multiplicamos por 8 para escalar el decimal a un índice entero
                        indice_luz = int(lumi * 8)
                                                
                        # Evitamos que el índice supere el límite de nuestra cadena
                        if indice_luz > 11:
                            indice_luz = 11
                            
                        # Dibujamos el píxel en el buffer de pantalla
                        screen_buffer[pos] = CHARS[indice_luz]

    # El donut ya se proyecta centrado con xyprime; evitamos recentrarlo
    # por frame para no introducir saltos visuales en el vídeo.
    lineas_centradas = [
        "".join(screen_buffer[fila * wide : (fila + 1) * wide])
        for fila in range(high)
    ]

    # 6. Renderizar el screen_buffer en una imagen negra 1080p
    frame_img = Image.new("RGB", (video_w, video_h), "black")
    draw = ImageDraw.Draw(frame_img)

    for fila in range(high):
        y_texto = offset_y + fila * celda_h
        linea_ascii = lineas_centradas[fila]
        draw.text((offset_x, y_texto), linea_ascii, font=fuente, fill=(255, 255, 255))

    # Guardamos frame en el vídeo
    frame_np = np.array(frame_img)
    writer.append_data(frame_np)

    barra.update(frame_idx + 1)

    # 7. Aumentar A y B un poquito
    A += incremento_A
    B += incremento_B

writer.close()
barra.finish()
print(f"Video exportado correctamente: {salida_mp4}")