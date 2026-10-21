from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from src.models import db
from src.models.cliente_fornecedor import ClienteFornecedor, Responsavel
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Email, ValidationError
import re

class ClienteForm(FlaskForm):
    id = HiddenField('ID')
    nome = StringField('Nome', validators=[DataRequired(message='Nome é obrigatório')])
    cpf_cnpj = StringField('CPF/CNPJ', validators=[DataRequired(message='CPF/CNPJ é obrigatório')])
    email = StringField('E-mail', validators=[DataRequired(message='E-mail é obrigatório'), Email(message='E-mail inválido')])
    telefone = StringField('Telefone', validators=[DataRequired(message='Telefone é obrigatório')])
    endereco = StringField('Endereço', validators=[Optional()])
    eh_cliente = HiddenField('É Cliente', default='1')
    submit_cliente = SubmitField('Salvar Cliente')
    
    def validate_cpf_cnpj(self, field):
        # Remover caracteres não numéricos
        valor = re.sub(r'\D', '', field.data)
        
        # Validar CPF (11 dígitos) ou CNPJ (14 dígitos)
        if len(valor) != 11 and len(valor) != 14:
            raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos')
        
        # Verificar se já existe outro cliente com este CPF/CNPJ
        cliente = ClienteFornecedor.query.filter_by(cpf_cnpj=field.data).first()
        if cliente and (not self.id.data or int(self.id.data) != cliente.id):
            raise ValidationError('Este CPF/CNPJ já está cadastrado')

class FornecedorForm(FlaskForm):
    id = HiddenField('ID')
    nome = StringField('Nome', validators=[Optional()])
    razao_social = StringField('Razão Social', validators=[Optional()])
    nome_fantasia = StringField('Nome Fantasia', validators=[Optional()])
    cpf_cnpj = StringField('CNPJ/CPF', validators=[DataRequired(message='CNPJ/CPF é obrigatório')])
    email = StringField('E-mail', validators=[DataRequired(message='E-mail é obrigatório'), Email(message='E-mail inválido')])
    telefone = StringField('Telefone', validators=[DataRequired(message='Telefone é obrigatório')])
    endereco = StringField('Endereço', validators=[DataRequired(message='Endereço é obrigatório')])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    eh_fornecedor = HiddenField('É Fornecedor', default='1')
    submit_fornecedor = SubmitField('Salvar Fornecedor')
    
    def validate_cpf_cnpj(self, field):
        # Remover caracteres não numéricos
        valor = re.sub(r'\D', '', field.data)
        
        # Validar CPF (11 dígitos) ou CNPJ (14 dígitos)
        if len(valor) != 11 and len(valor) != 14:
            raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos')
        
        # Verificar se já existe outro fornecedor com este CPF/CNPJ
        fornecedor = ClienteFornecedor.query.filter_by(cpf_cnpj=field.data).first()
        if fornecedor and (not self.id.data or int(self.id.data) != fornecedor.id):
            raise ValidationError('Este CPF/CNPJ já está cadastrado')

cliente_fornecedor_bp = Blueprint('cliente_fornecedor', __name__, url_prefix='/clientes-fornecedores')

@cliente_fornecedor_bp.route('/')
def listar():
    clientes = ClienteFornecedor.query.filter_by(eh_cliente=True).all()
    fornecedores = ClienteFornecedor.query.filter_by(eh_fornecedor=True).all()
    return render_template('cliente_fornecedor/listar.html', clientes=clientes, fornecedores=fornecedores)

@cliente_fornecedor_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    cliente_form = ClienteForm()
    fornecedor_form = FornecedorForm()
    
    # Determinar qual aba está ativa
    aba_ativa = request.args.get('aba', 'cliente')
    
    if request.method == 'POST':
        if 'submit_cliente' in request.form and cliente_form.validate_on_submit():
            cliente = ClienteFornecedor(
                nome=cliente_form.nome.data,
                cpf_cnpj=cliente_form.cpf_cnpj.data,
                email=cliente_form.email.data,
                telefone=cliente_form.telefone.data,
                endereco=cliente_form.endereco.data,
                eh_cliente=True,
                eh_fornecedor=False
            )
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('cliente_fornecedor.listar'))
        
        elif 'submit_fornecedor' in request.form and fornecedor_form.validate_on_submit():
            # Determinar o nome do fornecedor (razão social, nome fantasia ou nome)
            nome = fornecedor_form.nome.data
            if fornecedor_form.razao_social.data:
                nome = fornecedor_form.razao_social.data
            elif fornecedor_form.nome_fantasia.data:
                nome = fornecedor_form.nome_fantasia.data
            
            fornecedor = ClienteFornecedor(
                nome=nome,
                razao_social=fornecedor_form.razao_social.data,
                nome_fantasia=fornecedor_form.nome_fantasia.data,
                cpf_cnpj=fornecedor_form.cpf_cnpj.data,
                email=fornecedor_form.email.data,
                telefone=fornecedor_form.telefone.data,
                endereco=fornecedor_form.endereco.data,
                observacoes=fornecedor_form.observacoes.data,
                eh_cliente=False,
                eh_fornecedor=True
            )
            db.session.add(fornecedor)
            db.session.commit()
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('cliente_fornecedor.listar'))
    
    return render_template('cliente_fornecedor/form.html', 
                          cliente_form=cliente_form,
                          fornecedor_form=fornecedor_form,
                          titulo='Novo Cliente/Fornecedor',
                          aba_ativa=aba_ativa)

@cliente_fornecedor_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    cliente_fornecedor = ClienteFornecedor.query.get_or_404(id)
    responsaveis = Responsavel.query.filter_by(cliente_fornecedor_id=id).all()
    
    # Determinar qual aba está ativa
    aba_ativa = request.args.get('aba', 'cliente' if cliente_fornecedor.eh_cliente else 'fornecedor')
    
    cliente_form = ClienteForm(obj=cliente_fornecedor if cliente_fornecedor.eh_cliente else None)
    fornecedor_form = FornecedorForm(obj=cliente_fornecedor if cliente_fornecedor.eh_fornecedor else None)
    
    if request.method == 'POST':
        if 'submit_cliente' in request.form and cliente_form.validate_on_submit():
            cliente_form.populate_obj(cliente_fornecedor)
            cliente_fornecedor.eh_cliente = True
            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('cliente_fornecedor.listar'))
        
        elif 'submit_fornecedor' in request.form and fornecedor_form.validate_on_submit():
            # Determinar o nome do fornecedor (razão social, nome fantasia ou nome)
            nome = fornecedor_form.nome.data
            if fornecedor_form.razao_social.data:
                nome = fornecedor_form.razao_social.data
            elif fornecedor_form.nome_fantasia.data:
                nome = fornecedor_form.nome_fantasia.data
            
            fornecedor_form.populate_obj(cliente_fornecedor)
            cliente_fornecedor.nome = nome
            cliente_fornecedor.eh_fornecedor = True
            db.session.commit()
            flash('Fornecedor atualizado com sucesso!', 'success')
            return redirect(url_for('cliente_fornecedor.editar', id=cliente_fornecedor.id, aba='fornecedor'))
    
    return render_template('cliente_fornecedor/form.html', 
                          cliente_form=cliente_form,
                          fornecedor_form=fornecedor_form,
                          titulo='Editar Cliente/Fornecedor',
                          aba_ativa=aba_ativa,
                          cliente_fornecedor=cliente_fornecedor,
                          responsaveis=responsaveis)

@cliente_fornecedor_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    cliente_fornecedor = ClienteFornecedor.query.get_or_404(id)
    
    # Verificar se há produtos vinculados (se for fornecedor)
    if cliente_fornecedor.eh_fornecedor and cliente_fornecedor.produtos_fornecidos:
        flash(f'Não é possível excluir. Existem {len(cliente_fornecedor.produtos_fornecidos)} produtos vinculados a este fornecedor.', 'danger')
        return redirect(url_for('cliente_fornecedor.listar'))
    
    # Excluir responsáveis vinculados
    Responsavel.query.filter_by(cliente_fornecedor_id=id).delete()
    
    db.session.delete(cliente_fornecedor)
    db.session.commit()
    
    if cliente_fornecedor.eh_cliente:
        flash('Cliente excluído com sucesso!', 'success')
    else:
        flash('Fornecedor excluído com sucesso!', 'success')
    
    return redirect(url_for('cliente_fornecedor.listar'))

@cliente_fornecedor_bp.route('/responsaveis/adicionar', methods=['POST'])
def adicionar_responsavel():
    try:
        fornecedor_id = request.form.get('fornecedor_id', type=int)
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        
        if not fornecedor_id or not nome or not email or not telefone:
            return jsonify({'success': False, 'message': 'Dados incompletos'})
        
        responsavel = Responsavel(
            cliente_fornecedor_id=fornecedor_id,
            nome=nome,
            email=email,
            telefone=telefone
        )
        db.session.add(responsavel)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': responsavel.id,
            'nome': responsavel.nome,
            'email': responsavel.email,
            'telefone': responsavel.telefone
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@cliente_fornecedor_bp.route('/responsaveis/<int:id>/excluir', methods=['POST'])
def excluir_responsavel(id):
    try:
        responsavel = Responsavel.query.get_or_404(id)
        db.session.delete(responsavel)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
