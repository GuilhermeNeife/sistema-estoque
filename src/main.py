import os
import sys
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Configuração do caminho para importações
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importação dos modelos
from src.models import db
from src.models.categoria import Categoria
from src.models.cliente_fornecedor import ClienteFornecedor, Responsavel, Contato
from src.models.produto import Produto, ProdutoVariacao, Atributo, AtributoValor
from src.models.estoque import EntradaEstoque, SaidaEstoque

# Função para criar a aplicação Flask
def create_app():
    app = Flask(__name__)
    
    # Garantir que a pasta instance exista
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    try:
        if not os.path.exists(instance_path):
            os.makedirs(instance_path, exist_ok=True)
    except Exception as e:
        print(f"Aviso: Não foi possível criar o diretório instance: {str(e)}")
        # Fallback para o diretório atual se não conseguir criar a pasta instance
        instance_path = os.path.dirname(os.path.dirname(__file__))
    
    # Configuração do banco de dados com caminho absoluto e compatível com Windows/Linux
    db_path = os.path.abspath(os.path.join(instance_path, 'estoque_pimentamix.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'estoque_pimentamix_secret_key'
    
    # Inicialização do banco de dados
    db.init_app(app)
    
    # Registro dos blueprints
    from src.routes.home import home_bp
    from src.routes.categoria import categoria_bp
    from src.routes.cliente_fornecedor import cliente_fornecedor_bp
    from src.routes.produto import produto_bp
    from src.routes.estoque import estoque_bp
    from src.routes.relatorio import relatorio_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(cliente_fornecedor_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(relatorio_bp)
    
    # Criação das tabelas do banco de dados
    with app.app_context():
        try:
            db.create_all()
            print(f"Banco de dados criado com sucesso em: {db_path}")
        except Exception as e:
            print(f"Erro ao criar banco de dados: {str(e)}")
            print(f"Verifique se a pasta {instance_path} existe e tem permissões de escrita.")
            
            # Tentativa alternativa com caminho relativo se o absoluto falhar
            try:
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoque_pimentamix.db'
                db.init_app(app)
                db.create_all()
                print("Banco de dados criado com caminho relativo como fallback")
            except Exception as e2:
                print(f"Erro na tentativa alternativa: {str(e2)}")
    
    # Context processor para injetar variáveis em todos os templates
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now().year,
            'app_name': 'Estoque PimentaMix'
        }
    
    # Rota para API de dashboard
    @app.route('/api/dashboard/contadores')
    def api_dashboard_contadores():
        total_produtos = Produto.query.count()
        total_clientes = ClienteFornecedor.query.filter_by(eh_cliente=True).count()
        total_fornecedores = ClienteFornecedor.query.filter_by(eh_fornecedor=True).count()
        
        # Contar produtos com estoque baixo
        total_estoque_baixo = 0
        for produto in Produto.query.all():
            if produto.estoque_baixo():
                total_estoque_baixo += 1
        
        return jsonify({
            'total_produtos': total_produtos,
            'total_clientes': total_clientes,
            'total_fornecedores': total_fornecedores,
            'total_estoque_baixo': total_estoque_baixo
        })
    
    @app.route('/api/dashboard/estoque-baixo')
    def api_dashboard_estoque_baixo():
        produtos_estoque_baixo = []
        
        for produto in Produto.query.all():
            for variacao in produto.variacoes:
                if variacao.estoque_baixo():
                    produtos_estoque_baixo.append({
                        'produto_id': produto.id,
                        'produto_nome': produto.nome,
                        'variacao_id': variacao.id,
                        'variacao_nome': variacao.nome,
                        'sku': variacao.sku,
                        'quantidade_atual': variacao.quantidade_atual,
                        'estoque_minimo': variacao.estoque_minimo
                    })
        
        # Limitar a 5 produtos para o dashboard
        return jsonify({
            'produtos': produtos_estoque_baixo[:5],
            'total': len(produtos_estoque_baixo)
        })
    
    @app.route('/api/dashboard/ultimas-entradas')
    def api_dashboard_ultimas_entradas():
        entradas = EntradaEstoque.query.order_by(EntradaEstoque.data.desc()).limit(5).all()
        
        entradas_json = []
        for entrada in entradas:
            entradas_json.append({
                'id': entrada.id,
                'data': entrada.data.strftime('%d/%m/%Y'),
                'produto': entrada.variacao.produto.nome,
                'variacao': entrada.variacao.nome,
                'quantidade': entrada.quantidade,
                'fornecedor': entrada.fornecedor.nome if entrada.fornecedor else '-'
            })
        
        return jsonify({
            'entradas': entradas_json
        })
    
    @app.route('/api/dashboard/ultimas-saidas')
    def api_dashboard_ultimas_saidas():
        saidas = SaidaEstoque.query.order_by(SaidaEstoque.data.desc()).limit(5).all()
        
        saidas_json = []
        for saida in saidas:
            saidas_json.append({
                'id': saida.id,
                'data': saida.data.strftime('%d/%m/%Y'),
                'produto': saida.variacao.produto.nome,
                'variacao': saida.variacao.nome,
                'quantidade': saida.quantidade,
                'cliente': saida.cliente.nome if saida.cliente else '-'
            })
        
        return jsonify({
            'saidas': saidas_json
        })
    
    # Tratamento de erros
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    return app
