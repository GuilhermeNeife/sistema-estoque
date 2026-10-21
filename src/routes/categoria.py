from flask import Blueprint, render_template, redirect, url_for, request, flash
from src.models.categoria import Categoria
from src.models import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class CategoriaForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar')

categoria_bp = Blueprint('categoria', __name__, url_prefix='/categorias')

@categoria_bp.route('/')
def listar():
    categorias = Categoria.query.all()
    return render_template('categoria/listar.html', categorias=categorias)

@categoria_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    form = CategoriaForm()
    
    if form.validate_on_submit():
        categoria = Categoria(
            nome=form.nome.data,
            descricao=form.descricao.data
        )
        db.session.add(categoria)
        db.session.commit()
        flash('Categoria cadastrada com sucesso!', 'success')
        return redirect(url_for('categoria.listar'))
    
    return render_template('categoria/form.html', form=form, titulo='Nova Categoria')

@categoria_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    categoria = Categoria.query.get_or_404(id)
    form = CategoriaForm(obj=categoria)
    
    if form.validate_on_submit():
        form.populate_obj(categoria)
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('categoria.listar'))
    
    return render_template('categoria/form.html', form=form, titulo='Editar Categoria')

@categoria_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    categoria = Categoria.query.get_or_404(id)
    
    # Verificar se há produtos vinculados
    if categoria.produtos:
        flash(f'Não é possível excluir a categoria. Existem {len(categoria.produtos)} produtos vinculados.', 'danger')
        return redirect(url_for('categoria.listar'))
    
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('categoria.listar'))
