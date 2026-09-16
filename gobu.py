#!/usr/bin/env python3
import sys
import re
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

"""
Uso:
    gobu <ip>
    gobu <dominio>
    gobu <ip> <dominio>
"""

WORDLIST_DIRB = "/usr/share/wordlists/dirb/common.txt"
WORDLIST_SECLISTS = "/usr/share/seclists/Discovery/Web-Content/common.txt"


# ---------- utilidades ----------

def es_ip(valor):
    """Detecta si el string tiene forma de IPv4 (no valida rangos, solo formato)."""
    patron = r"^(\d{1,3}\.){3}\d{1,3}$"
    return re.match(patron, valor) is not None


def normalizar_url(objetivo):
    """Gobuster y curl necesitan el esquema (http/https), si no viene, se lo agregamos."""
    if not objetivo.startswith("http://") and not objetivo.startswith("https://"):
        return f"http://{objetivo}"
    return objetivo


def verificar_dependencias():
    """Chequea que gobuster y curl estén instalados antes de arrancar."""
    faltantes = [bin_ for bin_ in ("gobuster", "curl") if shutil.which(bin_) is None]
    if faltantes:
        print(f"[!] Faltan binarios en el PATH: {', '.join(faltantes)}")
        print("    Instalalos antes de correr gobu (ver README del repo).")
        sys.exit(1)


def ejecutar_comando(comando, mostrar_en_vivo=True):
    """
    Corre un comando (lista de strings) y devuelve stdout+stderr combinados.
    Si mostrar_en_vivo=True, va imprimiendo cada línea a medida que el
    proceso la genera (en vez de quedarse "colgado" en silencio), y al
    final muestra cuánto tardó.
    """
    if mostrar_en_vivo:
        print(f"[*] Ejecutando: {' '.join(comando)}")

    inicio = time.time()
    proceso = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    lineas = []
    for linea in proceso.stdout:
        lineas.append(linea)
        if mostrar_en_vivo:
            print(linea, end="", flush=True)

    proceso.wait()
    duracion = time.time() - inicio

    if mostrar_en_vivo:
        print(f"[+] Listo ({duracion:.1f}s)\n")

    return "".join(lineas)


def detectar_longitud_wildcard(salida):
    """
    Gobuster, cuando detecta que el servidor responde 200 a rutas random
    (falsos positivos), imprime algo como:
    [!] Wildcard response found: http://target/asdasd => 200 (Length: 178)
    Acá extraemos ese numero de longitud para poder excluirlo despues.
    """
    match = re.search(r"Length:\s*(\d+)", salida)
    return match.group(1) if match else None


# ---------- comandos gobuster ----------

def gobuster_dir(objetivo, wordlist, threads=None):
    if not Path(wordlist).is_file():
        return f"[!] Wordlist no encontrada, se saltea este paso: {wordlist}\n"

    url = normalizar_url(objetivo)
    comando = ["gobuster", "dir", "-u", url, "-w", wordlist]
    if threads:
        comando += ["-t", str(threads)]

    salida = ejecutar_comando(comando)
    bloque = f"$ {' '.join(comando)}\n{salida}\n"

    # si hubo wildcard response, reintentamos excluyendo esa longitud
    if "Wildcard response found" in salida:
        longitud = detectar_longitud_wildcard(salida)
        if longitud:
            comando_filtrado = comando + ["--exclude-length", longitud]
            salida_filtrada = ejecutar_comando(comando_filtrado)
            bloque += (
                f"\n[!] Wildcard detectado (Length: {longitud}), "
                f"reintentando con --exclude-length\n"
            )
            bloque += f"$ {' '.join(comando_filtrado)}\n{salida_filtrada}\n"

    return bloque


def gobuster_vhost(objetivo, wordlist=WORDLIST_DIRB):
    if not Path(wordlist).is_file():
        return f"[!] Wordlist no encontrada, se saltea este paso: {wordlist}\n"

    url = normalizar_url(objetivo)
    comando = ["gobuster", "vhost", "-u", url, "-w", wordlist]
    salida = ejecutar_comando(comando)
    return f"$ {' '.join(comando)}\n{salida}\n"


# ---------- comandos curl ----------

def curl_headers(objetivo):
    url = normalizar_url(objetivo)
    comando = ["curl", "-I", "-s", url]
    salida = ejecutar_comando(comando)
    return f"$ {' '.join(comando)}\n{salida}\n"


def curl_siguiendo_redirect(objetivo):
    url = normalizar_url(objetivo)
    comando = ["curl", "-I", "-s", "-L", url]
    salida = ejecutar_comando(comando)
    return f"$ {' '.join(comando)}\n{salida}\n"


def curl_robots(objetivo):
    url = normalizar_url(objetivo).rstrip("/") + "/robots.txt"
    comando = ["curl", "-s", url]
    salida = ejecutar_comando(comando)
    return f"$ {' '.join(comando)}\n{salida}\n"


def curl_titulo_pagina(objetivo):
    """Trae el html y busca el <title> para identificar rápido de qué se trata el sitio."""
    url = normalizar_url(objetivo)
    comando = ["curl", "-s", url]
    # acá no mostramos en vivo: es todo el HTML crudo, no aporta nada verlo pasar
    salida = ejecutar_comando(comando, mostrar_en_vivo=False)
    match = re.search(r"<title>(.*?)</title>", salida, re.IGNORECASE | re.DOTALL)
    titulo = match.group(1).strip() if match else "(no encontrado)"
    print(f"[*] {' '.join(comando)}  |  <title> encontrado: {titulo}\n")
    return f"$ {' '.join(comando)}  |  <title> encontrado: {titulo}\n"


# ---------- orquestacion por objetivo ----------

def escanear_objetivo(objetivo):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    encabezado = f"===== Objetivo: {objetivo} — {ts} =====\n"
    print(f"\n{encabezado}")

    pasos_totales = 7
    paso_actual = 0

    def marcar_paso(titulo):
        nonlocal paso_actual
        paso_actual += 1
        print(f"\n[{paso_actual}/{pasos_totales}] {titulo}")

    salida_gobuster = encabezado

    marcar_paso("gobuster dir (wordlist dirb)")
    salida_gobuster += "\n--- gobuster dir (wordlist dirb) ---\n"
    salida_gobuster += gobuster_dir(objetivo, WORDLIST_DIRB)

    marcar_paso("gobuster dir (wordlist seclists, 50 threads)")
    salida_gobuster += "\n--- gobuster dir (wordlist seclists, 50 threads) ---\n"
    salida_gobuster += gobuster_dir(objetivo, WORDLIST_SECLISTS, threads=50)

    marcar_paso("gobuster vhost")
    salida_gobuster += "\n--- gobuster vhost ---\n"
    salida_gobuster += gobuster_vhost(objetivo)

    salida_curl = encabezado

    marcar_paso("curl -I (headers)")
    salida_curl += "\n--- curl -I (headers) ---\n"
    salida_curl += curl_headers(objetivo)

    marcar_paso("curl -I -L (siguiendo redirects)")
    salida_curl += "\n--- curl -I -L (siguiendo redirects) ---\n"
    salida_curl += curl_siguiendo_redirect(objetivo)

    marcar_paso("curl robots.txt")
    salida_curl += "\n--- curl robots.txt ---\n"
    salida_curl += curl_robots(objetivo)

    marcar_paso("curl titulo de la pagina")
    salida_curl += "\n--- curl titulo de la pagina ---\n"
    salida_curl += curl_titulo_pagina(objetivo)

    return salida_gobuster, salida_curl


def determinar_archivos_salida(ip, domain):
    """
    Decide en qué archivos escribir los resultados de esta corrida.

    Si ya existe una corrida previa con exactamente esta misma combinación
    de ip/dominio (detectado por una marca interna guardada en el archivo),
    no la pisa ni sigue amontonando ahí: busca el siguiente archivo libre
    (gobuster2.txt/curl2.txt, gobuster3.txt/curl3.txt, ...).

    Si es la primera vez que se corre esta combinación, usa/crea el
    archivo base (gobuster.txt/curl.txt), acumulando como antes.
    """
    marcador = f"# RUN_KEY: ip={ip} dominio={domain}"
    numero = 1

    while True:
        sufijo = "" if numero == 1 else str(numero)
        ruta_gobuster = Path.cwd() / f"gobuster{sufijo}.txt"
        ruta_curl = Path.cwd() / f"curl{sufijo}.txt"

        if not ruta_gobuster.exists():
            return ruta_gobuster, ruta_curl, marcador

        contenido_previo = ruta_gobuster.read_text(encoding="utf-8", errors="ignore")
        if marcador not in contenido_previo:
            return ruta_gobuster, ruta_curl, marcador

        numero += 1


def scaning(ip=None, domain=None):
    objetivos = [valor for valor in (ip, domain) if valor]
    if not objetivos:
        raise ValueError("Tenes que pasar al menos una IP o un dominio")

    resultado_gobuster_total = ""
    resultado_curl_total = ""

    for objetivo in objetivos:
        g, c = escanear_objetivo(objetivo)
        resultado_gobuster_total += g + "\n"
        resultado_curl_total += c + "\n"

    return resultado_gobuster_total, resultado_curl_total


# ---------- entrada del programa ----------

def main():
    if len(sys.argv) < 2:
        print("Uso: gobu <ip> [dominio]  (el orden no importa)")
        sys.exit(1)

    verificar_dependencias()

    ip = None
    domain = None

    for arg in sys.argv[1:]:
        if es_ip(arg):
            ip = arg
        else:
            domain = arg

    ruta_gobuster, ruta_curl, marcador = determinar_archivos_salida(ip, domain)

    inicio_total = time.time()
    resultado_gobuster, resultado_curl = scaning(ip=ip, domain=domain)
    duracion_total = time.time() - inicio_total

    # la marca va al principio del bloque para poder detectar reruns de este
    # mismo objetivo la próxima vez que se corra gobu
    resultado_gobuster = f"{marcador}\n" + resultado_gobuster
    resultado_curl = f"{marcador}\n" + resultado_curl

    # "a" = append, para ir acumulando resultados de distintas corridas
    with ruta_gobuster.open("a", encoding="utf-8") as f:
        f.write(resultado_gobuster)

    with ruta_curl.open("a", encoding="utf-8") as f:
        f.write(resultado_curl)

    print(f"\n[+] Escaneo completo en {duracion_total:.1f}s")
    print(f"Resultados guardados en:\n  {ruta_gobuster}\n  {ruta_curl}")


if __name__ == "__main__":
    main()
