from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.forms import EmailField
import uuid # Para gerar usernames únicos

class EmailAuthenticationForm(AuthenticationForm):
    """Formulário de autenticação que usa email em vez de username."""
    username = EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "autofocus": True, 
            "placeholder": "seu@email.com"
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajusta o placeholder do campo de senha
        if "password" in self.fields:
            self.fields["password"].widget = forms.PasswordInput(attrs={
                "placeholder": "Senha",
                # Mantém o atributo padrão para autocomplete
                "autocomplete": "current-password", 
            })


class SimplifiedUserCreationForm(UserCreationForm):
    # Mantém os campos extras do formulário anterior
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'placeholder': 'Seu e-mail'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Nome (opcional)'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Sobrenome (opcional)'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Define os campos que REALMENTE serão usados pelo formulário
        # Note que 'username' NÃO está aqui
        fields = ("email", "first_name", "last_name") 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o help_text dos campos de senha herdados
        if 'password2' in self.fields:
            self.fields['password2'].help_text = ''
        # O help_text do password1 já é removido por padrão no UserCreationForm moderno
        # Adiciona placeholders aos campos de senha para clareza
        if 'password1' in self.fields:
             self.fields['password1'].widget = forms.PasswordInput(attrs={'placeholder': 'Senha'}) 
        if 'password2' in self.fields:
             self.fields['password2'].widget = forms.PasswordInput(attrs={'placeholder': 'Confirme a senha'}) 

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Garante unicidade do e-mail (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outra conta.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False) # Cria o objeto User mas não salva no BD ainda
        
        # Gera um username único baseado no email (parte antes do @) + UUID
        email_prefix = self.cleaned_data["email"].split('@')[0]
        unique_suffix = str(uuid.uuid4()).split('-')[0] # Pega uma parte curta do UUID
        user.username = f"{email_prefix}_{unique_suffix}" 
        
        # Garante que o username gerado seja realmente único (caso extremo)
        while User.objects.filter(username=user.username).exists():
             unique_suffix = str(uuid.uuid4()).split('-')[0]
             user.username = f"{email_prefix}_{unique_suffix}"

        # Popula os outros campos
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save() # Salva o usuário no banco de dados
        return user