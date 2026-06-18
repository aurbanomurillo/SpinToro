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


def xyz(theta:float, phi:float) -> list[float,float,float]:
    x = (R2+R1*cos(theta))*(cos(B)*cos(phi)+sin(A)*sin(B)*sin(phi))-R1*cos(A)*sin(B)*sin(theta)
    y = (R2+R1*cos(theta))*(sin(B)*cos(phi)-sin(A)*cos(B)*sin(phi))+R1*cos(A)*cos(B)*sin(theta)
    z = K2+cos(A)*(R2+R1*cos(theta))*sin(phi)+R1*sin(A)*sin(theta)
    return [x,y,z]

def xyprime(xyz:list[float,float,float]) -> list[int,int]:
    x = xyz[0]
    y = xyz[1]
    z = xyz[2]
    
    xprime = int((wide//2) + (K1*x)/z)
    # Multiplicamos por 0.5 para compensar la altura de las fuentes de la terminal
    yprime = int((high//2) - (K1*y*0.5)/z) 
    return [xprime,yprime]


def L(theta:float, phi:float) -> float:
    L = cos(phi)*cos(theta)*sin(B) - cos(A)*cos(theta)*sin(phi) - sin(A)*sin(theta) + cos(B)*(cos(A)*sin(theta) - cos(theta)*sin(A)*sin(phi))
    return L

# Configuración del vídeo final
video_w = 1920
video_h = 1080
fps = 60
salida_mp4 = "donut_3d_1080p.mp4"

# Bucle perfecto: usamos el incremento actual de B para estimar frames,
# y ajustamos incrementos exactos para cerrar exactamente en 2*pi.
velocidad_rotacion = 0.5
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

usar_cv2 = True
cv2 = None
imageio = None

try:
    cv2 = importlib.import_module("cv2")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(salida_mp4, fourcc, fps, (video_w, video_h))
    if not writer.isOpened():
        raise RuntimeError("OpenCV no pudo abrir el escritor de vídeo")
except Exception:
    usar_cv2 = False
    imageio = importlib.import_module("imageio.v2")
    writer = imageio.get_writer(
        salida_mp4,
        fps=fps,
        codec="libx264",
        quality=10,
        macro_block_size=None,
    )

barra = progressbar.ProgressBar(
    max_value=frames_totales,
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

    theta = 0.0
    while theta <= float(2*pi):

        phi = 0.0
        while phi <= float(2*pi):
            
            # 1. Calcular posición 3D (x, y, z)
            # 2. Rotar posición 3D usando A y B

            coords = xyz(theta,phi)

            # 3. Calcular normal, rotarla y hacer producto escalar con la luz
            lumi = L(theta, phi)

            # 4. Proyectar a coordenadas 2D (x', y')
            coords_prime = xyprime(coords)
            xp = coords_prime[0]
            yp = coords_prime[1]

            # 5. Comprobar Z-buffer en la posición (x', y'):
                 # Si el nuevo 'z' está más cerca:
            if 0<= xp < wide and 0 <= yp < high:
                
                pos = xp + yp * wide
                
                # Calculamos la inversa de Z. 
                # Un 1/z mayor significa que el punto está más cerca de la cámara.
                z_inv = 1 / coords[2]
                
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

            phi += 0.05

        theta += 0.05

    # Centramos el contenido real del donut dentro del buffer ASCII
    min_x = wide
    max_x = -1
    min_y = high
    max_y = -1

    for fila in range(high):
        inicio = fila * wide
        fin = inicio + wide
        linea = screen_buffer[inicio:fin]
        if any(c != " " for c in linea):
            min_y = min(min_y, fila)
            max_y = max(max_y, fila)
            for col, c in enumerate(linea):
                if c != " ":
                    min_x = min(min_x, col)
                    max_x = max(max_x, col)

    lineas_centradas = [" " * wide for _ in range(high)]
    if max_x >= 0 and max_y >= 0:
        centro_obj_x = (min_x + max_x) / 2.0
        centro_obj_y = (min_y + max_y) / 2.0
        centro_buf_x = (wide - 1) / 2.0
        centro_buf_y = (high - 1) / 2.0
        shift_x = int(round(centro_buf_x - centro_obj_x))
        shift_y = int(round(centro_buf_y - centro_obj_y))

        temp_rows = [list(" " * wide) for _ in range(high)]
        for fila in range(high):
            inicio = fila * wide
            fin = inicio + wide
            linea = screen_buffer[inicio:fin]
            nueva_fila = fila + shift_y
            if 0 <= nueva_fila < high:
                for col, c in enumerate(linea):
                    if c != " ":
                        nueva_col = col + shift_x
                        if 0 <= nueva_col < wide:
                            temp_rows[nueva_fila][nueva_col] = c
        lineas_centradas = ["".join(r) for r in temp_rows]

    # 6. Renderizar el screen_buffer en una imagen negra 1080p
    frame_img = Image.new("RGB", (video_w, video_h), "black")
    draw = ImageDraw.Draw(frame_img)

    for fila in range(high):
        y_texto = offset_y + fila * celda_h
        linea_ascii = lineas_centradas[fila]
        draw.text((offset_x, y_texto), linea_ascii, font=fuente, fill=(255, 255, 255))

    # Guardamos frame en el vídeo
    frame_np = np.array(frame_img)
    if usar_cv2:
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)
    else:
        writer.append_data(frame_np)

    barra.update(frame_idx + 1)

    # 7. Aumentar A y B un poquito
    A += incremento_A
    B += incremento_B

if usar_cv2:
    writer.release()
else:
    writer.close()
barra.finish()
print(f"Video exportado correctamente: {salida_mp4}")