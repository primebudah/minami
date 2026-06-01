# Deploy Minami Service - Streamlit Cloud + Supabase

Arquitetura recomendada:
- **Streamlit Cloud**: Hospeda a interface web
- **Supabase**: Banco PostgreSQL persistente

---

## Parte 1: Supabase (Banco de dados)

### 1.1 Criar conta e projeto
1. Acesse https://supabase.com → Sign up (pode usar GitHub)
2. New Project → Organization: padrão
3. Project name: `minami-service`
4. Database Password: gere uma senha forte (salve!)
5. Region: `Northeast Asia (Tokyo)` (mais próximo)
6. Click "Create new project" (demora ~2 min)

### 1.2 Criar tabelas
No projeto Supabase:
1. Menu lateral → SQL Editor
2. New query
3. Cole o SQL abaixo e execute (Run):

```sql
-- Tabela de clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    contato TEXT,
    shaken_vencimento DATE,
    veiculo TEXT,
    placa TEXT,
    chassi TEXT UNIQUE,
    data_registro DATE,
    data_conclusao DATE,
    status TEXT DEFAULT 'Pendente',
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela de historico (undo)
CREATE TABLE historico_acoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    acao TEXT,
    dados_anteriores JSONB,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Indices para performance
CREATE INDEX idx_chassi ON clientes(chassi);
CREATE INDEX idx_status ON clientes(status);
CREATE INDEX idx_nome ON clientes(nome);
```

### 1.3 Copiar credenciais
Settings → API:
- `Project URL`: copie (ex: `https://xxxx.supabase.co`)
- `Project API keys` → `anon public`: copie a chave

Guarde esses 2 valores para o próximo passo!

---

## Parte 2: Streamlit Cloud (Interface)

### 2.1 Preparar código local
```bash
# Na pasta do projeto
git add .
git commit -m "Preparando para deploy"
```

### 2.2 Criar repositório GitHub
1. github.com/new
2. Repository name: `minami-service`
3. Private (recomendado)
4. Create repository
5. Siga as instruções para "push an existing repository"

### 2.3 Deploy no Streamlit Cloud
1. Acesse https://share.streamlit.io
2. Continue with GitHub
3. "New app"
4. Deploy an app:
   - Repository: `seu-usuario/minami-service`
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Deploy"

### 2.4 Configurar Secrets
No dashboard do app (Streamlit Cloud):
1. Settings → Secrets
2. Cole no formato TOML:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIs..."

[users]
[users.admin]
password = "sua_senha_aqui"
role = "admin"
nome = "Administrador"
```

3. Save → Reboot app

---

## Parte 3: Testar em dispositivos

### Tablet Redmi
1. Abra Chrome ou navegador padrão
2. Digite a URL do app: `https://minami-service-xxx.streamlit.app`
3. Faça login e teste o registro manual

### iPhone (dono Minami Service)
1. Abra Safari
2. Acesse a mesma URL
3. Adicione à tela inicial (Share → Add to Home Screen)
4. Funciona como "app nativo"

---

## Migrar dados do SQLite (opcional)
Se tem dados no `.db` local:
1. Baixe o arquivo `database_supabase.py`
2. Execute script de migração (veja função `migrar_dados_sqlite`)

---

## Troubleshooting

**Erro "SUPABASE_URL not configured"**
→ Verifique se colocou os secrets no Streamlit Cloud

**Tabela não existe**
→ Execute o SQL no Supabase SQL Editor novamente

**App lento**
→ Verifique se criou os índices no SQL
