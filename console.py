from math import cos,sin,pi
import time

scale = 1



wide = 80*scale
high = 24*scale
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
K1 = 30.0*scale # Escala para hacer el donut más grande en la pantalla

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

# Limpiar la terminal por completo antes de empezar la animación
print('\x1b[2J', end='')

while True: # Bucle infinito (cada ciclo es un frame)
    
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

    # 6. Imprimir el screen_buffer completo en la terminal
    # Movemos el cursor a la posición 0,0 de la terminal antes de dibujar
    print('\x1b[H', end="")

    # 6. Imprimir el screen_buffer completo en la terminal
    n = 0
    for _ in range(high): # Quitamos el len()
        for _ in range(wide): # Quitamos el len()
            print(screen_buffer[n], end="")
            n += 1
        print("") # Salto de línea al final de cada fila

    # 7. Aumentar A y B un poquito
    A += 0.04
    B += 0.02

    # 8. Pausa para estabilizar los FPS
    time.sleep(0.02)