# Guia de Configuração - Minami Service

Este guia explica como configurar o projeto Minami Service do zero, tanto para uso local quanto para deploy no Streamlit Cloud.

## Opção 1: Uso Local (SQLite)

Para uso local, o projeto funciona automaticamente com SQLite sem necessidade de configuração adicional.

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o aplicativo:
```bash
streamlit run app.py
```

O banco de dados SQLite será criado automaticamente na primeira execução.

## Opção 2: Deploy no Streamlit Cloud com Supabase

Para usar Supabase como backend, siga estes passos:

### Passo 1: Criar projeto no Supabase

1. Acesse [https://supabase.com](https://supabase.com)
2. Clique em "New Project"
3. Preencha:
   - Name: `minami-service` (ou outro nome de sua preferência)
   - Database Password: (anote esta senha)
   - Region: Escolha a região mais próxima
4. Clique em "Create new project"
5. Aguarde o projeto ser criado (2-3 minutos)

### Passo 2: Criar tabelas no Supabase

1. No painel do Supabase, clique em **SQL Editor** (ícone de código no menu lateral)
2. Clique em **New Query**
3. Copie todo o conteúdo do arquivo `supabase_schema.sql`
4. Cole no SQL Editor
5. Clique em **Run** (ou pressione Ctrl+Enter)

### Passo 3: Criar funções RPC no Supabase

1. Abra outra nova query no SQL Editor
2. Copie todo o conteúdo do arquivo `supabase_rpc_functions.sql`
3. Cole no SQL Editor
4. Clique em **Run** (ou pressione Ctrl+Enter)

### Passo 4: Obter credenciais do Supabase

1. No painel do Supabase, clique em **Settings** (engrenagem no menu lateral)
2. Clique em **API**
3. Copie:
   - **Project URL** (será usado como SUPABASE_URL)
   - **anon public** key (será usado como SUPABASE_KEY)

### Passo 5: Configurar Streamlit Cloud

1. Acesse [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Clique em "New app"
3. Conecte seu repositório GitHub: `primebudah/Minami-service`
4. Selecione o branch: `main`
5. Em "Advanced settings", clique em "Secrets"
6. Adicione os seguintes secrets:
   ```
   SUPABASE_URL = https://seu-projeto.supabase.co
   SUPABASE_KEY = sua-chave-anon-publica
   OPENAI_API_KEY = sua-chave-openai (opcional, para OCR)
   ```
7. Clique em "Deploy"

### Passo 6: Reiniciar projeto Supabase (importante)

Após criar as funções RPC, é necessário reiniciar o projeto do Supabase para limpar o cache do PostgREST:

1. No painel do Supabase, clique em **Settings** (engrenagem)
2. Clique em **General**
3. Role até encontrar **Restart project**
4. Clique em **Restart project**
5. Confirme clicando em **Restart project** novamente

O reinício levará cerca de 1-2 minutos.

## Estrutura do Projeto

- `app.py` - Aplicação Streamlit principal
- `database.py` - Camada de abstração do banco (auto-detecta SQLite/Supabase)
- `database_supabase.py` - Implementação específica para Supabase
- `supabase_schema.sql` - Script para criar tabelas no Supabase
- `supabase_rpc_functions.sql` - Script para criar funções RPC no Supabase
- `ocr_service.py` - Serviço de OCR usando OpenAI (opcional)
- `requirements.txt` - Dependências Python

## Troubleshooting

### Erro: "Funções RPC não encontradas"
- Execute o arquivo `supabase_rpc_functions.sql` no SQL Editor
- Reinicie o projeto no Supabase (Settings > General > Restart project)

### Erro: "Could not find the table 'public.clientes'"
- Execute o arquivo `supabase_schema.sql` no SQL Editor
- Verifique se as tabelas foram criadas no Table Editor do Supabase

### Erro: "ModuleNotFoundError: No module named 'openai'"
- O OCR é opcional. Se não usar, o erro não afeta o funcionamento
- Para usar OCR, adicione `OPENAI_API_KEY` nos secrets do Streamlit Cloud

## Suporte

Para problemas, verifique os logs no Streamlit Cloud ou execute localmente para debugar.
