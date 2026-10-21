import os
import sys
import shutil
from datetime import datetime

# Adicionar o diretório atual ao path para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar app e modelos
from app import app
from src.models import db
from src.models.estoque import SaidaEstoque
from src.models.produto import ProdutoVariacao

def criar_backup():
    """Cria um backup do banco de dados atual"""
    # Determinar o caminho do banco de dados
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_path, 'estoque_pimentamix.db')
    
    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em: {db_path}")
        return False
    
    # Criar nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = os.path.join(instance_path, f'estoque_pimentamix_backup_{timestamp}.db')
    
    # Copiar o arquivo
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Backup criado com sucesso em: {backup_path}")
        return True
    except Exception as e:
        print(f"Erro ao criar backup: {str(e)}")
        return False

def executar_migracao():
    """Executa a migração do banco de dados"""
    with app.app_context():
        try:
            # Verificar se as colunas já existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            colunas_existentes = [c['name'] for c in inspector.get_columns('saida_estoque')]
            
            # Adicionar coluna preco_venda se não existir
            if 'preco_venda' not in colunas_existentes:
                print("Adicionando coluna preco_venda à tabela saida_estoque...")
                db.engine.execute('ALTER TABLE saida_estoque ADD COLUMN preco_venda FLOAT DEFAULT 0')
                print("Coluna preco_venda adicionada com sucesso!")
            else:
                print("Coluna preco_venda já existe.")
            
            # Adicionar coluna valor_total se não existir
            if 'valor_total' not in colunas_existentes:
                print("Adicionando coluna valor_total à tabela saida_estoque...")
                db.engine.execute('ALTER TABLE saida_estoque ADD COLUMN valor_total FLOAT DEFAULT 0')
                print("Coluna valor_total adicionada com sucesso!")
            else:
                print("Coluna valor_total já existe.")
            
            # Atualizar registros existentes com valores dos produtos
            print("Atualizando registros existentes...")
            saidas = SaidaEstoque.query.all()
            for saida in saidas:
                variacao = ProdutoVariacao.query.get(saida.variacao_id)
                if variacao:
                    saida.preco_venda = variacao.preco_venda
                    saida.valor_total = saida.quantidade * saida.preco_venda
            
            db.session.commit()
            print("Registros existentes atualizados com sucesso!")
            print("Migração concluída com sucesso!")
            return True
        except Exception as e:
            print(f"Erro durante a migração: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== Script de Migração do Banco de Dados ===")
    print("Este script irá adicionar as colunas preco_venda e valor_total à tabela saida_estoque.")
    
    # Criar backup antes de prosseguir
    if criar_backup():
        print("\nIniciando migração do banco de dados...")
        if executar_migracao():
            print("\nMigração concluída com sucesso!")
            print("Agora você pode executar o app.py normalmente.")
        else:
            print("\nErro durante a migração. Verifique as mensagens acima.")
    else:
        print("\nNão foi possível criar o backup. Migração cancelada por segurança.")
