# Antara — servidor + APK

## Qué contiene

- `antara_python/`: servidor Flask de Antara.
- PostgreSQL en producción y SQLite si no se define `DATABASE_URL`.
- POO con `Taller`, `Usuario`, `TipoPelotita`, `Compra`, `Pulsera`, etc.
- Código de invitación mediante la variable privada `INVITE_CODE`.
- `render.yaml`: configuración para desplegar servidor + PostgreSQL.
- `AntaraAPK/`: proyecto Android WebView. El APK se conecta al servidor público.

## 1. Probar Antara en tu PC

En una terminal:

```powershell
cd antara_python
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:INVITE_CODE="ANTARA-2026"
$env:SECRET_KEY="cambia-esto-por-una-clave-larga"
python app.py
```

Abre:

`http://127.0.0.1:5000`

El archivo `antara.db` se crea automáticamente para la prueba local.

## 2. Publicar el servidor

La opción preparada en este proyecto es Render.

1. Sube la carpeta del proyecto a GitHub.
2. En Render crea un Blueprint y selecciona el repositorio.
3. Render leerá `render.yaml` y creará el servicio web y la base de datos.
4. Cuando pida `INVITE_CODE`, escribe el código privado que tú quieras entregar a tu amiga.
5. `SECRET_KEY` puede generarse automáticamente.
6. Espera a que el servicio termine de desplegarse.
7. Prueba `https://TU-SERVICIO.onrender.com/health`. Debe responder:
   `{"app":"Antara","status":"ok"}`

## 3. Preparar el APK

Abre la carpeta `AntaraAPK` en Android Studio.

Antes de compilar:

1. Abre:
   `app/src/main/res/values/strings.xml`
2. Cambia:
   `https://TU-URL-DE-ANTARA.onrender.com`
   por la URL real de Antara.
3. Pulsa Sync Project with Gradle Files.
4. Luego selecciona:
   Build > Build Bundle(s) / APK(s) > Build APK(s).

El APK de prueba quedará normalmente dentro de:

`AntaraAPK/app/build/outputs/apk/debug/`

## Importante

El APK es una aplicación Android que muestra la interfaz web de Antara. Los datos viven en el servidor y PostgreSQL, no en el APK.

No pongas `INVITE_CODE` ni `SECRET_KEY` dentro del APK. Deben quedarse como variables privadas del servidor.

Para distribuirla a otras personas, primero prueba el APK con tu propia cuenta y verifica que compras, inventario, pulseras y dijes se actualicen correctamente.
