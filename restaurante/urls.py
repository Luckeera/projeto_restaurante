from django.urls import path
from . import views

urlpatterns = [

    # Cardápio
    path('', views.cardapio, name='cardapio'),
    path('prato/<str:id_prato>/', views.prato, name='prato'),  # Exibe detalhes de um prato específico

    # Pedidos
    path('pedido/', views.pedidos, name='pedido'),  # Exibe a lista de pedidos
    path('pedido/<int:id>/atualizar/', views.atualizar_status_pedido, name='atualizar_status_pedido'),
    path('pedido/criar/', views.criar_pedido, name='criar_pedido'),
    path('pedido/meus_pedidos/', views.meus_pedidos, name='meus_pedidos'),

    # Estoque e Ingredientes
    path('estoque/', views.estoque, name='estoque'),  # Exibe o estoque de ingredientes
    path('ingredientes/', views.lista_ingredientes, name='lista_ingredientes'),  # Exibe a lista de ingredientes
    path('ingredientes/novo/', views.criar_ingrediente, name='criar_ingrediente'),  # Página para criar ingrediente
    path('ingredientes/<int:id>/editar/', views.editar_ingrediente, name='editar_ingrediente'),  # Editar ingrediente específico
    
    # logo abaixo de editar_ingrediente, por exemplo:
    path('estoque/repor/<int:id_ingrediente>/', views.repor_estoque, name='repor_estoque'),
    path('ingrediente/delete/<int:id_ingrediente>/', views.delete_ingrediente, name='delete_ingrediente'),

    # Novo prato e edição de pratos
    path('new_prato/', views.new_prato, name='new_prato'),  # Criar um novo prato
    path('edit_prato/<str:id_prato>/', views.edit_prato, name='edit_prato'),  # Editar prato específico
    path('delete_prato/<str:id_prato>/', views.delete_prato, name='delete_prato'),  # Deletar prato específico


]