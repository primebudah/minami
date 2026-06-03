-- Verifica se a coluna data_conclusao existe na tabela clientes
-- Execute no SQL Editor do Supabase

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'clientes' 
ORDER BY ordinal_position;
