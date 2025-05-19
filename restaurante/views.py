from django.shortcuts import render, redirect, get_object_or_404
from .models import Prato, Ingrediente, Pedido, PratoIngrediente, Estoque, PedidoPrato
from .forms import PratoForm, IngredienteForm, ReposicaoEstoqueForm
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Prefetch, F
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from users.forms import SimplifiedUserCreationForm
from django.contrib.auth import login
from django.db import transaction

staff_required = user_passes_test(lambda u: u.is_staff, login_url='login')

def cardapio(request):
    prato = Prato.objects.order_by('nome')
    context = {'pratos': prato}
    return render(request, 'restaurante/cardapio.html', context)

def prato(request, id_prato):
    prato = Prato.objects.get(id_prato=id_prato)
    context = {'prato': prato}
    return render(request, 'restaurante/prato.html', context)

@login_required
@staff_required
def new_prato(request):
    ingredientes_all = Ingrediente.objects.all()
    if request.method == 'POST':
        form = PratoForm(request.POST)
        if form.is_valid():
            prato = form.save()
            ids = request.POST.getlist('ingredientes')
            if not ids:
                form.add_error(None, 'Você precisa selecionar ao menos um ingrediente.')
                return render(request, 'restaurante/new_prato.html', {'form': form, 'ingredientes': ingredientes_all})
            for id_ in ids:
                qty = request.POST.get(f'quantidade_{id_}')
                if not qty:
                    form.add_error(None, 'Quantidade obrigatória para todos os ingredientes marcados.')
                    prato.delete()
                    return render(request, 'restaurante/new_prato.html', {'form': form, 'ingredientes': ingredientes_all})
                try:
                    q = float(qty)
                except ValueError:
                    form.add_error(None, f'Quantidade inválida para o ingrediente {id_}.')
                    prato.delete()
                    return render(request, 'restaurante/new_prato.html', {'form': form, 'ingredientes': ingredientes_all})
                PratoIngrediente.objects.create(prato=prato, ingrediente_id=id_, quantidade=q)
            return redirect('cardapio')
    else:
        form = PratoForm()
    return render(request, 'restaurante/new_prato.html', {'form': form, 'ingredientes': ingredientes_all})

@login_required
def edit_prato(request, id_prato):
    prato = get_object_or_404(Prato, id_prato=id_prato)
    todos_ingredientes = Ingrediente.objects.all()
    def preparar_dados_ingredientes(prato_obj, ingredientes_lista, post_data=None):
        ingredientes_data = []
        quantidades_atuais = {pi.ingrediente.id: pi.quantidade for pi in PratoIngrediente.objects.filter(prato=prato_obj)}
        ids_selecionados_post = set(post_data.getlist("ingredientes")) if post_data else None
        for ing in ingredientes_lista:
            quantidade_valor = ""
            selecionado = False
            if post_data:
                if str(ing.id) in ids_selecionados_post:
                    selecionado = True
                    quantidade_valor = post_data.get(f"quantidade_{ing.id}", "")
            else:
                if ing.id in quantidades_atuais:
                    selecionado = True
                    quantidade_valor = quantidades_atuais.get(ing.id, "")
            ingredientes_data.append({
                "id": ing.id,
                "nome": ing.nome,
                "selecionado": selecionado,
                "quantidade": quantidade_valor
            })
        return ingredientes_data
    if request.method == 'POST':
        form = PratoForm(request.POST, instance=prato)
        if form.is_valid():
            prato = form.save()
            PratoIngrediente.objects.filter(prato=prato).delete()
            ids_selecionados = request.POST.getlist('ingredientes')
            if not ids_selecionados:
                form.add_error(None, 'Você precisa selecionar ao menos um ingrediente.')
                ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
                return render(request, 'restaurante/edit_prato.html', {'form': form, 'ingredientes_data': ingredientes_para_template, 'prato': prato})
            erro_quantidade = False
            for id_ingrediente in ids_selecionados:
                quantidade_str = request.POST.get(f'quantidade_{id_ingrediente}')
                ingrediente_obj = get_object_or_404(Ingrediente, id=id_ingrediente)
                if not quantidade_str:
                    form.add_error(None, f'Você deve fornecer uma quantidade para o ingrediente "{ingrediente_obj.nome}".')
                    erro_quantidade = True
                    continue
                try:
                    quantidade_float = float(quantidade_str.replace(',', '.'))
                    if quantidade_float <= 0:
                        form.add_error(None, f'A quantidade para o ingrediente "{ingrediente_obj.nome}" deve ser positiva.')
                        erro_quantidade = True
                        continue
                    PratoIngrediente.objects.create(prato=prato, ingrediente_id=id_ingrediente, quantidade=quantidade_float)
                except ValueError:
                    form.add_error(None, f'Quantidade inválida fornecida para o ingrediente "{ingrediente_obj.nome}". Use números.')
                    erro_quantidade = True
            if erro_quantidade:
                ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
                return render(request, 'restaurante/edit_prato.html', {'form': form, 'ingredientes_data': ingredientes_para_template, 'prato': prato})
            return redirect('cardapio')
        else:
            ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
            return render(request, 'restaurante/edit_prato.html', {'form': form, 'ingredientes_data': ingredientes_para_template, 'prato': prato})
    else:
        form = PratoForm(instance=prato)
        ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes)
    return render(request, 'restaurante/edit_prato.html', {'form': form, 'ingredientes_data': ingredientes_para_template, 'prato': prato})

@login_required
@staff_required
def delete_prato(request, id_prato):
    prato = Prato.objects.get(id_prato=id_prato)
    if request.method == 'POST':
        prato.delete()
        return redirect('cardapio')
    context = {'prato': prato}
    return render(request, 'restaurante/delete_prato.html', context)

@login_required
@staff_required
def estoque(request):
    for ing in Ingrediente.objects.all():
        Estoque.objects.get_or_create(ingrediente=ing)
    estoques = Estoque.objects.select_related('ingrediente').all()
    return render(request, 'restaurante/estoque.html', {'estoques': estoques})

@login_required
@staff_required
def criar_ingrediente(request):
    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = IngredienteForm()
    return render(request, 'restaurante/criar_ingrediente.html', {'form': form})

@login_required
@staff_required
def editar_ingrediente(request, id):
    ingrediente = get_object_or_404(Ingrediente, id=id)
    estoque, _ = Estoque.objects.get_or_create(ingrediente=ingrediente)
    if request.method == 'POST':
        form = IngredienteForm(request.POST, instance=ingrediente)
        nova_quantidade = request.POST.get('quantidade_estoque')
        if form.is_valid():
            form.save()
            try:
                estoque.quantidade = Decimal(nova_quantidade)
                estoque.save()
            except:
                messages.error(request, "Erro ao salvar a quantidade. Certifique-se de que é um número válido.")
                return render(request, 'restaurante/editar_ingrediente.html', {'form': form, 'ingrediente': ingrediente, 'quantidade_estoque': estoque.quantidade})
            return redirect('estoque')
    else:
        form = IngredienteForm(instance=ingrediente)
    return render(request, 'restaurante/editar_ingrediente.html', {'form': form, 'ingrediente': ingrediente, 'quantidade_estoque': estoque.quantidade})

@login_required
@staff_required
def lista_ingredientes(request):
    ingredientes = Ingrediente.objects.all()
    for ingrediente in ingredientes:
        ingrediente.estoque_quantidade = ingrediente.estoque.quantidade if ingrediente.estoque else 0
    return render(request, 'restaurante/ingredientes.html', {'ingredientes': ingredientes})

@login_required
@staff_required
def pedidos(request):
    pedidos = Pedido.objects.prefetch_related(Prefetch('pratos', queryset=PedidoPrato.objects.select_related('prato'))).order_by('-data_criacao')
    return render(request, 'restaurante/pedido.html', {'pedidos': pedidos})

@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_pedido').prefetch_related(Prefetch('pratos', queryset=PedidoPrato.objects.select_related('prato')))
    return render(request, 'restaurante/meus_pedidos.html', {'pedidos': pedidos})

@login_required
@staff_required
@require_POST
def atualizar_status_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    novo_status = request.POST.get('status')
    status_validos = dict(Pedido.STATUS_CHOICES).keys()
    if novo_status not in status_validos:
        return HttpResponseBadRequest("Status inválido.")
    pedido.status = novo_status
    pedido.save()
    return redirect('pedido')

@login_required
def criar_pedido(request):
    pratos_disponiveis = Prato.objects.prefetch_related(Prefetch('pratoingrediente_set', queryset=PratoIngrediente.objects.select_related('ingrediente__estoque'))).all()
    if request.method == 'POST':
        pratos_selecionados_ids = request.POST.getlist('prato')
        if not pratos_selecionados_ids:
            messages.error(request, "Você deve selecionar pelo menos um prato para criar o pedido.")
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})
        quantidades_pedidas = {}
        erro_quantidade_invalida = False
        for prato_id in pratos_selecionados_ids:
            quantidade_str = request.POST.get(f'quantidade_{prato_id}')
            try:
                quantidade = int(quantidade_str)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser positiva.")
                quantidades_pedidas[prato_id] = quantidade
            except (ValueError, TypeError):
                erro_quantidade_invalida = True
                messages.error(request, f"Quantidade inválida para o prato ID {prato_id}. Por favor, insira um número inteiro positivo.")
                break
        if erro_quantidade_invalida:
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})
        try:
            with transaction.atomic():
                estoque_insuficiente = False
                for prato_id, quantidade_pedida in quantidades_pedidas.items():
                    prato_obj = next((p for p in pratos_disponiveis if str(p.id_prato) == prato_id), None)
                    if not prato_obj:
                        messages.error(request, f"Prato com ID {prato_id} não encontrado.")
                        estoque_insuficiente = True
                        break
                    for item_receita in prato_obj.pratoingrediente_set.all():
                        ingrediente = item_receita.ingrediente
                        quantidade_necessaria = item_receita.quantidade * quantidade_pedida
                        try:
                            estoque_atual = ingrediente.estoque.quantidade
                        except Estoque.DoesNotExist:
                            estoque_atual = Decimal('0')
                        if estoque_atual < quantidade_necessaria:
                            messages.error(request, f"Estoque insuficiente para o ingrediente '{ingrediente.nome}' necessário para o prato '{prato_obj.nome}'.")
                            estoque_insuficiente = True
                            break
                    if estoque_insuficiente:
                        break
                if estoque_insuficiente:
                    raise ValueError("Estoque insuficiente detectado.")
                pedido = Pedido.objects.create(status='P', cliente=request.user)
                itens_pedido_para_criar = []
                for prato_id, quantidade_pedida in quantidades_pedidas.items():
                    prato_obj = next((p for p in pratos_disponiveis if str(p.id_prato) == prato_id), None)
                    itens_pedido_para_criar.append(PedidoPrato(pedido=pedido, prato=prato_obj, quantidade=quantidade_pedida))
                    for item_receita in prato_obj.pratoingrediente_set.all():
                        quantidade_a_deduzir = item_receita.quantidade * quantidade_pedida
                        Estoque.objects.filter(ingrediente=item_receita.ingrediente).update(quantidade=F('quantidade') - quantidade_a_deduzir)
                PedidoPrato.objects.bulk_create(itens_pedido_para_criar)
                messages.success(request, "Pedido criado com sucesso e estoque atualizado!")
                if request.user.is_staff:
                    return redirect('pedido')
                return redirect('meus_pedidos')
        except ValueError as e:
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})
    return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})

@login_required
@staff_required
def repor_estoque(request, id_ingrediente):
    ingrediente = get_object_or_404(Ingrediente, id=id_ingrediente)
    estoque, created = Estoque.objects.get_or_create(ingrediente=ingrediente)
    if request.method == 'POST':
        form = ReposicaoEstoqueForm(request.POST)
        if form.is_valid():
            adicionar = form.cleaned_data['quantidade']
            estoque.quantidade += adicionar
            estoque.save()
            return redirect('estoque')
    else:
        form = ReposicaoEstoqueForm()
    return render(request, 'restaurante/repor_estoque.html', {'ingrediente': ingrediente, 'estoque': estoque, 'form': form})

@login_required
@staff_required
def delete_ingrediente(request, id_ingrediente):
    ingrediente = get_object_or_404(Ingrediente, pk=id_ingrediente)
    if request.method == 'POST':
        ingrediente.delete()
        return redirect('estoque')
    return render(request, 'restaurante/confirm_delete_ingrediente.html', {'ingrediente': ingrediente})

def register(request):
    if request.method == 'POST':
        form = SimplifiedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                login(request, user, backend='users.backends.EmailBackend')
                messages.success(request, f'Conta criada com sucesso para {user.username}! Você foi logado.')
                return redirect('cardapio')
            except ValueError as e:
                messages.error(request, f"Erro ao fazer login após registro: {e}. Tente fazer login manualmente.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Ocorreu um erro inesperado após o registro: {e}. Tente fazer login manualmente.")
                return redirect('login')
    else:
        form = SimplifiedUserCreationForm()
    return render(request, 'users/register.html', {'form': form})
