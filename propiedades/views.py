from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.contrib import messages
from .models import Inmuebles, Usuarios, Roles, Favoritos, HistorialBusqueda, Conversacion, Mensaje
from .decorators import login_required, role_required

# --- Roles del sistema ---
ROLES_ADMIN = ('SuperAdmin', 'Admin')
ROLES_CLIENTE = ('Cliente',)

def _es_admin(usuario):
    return usuario.is_authenticated and usuario.rol and usuario.rol.nombre in ROLES_ADMIN

def lista_inmuebles(request):
    query = request.GET.get('q')
    propiedades = Inmuebles.objects.all()

    if query:
        propiedades = propiedades.filter(
            Q(titulo__icontains=query) |
            Q(ubicacion_especifica__icontains=query)
        )
        # Guardar historial si el usuario está autenticado
        if request.user.is_authenticated:
            HistorialBusqueda.objects.create(usuario=request.user, query=query)

    favoritos_ids = []
    if request.user.is_authenticated:
        favoritos_ids = list(
            Favoritos.objects.filter(usuario=request.user).values_list('inmueble_id', flat=True)
        )

    return render(request, 'propiedades/index.html', {
        'propiedades': propiedades,
        'favoritos_ids': favoritos_ids,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        return render(request, 'propiedades/login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'propiedades/login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'propiedades/register.html', {'error': 'Las contraseñas no coinciden'})

        if Usuarios.objects.filter(email=email).exists():
            return render(request, 'propiedades/register.html', {'error': 'El email ya está registrado'})

        rol_cliente, _ = Roles.objects.get_or_create(nombre='Cliente')
        user = Usuarios(
            nombre=nombre,
            email=email,
            rol=rol_cliente,
        )
        user.set_password(password)
        user.save()

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
        return redirect('index')

    return render(request, 'propiedades/register.html')

@login_required
def dashboard(request):
    user = request.user
    rol = user.rol.nombre if user.rol else 'Sin rol'

    if _es_admin(user):
        propiedades = Inmuebles.objects.all()
    else:
        propiedades = Inmuebles.objects.filter(propietario=user)

    total = propiedades.count()
    en_venta = propiedades.filter(tipo_negocio='Venta').count()
    en_arriendo = propiedades.filter(tipo_negocio='Arriendo').count()

    context = {
        'user': user,
        'rol': rol,
        'propiedades': propiedades,
        'total': total,
        'en_venta': en_venta,
        'en_arriendo': en_arriendo,
    }

    # --- Secciones extras para clientes ---
    if not _es_admin(user):
        context['favoritos'] = Favoritos.objects.filter(usuario=user).select_related('inmueble')
        context['busquedas'] = HistorialBusqueda.objects.filter(usuario=user).order_by('-creado')[:10]

    # --- Conversaciones ---
    if _es_admin(user):
        context['conversaciones'] = Conversacion.objects.filter(
            Q(asesor=user) | Q(inmueble__propietario=user)
        ).distinct()[:5]
    else:
        context['conversaciones'] = Conversacion.objects.filter(cliente=user)[:5]

    return render(request, 'propiedades/dashboard.html', context)

@login_required
def agregar_propiedad(request):
    if _es_admin(request.user):
        messages.error(request, 'Los administradores usan el panel de Django para crear propiedades.')
        return redirect('dashboard')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        ubicacion = request.POST.get('ubicacion_especifica')
        valor = request.POST.get('valor_inmueble')
        tipo_negocio = request.POST.get('tipo_negocio')
        zona = request.POST.get('zona')
        imagen = request.FILES.get('imagen')

        if not titulo or not valor:
            return render(request, 'propiedades/propiedad_form.html', {
                'error': 'Título y valor son obligatorios',
                'editando': False,
            })

        Inmuebles.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            ubicacion_especifica=ubicacion,
            valor_inmueble=valor,
            tipo_negocio=tipo_negocio,
            zona=zona,
            imagen=imagen,
            propietario=request.user,
        )
        messages.success(request, 'Propiedad publicada exitosamente.')
        return redirect('dashboard')

    return render(request, 'propiedades/propiedad_form.html', {'editando': False})

@login_required
def editar_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Inmuebles, id=propiedad_id)

    if not _es_admin(request.user) and propiedad.propietario != request.user:
        messages.error(request, 'No tienes permiso para editar esta propiedad.')
        return redirect('dashboard')

    if request.method == 'POST':
        propiedad.titulo = request.POST.get('titulo')
        propiedad.descripcion = request.POST.get('descripcion')
        propiedad.ubicacion_especifica = request.POST.get('ubicacion_especifica')
        propiedad.valor_inmueble = request.POST.get('valor_inmueble')
        propiedad.tipo_negocio = request.POST.get('tipo_negocio')
        propiedad.zona = request.POST.get('zona')
        if request.FILES.get('imagen'):
            propiedad.imagen = request.FILES['imagen']
        propiedad.save()
        messages.success(request, 'Propiedad actualizada.')
        return redirect('dashboard')

    return render(request, 'propiedades/propiedad_form.html', {
        'propiedad': propiedad,
        'editando': True,
    })

@login_required
def toggle_favorito(request, propiedad_id):
    propiedad = get_object_or_404(Inmuebles, id=propiedad_id)
    fav, created = Favoritos.objects.get_or_create(
        usuario=request.user, inmueble=propiedad
    )
    if not created:
        fav.delete()
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# ============================================================
# CONVERSACIONES
# ============================================================

@login_required
def iniciar_conversacion(request, propiedad_id):
    propiedad = get_object_or_404(Inmuebles, id=propiedad_id)
    user = request.user

    # Ver si ya existe una conversación abierta para este cliente + propiedad
    conversacion = Conversacion.objects.filter(
        inmueble=propiedad, cliente=user
    ).exclude(estado='cerrado').first()

    if not conversacion:
        # Asignar asesor: el propietario si es admin, o cualquier admin disponible
        asesor = None
        if propiedad.propietario and _es_admin(propiedad.propietario):
            asesor = propiedad.propietario
        if not asesor:
            asesor = Usuarios.objects.filter(
                rol__nombre__in=ROLES_ADMIN
            ).first()

        conversacion = Conversacion.objects.create(
            inmueble=propiedad,
            cliente=user,
            asesor=asesor,
        )

        es_visita = request.GET.get('visita') == '1'
        if es_visita:
            mensaje = f"Hola, me gustaría agendar una visita para ver {propiedad.titulo} en {propiedad.ubicacion_especifica or 'Tocancipá'}. ¿Cuándo podríamos coordinar?"
        else:
            mensaje = f"Hola, estoy interesado en {propiedad.titulo}. Me gustaría recibir más información."

        Mensaje.objects.create(
            conversacion=conversacion,
            remitente=user,
            contenido=mensaje,
        )

    return redirect('conversacion_detalle', conv_id=conversacion.id)

@login_required
def mis_conversaciones(request):
    user = request.user
    if _es_admin(user):
        conversaciones = Conversacion.objects.filter(
            Q(asesor=user) | Q(inmueble__propietario=user)
        ).distinct() if not user.rol or user.rol.nombre == 'SuperAdmin' else \
            Conversacion.objects.filter(asesor=user)
    else:
        conversaciones = Conversacion.objects.filter(cliente=user)

    return render(request, 'propiedades/conversaciones.html', {
        'conversaciones': conversaciones,
    })

@login_required
def conversacion_detalle(request, conv_id):
    conversacion = get_object_or_404(Conversacion, id=conv_id)
    user = request.user

    # Permisos
    puede_ver = (
        conversacion.cliente == user or
        conversacion.asesor == user or
        _es_admin(user)
    )
    if not puede_ver:
        messages.error(request, 'No tienes acceso a esta conversación.')
        return redirect('mis_conversaciones')

    # Marcar mensajes como leídos si el usuario no es el remitente
    Mensaje.objects.filter(conversacion=conversacion, leido=False).exclude(remitente=user).update(leido=True)

    return render(request, 'propiedades/conversacion_detalle.html', {
        'conversacion': conversacion,
    })

@login_required
def enviar_mensaje(request, conv_id):
    conversacion = get_object_or_404(Conversacion, id=conv_id)
    user = request.user

    puede_escribir = (
        conversacion.cliente == user or
        conversacion.asesor == user or
        _es_admin(user)
    )
    if not puede_escribir:
        messages.error(request, 'No puedes enviar mensajes aquí.')
        return redirect('mis_conversaciones')

    if request.method == 'POST':
        contenido = request.POST.get('contenido', '').strip()
        archivo = request.FILES.get('archivo')

        if contenido or archivo:
            Mensaje.objects.create(
                conversacion=conversacion,
                remitente=user,
                contenido=contenido or '(Archivo adjunto)',
                archivo=archivo,
            )
            conversacion.actualizado = None
            conversacion.save()

    return redirect('conversacion_detalle', conv_id=conv_id)

@login_required
def cambiar_estado(request, conv_id):
    conversacion = get_object_or_404(Conversacion, id=conv_id)
    if not _es_admin(request.user):
        messages.error(request, 'Solo los administradores pueden cambiar el estado.')
        return redirect('conversacion_detalle', conv_id=conv_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Conversacion.ESTADOS):
            conversacion.estado = nuevo_estado
            conversacion.save()
            messages.success(request, f'Estado cambiado a {conversacion.get_estado_display()}.')

    return redirect('conversacion_detalle', conv_id=conv_id)