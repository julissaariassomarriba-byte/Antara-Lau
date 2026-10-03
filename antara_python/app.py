"""
Antara - Taller de Pulseras
Servidor Flask. La interfaz está en templates/ y los estilos en static/.
"""
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

from models import db, Usuario, Taller, crear_usuario, validar_usuario

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

database_url = os.environ.get("DATABASE_URL", "sqlite:///antara.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura

def usuario_actual():
    return db.session.get(Usuario, session["usuario_id"])

def taller_actual():
    return Taller(usuario_actual())

@app.route("/")
def index():
    return redirect(url_for("compras") if "usuario_id" in session else url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        invite = request.form.get("codigo", "").strip()
        expected = os.environ.get("INVITE_CODE", "")
        if not expected or invite != expected:
            error = "El código de acceso no es válido."
        else:
            usuario = request.form.get("usuario", "").strip()
            password = request.form.get("password", "")
            if len(usuario) < 3 or len(usuario) > 50:
                error = "El usuario debe tener entre 3 y 50 caracteres."
            elif len(password) < 6:
                error = "La contraseña debe tener al menos 6 caracteres."
            else:
                ok, msg = crear_usuario(usuario, password)
                if ok:
                    flash("Cuenta creada. Ahora inicia sesión.")
                    return redirect(url_for("login"))
                error = msg
    return render_template("signup.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        ok, resultado = validar_usuario(usuario, password)
        if ok:
            session.clear()
            session["usuario_id"] = resultado.id
            session["usuario"] = resultado.username
            return redirect(url_for("compras"))
        error = resultado
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/compras", methods=["GET", "POST"])
@login_requerido
def compras():
    taller = taller_actual()
    mensaje = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        color = request.form.get("color", "#2FA89C")
        try:
            por = int(request.form.get("por_ristra", 0))
            cant = int(request.form.get("cant_ristras", 0))
        except (TypeError, ValueError):
            por = cant = 0
        if nombre and por > 0 and cant > 0:
            taller.registrar_compra(nombre, color, por, cant)
            mensaje = f"¡Compra registrada! +{por * cant} pelotitas de {nombre}."
        else:
            mensaje = "Completa los campos con valores mayores que cero."
    historial = [
        {"tipo": c.tipo.nombre, "por": c.pelotitas_por_ristra,
         "cant": c.cantidad_ristras,
         "total": c.pelotitas_por_ristra * c.cantidad_ristras,
         "fecha": c.fecha}
        for c in taller.compras
    ]
    return render_template("compras.html", usuario=session["usuario"],
                           mensaje=mensaje, historial=historial)

@app.route("/pulsera", methods=["GET", "POST"])
@login_requerido
def pulsera():
    taller = taller_actual()
    mensaje = None
    if request.method == "POST":
        accion = request.form.get("accion")
        if accion == "agregar_extra":
            nombre = request.form.get("extra_nombre", "").strip()
            try:
                cant = int(request.form.get("extra_cantidad", 0))
            except (TypeError, ValueError):
                cant = 0
            if nombre and cant > 0:
                taller.registrar_extra(nombre, cant)
                mensaje = "Extra agregado al inventario."
            else:
                mensaje = "Completa nombre y cantidad del extra."
        elif accion == "crear_pulsera":
            nombre = request.form.get("nombre_pulsera", "").strip()
            extra_id = request.form.get("extra_id") or None
            tipo_ids = request.form.getlist("tipo_id")
            cantidades = request.form.getlist("cantidad_uso")
            componentes = []
            for tid, cantidad in zip(tipo_ids, cantidades):
                if tid and cantidad:
                    componentes.append({"tipo_id": tid, "cantidad": cantidad})
            if not componentes:
                mensaje = "Agrega al menos una pelotita a la pulsera."
            else:
                ok, err = taller.crear_pulsera(nombre, componentes, extra_id)
                mensaje = "¡Pulsera guardada!" if ok else err

    pulseras_vista = []
    for p in taller.pulseras:
        comps = ", ".join(f"{c.tipo.nombre} ×{c.cantidad}" for c in p.componentes)
        pulseras_vista.append({
            "nombre": p.nombre, "comps": comps,
            "extra": p.extra.nombre if p.extra else "—",
            "fecha": p.fecha
        })
    return render_template("pulsera.html", usuario=session["usuario"],
                           mensaje=mensaje, pelotitas=taller.pelotitas,
                           extras=taller.extras, pulseras=pulseras_vista)

@app.route("/inventario")
@login_requerido
def inventario():
    taller = taller_actual()
    return render_template(
        "inventario.html", usuario=session["usuario"],
        pelotitas=taller.pelotitas, extras=taller.extras,
        total_compras=len(taller.compras), total_pulseras=len(taller.pulseras)
    )

@app.get("/health")
def health():
    return {"status": "ok", "app": "Antara"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
