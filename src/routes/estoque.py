from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from src.models import db
from src.models.estoque import EntradaEstoque, SaidaEstoque
from src.models.produto import Produto, ProdutoVariacao
from src.models.cliente_fornecedor import ClienteFornecedor
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, HiddenField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import datetime, timedelta
from sqlalchemy import or_

class EntradaEstoqueForm(FlaskForm):
    id = HiddenField('ID')
    produto_id = SelectField('Produto', coerce=int, validators=[DataRequired(message='Produto é obrigatório')])
    variacao_id = SelectField('Variação', coerce=int, validators=[Optional()])
    fornecedor_id = SelectField('Fornecedor', coerce=int, validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    preco_custo = FloatField('Preço de Custo', validators=[DataRequired(message='Preço de custo é obrigatório'), NumberRange(min=0, message='Preço deve ser maior ou igual a zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')], default=datetime.now)
    nota_fiscal = StringField('Nota Fiscal', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Registrar Entrada')

class SaidaEstoqueForm(FlaskForm):
    id = HiddenField('ID')
    produto_id = SelectField('Produto', coerce=int, validators=[DataRequired(message='Produto é obrigatório')])
    variacao_id = SelectField('Variação', coerce=int, validators=[Optional()])
    cliente_id = SelectField('Cliente', coerce=int, validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    preco_venda = FloatField('Preço de Venda', validators=[DataRequired(message='Preço de venda é obrigatório'), NumberRange(min=0, message='Preço deve ser maior ou igual a zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')], default=datetime.now)
    motivo = StringField('Motivo', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Registrar Saída')

class EntradaEstoqueEditForm(FlaskForm):
    id = HiddenField('ID')
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    preco_custo = FloatField('Preço de Custo', validators=[DataRequired(message='Preço de custo é obrigatório'), NumberRange(min=0, message='Preço deve ser maior ou igual a zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')])
    nota_fiscal = StringField('Nota Fiscal', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Salvar Alterações')

class SaidaEstoqueEditForm(FlaskForm):
    id = HiddenField('ID')
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    preco_venda = FloatField('Preço de Venda', validators=[DataRequired(message='Preço de venda é obrigatório'), NumberRange(min=0, message='Preço deve ser maior ou igual a zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')])
    motivo = StringField('Motivo', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Salvar Alterações')

estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')

@estoque_bp.route('/')
def index():
    # Buscar produtos com estoque baixo
    produtos_estoque_baixo = []
    produtos = Produto.query.all()
    
    for produto in produtos:
        for variacao in produto.variacoes:
            if variacao.estoque_baixo():
                produtos_estoque_baixo.append({
                    'produto': produto,
                    'variacao': variacao
                })
    
    # Buscar últimas movimentações
    entradas_recentes = EntradaEstoque.query.order_by(EntradaEstoque.data.desc()).limit(5).all()
    saidas_recentes = SaidaEstoque.query.order_by(SaidaEstoque.data.desc()).limit(5).all()
    
    return render_template('estoque/index.html', 
                          produtos_estoque_baixo=produtos_estoque_baixo,
                          entradas_recentes=entradas_recentes,
                          saidas_recentes=saidas_recentes)

@estoque_bp.route('/entradas', methods=['GET', 'POST'])
def entradas():
    # Obter parâmetros de filtro
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    produto_busca = request.args.get('produto_busca', '')
    fornecedor_id = request.args.get('fornecedor_id', '')
    nota_fiscal = request.args.get('nota_fiscal', '')
    
    # Iniciar a consulta
    query = EntradaEstoque.query
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        query = query.filter(EntradaEstoque.data >= data_inicio)
    
    if data_fim:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
        query = query.filter(EntradaEstoque.data <= data_fim)
    
    if produto_busca:
        query = query.join(ProdutoVariacao, EntradaEstoque.variacao_id == ProdutoVariacao.id) \
                    .join(Produto, ProdutoVariacao.produto_id == Produto.id) \
                    .filter(or_(
                        Produto.nome.ilike(f'%{produto_busca}%'),
                        ProdutoVariacao.nome.ilike(f'%{produto_busca}%'),
                        ProdutoVariacao.sku.ilike(f'%{produto_busca}%')
                    ))
    
    if fornecedor_id and fornecedor_id != '0':
        query = query.filter(EntradaEstoque.fornecedor_id == fornecedor_id)
    
    if nota_fiscal:
        query = query.filter(EntradaEstoque.nota_fiscal.ilike(f'%{nota_fiscal}%'))
    
    # Ordenar e obter resultados
    entradas = query.order_by(EntradaEstoque.data.desc()).all()
    
    # Obter lista de fornecedores para o filtro
    fornecedores = ClienteFornecedor.query.filter_by(eh_fornecedor=True).all()
    
    return render_template('estoque/entradas.html', 
                          entradas=entradas,
                          fornecedores=fornecedores,
                          filtros={
                              'data_inicio': data_inicio,
                              'data_fim': data_fim,
                              'produto_busca': produto_busca,
                              'fornecedor_id': fornecedor_id,
                              'nota_fiscal': nota_fiscal
                          })

@estoque_bp.route('/entradas/nova', methods=['GET', 'POST'])
def nova_entrada():
    form = EntradaEstoqueForm()
    
    # Carregar opções para os campos select
    produtos = [(0, '-- Selecione --')]
    for produto in Produto.query.order_by(Produto.nome).all():
        produtos.append((produto.id, produto.nome))
    
    form.produto_id.choices = produtos
    form.variacao_id.choices = [(0, '-- Selecione --')]
    form.fornecedor_id.choices = [(0, '-- Selecione --')] + [(f.id, f.nome) for f in ClienteFornecedor.query.filter_by(eh_fornecedor=True).all()]
    
    if form.validate_on_submit():
        produto_id = form.produto_id.data
        variacao_id = form.variacao_id.data
        
        # Obter o produto
        produto = Produto.query.get(produto_id)
        if not produto:
            flash('Produto não encontrado!', 'danger')
            return redirect(url_for('estoque.nova_entrada'))
        
        # Verificar se é um produto sem variação
        if variacao_id == 0:
            # Verificar se já existe uma variação padrão
            variacao = produto.get_variacao_padrao()
            if not variacao:
                # Criar variação padrão
                variacao = produto.criar_variacao_padrao(preco_venda=0)
            variacao_id = variacao.id
        else:
            variacao = ProdutoVariacao.query.get(variacao_id)
            if not variacao:
                flash('Variação de produto não encontrada!', 'danger')
                return redirect(url_for('estoque.nova_entrada'))
        
        entrada = EntradaEstoque(
            variacao_id=variacao_id,
            fornecedor_id=form.fornecedor_id.data if form.fornecedor_id.data != 0 else None,
            quantidade=form.quantidade.data,
            preco_custo=form.preco_custo.data,
            data=form.data.data,
            nota_fiscal=form.nota_fiscal.data,
            observacao=form.observacao.data
        )
        
        # Atualizar estoque da variação
        variacao.quantidade_atual += form.quantidade.data
        
        db.session.add(entrada)
        db.session.commit()
        
        flash('Entrada de estoque registrada com sucesso!', 'success')
        return redirect(url_for('estoque.entradas'))
    
    return render_template('estoque/entrada_form.html', form=form, titulo='Nova Entrada de Estoque')

@estoque_bp.route('/saidas', methods=['GET', 'POST'])
def saidas():
    # Obter parâmetros de filtro
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    produto_busca = request.args.get('produto_busca', '')
    cliente_id = request.args.get('cliente_id', '')
    motivo = request.args.get('motivo', '')
    
    # Iniciar a consulta
    query = SaidaEstoque.query
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        query = query.filter(SaidaEstoque.data >= data_inicio)
    
    if data_fim:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
        query = query.filter(SaidaEstoque.data <= data_fim)
    
    if produto_busca:
        query = query.join(ProdutoVariacao, SaidaEstoque.variacao_id == ProdutoVariacao.id) \
                    .join(Produto, ProdutoVariacao.produto_id == Produto.id) \
                    .filter(or_(
                        Produto.nome.ilike(f'%{produto_busca}%'),
                        ProdutoVariacao.nome.ilike(f'%{produto_busca}%'),
                        ProdutoVariacao.sku.ilike(f'%{produto_busca}%')
                    ))
    
    if cliente_id and cliente_id != '0':
        query = query.filter(SaidaEstoque.cliente_id == cliente_id)
    
    if motivo:
        query = query.filter(SaidaEstoque.motivo.ilike(f'%{motivo}%'))
    
    # Ordenar e obter resultados
    saidas = query.order_by(SaidaEstoque.data.desc()).all()
    
    # Obter lista de clientes para o filtro
    clientes = ClienteFornecedor.query.filter_by(eh_cliente=True).all()
    
    return render_template('estoque/saidas.html', 
                          saidas=saidas,
                          clientes=clientes,
                          filtros={
                              'data_inicio': data_inicio,
                              'data_fim': data_fim,
                              'produto_busca': produto_busca,
                              'cliente_id': cliente_id,
                              'motivo': motivo
                          })

@estoque_bp.route('/saidas/nova', methods=['GET', 'POST'])
def nova_saida():
    form = SaidaEstoqueForm()
    
    # Carregar opções para os campos select
    produtos = [(0, '-- Selecione --')]
    for produto in Produto.query.order_by(Produto.nome).all():
        # Verificar se o produto tem estoque (em qualquer variação)
        if produto.estoque_total() > 0:
            produtos.append((produto.id, produto.nome))
    
    form.produto_id.choices = produtos
    form.variacao_id.choices = [(0, '-- Selecione --')]
    form.cliente_id.choices = [(0, '-- Selecione --')] + [(c.id, c.nome) for c in ClienteFornecedor.query.filter_by(eh_cliente=True).all()]
    
    if form.validate_on_submit():
        produto_id = form.produto_id.data
        variacao_id = form.variacao_id.data
        
        # Obter o produto
        produto = Produto.query.get(produto_id)
        if not produto:
            flash('Produto não encontrado!', 'danger')
            return redirect(url_for('estoque.nova_saida'))
        
        # Verificar se é um produto sem variação
        if variacao_id == 0:
            # Verificar se já existe uma variação padrão
            variacao = produto.get_variacao_padrao()
            if not variacao:
                flash('Produto sem variação padrão!', 'danger')
                return redirect(url_for('estoque.nova_saida'))
            variacao_id = variacao.id
        else:
            variacao = ProdutoVariacao.query.get(variacao_id)
            if not variacao:
                flash('Variação de produto não encontrada!', 'danger')
                return redirect(url_for('estoque.nova_saida'))
        
        # Verificar se há estoque suficiente
        if variacao.quantidade_atual < form.quantidade.data:
            flash(f'Estoque insuficiente! Disponível: {variacao.quantidade_atual}', 'danger')
            return redirect(url_for('estoque.nova_saida'))
        
        # Calcular valor total
        valor_total = form.quantidade.data * form.preco_venda.data
        
        saida = SaidaEstoque(
            variacao_id=variacao_id,
            cliente_id=form.cliente_id.data if form.cliente_id.data != 0 else None,
            quantidade=form.quantidade.data,
            preco_venda=form.preco_venda.data,
            valor_total=valor_total,
            data=form.data.data,
            motivo=form.motivo.data,
            observacao=form.observacao.data
        )
        
        # Atualizar estoque da variação
        variacao.quantidade_atual -= form.quantidade.data
        
        db.session.add(saida)
        db.session.commit()
        
        flash('Saída de estoque registrada com sucesso!', 'success')
        return redirect(url_for('estoque.saidas'))
    
    return render_template('estoque/saida_form.html', form=form, titulo='Nova Saída de Estoque')

@estoque_bp.route('/entradas/<int:id>/editar', methods=['GET', 'POST'])
def editar_entrada(id):
    entrada = EntradaEstoque.query.get_or_404(id)
    form = EntradaEstoqueEditForm(obj=entrada)
    
    if form.validate_on_submit():
        # Calcular a diferença de quantidade
        diferenca_quantidade = form.quantidade.data - entrada.quantidade
        
        # Verificar se há estoque suficiente em caso de redução
        if diferenca_quantidade < 0 and entrada.variacao.quantidade_atual < abs(diferenca_quantidade):
            flash(f'Estoque insuficiente para reduzir a quantidade! Disponível: {entrada.variacao.quantidade_atual}', 'danger')
            return redirect(url_for('estoque.editar_entrada', id=id))
        
        # Atualizar os campos da entrada
        entrada.quantidade = form.quantidade.data
        entrada.preco_custo = form.preco_custo.data
        entrada.data = form.data.data
        entrada.nota_fiscal = form.nota_fiscal.data
        entrada.observacao = form.observacao.data
        
        # Atualizar o estoque da variação
        entrada.variacao.quantidade_atual += diferenca_quantidade
        
        db.session.commit()
        
        flash('Entrada de estoque atualizada com sucesso!', 'success')
        return redirect(url_for('estoque.entradas'))
    
    return render_template('estoque/entrada_edit_form.html', form=form, entrada=entrada)

@estoque_bp.route('/saidas/<int:id>/editar', methods=['GET', 'POST'])
def editar_saida(id):
    saida = SaidaEstoque.query.get_or_404(id)
    form = SaidaEstoqueEditForm(obj=saida)
    
    if form.validate_on_submit():
        # Calcular a diferença de quantidade
        diferenca_quantidade = form.quantidade.data - saida.quantidade
        
        # Verificar se há estoque suficiente em caso de aumento
        if diferenca_quantidade > 0 and saida.variacao.quantidade_atual < diferenca_quantidade:
            flash(f'Estoque insuficiente para aumentar a quantidade! Disponível: {saida.variacao.quantidade_atual}', 'danger')
            return redirect(url_for('estoque.editar_saida', id=id))
        
        # Atualizar os campos da saída
        saida.quantidade = form.quantidade.data
        saida.preco_venda = form.preco_venda.data
        saida.valor_total = form.quantidade.data * form.preco_venda.data
        saida.data = form.data.data
        saida.motivo = form.motivo.data
        saida.observacao = form.observacao.data
        
        # Atualizar o estoque da variação (reduzir se aumentou a quantidade, aumentar se reduziu)
        saida.variacao.quantidade_atual -= diferenca_quantidade
        
        db.session.commit()
        
        flash('Saída de estoque atualizada com sucesso!', 'success')
        return redirect(url_for('estoque.saidas'))
    
    return render_template('estoque/saida_edit_form.html', form=form, saida=saida)

@estoque_bp.route('/entradas/<int:id>/excluir', methods=['POST'])
def excluir_entrada(id):
    entrada = EntradaEstoque.query.get_or_404(id)
    
    try:
        # Verificar se há estoque suficiente para remover
        if entrada.variacao.quantidade_atual < entrada.quantidade:
            flash(f'Não é possível excluir esta entrada pois não há estoque suficiente. Disponível: {entrada.variacao.quantidade_atual}', 'danger')
            return redirect(url_for('estoque.entradas'))
        
        # Atualizar o estoque da variação
        entrada.variacao.quantidade_atual -= entrada.quantidade
        
        db.session.delete(entrada)
        db.session.commit()
        
        flash('Entrada de estoque excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir entrada: {str(e)}', 'danger')
    
    return redirect(url_for('estoque.entradas'))

@estoque_bp.route('/saidas/<int:id>/excluir', methods=['POST'])
def excluir_saida(id):
    saida = SaidaEstoque.query.get_or_404(id)
    
    try:
        # Atualizar o estoque da variação
        saida.variacao.quantidade_atual += saida.quantidade
        
        db.session.delete(saida)
        db.session.commit()
        
        flash('Saída de estoque excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir saída: {str(e)}', 'danger')
    
    return redirect(url_for('estoque.saidas'))

@estoque_bp.route('/variacao/<int:id>/info')
def get_variacao_info(id):
    variacao = ProdutoVariacao.query.get_or_404(id)
    return jsonify({
        'quantidade_atual': variacao.quantidade_atual,
        'preco_venda': variacao.preco_venda
    })

@estoque_bp.route('/produto/<int:id>/variacoes')
def get_variacoes_produto(id):
    produto = Produto.query.get_or_404(id)
    
    # Se o produto não tem variações, criar uma variação padrão
    if len(produto.variacoes) == 0:
        variacao = produto.criar_variacao_padrao()
        return jsonify([{
            'id': variacao.id,
            'nome': produto.nome,
            'sku': variacao.sku,
            'quantidade_atual': variacao.quantidade_atual,
            'preco_venda': variacao.preco_venda,
            'eh_padrao': True
        }])
    
    # Verificar se alguma variação é padrão
    tem_padrao = False
    for variacao in produto.variacoes:
        if variacao.eh_padrao:
            tem_padrao = True
            break
    
    # Se não tem variação padrão e tem apenas uma variação, marcar como padrão
    if not tem_padrao and len(produto.variacoes) == 1:
        produto.variacoes[0].eh_padrao = True
        db.session.commit()
    
    # Retornar todas as variações
    variacoes = []
    for variacao in produto.variacoes:
        # Para saída, só mostrar variações com estoque
        if request.args.get('tipo') == 'saida' and variacao.quantidade_atual <= 0:
            continue
            
        variacoes.append({
            'id': variacao.id,
            'nome': variacao.nome,
            'sku': variacao.sku,
            'quantidade_atual': variacao.quantidade_atual,
            'preco_venda': variacao.preco_venda,
            'eh_padrao': variacao.eh_padrao
        })
    
    return jsonify(variacoes)
