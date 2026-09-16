# gobu

Wrapper en Python de `gobuster` + `curl` para automatizar reconocimiento web básico
(dir busting con dos wordlists, vhost busting, headers, redirects, robots.txt y
título de la página). Guarda todo en `gobuster.txt` y `curl.txt` en el directorio
donde lo corras.

## Requisitos

- Python 3
- [`gobuster`](https://github.com/OJ/gobuster) instalado y en el PATH
- `curl` instalado y en el PATH
- Wordlists (por defecto usa las que trae Kali):
  - `/usr/share/wordlists/dirb/common.txt`
  - `/usr/share/seclists/Discovery/Web-Content/common.txt`

Si alguna wordlist no existe, ese paso se saltea con un aviso en vez de romper
todo el script.

## Instalación

```bash
git clone <url-de-tu-repo>.git
cd gobu
sudo ./install.sh
```

Esto copia `gobu.py` a `/usr/local/bin/gobu` y lo deja como comando global,
igual que `nmap` o `gobuster`.

## Uso

```bash
gobu <ip>
gobu <dominio>
gobu <ip> <dominio>
```

Ejemplos:

```bash
gobu 10.10.10.10
gobu ejemplo.com
gobu 10.10.10.10 ejemplo.com
```

Los resultados se van agregando (append) a `gobuster.txt` y `curl.txt` en el
directorio actual, así podés acumular corridas de distintos objetivos o
distintos días.

## Desinstalar

```bash
sudo ./uninstall.sh
```

## Actualizar

Si ya lo tenés clonado y sacan una versión nueva:

```bash
git pull
sudo ./install.sh
```

## Aviso

Esta herramienta hace requests activos contra el objetivo (dir busting,
vhost busting, etc). Usala solo contra sistemas para los que tenés
autorización explícita.
