-- Remove colunas criado_em e atualizado_em da tabela clientes
-- Execute no SQL Editor do Supabase

-- Remove o trigger que usa atualizado_em
DROP TRIGGER IF EXISTS update_clientes_updated_at ON clientes;

-- Remove a função do trigger
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Remove as colunas da tabela clientes
ALTER TABLE clientes DROP COLUMN IF EXISTS criado_em;
ALTER TABLE clientes DROP COLUMN IF EXISTS atualizado_em;
