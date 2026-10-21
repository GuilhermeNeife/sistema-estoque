from src.models import db
from datetime import datetime

class ClienteFornecedor(db.Model):
    __tablename__ = 'cliente_fornecedor'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    razao_social = db.Column(db.String(100), nullable=True)
    nome_fantasia = db.Column(db.String(100), nullable=True)
    cpf_cnpj = db.Column(db.String(20), nullable=True, unique=True)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    eh_cliente = db.Column(db.Boolean, default=False)
    eh_fornecedor = db.Column(db.Boolean, default=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    responsaveis = db.relationship('Responsavel', backref='cliente_fornecedor', lazy=True, cascade="all, delete-orphan")
    contatos = db.relationship('Contato', backref='cliente_fornecedor', lazy=True, cascade="all, delete-orphan")
    produtos_fornecidos = db.relationship('Produto', backref='fornecedor', lazy=True)
    entradas_estoque = db.relationship('EntradaEstoque', backref='fornecedor', lazy=True)
    saidas_estoque = db.relationship('SaidaEstoque', backref='cliente', lazy=True)
    
    def __repr__(self):
        return f'<ClienteFornecedor {self.nome}>'

class Responsavel(db.Model):
    __tablename__ = 'responsavel'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_fornecedor_id = db.Column(db.Integer, db.ForeignKey('cliente_fornecedor.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    cargo = db.Column(db.String(50), nullable=True)
    
    def __repr__(self):
        return f'<Responsavel {self.nome}>'

class Contato(db.Model):
    __tablename__ = 'contato'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_fornecedor_id = db.Column(db.Integer, db.ForeignKey('cliente_fornecedor.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # email, telefone, celular, etc.
    valor = db.Column(db.String(100), nullable=False)
    observacao = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<Contato {self.tipo}: {self.valor}>'
