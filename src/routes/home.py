from flask import Blueprint, render_template
from src.models.produto import Produto

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    # Buscar produtos com estoque baixo para exibir alertas na página inicial
    produtos_estoque_baixo = []
    try:
        produtos_estoque_baixo = [p for p in Produto.query.all() if p.estoque_baixo()]
    except Exception as e:
        print(f"Erro ao buscar produtos com estoque baixo: {e}")
    
    return render_template('home/index.html', produtos_estoque_baixo=produtos_estoque_baixo)
