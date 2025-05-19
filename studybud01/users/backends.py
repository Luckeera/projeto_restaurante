# /home/ubuntu/projeto_restaurante/studybud01/users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """Autentica usando email."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        # O parâmetro "username" aqui na verdade receberá o email do nosso formulário
        email = username 
        try:
            # Tenta encontrar um usuário com o email fornecido (case-insensitive)
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # Nenhum usuário encontrado com este email
            return None
        except UserModel.MultipleObjectsReturned:
            # Caso raro: mais de um usuário com o mesmo email (não deveria acontecer se a validação no registro estiver correta)
            # Retorna None para segurança, ou loga o erro
            return None 
        else:
            # Verifica a senha
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    def get_user(self, user_id):
        # Necessário para o funcionamento do backend
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
