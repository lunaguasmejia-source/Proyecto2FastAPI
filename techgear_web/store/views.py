from datetime import datetime, timezone
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
# Create your views here.
from django.contrib import messages
from django.shortcuts import redirect, render

from . import api_client
from .api_client import ApiError
from .decorators import admin_required,  cliente_required


def catalogo(request):
    categoria = request.GET.get("categoria") or None
    try:
        productos = api_client.listar_productos(categoria)
    except ApiError as e:
        messages.error(request, e.detail)
        productos = []
    return render(request, "catalogo.html",
                  {"productos": productos, "categoria": categoria or ""})


def login_view(request):
    if request.session.get("token"):
        return redirect("catalogo")
    if request.method == "POST":
        rol_elegido = request.POST.get("rol", "cliente")
        try:
            data = api_client.login(
                request.POST.get("email", "").strip(),
                request.POST.get("password", ""),
            )
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            rol_real = data["usuario"]["rol"]
            if rol_elegido != rol_real:
                if rol_elegido == "administrador":
                    messages.error(request, "Esta cuenta no tiene permisos de administrador")
                else:
                    messages.error(request, "Esta cuenta es de administrador: elige 'Administrador' para entrar")
            else:
                request.session["token"] = data["access_token"]
                request.session["usuario"] = data["usuario"]
                if rol_real == "administrador":
                    return redirect("panel_admin")
                destino = request.GET.get("next", "")
                if destino and url_has_allowed_host_and_scheme(
                    destino, allowed_hosts={request.get_host()}
                ):
                    return redirect(destino)
                return redirect("catalogo")
    return render(request, "login.html")

def registro_view(request):
    if request.method == "POST":
        try:
            api_client.registro(
                request.POST.get("nombre", "").strip(),
                request.POST.get("email", "").strip(),
                request.POST.get("password", ""),
            )
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect("login")
    return render(request, "registro.html")


def logout_view(request):
    request.session.flush()       # borra token y datos de la sesión
    return redirect("catalogo")

def _datos_producto(post):
    """Convierte el formulario en el JSON que espera la API."""
    return {
        "nombre": post.get("nombre", "").strip(),
        "descripcion": post.get("descripcion", "").strip(),
        "precio": float(post.get("precio", "0")),
        "stock": int(post.get("stock", "0")),
        "categoria": post.get("categoria", "").strip(),
        "imagen_url": post.get("imagen_url", "").strip() or None,
    }


@admin_required
def panel_admin(request):
    try:
        productos = api_client.listar_productos()
    except ApiError as e:
        messages.error(request, e.detail)
        productos = []
    return render(request, "panel_admin.html", {"productos": productos})


@admin_required
def producto_nuevo(request):
    producto = {}
    if request.method == "POST":
        producto = request.POST.dict()      # conserva lo escrito si hay error
        try:
            api_client.crear_producto(_datos_producto(request.POST))
        except ValueError:
            messages.error(request, "Precio y stock deben ser números")
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            messages.success(request, "Producto creado correctamente")
            return redirect("panel_admin")
    return render(request, "producto_form.html", {"producto": producto, "modo": "nuevo"})


@admin_required
def producto_editar(request, producto_id):
    try:
        producto = api_client.obtener_producto(producto_id)
    except ApiError as e:
        messages.error(request, e.detail)
        return redirect("panel_admin")

    if request.method == "POST":
        producto = {**producto, **request.POST.dict()}
        try:
            api_client.actualizar_producto(producto_id, _datos_producto(request.POST))
        except ValueError:
            messages.error(request, "Precio y stock deben ser números")
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            messages.success(request, "Producto actualizado")
            return redirect("panel_admin")
    return render(request, "producto_form.html", {"producto": producto, "modo": "editar"})


@admin_required
def producto_eliminar(request, producto_id):
    if request.method != "POST":            # solo se elimina con el botón (POST)
        return redirect("panel_admin")
    try:
        api_client.eliminar_producto(producto_id)
    except ApiError as e:
        messages.error(request, e.detail)
    else:
        messages.success(request, "Producto eliminado")
    return redirect("panel_admin")

def _sesion_expirada(request):
    request.session.flush()
    messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
    return redirect("login")


@cliente_required
def comprar(request, producto_id):
    try:
        producto = api_client.obtener_producto(producto_id)
    except ApiError as e:
        messages.error(request, e.detail)
        return redirect("catalogo")

    if request.method == "POST":
        try:
            cantidad = int(request.POST.get("cantidad", "1"))
            api_client.crear_pedido(
                request.session["token"],
                [{"producto_id": producto_id, "cantidad": cantidad}],
                request.POST.get("direccion", "").strip(),
            )
        except ValueError:
            messages.error(request, "La cantidad debe ser un número")
        except ApiError as e:
            if e.status == 401:
                return _sesion_expirada(request)
            messages.error(request, e.detail)
        else:
            messages.success(request, "¡Pedido realizado con éxito!")
            return redirect("mis_pedidos")
    return render(request, "comprar.html", {"producto": producto})


@cliente_required
def mis_pedidos(request):
    try:
        pedidos = api_client.mis_pedidos(request.session["token"])
    except ApiError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, e.detail)
        pedidos = []
    for p in pedidos:                      # texto ISO -> fecha real
        f = datetime.fromisoformat(p["fecha"].replace("Z", "+00:00"))
        p["fecha"] = f if f.tzinfo else f.replace(tzinfo=timezone.utc)
    return render(request, "mis_pedidos.html", {"pedidos": pedidos})