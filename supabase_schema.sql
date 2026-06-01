-- Schema Minami Service para Supabase
-- Execute no SQL Editor do Supabase

-- Tabela principal de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    contato TEXT,
    shaken_vencimento DATE,
    veiculo TEXT,
    placa TEXT,
    chassi TEXT UNIQUE,
    fabricante TEXT,
    modelo_katashiki TEXT,
    chassi_completo TEXT,
    data_registro DATE,
    data_conclusao DATE,
    status TEXT DEFAULT 'Pendente',
    observacao TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de historico de acoes (undo)
CREATE TABLE IF NOT EXISTS historico_acoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    acao TEXT, -- 'criar', 'atualizar', 'deletar'
    dados_anteriores JSONB,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de historico de exclusoes
CREATE TABLE IF NOT EXISTS historico_exclusoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    nome TEXT,
    contato TEXT,
    shaken_vencimento DATE,
    veiculo TEXT,
    placa TEXT,
    chassi TEXT,
    fabricante TEXT,
    modelo_katashiki TEXT,
    chassi_completo TEXT,
    data_registro DATE,
    data_exclusao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    restaurado BOOLEAN DEFAULT FALSE
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_clientes_chassi ON clientes(chassi);
CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_clientes_placa ON clientes(placa);
CREATE INDEX IF NOT EXISTS idx_historico_cliente_id ON historico_acoes(cliente_id);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_clientes_updated_at ON clientes;
CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Políticas de segurança (RLS) - opcional mas recomendado
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;

-- Política: permitir todas operações para usuarios autenticados
-- (substitua por regras mais restritivas se necessario)
CREATE POLICY "Allow all" ON clientes
    FOR ALL
    TO anon, authenticated
    USING (true)
    WITH CHECK (true);
