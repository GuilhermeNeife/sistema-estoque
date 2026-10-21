from src.models import db
from datetime import datetime

# Tabela de relacionamento entre ProdutoVariacao e AtributoValor
produto_variacao_atributo_valor = db.Table('produto_variacao_atributo_valor',
    db.Column('produto_variacao_id', db.Integer, db.ForeignKey('produto_variacao.id'), primary_key=True),
    db.Column('atributo_valor_id', db.Integer, db.ForeignKey('atributo_valor.id'), primary_key=True)
)

class Produto(db.Model):
    __tablename__ = 'produto'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    sku_base = db.Column(db.String(50), nullable=True, unique=True)
    isbn = db.Column(db.String(20), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('cliente_fornecedor.id'), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    variacoes = db.relationship('ProdutoVariacao', backref='produto', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
    
    def estoque_baixo(self):
        """Verifica se alguma variação do produto está com estoque baixo"""
        for variacao in self.variacoes:
            if variacao.estoque_baixo():
                return True
        return False

    def estoque_total(self):
        """Calcula o estoque total somando todas as variações"""
        return sum(variacao.quantidade_atual for variacao in self.variacoes)
    
    def tem_variacao_padrao(self):
        """Verifica se o produto já tem uma variação padrão"""
        for variacao in self.variacoes:
            if variacao.eh_padrao:
                return True
        return False
    
    def get_variacao_padrao(self):
        """Retorna a variação padrão do produto, se existir"""
        for variacao in self.variacoes:
            if variacao.eh_padrao:
                return variacao
        return None
    
    def criar_variacao_padrao(self, preco_venda=0, estoque_minimo=5):
        """Cria uma variação padrão para o produto sem variações"""
        if self.tem_variacao_padrao():
            return self.get_variacao_padrao()
        
        # Gerar SKU para variação padrão
        sku = f"{self.sku_base or f'PROD{self.id}'}-PADRAO"
        
        # Criar variação padrão
        variacao = ProdutoVariacao(
            produto_id=self.id,
            nome=self.nome,
            sku=sku,
            preco_venda=preco_venda,
            estoque_minimo=estoque_minimo,
            eh_padrao=True
        )
        
        db.session.add(variacao)
        db.session.commit()
        
        return variacao

class ProdutoVariacao(db.Model):
    __tablename__ = 'produto_variacao'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), nullable=False, unique=True)
    preco_venda = db.Column(db.Float, nullable=False)
    quantidade_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=5)
    eh_padrao = db.Column(db.Boolean, default=False)  # Novo campo para identificar variação padrão
    
    # Relacionamentos
    atributos_valores = db.relationship('AtributoValor', secondary=produto_variacao_atributo_valor, 
                                       backref=db.backref('variacoes', lazy=True))
    entradas = db.relationship('EntradaEstoque', backref='variacao', lazy=True)
    saidas = db.relationship('SaidaEstoque', backref='variacao', lazy=True)
    
    def __repr__(self):
        return f'<ProdutoVariacao {self.nome} - {self.sku}>'
    
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo"""
        return self.quantidade_atual < self.estoque_minimo

class Atributo(db.Model):
    __tablename__ = 'atributo'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    valores = db.relationship('AtributoValor', backref='atributo', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Atributo {self.nome}>'

class AtributoValor(db.Model):
    __tablename__ = 'atributo_valor'
    
    id = db.Column(db.Integer, primary_key=True)
    atributo_id = db.Column(db.Integer, db.ForeignKey('atributo.id'), nullable=False)
    valor = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<AtributoValor {self.valor}>'
