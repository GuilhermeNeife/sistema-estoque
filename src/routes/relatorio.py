from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from src.models import db
from src.models.produto import Produto, ProdutoVariacao
from src.models.cliente_fornecedor import ClienteFornecedor
from src.models.estoque import EntradaEstoque, SaidaEstoque
from datetime import datetime, timedelta
from sqlalchemy import func

relatorio_bp = Blueprint('relatorio', __name__, url_prefix='/relatorios')

@relatorio_bp.route('/')
def index():
    return render_template('relatorio/index.html')

@relatorio_bp.route('/estoque-atual')
def estoque_atual():
    produtos = Produto.query.all()
    
    # Organizar dados para o relatório
    dados = []
    for produto in produtos:
        for variacao in produto.variacoes:
            dados.append({
                'produto': produto,
                'variacao': variacao,
                'estoque_baixo': variacao.estoque_baixo()
            })
    
    return render_template('relatorio/estoque_atual.html', dados=dados)

@relatorio_bp.route('/estoque-baixo')
def estoque_baixo():
    produtos = Produto.query.all()
    
    # Filtrar apenas variações com estoque baixo
    dados = []
    for produto in produtos:
        for variacao in produto.variacoes:
            if variacao.estoque_baixo():
                dados.append({
                    'produto': produto,
                    'variacao': variacao,
                    'quantidade_atual': variacao.quantidade_atual,
                    'estoque_minimo': variacao.estoque_minimo
                })
    
    return render_template('relatorio/estoque_baixo.html', dados=dados)

@relatorio_bp.route('/movimentacoes', methods=['GET', 'POST'])
def movimentacoes():
    # Definir período padrão (último mês)
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)
    
    # Processar filtros
    if request.method == 'POST':
        data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d')
        data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d')
        # Ajustar data_fim para incluir todo o dia
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
    
    # Buscar entradas no período
    entradas = EntradaEstoque.query.filter(
        EntradaEstoque.data >= data_inicio,
        EntradaEstoque.data <= data_fim
    ).order_by(EntradaEstoque.data.desc()).all()
    
    # Buscar saídas no período
    saidas = SaidaEstoque.query.filter(
        SaidaEstoque.data >= data_inicio,
        SaidaEstoque.data <= data_fim
    ).order_by(SaidaEstoque.data.desc()).all()
    
    # Calcular totais
    total_entradas = sum(entrada.quantidade for entrada in entradas)
    total_saidas = sum(saida.quantidade for saida in saidas)
    valor_total_entradas = sum(entrada.quantidade * entrada.preco_custo for entrada in entradas)
    
    return render_template('relatorio/movimentacoes.html', 
                          entradas=entradas,
                          saidas=saidas,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          total_entradas=total_entradas,
                          total_saidas=total_saidas,
                          valor_total_entradas=valor_total_entradas)

@relatorio_bp.route('/clientes-fornecedores')
def clientes_fornecedores():
    clientes = ClienteFornecedor.query.filter_by(eh_cliente=True).all()
    fornecedores = ClienteFornecedor.query.filter_by(eh_fornecedor=True).all()
    
    # Contar movimentações por cliente/fornecedor
    for cliente in clientes:
        cliente.total_saidas = SaidaEstoque.query.filter_by(cliente_id=cliente.id).count()
    
    for fornecedor in fornecedores:
        fornecedor.total_entradas = EntradaEstoque.query.filter_by(fornecedor_id=fornecedor.id).count()
        fornecedor.total_responsaveis = len(fornecedor.responsaveis)
    
    return render_template('relatorio/clientes_fornecedores.html', 
                          clientes=clientes,
                          fornecedores=fornecedores)

@relatorio_bp.route('/api/dados-estoque')
def api_dados_estoque():
    # Buscar produtos com mais saídas nos últimos 30 dias
    data_limite = datetime.now() - timedelta(days=30)
    
    # Contar saídas por produto
    saidas_por_produto = db.session.query(
        Produto.nome,
        func.sum(SaidaEstoque.quantidade).label('total_saidas')
    ).join(ProdutoVariacao, SaidaEstoque.variacao_id == ProdutoVariacao.id
    ).join(Produto, ProdutoVariacao.produto_id == Produto.id
    ).filter(SaidaEstoque.data >= data_limite
    ).group_by(Produto.id
    ).order_by(func.sum(SaidaEstoque.quantidade).desc()
    ).limit(5).all()
    
    # Contar produtos por categoria
    produtos_por_categoria = db.session.query(
        db.func.coalesce(db.func.count(Produto.id), 0).label('total'),
        db.func.coalesce(db.func.sum(db.case([(Produto.estoque_baixo(), 1)], else_=0)), 0).label('estoque_baixo')
    ).all()
    
    # Formatar dados para gráficos
    labels_saidas = [item[0] for item in saidas_por_produto]
    dados_saidas = [int(item[1]) for item in saidas_por_produto]
    
    return jsonify({
        'produtos_mais_vendidos': {
            'labels': labels_saidas,
            'dados': dados_saidas
        },
        'resumo_estoque': {
            'total_produtos': sum(produto.variacoes.count() for produto in Produto.query.all()),
            'estoque_baixo': sum(1 for produto in Produto.query.all() if produto.estoque_baixo()),
            'sem_estoque': sum(1 for variacao in ProdutoVariacao.query.all() if variacao.quantidade_atual == 0)
        }
    })
