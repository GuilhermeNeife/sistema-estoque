from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from src.models import db
from src.models.estoque import EntradaEstoque, SaidaEstoque
from src.models.produto import Produto, ProdutoVariacao
from src.models.cliente_fornecedor import ClienteFornecedor
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, HiddenField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import datetime

class EntradaEstoqueForm(FlaskForm):
    id = HiddenField('ID')
    variacao_id = SelectField('Produto/Variação', coerce=int, validators=[DataRequired(message='Produto é obrigatório')])
    fornecedor_id = SelectField('Fornecedor', coerce=int, validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    preco_custo = FloatField('Preço de Custo', validators=[DataRequired(message='Preço de custo é obrigatório'), NumberRange(min=0, message='Preço deve ser maior ou igual a zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')], default=datetime.now)
    nota_fiscal = StringField('Nota Fiscal', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Registrar Entrada')

class SaidaEstoqueForm(FlaskForm):
    id = HiddenField('ID')
    variacao_id = SelectField('Produto/Variação', coerce=int, validators=[DataRequired(message='Produto é obrigatório')])
    cliente_id = SelectField('Cliente', coerce=int, validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='Quantidade é obrigatória'), NumberRange(min=1, message='Quantidade deve ser maior que zero')])
    data = DateField('Data', validators=[DataRequired(message='Data é obrigatória')], default=datetime.now)
    motivo = StringField('Motivo', validators=[Optional()])
    observacao = TextAreaField('Observação', validators=[Optional()])
    submit = SubmitField('Registrar Saída')

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

@estoque_bp.route('/entradas')
def entradas():
    entradas = EntradaEstoque.query.order_by(EntradaEstoque.data.desc()).all()
    return render_template('estoque/entradas.html', entradas=entradas)

@estoque_bp.route('/entradas/nova', methods=['GET', 'POST'])
def nova_entrada():
    form = EntradaEstoqueForm()
    
    # Carregar opções para os campos select
    variacoes = []
    for produto in Produto.query.all():
        for variacao in produto.variacoes:
            variacoes.append((variacao.id, f"{produto.nome} - {variacao.nome} ({variacao.sku})"))
    
    form.variacao_id.choices = [(0, '-- Selecione --')] + variacoes
    form.fornecedor_id.choices = [(0, '-- Selecione --')] + [(f.id, f.nome) for f in ClienteFornecedor.query.filter_by(eh_fornecedor=True).all()]
    
    if form.validate_on_submit():
        variacao = ProdutoVariacao.query.get(form.variacao_id.data)
        if not variacao:
            flash('Variação de produto não encontrada!', 'danger')
            return redirect(url_for('estoque.nova_entrada'))
        
        entrada = EntradaEstoque(
            variacao_id=form.variacao_id.data,
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

@estoque_bp.route('/saidas')
def saidas():
    saidas = SaidaEstoque.query.order_by(SaidaEstoque.data.desc()).all()
    return render_template('estoque/saidas.html', saidas=saidas)

@estoque_bp.route('/saidas/nova', methods=['GET', 'POST'])
def nova_saida():
    form = SaidaEstoqueForm()
    
    # Carregar opções para os campos select
    variacoes = []
    for produto in Produto.query.all():
        for variacao in produto.variacoes:
            if variacao.quantidade_atual > 0:  # Só mostrar variações com estoque
                variacoes.append((variacao.id, f"{produto.nome} - {variacao.nome} ({variacao.sku}) - Estoque: {variacao.quantidade_atual}"))
    
    form.variacao_id.choices = [(0, '-- Selecione --')] + variacoes
    form.cliente_id.choices = [(0, '-- Selecione --')] + [(c.id, c.nome) for c in ClienteFornecedor.query.filter_by(eh_cliente=True).all()]
    
    if form.validate_on_submit():
        variacao = ProdutoVariacao.query.get(form.variacao_id.data)
        if not variacao:
            flash('Variação de produto não encontrada!', 'danger')
            return redirect(url_for('estoque.nova_saida'))
        
        # Verificar se há estoque suficiente
        if variacao.quantidade_atual < form.quantidade.data:
            flash(f'Estoque insuficiente! Disponível: {variacao.quantidade_atual}', 'danger')
            return redirect(url_for('estoque.nova_saida'))
        
        saida = SaidaEstoque(
            variacao_id=form.variacao_id.data,
            cliente_id=form.cliente_id.data if form.cliente_id.data != 0 else None,
            quantidade=form.quantidade.data,
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

@estoque_bp.route('/entradas/<int:id>/excluir', methods=['POST'])
def excluir_entrada(id):
    entrada = EntradaEstoque.query.get_or_404(id)
    variacao = entrada.variacao
    
    # Verificar se há estoque suficiente para estornar
    if variacao.quantidade_atual < entrada.quantidade:
        flash('Não é possível excluir esta entrada. Estoque atual insuficiente para estorno.', 'danger')
        return redirect(url_for('estoque.entradas'))
    
    # Atualizar estoque da variação
    variacao.quantidade_atual -= entrada.quantidade
    
    db.session.delete(entrada)
    db.session.commit()
    
    flash('Entrada de estoque excluída com sucesso!', 'success')
    return redirect(url_for('estoque.entradas'))

@estoque_bp.route('/saidas/<int:id>/excluir', methods=['POST'])
def excluir_saida(id):
    saida = SaidaEstoque.query.get_or_404(id)
    variacao = saida.variacao
    
    # Atualizar estoque da variação
    variacao.quantidade_atual += saida.quantidade
    
    db.session.delete(saida)
    db.session.commit()
    
    flash('Saída de estoque excluída com sucesso!', 'success')
    return redirect(url_for('estoque.saidas'))

@estoque_bp.route('/api/variacao/<int:id>/info')
def get_variacao_info(id):
    variacao = ProdutoVariacao.query.get_or_404(id)
    produto = variacao.produto
    
    return jsonify({
        'id': variacao.id,
        'sku': variacao.sku,
        'nome': variacao.nome,
        'produto_nome': produto.nome,
        'quantidade_atual': variacao.quantidade_atual,
        'preco_venda': variacao.preco_venda
    })
