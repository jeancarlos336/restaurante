from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Rol
from django.core.exceptions import ValidationError

class UsuarioCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=15, required=False)
    foto_perfil = forms.ImageField(required=False)
    rol = forms.ModelChoiceField(queryset=Rol.objects.all(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'telefono', 'foto_perfil', 'rol']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está en uso.")
        return email

class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'foto_perfil', 'rol', 'esta_activo']
        widgets = {
            'esta_activo': forms.CheckboxInput(),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )