from flask import Blueprint

home_bp = Blueprint('home', __name__)
categoria_bp = Blueprint('categoria', __name__, url_prefix='/categorias')
cliente_fornecedor_bp = Blueprint('cliente_fornecedor', __name__, url_prefix='/clientes-fornecedores')
produto_bp = Blueprint('produto', __name__, url_prefix='/produtos')
estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')
relatorio_bp = Blueprint('relatorio', __name__, url_prefix='/relatorios')
