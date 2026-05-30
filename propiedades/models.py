from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal

class Roles(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'roles'
    
    def __str__(self):
        return self.nombre

class Usuarios(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    rol = models.ForeignKey(Roles, models.DO_NOTHING, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'usuarios'
    
    def __str__(self):
        return self.nombre

    # --- Compatibilidad con Django Auth ---
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_staff(self):
        return self.rol is not None and self.rol.nombre in ('SuperAdmin', 'Admin')

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_perms(self, perm_list, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def get_all_permissions(self, obj=None):
        return set()

    def get_group_permissions(self, obj=None):
        return set()

    def get_user_permissions(self, obj=None):
        return set()

    def get_username(self):
        return self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

class Inmuebles(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, null=True)
    ubicacion_especifica = models.CharField(max_length=255, blank=True, null=True)
    
    valor_inmueble = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    tipo_negocio = models.CharField(
        max_length=20, 
        choices=[('Venta', 'Venta'), ('Arriendo', 'Arriendo')],
        default='Venta'
    )
    
    zona = models.CharField(
        max_length=20, 
        choices=[('Urbana', 'Urbana'), ('Rural', 'Rural')],
        default='Urbana'
    )
    
    imagen = models.ImageField(upload_to='propiedades/', blank=True, null=True)
    propietario = models.ForeignKey(Usuarios, models.SET_NULL, blank=True, null=True, db_constraint=False, verbose_name="Propietario")

    class Meta:
        managed = True
        db_table = 'propiedades_inmuebles'

    def calcular_comision(self):
        if not self.valor_inmueble:
            return Decimal('0.00')

        if self.tipo_negocio == 'Arriendo':
            return self.valor_inmueble * Decimal('0.10')
        
        porcentaje = Decimal('0.10') if self.zona == 'Rural' else Decimal('0.03')
        return self.valor_inmueble * porcentaje

    def total_con_comision(self):
        return self.valor_inmueble + self.calcular_comision()

    def __str__(self):
        return f"{self.titulo} ({self.tipo_negocio})"

class Favoritos(models.Model):
    usuario = models.ForeignKey(Usuarios, models.CASCADE, related_name='favoritos', db_constraint=False)
    inmueble = models.ForeignKey(Inmuebles, models.CASCADE, related_name='favs', db_constraint=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'favoritos'
        unique_together = ('usuario', 'inmueble')

    def __str__(self):
        return f"{self.usuario.nombre} -> {self.inmueble.titulo}"

class HistorialBusqueda(models.Model):
    usuario = models.ForeignKey(Usuarios, models.CASCADE, related_name='busquedas', db_constraint=False)
    query = models.CharField(max_length=200)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'historial_busquedas'
        verbose_name_plural = 'Historial de búsquedas'

    def __str__(self):
        return f"{self.usuario.nombre}: {self.query}"

class Comisiones(models.Model):
    inmueble = models.ForeignKey(Inmuebles, models.DO_NOTHING, blank=True, null=True)
    monto_pagado = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    tipo_pago = models.CharField(max_length=50, blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'comisiones'

    def __str__(self):
        return f"Pago {self.tipo_pago} - {self.monto_pagado}"

class Conversacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('negociacion', 'En Negociación'),
        ('cerrado', 'Cerrado'),
    ]
    inmueble = models.ForeignKey(Inmuebles, models.CASCADE, db_constraint=False)
    cliente = models.ForeignKey(Usuarios, models.CASCADE, related_name='conversaciones_cliente', db_constraint=False)
    asesor = models.ForeignKey(Usuarios, models.SET_NULL, blank=True, null=True, related_name='conversaciones_asesor', db_constraint=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'conversaciones'
        ordering = ['-actualizado']

    def __str__(self):
        return f"{self.cliente.nombre} - {self.inmueble.titulo} ({self.estado})"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, models.CASCADE, related_name='mensajes', db_constraint=False)
    remitente = models.ForeignKey(Usuarios, models.CASCADE, db_constraint=False)
    contenido = models.TextField()
    archivo = models.FileField(upload_to='mensajes/', blank=True, null=True)
    leido = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'mensajes'
        ordering = ['creado']

    def __str__(self):
        return f"{self.remitente.nombre}: {self.contenido[:50]}"