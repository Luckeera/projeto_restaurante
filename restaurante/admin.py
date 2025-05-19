from django.contrib import admin
from .models import Prato, Ingrediente, Estoque, PratoIngrediente, Pedido

# Inline para associar ingredientes a pratos
class PratoIngredienteInline(admin.TabularInline):
    model = PratoIngrediente
    extra = 1

# Admin de Prato

class PratoAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'preco', 'descricao')
    search_fields = ('nome',)
    inlines       = [PratoIngredienteInline]

# Admin de Ingrediente

class IngredienteAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'estoque_atual')
    search_fields = ('nome',)

    def estoque_atual(self, obj):
        return obj.estoque.quantidade if hasattr(obj, 'estoque') else 0
    estoque_atual.short_description = 'Estoque (g)'

# Admin de Estoque (caso queira ver/editar diretamente)

class EstoqueAdmin(admin.ModelAdmin):
    list_display = ('ingrediente', 'quantidade')

# Admin de Pedido

class PedidoAdmin(admin.ModelAdmin):
    list_display   = ('prato', 'quantidade', 'status', 'data_pedido')
    list_filter    = ('status',)
    search_fields  = ('prato__nome',)
    date_hierarchy = 'data_pedido'


admin.site.register(Ingrediente)
admin.site.register(Estoque)
admin.site.register(Prato)
admin.site.register(PratoIngrediente)
admin.site.register(Pedido)