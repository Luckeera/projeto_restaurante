from django.db import models
from django.utils import timezone
from django.conf import settings


class Prato(models.Model):
    id_prato = models.AutoField(primary_key=True)
    descricao = models.TextField(blank=True, null=True)
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ingredientes = models.ManyToManyField('Ingrediente', through='PratoIngrediente', related_name='pratos')

    def __str__(self):
        return self.nome

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('C', 'Concluído'),
    ]
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meus_pedidos'
    )
    id = models.AutoField(primary_key=True)
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='P')
    data_criacao = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Pedido {self.id} - {self.get_status_display()}"

class PedidoPrato(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='pratos', on_delete=models.CASCADE)
    prato = models.ForeignKey(Prato, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantidade} x {self.prato.nome} no Pedido {self.pedido.id}"

class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Estoque(models.Model):
    ingrediente = models.OneToOneField(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ingrediente.nome} - {self.quantidade} gramas"

class PratoIngrediente(models.Model):
    prato = models.ForeignKey(Prato, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.SET_NULL, null=True)
    quantidade = models.FloatField()

    def __str__(self):
        return f"{self.quantidade} de {self.ingrediente.nome} em {self.prato.nome}"




# Create your models here.

