from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.shortcuts import redirect, render

from . import api_client
from .api_client import ApiError


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
        try:
            data = api_client.login(
                request.POST.get("email", "").strip(),
                request.POST.get("password", ""),
            )
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            request.session["token"] = data["access_token"]   # JWT en la sesión
            request.session["usuario"] = data["usuario"]
            messages.success(request, f"Bienvenido, {data['usuario']['nombre']}")
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
    messages.info(request, "Sesión cerrada")
    return redirect("catalogo")
