# compras/forms.py
from django import forms
from .models import Proveedor, Compra

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'email', 'direccion', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['fecha', 'proveedor', 'tipo_documento', 'numero_documento', 
                 'destino', 'detalle', 'total', 'comprobante', 'notas_adicionales']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'detalle': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprobante': forms.FileInput(attrs={'class': 'form-control'}),
            'notas_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }