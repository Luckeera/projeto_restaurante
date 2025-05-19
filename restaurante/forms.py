from django import forms
from .models import Prato, Ingrediente




class PratoForm(forms.ModelForm):
    class Meta:
        model = Prato
        fields = ['nome', 'descricao', 'preco']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = ['nome']

class ReposicaoEstoqueForm(forms.Form):
    quantidade = forms.DecimalField(
        label="Quantidade a adicionar (g)",
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        help_text="Informe quanto de ingrediente deseja somar ao estoque atual.",
    )

