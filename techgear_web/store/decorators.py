from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para comprar")
            return redirect(f"{reverse('login')}?next={request.path}")
        if usuario.get("rol") != "administrador":
            messages.error(request, "No tienes permisos de administrador")
            return redirect("catalogo")
        return view(request, *args, **kwargs)
    return wrapper

def cliente_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para comprar")
            return redirect("login")
        if usuario.get("rol") == "administrador":
            messages.info(request, "Las cuentas de administrador no realizan compras")
            return redirect("panel_admin")
        return view(request, *args, **kwargs)
    return wrapper