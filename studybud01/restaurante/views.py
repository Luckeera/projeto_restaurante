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
# Create your views here.

def cardapio (request):
    prato = Prato.objects.order_by('nome')
    context = {
        'pratos': prato,
    }
    return render(request, 'restaurante/cardapio.html', context)

def prato(request, id_prato):
    prato = Prato.objects.get(id_prato=id_prato)
    context = {
        'prato': prato,  # 👈 passando o objeto inteiro
    }
    return render(request, 'restaurante/prato.html', context)

@login_required
@staff_required  # Garante que apenas usuários staff possam acessar essa view
def new_prato(request):
    ingredientes_all = Ingrediente.objects.all()

    if request.method == 'POST':
        form = PratoForm(request.POST)
        if form.is_valid():
            prato = form.save()

            ids = request.POST.getlist('ingredientes')  # IDs só dos marcados
            if not ids:
                form.add_error(None, 'Você precisa selecionar ao menos um ingrediente.')
                return render(request, 'restaurante/new_prato.html', {
                    'form': form, 'ingredientes': ingredientes_all
                })

            for id_ in ids:
                qty = request.POST.get(f'quantidade_{id_}')
                if not qty:
                    form.add_error(None, 'Quantidade obrigatória para todos os ingredientes marcados.')
                    prato.delete()
                    return render(request, 'restaurante/new_prato.html', {
                        'form': form, 'ingredientes': ingredientes_all
                    })
                try:
                    q = float(qty)
                except ValueError:
                    form.add_error(None, f'Quantidade inválida para o ingrediente {id_}.')
                    prato.delete()
                    return render(request, 'restaurante/new_prato.html', {
                        'form': form, 'ingredientes': ingredientes_all
                    })
                PratoIngrediente.objects.create(
                    prato=prato,
                    ingrediente_id=id_,
                    quantidade=q
                )

            return redirect('cardapio')
    else:
        form = PratoForm()

    return render(request, 'restaurante/new_prato.html', {
        'form': form,
        'ingredientes': ingredientes_all
    })

@login_required
def edit_prato(request, id_prato):
    prato = get_object_or_404(Prato, id_prato=id_prato)
    todos_ingredientes = Ingrediente.objects.all()

    # Função auxiliar para preparar dados dos ingredientes para o template
    def preparar_dados_ingredientes(prato_obj, ingredientes_lista, post_data=None):
        ingredientes_data = []
        quantidades_atuais = {pi.ingrediente.id: pi.quantidade 
                              for pi in PratoIngrediente.objects.filter(prato=prato_obj)}
        ids_selecionados_post = set(post_data.getlist("ingredientes")) if post_data else None
        
        for ing in ingredientes_lista:
            quantidade_valor = ""
            selecionado = False

            if post_data: # Se for um POST (com ou sem erro)
                if str(ing.id) in ids_selecionados_post:
                    selecionado = True
                    # Pega a quantidade do POST, mesmo que inválida, para repopular
                    quantidade_valor = post_data.get(f"quantidade_{ing.id}", "") 
                # Se não estava no POST, não marca e não põe quantidade
            else: # Se for um GET inicial
                if ing.id in quantidades_atuais:
                    selecionado = True
                    quantidade_valor = quantidades_atuais.get(ing.id, "")
            
            ingredientes_data.append({
                "id": ing.id,
                "nome": ing.nome,
                "selecionado": selecionado,
                "quantidade": quantidade_valor # Pode ser string vazia, valor do POST ou valor atual
            })
        return ingredientes_data

    if request.method == 'POST':
        form = PratoForm(request.POST, instance=prato)

        if form.is_valid():
            prato = form.save()  # Atualiza o prato
            PratoIngrediente.objects.filter(prato=prato).delete()
            ids_selecionados = request.POST.getlist('ingredientes')

            if not ids_selecionados:
                form.add_error(None, 'Você precisa selecionar ao menos um ingrediente.')
                # Prepara dados para re-renderizar com erro
                ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
                return render(request, 'restaurante/edit_prato.html', {
                    'form': form, 
                    'ingredientes_data': ingredientes_para_template, 
                    'prato': prato
                })

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
                         
                    PratoIngrediente.objects.create(
                        prato=prato,
                        ingrediente_id=id_ingrediente,
                        quantidade=quantidade_float
                    )
                except ValueError:
                    form.add_error(None, f'Quantidade inválida fornecida para o ingrediente "{ingrediente_obj.nome}". Use números.')
                    erro_quantidade = True
            
            if erro_quantidade:
                # Prepara dados para re-renderizar com erro
                # Note que ingredientes recém-criados antes do erro não serão deletados aqui
                # A lógica assume que o delete no início do POST válido limpa tudo.
                ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
                return render(request, 'restaurante/edit_prato.html', {
                    'form': form, 
                    'ingredientes_data': ingredientes_para_template, 
                    'prato': prato
                })

            return redirect('cardapio')
        else:
            # PratoForm inválido
            ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes, request.POST)
            return render(request, 'restaurante/edit_prato.html', {
                'form': form, 
                'ingredientes_data': ingredientes_para_template, 
                'prato': prato
            })

    # --- Lógica GET ---    
    else:
        form = PratoForm(instance=prato)
        ingredientes_para_template = preparar_dados_ingredientes(prato, todos_ingredientes)

    return render(request, 'restaurante/edit_prato.html', {
        'form': form,
        'ingredientes_data': ingredientes_para_template, 
        'prato': prato
    })

   
@login_required
@staff_required
def delete_prato(request, id_prato):
    prato = Prato.objects.get(id_prato=id_prato)
    if request.method == 'POST':
        prato.delete()
        return redirect('cardapio')  # troque pelo nome correto da URL da listagem

    context = {'prato': prato}
    return render(request, 'restaurante/delete_prato.html', context)

@login_required
@staff_required
def estoque(request):
    # Garante que cada ingrediente tenha um Estoque criado
    for ing in Ingrediente.objects.all():
        Estoque.objects.get_or_create(ingrediente=ing)

    estoques = Estoque.objects.select_related('ingrediente').all()
    return render(request, 'restaurante/estoque.html', {
        'estoques': estoques
    })

@login_required
@staff_required
def criar_ingrediente(request):
    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')  # redireciona para a lista de ingredientes
    else:
        form = IngredienteForm()
    return render(request, 'restaurante/criar_ingrediente.html', {'form': form})

@login_required
@staff_required
def editar_ingrediente(request, id):
    ingrediente = get_object_or_404(Ingrediente, id=id)
    estoque, _ = Estoque.objects.get_or_create(ingrediente=ingrediente)  # Garante que o estoque existe

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
                return render(request, 'restaurante/editar_ingrediente.html', {
                    'form': form, 'ingrediente': ingrediente, 'quantidade_estoque': estoque.quantidade
                })

            return redirect('estoque')
    else:
        form = IngredienteForm(instance=ingrediente)

    return render(request, 'restaurante/editar_ingrediente.html', {
        'form': form,
        'ingrediente': ingrediente,
        'quantidade_estoque': estoque.quantidade
    })

@login_required
@staff_required
def lista_ingredientes(request):
    ingredientes = Ingrediente.objects.all()
    # Garantir que cada ingrediente tem um Estoque
    for ingrediente in ingredientes:
        # Adiciona a quantidade de estoque na lista de contexto
        ingrediente.estoque_quantidade = ingrediente.estoque.quantidade if ingrediente.estoque else 0

    return render(request, 'restaurante/ingredientes.html', {
        'ingredientes': ingredientes
    })

@login_required
@staff_required
def pedidos(request):
    # Vamos prefetchar os itens do pedido e, dentro deles, cada prato
    pedidos = Pedido.objects.prefetch_related(
        Prefetch('pratos', queryset=PedidoPrato.objects.select_related('prato'))
    ).order_by('-data_criacao')  # opcional: mais recentes primeiro

    return render(request, 'restaurante/pedido.html', {'pedidos': pedidos})

@login_required
def meus_pedidos(request):
    pedidos = (
        Pedido.objects
        .filter(cliente=request.user)
        .order_by('-data_pedido')  # mais recentes primeiro
        .prefetch_related(
            Prefetch(
                'pratos',  # related_name de PedidoPrato
                queryset=PedidoPrato.objects.select_related('prato')
            )
        )
    )
    return render(request, 'restaurante/meus_pedidos.html', {
        'pedidos': pedidos
    })

@login_required
@staff_required
@require_POST
def atualizar_status_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    novo_status = request.POST.get('status')

    # Validação segura usando os códigos de status
    status_validos = dict(Pedido.STATUS_CHOICES).keys()
    if novo_status not in status_validos:
        return HttpResponseBadRequest("Status inválido.")

    pedido.status = novo_status
    pedido.save()

    return redirect('pedido')

@login_required
def criar_pedido(request):
    pratos_disponiveis = Prato.objects.prefetch_related(
        Prefetch(
            'pratoingrediente_set', # related_name de PratoIngrediente para Prato
            queryset=PratoIngrediente.objects.select_related('ingrediente__estoque')
        )
    ).all()

    if request.method == 'POST':
        pratos_selecionados_ids = request.POST.getlist('prato') # IDs dos checkboxes marcados

        if not pratos_selecionados_ids:
            messages.error(request, "Você deve selecionar pelo menos um prato para criar o pedido.")
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})

        # Dicionário para armazenar a quantidade pedida de cada prato
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
                break # Para o loop se encontrar um erro de quantidade

        if erro_quantidade_invalida:
            # Renderiza o formulário novamente com a mensagem de erro
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})

        # <<< INÍCIO DA LÓGICA DE ESTOQUE E TRANSAÇÃO >>>
        try:
            with transaction.atomic(): # Garante que ou tudo funciona ou nada é alterado
                # 1. Verificar estoque para todos os itens ANTES de deduzir
                estoque_insuficiente = False
                for prato_id, quantidade_pedida in quantidades_pedidas.items():
                    # Usar o Prefetch para evitar queries extras no loop
                    prato_obj = next((p for p in pratos_disponiveis if str(p.id_prato) == prato_id), None)
                    if not prato_obj:
                        messages.error(request, f"Prato com ID {prato_id} não encontrado.")
                        estoque_insuficiente = True
                        break # Sai do loop de verificação

                    for item_receita in prato_obj.pratoingrediente_set.all():
                        ingrediente = item_receita.ingrediente
                        quantidade_necessaria = item_receita.quantidade * quantidade_pedida
                        
                        # Tenta obter o estoque do ingrediente (pode não existir se foi criado e nunca reposto)
                        try:
                            estoque_atual = ingrediente.estoque.quantidade
                        except Estoque.DoesNotExist:
                             estoque_atual = Decimal('0') # Considera 0 se não houver registro de estoque

                        if estoque_atual < quantidade_necessaria:
                            messages.error(request, f"Estoque insuficiente para o ingrediente '{ingrediente.nome}' necessário para o prato '{prato_obj.nome}'.")
                            estoque_insuficiente = True
                            break # Sai do loop interno (ingredientes)
                    if estoque_insuficiente:
                        break # Sai do loop externo (pratos)

                # Se o estoque foi insuficiente em algum momento, a transação será revertida automaticamente ao sair do 'with'
                if estoque_insuficiente:
                    raise ValueError("Estoque insuficiente detectado.") # Força o rollback da transação

                # 2. Se chegou aqui, há estoque suficiente. Criar o pedido.
                pedido = Pedido.objects.create(status='P', cliente=request.user)

                # 3. Deduzir do estoque e preparar itens do pedido para bulk_create
                itens_pedido_para_criar = []
                for prato_id, quantidade_pedida in quantidades_pedidas.items():
                    prato_obj = next((p for p in pratos_disponiveis if str(p.id_prato) == prato_id), None)
                    # Adiciona à lista para criação em lote
                    itens_pedido_para_criar.append(
                        PedidoPrato(pedido=pedido, prato=prato_obj, quantidade=quantidade_pedida)
                    )
                    # Deduz do estoque
                    for item_receita in prato_obj.pratoingrediente_set.all():
                        quantidade_a_deduzir = item_receita.quantidade * quantidade_pedida
                        # Atualização atômica usando F() para segurança em concorrência
                        Estoque.objects.filter(ingrediente=item_receita.ingrediente).update(quantidade=F('quantidade') - quantidade_a_deduzir)
                        # Recarrega o objeto estoque se precisar usar o valor atualizado depois
                        # item_receita.ingrediente.estoque.refresh_from_db()

                # 4. Cria todos os itens do pedido no banco de dados de uma vez
                PedidoPrato.objects.bulk_create(itens_pedido_para_criar)

                # 5. Mensagem de sucesso e redirecionamento (após a transação ser confirmada)
                messages.success(request, "Pedido criado com sucesso e estoque atualizado!")
                if request.user.is_staff:
                    return redirect('pedido') # Redireciona funcionário para lista geral
                return redirect('meus_pedidos') # Redireciona cliente para seus pedidos

        except ValueError as e: # Captura o erro de estoque insuficiente
            # A transação já foi revertida. Apenas renderiza a página com a mensagem de erro.
            # As mensagens de erro já foram adicionadas dentro do loop de verificação.
            return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})
        # <<< FIM DA LÓGICA DE ESTOQUE E TRANSAÇÃO >>>

    # Se não for POST, apenas renderiza o formulário
    return render(request, 'restaurante/criar_pedido.html', {'pratos': pratos_disponiveis})

@login_required
@staff_required
def repor_estoque(request, id_ingrediente):
    # 1) Busca ingrediente e seu estoque (ou cria se não existir)
    ingrediente = get_object_or_404(Ingrediente, id=id_ingrediente)
    estoque, created = Estoque.objects.get_or_create(ingrediente=ingrediente)

    if request.method == 'POST':
        form = ReposicaoEstoqueForm(request.POST)
        if form.is_valid():
            adicionar = form.cleaned_data['quantidade']
            estoque.quantidade += adicionar
            estoque.save()
            return redirect('estoque')  # Redireciona para o estoque após a reposição
    else:
        form = ReposicaoEstoqueForm()

    return render(request, 'restaurante/repor_estoque.html', {  # Certifique-se de que o caminho esteja correto
        'ingrediente': ingrediente,
        'estoque': estoque,
        'form': form,
    })

@login_required
@staff_required
def delete_ingrediente(request, id_ingrediente):
    # use pk=id_ingrediente (ou id=id_ingrediente)
    ingrediente = get_object_or_404(Ingrediente, pk=id_ingrediente)

    if request.method == 'POST':
        ingrediente.delete()
        return redirect('estoque')

    return render(request, 'restaurante/confirm_delete_ingrediente.html', {
        'ingrediente': ingrediente
    })

def register(request):
    if request.user.is_authenticated:
        return redirect("cardapio")

    if request.method == "POST":
        # Use o formulário correto
        form = SimplifiedUserCreationForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registro realizado com sucesso! Bem-vindo(a)!")
            return redirect("cardapio")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        # Use o formulário correto
        form = SimplifiedUserCreationForm() 
    
    return render(request, "users/register.html", {"form": form})