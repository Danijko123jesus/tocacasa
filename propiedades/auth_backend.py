from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password
from .models import Usuarios

class UsuariosAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = Usuarios.objects.get(email=username)
        except Usuarios.DoesNotExist:
            return None

        # 1. Intentar con password hasheado (nuevo formato)
        if check_password(password, user.password):
            return user

        # 2. Compatibilidad con passwords en texto plano (legado)
        if user.password == password:
            user.set_password(password)
            user.save(update_fields=['password'])
            return user

        return None

    def get_user(self, user_id):
        try:
            return Usuarios.objects.get(pk=user_id)
        except Usuarios.DoesNotExist:
            return None
