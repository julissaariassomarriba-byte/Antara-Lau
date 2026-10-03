# Antara · Taller de Pulseras

Aplicación para llevar el control del emprendimiento de pulseras de Antara:
compras de ristras, armado de pulseras (con pelotitas y un dije/extra opcional)
e inventario. El backend está escrito en Python (POO) y solo la interfaz
está en HTML.

## Estructura del proyecto

```
antara_python/
├── app.py                 # Rutas Flask (acceso, compras, pulsera, inventario)
├── models.py               # Clases: TipoPelotita, Extra, Compra, Pulsera,
│                            # Taller (inventario + lógica) y CuentaManager (acceso)
├── requirements.txt
├── data/                    # Se crea sola: usuarios.json + un taller_<usuario>.json por cuenta
├── static/
│   └── style.css
└── templates/               # Solo interfaz (HTML), sin lógica de negocio
    ├── base.html
    ├── login.html
    ├── signup.html
    ├── compras.html
    ├── pulsera.html
    └── inventario.html
```

## Cómo ejecutarlo

1. Instala Python 3.9 o superior.
2. Dentro de la carpeta del proyecto, instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```
   python app.py
   ```
4. Abre en el navegador: **http://localhost:5000**

La primera vez, Antara debe crear su cuenta (usuario y contraseña) desde
"Créala aquí" en la pantalla de inicio de sesión. Esa cuenta y sus datos
(pelotitas, extras, compras, pulseras) se guardan como archivos JSON dentro
de la carpeta `data/`.

## Cómo funciona (resumen)

- **CuentaManager** (en `models.py`) es la "clase de acceso": guarda usuarios
  y contraseñas (con hash) en `data/usuarios.json` y valida el inicio de sesión.
- **Taller** es el inventario de cada cuenta: sabe registrar compras de
  ristras, registrar dijes/extras, armar una pulsera (descontando del stock
  y validando que haya suficiente) y guardarse/cargarse de su propio archivo
  JSON en `data/taller_<usuario>.json`.
- `app.py` conecta esas clases con las rutas web; `templates/*.html` solo
  muestran los datos y formularios (no contienen lógica de negocio).

## Antes de compartirla

- Cambia el valor de `app.secret_key` en `app.py` por uno propio y secreto.
- `debug=True` es solo para pruebas locales; para producción usa
  `app.run(debug=False)` o un servidor como `waitress`/`gunicorn`.

## Si más adelante quieres una URL pública

Esta versión guarda los datos en archivos locales, así que corre en el
equipo donde la ejecutes. Si luego quieres que Antara la use desde su
celular con una URL propia, se puede desplegar en un servicio como
PythonAnywhere, Render o Railway sin cambiar la lógica de `models.py`.
