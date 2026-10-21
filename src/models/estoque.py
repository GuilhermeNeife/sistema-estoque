from src.models import db
from datetime import datetime

class EntradaEstoque(db.Model):
    __tablename__ = 'entrada_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    variacao_id = db.Column(db.Integer, db.ForeignKey('produto_variacao.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_custo = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('cliente_fornecedor.id'), nullable=True)
    nota_fiscal = db.Column(db.String(50), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<EntradaEstoque {self.id} - {self.quantidade} unidades>'

class SaidaEstoque(db.Model):
    __tablename__ = 'saida_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    variacao_id = db.Column(db.Integer, db.ForeignKey('produto_variacao.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)  # Novo campo
    valor_total = db.Column(db.Float, nullable=False)  # Novo campo
    
    data = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente_fornecedor.id'), nullable=True)
    motivo = db.Column(db.String(100), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SaidaEstoque {self.id} - {self.quantidade} unidades>'
