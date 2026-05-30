from django.contrib import admin
from .models import Roles, Usuarios, Inmuebles, Comisiones, Favoritos, HistorialBusqueda, Conversacion, Mensaje
from django.utils.html import format_html

# 1. Registro sencillo para Roles
@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

# 2. Registro para Usuarios (Tus usuarios personalizados)
@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'rol', 'fecha_registro')
    list_filter = ('rol',)
    search_fields = ('nombre', 'email')
    readonly_fields = ('fecha_registro',) # Evita que se edite la fecha manualmente

# 3. Registro para Inmuebles (Con las funciones de cálculo + vista previa)
@admin.register(Inmuebles)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ('mostrar_foto', 'titulo', 'valor_inmueble', 'tipo_negocio', 'zona', 'propietario', 'comision_estimada')
    list_filter = ('tipo_negocio', 'zona')
    search_fields = ('titulo', 'ubicacion_especifica')
    
    def comision_estimada(self, obj):
        return f"${obj.calcular_comision():,.2f}"
    comision_estimada.short_description = 'Comisión Calculada'

    def mostrar_foto(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 5px;" />', obj.imagen.url)
        return "Sin foto"
    mostrar_foto.short_description = 'Vista Previa'

# 4. Registro para Comisiones
@admin.register(Comisiones)
class ComisionesAdmin(admin.ModelAdmin):
    list_display = ('inmueble', 'monto_pagado', 'tipo_pago', 'fecha_pago')
    list_filter = ('tipo_pago',)

@admin.register(Favoritos)
class FavoritosAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'inmueble', 'creado')
    list_filter = ('creado',)

@admin.register(HistorialBusqueda)
class HistorialBusquedaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'query', 'creado')
    list_filter = ('creado',)

@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('inmueble', 'cliente', 'asesor', 'estado', 'actualizado')
    list_filter = ('estado',)

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('conversacion', 'remitente', 'creado', 'leido')
    list_filter = ('leido',)


    