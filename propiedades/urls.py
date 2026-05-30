from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_inmuebles, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('propiedades/agregar/', views.agregar_propiedad, name='agregar_propiedad'),
    path('propiedades/editar/<int:propiedad_id>/', views.editar_propiedad, name='editar_propiedad'),
    path('propiedades/favorito/<int:propiedad_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('conversaciones/', views.mis_conversaciones, name='mis_conversaciones'),
    path('conversaciones/iniciar/<int:propiedad_id>/', views.iniciar_conversacion, name='iniciar_conversacion'),
    path('conversaciones/<int:conv_id>/', views.conversacion_detalle, name='conversacion_detalle'),
    path('conversaciones/<int:conv_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('conversaciones/<int:conv_id>/estado/', views.cambiar_estado, name='cambiar_estado'),
]