# Integração Minami Service + Supabase

## 1. Criar projeto Supabase
1. Acesse https://supabase.com
2. Sign up/login
3. New Project → nome: `minami-service`
4. Aguarde provisioning (1-2 min)

## 2. Configurar Database
No SQL Editor, execute:

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

-- Tabela de histórico (undo)
CREATE TABLE historico_acoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    acao TEXT,
    dados_anteriores JSONB,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_chassi ON clientes(chassi);
CREATE INDEX idx_status ON clientes(status);
CREATE INDEX idx_nome ON clientes(nome);
```

## 3. Obter credenciais
Settings > API:
- `SUPABASE_URL`: https://xxxx.supabase.co
- `SUPABASE_KEY`: eyJ...

## 4. Atualizar Streamlit Secrets
No Streamlit Cloud (Deploy > Advanced settings > Secrets):

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "eyJ..."

[users]
[users.admin]
password = "sua_senha"
role = "admin"
nome = "Administrador"
```

## 5. Instalar dependência
Adicionar no `requirements.txt`:
```
supabase>=2.0.0
```

## 6. Atualizar database.py
Substituir SQLite por PostgreSQL via Supabase.

---

## Deploy completo

### Streamlit Cloud (interface)
- Conecta com GitHub
- Usa `app.py` como entrypoint

### Supabase (dados)
- PostgreSQL persistente
- Acessível de qualquer lugar

---

## URLs para teste
Após deploy:
- Tablet/iPhone: `https://minami-service-xxx.streamlit.app`
- Mesma URL funciona em todos dispositivos
