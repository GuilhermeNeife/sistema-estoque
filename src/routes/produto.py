from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from src.models import db
from src.models.produto import Produto, ProdutoVariacao, Atributo, AtributoValor
from src.models.categoria import Categoria
from src.models.cliente_fornecedor import ClienteFornecedor # Import ClienteFornecedor
from datetime import datetime
import json
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional # Import Optional

produto_bp = Blueprint("produto", __name__, url_prefix="/produtos")

@produto_bp.route("/")
def listar():
    produtos = Produto.query.all()
    return render_template("produto/listar.html", produtos=produtos, titulo="Produtos")

# --- Formulário de Produto Base ---
class ProdutoForm(FlaskForm):
    id = HiddenField("ID")
    nome = StringField("Nome", validators=[DataRequired(), Length(min=3, max=100)])
    sku_base = StringField("SKU Base", validators=[Optional(), Length(max=50)]) # Adicionado SKU Base
    isbn = StringField("ISBN", validators=[Optional(), Length(max=20)]) # Adicionado ISBN
    descricao = TextAreaField("Descrição")
    categoria_id = SelectField("Categoria", coerce=int, validators=[DataRequired()])
    fornecedor_id = SelectField("Fornecedor Principal", coerce=int, validators=[Optional()]) # Tornar opcional
    submit = SubmitField("Salvar")

# --- Funções Auxiliares --- 
def carregar_opcoes_form(form):
    """Carrega as opções de Categoria e Fornecedor para o formulário."""
    categorias = Categoria.query.order_by(Categoria.nome).all()
    form.categoria_id.choices = [(c.id, c.nome) for c in categorias]
    
    fornecedores = ClienteFornecedor.query.filter_by(eh_fornecedor=True).order_by(ClienteFornecedor.nome).all()
    form.fornecedor_id.choices = [(0, "Selecione...")] + [(f.id, f.nome) for f in fornecedores]

# --- Rotas CRUD Produto --- 
@produto_bp.route("/novo", methods=["GET", "POST"])
def novo():
    form = ProdutoForm()
    carregar_opcoes_form(form)
    
    if form.validate_on_submit():
        # Verificar unicidade do SKU Base
        if form.sku_base.data:
            existing_sku = Produto.query.filter_by(sku_base=form.sku_base.data).first()
            if existing_sku:
                flash("Erro: SKU Base já existe.", "danger")
                # Passar produto=None aqui também em caso de erro
                return render_template("produto/form.html", form=form, titulo="Novo Produto", produto=None)

        produto = Produto(
            nome=form.nome.data,
            sku_base=form.sku_base.data if form.sku_base.data else None,
            isbn=form.isbn.data if form.isbn.data else None,
            descricao=form.descricao.data,
            categoria_id=form.categoria_id.data,
            fornecedor_id=form.fornecedor_id.data if form.fornecedor_id.data and form.fornecedor_id.data != 0 else None
        )
        
        db.session.add(produto)
        db.session.commit()
        
        flash("Produto cadastrado com sucesso! Agora você pode adicionar variações.", "success")
        return redirect(url_for("produto.editar", id=produto.id))
    
    # Corrigido: Passar produto=None ao renderizar o formulário de novo produto
    return render_template("produto/form.html", form=form, titulo="Novo Produto", produto=None)

@produto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    carregar_opcoes_form(form)
    
    if form.validate_on_submit():
        # Verificar unicidade do SKU Base (excluindo o próprio produto)
        if form.sku_base.data:
            existing_sku = Produto.query.filter(Produto.id != id, Produto.sku_base == form.sku_base.data).first()
            if existing_sku:
                flash("Erro: SKU Base já existe em outro produto.", "danger")
                atributos = Atributo.query.all()
                variacoes = ProdutoVariacao.query.filter_by(produto_id=id).all()
                return render_template("produto/form.html", form=form, produto=produto, 
                                      atributos=atributos, variacoes=variacoes, titulo="Editar Produto")

        produto.nome = form.nome.data
        produto.sku_base = form.sku_base.data if form.sku_base.data else None
        produto.isbn = form.isbn.data if form.isbn.data else None
        produto.descricao = form.descricao.data
        produto.categoria_id = form.categoria_id.data
        produto.fornecedor_id = form.fornecedor_id.data if form.fornecedor_id.data and form.fornecedor_id.data != 0 else None
        
        db.session.commit()
        
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("produto.listar"))
    
    # Carregar atributos para a aba de variações
    atributos = Atributo.query.all()
    variacoes = ProdutoVariacao.query.filter_by(produto_id=id).all()
    
    return render_template("produto/form.html", form=form, produto=produto, 
                          atributos=atributos, variacoes=variacoes, titulo="Editar Produto")

@produto_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    produto = Produto.query.get_or_404(id)
    
    try:
        # Verificar se há variações com estoque
        for variacao in produto.variacoes:
            if variacao.quantidade_atual > 0:
                flash(f"Erro: Não é possível excluir o produto pois a variação ", "danger")
                return redirect(url_for("produto.listar"))
        
        db.session.delete(produto)
        db.session.commit()
        flash("Produto excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir produto: {str(e)}", "danger")
    
    return redirect(url_for("produto.listar"))

@produto_bp.route("/detalhes/<int:id>")
def detalhes(id):
    produto = Produto.query.get_or_404(id)
    return render_template("produto/detalhes.html", produto=produto, titulo=f"Detalhes do Produto: {produto.nome}")

# --- Rotas para Variações (SKUs Filhos) --- 
@produto_bp.route("/variacao/atualizar/<int:id>", methods=["POST"])
def atualizar_variacao(id):
    variacao = ProdutoVariacao.query.get_or_404(id)
    
    try:
        # SKU não é mais atualizado aqui, pois é gerado automaticamente
        # novo_sku = request.form.get("sku")
        # Verificar unicidade do SKU da variação (excluindo a própria variação)
        # existing_sku = ProdutoVariacao.query.filter(ProdutoVariacao.id != id, ProdutoVariacao.sku == novo_sku).first()
        # if existing_sku:
        #     return jsonify({
        #         "success": False,
        #         "message": f"Erro: O SKU ",
        #     })

        # variacao.sku = novo_sku 
        # O nome da variação também é gerado automaticamente e não deve ser editado aqui
        # variacao.nome = request.form.get("nome") 
        variacao.preco_venda = float(request.form.get("preco_venda"))
        variacao.estoque_minimo = int(request.form.get("estoque_minimo"))
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Variação atualizada com sucesso!"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })

@produto_bp.route("/variacao/excluir/<int:id>", methods=["POST"])
def excluir_variacao(id):
    variacao = ProdutoVariacao.query.get_or_404(id)
    
    try:
        if variacao.quantidade_atual > 0:
             return jsonify({
                "success": False,
                "message": f"Erro: Não é possível excluir a variação ",
            })

        # Remover associações de atributos antes de excluir
        variacao.atributos_valores = []
        db.session.commit()

        db.session.delete(variacao)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Variação excluída com sucesso!"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })

@produto_bp.route("/variacao/gerar/<int:id>", methods=["POST"])
def gerar_variacoes(id):
    produto = Produto.query.get_or_404(id)
    
    try:
        data = request.json
        prefixo_sku = data.get("prefixo_sku", produto.sku_base or f"PROD{produto.id}") # Usa SKU base ou um padrão
        # Tornar preço e estoque opcionais, usando 0 como valor padrão
        preco_padrao = float(data.get("preco_padrao", 0))
        estoque_minimo_padrao = int(data.get("estoque_minimo_padrao", 0))
        combinacoes = data.get("combinacoes")
        
        variacoes_criadas = 0
        skus_existentes = []

        for combinacao in combinacoes:
            # Criar nome da variação
            nome_variacao = produto.nome + " - " + ", ".join([f"{combinacao[i]['atributoNome']}: {combinacao[i]['valor']}" for i in range(len(combinacao))])
            
            # Criar SKU (usando prefixo + valores)
            # Ordenar valores por atributo_id para garantir consistência do SKU
            combinacao_ordenada = sorted(combinacao, key=lambda x: x["atributoId"])
            sufixo_sku = "-".join([item["valor"].replace(" ", "").upper() for item in combinacao_ordenada])
            sku = f"{prefixo_sku}-{sufixo_sku}"
            
            # Verificar se já existe variação com este SKU para este produto
            variacao_existente = ProdutoVariacao.query.filter_by(produto_id=produto.id, sku=sku).first()
            if variacao_existente:
                skus_existentes.append(sku)
                continue
            
            # Criar variação
            variacao = ProdutoVariacao(
                produto_id=produto.id,
                nome=nome_variacao,
                sku=sku,
                preco_venda=preco_padrao,
                estoque_minimo=estoque_minimo_padrao
            )
            
            db.session.add(variacao)
            db.session.flush()  # Para obter o ID da variação
            
            # Adicionar valores de atributos à variação
            for item in combinacao:
                valor = AtributoValor.query.get(item["valorId"])
                if valor:
                    variacao.atributos_valores.append(valor)
            
            variacoes_criadas += 1
        
        db.session.commit()
        
        mensagem = f"{variacoes_criadas} variações geradas com sucesso!"
        if skus_existentes:
            mensagem += f" SKUs já existentes ignorados: {', '.join(skus_existentes)}."
        
        return jsonify({
            "success": True,
            "message": mensagem
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })

# --- Rotas para Categorias (Gerenciamento Rápido) ---
@produto_bp.route("/categorias") # Rota principal movida para categoria.py
def listar_categorias():
     return redirect(url_for("categoria.listar")) # Redireciona para o blueprint correto

@produto_bp.route("/categorias/nova", methods=["GET", "POST"])
def nova_categoria():
    # Esta rota agora serve apenas para o modal/popup de cadastro rápido
    from src.routes.categoria import CategoriaForm # Reutiliza o form de categoria
    form = CategoriaForm()

    if request.method == "POST" and form.validate_on_submit():
        try:
            categoria = Categoria(
                nome=form.nome.data,
                descricao=form.descricao.data
            )
            db.session.add(categoria)
            db.session.commit()
            # Retorna dados da nova categoria para atualizar o select no formulário principal
            return jsonify({"success": True, "id": categoria.id, "nome": categoria.nome})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)})
    
    # Se GET, retorna o HTML do formulário para ser carregado no modal
    return render_template("produto/categorias/form_modal.html", form=form, titulo="Nova Categoria")

# Rota para cadastro rápido de fornecedor (similar à de categoria)
@produto_bp.route("/fornecedores/nova_modal", methods=["GET", "POST"])
def novo_fornecedor_modal():
    from src.routes.cliente_fornecedor import FornecedorForm # Reutiliza o form
    form = FornecedorForm()
    # Remover validadores não essenciais para cadastro rápido?
    form.razao_social.validators = [Optional()]
    form.nome_fantasia.validators = [Optional()]
    form.endereco.validators = [Optional()]
    form.observacoes.validators = [Optional()]

    if request.method == "POST" and form.validate_on_submit():
        try:
            # Determinar o nome do fornecedor
            nome = form.nome.data
            if form.razao_social.data:
                nome = form.razao_social.data
            elif form.nome_fantasia.data:
                nome = form.nome_fantasia.data
            if not nome: # Se nenhum foi preenchido, usa o CPF/CNPJ como fallback
                 nome = form.cpf_cnpj.data

            fornecedor = ClienteFornecedor(
                nome=nome,
                razao_social=form.razao_social.data,
                nome_fantasia=form.nome_fantasia.data,
                cpf_cnpj=form.cpf_cnpj.data,
                email=form.email.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                observacoes=form.observacoes.data,
                eh_cliente=False,
                eh_fornecedor=True
            )
            db.session.add(fornecedor)
            db.session.commit()
            return jsonify({"success": True, "id": fornecedor.id, "nome": fornecedor.nome})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)})

    # Se GET, retorna o HTML do formulário para ser carregado no modal
    return render_template("produto/fornecedor/form_modal.html", form=form, titulo="Novo Fornecedor")


# --- Rotas para Atributos --- 
@produto_bp.route("/atributos")
def listar_atributos():
    atributos = Atributo.query.order_by(Atributo.nome).all()
    return render_template("produto/atributos/listar.html", atributos=atributos, titulo="Atributos")

@produto_bp.route("/atributos/novo", methods=["GET", "POST"])
def novo_atributo():
    from flask_wtf import FlaskForm # Mover imports para dentro para evitar ciclos
    from wtforms import StringField, TextAreaField, SubmitField
    from wtforms.validators import DataRequired, Length
    
    class AtributoForm(FlaskForm):
        nome = StringField("Nome", validators=[DataRequired(), Length(min=2, max=50)])
        descricao = TextAreaField("Descrição")
        submit = SubmitField("Salvar")
    
    form = AtributoForm()
    
    if form.validate_on_submit():
        # Verificar unicidade
        if Atributo.query.filter_by(nome=form.nome.data).first():
            flash(f"Erro: Atributo ", "danger")
        else:
            atributo = Atributo(
                nome=form.nome.data,
                descricao=form.descricao.data
            )
            db.session.add(atributo)
            db.session.commit()
            flash("Atributo cadastrado com sucesso!", "success")
            return redirect(url_for("produto.listar_atributos"))
    
    return render_template("produto/atributos/form.html", form=form, titulo="Novo Atributo")

@produto_bp.route("/atributos/editar/<int:id>", methods=["GET", "POST"])
def editar_atributo(id):
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, SubmitField
    from wtforms.validators import DataRequired, Length
    
    class AtributoForm(FlaskForm):
        nome = StringField("Nome", validators=[DataRequired(), Length(min=2, max=50)])
        descricao = TextAreaField("Descrição")
        submit = SubmitField("Salvar")
    
    atributo = Atributo.query.get_or_404(id)
    form = AtributoForm(obj=atributo)
    
    if form.validate_on_submit():
        # Verificar unicidade (excluindo o próprio atributo)
        existing = Atributo.query.filter(Atributo.id != id, Atributo.nome == form.nome.data).first()
        if existing:
            flash(f"Erro: Atributo ", "danger")
        else:
            atributo.nome = form.nome.data
            atributo.descricao = form.descricao.data
            db.session.commit()
            flash("Atributo atualizado com sucesso!", "success")
            return redirect(url_for("produto.listar_atributos"))
    
    return render_template("produto/atributos/form.html", form=form, titulo="Editar Atributo")

@produto_bp.route("/atributos/excluir/<int:id>", methods=["POST"])
def excluir_atributo(id):
    atributo = Atributo.query.get_or_404(id)
    
    try:
        # Verificar se há valores associados
        if atributo.valores:
            flash(f"Erro: Não é possível excluir o atributo ", "danger")
            return redirect(url_for("produto.listar_atributos"))
        
        db.session.delete(atributo)
        db.session.commit()
        flash("Atributo excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir atributo: {str(e)}", "danger")
    
    return redirect(url_for("produto.listar_atributos"))

# --- Rotas para Valores de Atributos (CORRIGIDO) --- 
# Rota para adicionar valor diretamente na listagem de atributos
@produto_bp.route("/atributos/<int:atributo_id>/valor/novo", methods=["POST"])
def novo_valor_atributo(atributo_id):
    atributo = Atributo.query.get_or_404(atributo_id)
    valor_texto = request.form.get("valor")
    
    # Verificar se o valor já existe para este atributo
    valor_existente = AtributoValor.query.filter_by(atributo_id=atributo_id, valor=valor_texto).first()
    
    if valor_existente:
        if request.args.get("source") == "modal":
            return jsonify({
                "success": False,
                "message": f"Valor '{valor_texto}' já existe para este atributo."
            })
        flash(f"Erro: Valor '{valor_texto}' já existe para este atributo.", "danger")
        return redirect(url_for("produto.listar_atributos"))
    
    try:
        novo_valor = AtributoValor(
            atributo_id=atributo_id,
            valor=valor_texto
        )
        db.session.add(novo_valor)
        db.session.commit()
        
        if request.args.get("source") == "modal":
            return jsonify({
                "success": True,
                "id": novo_valor.id,
                "valor": novo_valor.valor,
                "message": "Valor adicionado com sucesso!"
            })
        
        flash("Valor adicionado com sucesso!", "success")
        return redirect(url_for("produto.listar_atributos"))
    
    except Exception as e:
        db.session.rollback()
        if request.args.get("source") == "modal":
            return jsonify({
                "success": False,
                "message": str(e)
            })
        flash(f"Erro ao adicionar valor: {str(e)}", "danger")
        return redirect(url_for("produto.listar_atributos"))

# Rota para excluir valor diretamente da listagem de atributos
@produto_bp.route("/atributos/valor/<int:id>/excluir", methods=["POST"])
def excluir_valor_atributo(id):
    valor = AtributoValor.query.get_or_404(id)
    atributo_id = valor.atributo_id
    
    # Verificar se o valor está sendo usado em alguma variação
    if valor.variacoes:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "message": "Este valor está sendo usado em variações de produtos e não pode ser excluído."
            })
        flash("Este valor está sendo usado em variações de produtos e não pode ser excluído.", "danger")
        return redirect(url_for("produto.listar_atributos"))
    
    try:
        db.session.delete(valor)
        db.session.commit()
        
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": True,
                "message": "Valor excluído com sucesso!"
            })
        
        flash("Valor excluído com sucesso!", "success")
        return redirect(url_for("produto.listar_atributos"))
    
    except Exception as e:
        db.session.rollback()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "message": str(e)
            })
        flash(f"Erro ao excluir valor: {str(e)}", "danger")
        return redirect(url_for("produto.listar_atributos"))

# --- API para Atributos e Valores ---
@produto_bp.route("/api/atributos")
def api_atributos():
    atributos = Atributo.query.all()
    result = []
    
    for atributo in atributos:
        valores = []
        for valor in atributo.valores:
            valores.append({
                "id": valor.id,
                "valor": valor.valor
            })
        
        result.append({
            "id": atributo.id,
            "nome": atributo.nome,
            "valores": valores
        })
    
    return jsonify(result)

@produto_bp.route("/api/atributos/<int:id>/valores")
def api_valores_atributo(id):
    atributo = Atributo.query.get_or_404(id)
    valores = []
    
    for valor in atributo.valores:
        valores.append({
            "id": valor.id,
            "valor": valor.valor
        })
    
    return jsonify({
        "id": atributo.id,
        "nome": atributo.nome,
        "valores": valores
    })

# --- API para Variações ---
@produto_bp.route("/api/produto/<int:id>/variacoes")
def api_variacoes_produto(id):
    produto = Produto.query.get_or_404(id)
    variacoes = []
    
    for variacao in produto.variacoes:
        atributos_valores = []
        for av in variacao.atributos_valores:
            atributos_valores.append({
                "atributo_id": av.atributo_id,
                "atributo_nome": av.atributo.nome,
                "valor_id": av.id,
                "valor": av.valor
            })
        
        variacoes.append({
            "id": variacao.id,
            "nome": variacao.nome,
            "sku": variacao.sku,
            "preco_venda": variacao.preco_venda,
            "quantidade_atual": variacao.quantidade_atual,
            "estoque_minimo": variacao.estoque_minimo,
            "atributos_valores": atributos_valores
        })
    
    return jsonify({
        "id": produto.id,
        "nome": produto.nome,
        "variacoes": variacoes
    })
