from src.models import db
from datetime import datetime

class Categoria(db.Model):
    __tablename__ = 'categoria'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    produtos = db.relationship('Produto', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'
