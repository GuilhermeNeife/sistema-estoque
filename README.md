# Sistema de Controle de Estoque - Documentação

## Visão Geral

Este sistema foi desenvolvido para gerenciar o controle de estoque, clientes, fornecedores e produtos de forma completa e integrada. Utilizando Flask como framework web e SQLite como banco de dados, o sistema oferece uma interface simples e funcional para todas as operações necessárias.

## Funcionalidades Principais

### Cadastro de Produtos
- Cadastro de produtos com nome, descrição e categoria
- Suporte a múltiplas variações de produto (cor, tamanho, etc.)
- Cada variação possui SKU único
- Preço de venda fixo no cadastro do produto
- Preço de custo registrado no momento da entrada do produto

### Cadastro de Clientes/Fornecedores
- Cadastro unificado (uma entidade pode ser cliente, fornecedor ou ambos)
- Dados básicos: nome, CPF/CNPJ (opcional), endereço
- Múltiplos contatos: emails e telefones
- Múltiplos responsáveis pela comunicação

### Cadastro de Categorias
- Organização de produtos por categorias
- Cadastro simples com nome e descrição

### Controle de Estoque
- Registro de entradas (compras): quantidade, data, preço de custo, fornecedor
- Registro de saídas (vendas/uso): quantidade, data, cliente, motivo/observação
- Atualização automática do estoque para cada variação de produto
- Alertas visuais quando o estoque está abaixo do limite mínimo configurado

### Relatórios
- Estoque atual por produto e variação
- Entradas e saídas em período selecionado
- Produtos com estoque baixo
- Lista de clientes/fornecedores

## Requisitos Técnicos

- Python 3.6+
- Flask
- SQLite
- Navegador web moderno

## Instalação e Execução

1. Clone ou baixe este repositório
2. Crie um ambiente virtual Python:
   ```
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
5. Execute a aplicação:
   ```
   python app.py
   ```
6. Acesse no navegador: `http://localhost:5000`

## Estrutura do Projeto

```
sistema_estoque/
├── app.py                  # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── instance/               # Banco de dados SQLite (criado automaticamente)
└── src/
    ├── main.py             # Configuração principal do Flask
    ├── models/             # Modelos de dados
    │   ├── __init__.py
    │   ├── categoria.py
    │   ├── cliente_fornecedor.py
    │   ├── estoque.py
    │   └── produto.py
    ├── routes/             # Rotas e controladores
    │   ├── __init__.py
    │   ├── categoria.py
    │   ├── cliente_fornecedor.py
    │   ├── estoque.py
    │   ├── home.py
    │   ├── produto.py
    │   └── relatorio.py
    ├── static/             # Arquivos estáticos (CSS, JS, imagens)
    │   └── css/
    │       └── style.css
    ├── templates/          # Templates HTML
    │   ├── base.html
    │   ├── categoria/
    │   ├── cliente_fornecedor/
    │   ├── estoque/
    │   ├── home/
    │   ├── produto/
    │   └── relatorio/
    └── utils/              # Utilitários e funções auxiliares
```

## Uso do Sistema

### Dashboard
A página inicial apresenta um resumo do sistema, incluindo:
- Totais de produtos, categorias, clientes e fornecedores
- Alertas de produtos com estoque baixo
- Últimas entradas e saídas de estoque

### Cadastros
Acesse os cadastros através do menu superior:
- Categorias: Cadastre categorias para organizar seus produtos
- Produtos: Cadastre produtos e suas variações
- Clientes/Fornecedores: Cadastre clientes, fornecedores ou ambos

### Controle de Estoque
- Entradas: Registre compras de produtos
- Saídas: Registre vendas ou outras saídas
- Visão Geral: Visualize o status atual do estoque

### Relatórios
- Estoque Atual: Visualize o estoque atual de todos os produtos
- Estoque Baixo: Visualize produtos com estoque abaixo do mínimo
- Movimentações: Visualize entradas e saídas por período
- Clientes/Fornecedores: Lista completa de clientes e fornecedores

## Futuras Melhorias

O sistema foi projetado para facilitar futuras melhorias, como:
- Autenticação de usuários e controle de acesso
- Geração de PDF para relatórios
- Integração com sistemas de vendas
- Dashboard com gráficos e estatísticas avançadas
- Controle financeiro integrado

## Suporte

Para suporte ou dúvidas sobre o sistema, entre em contato com o desenvolvedor.
