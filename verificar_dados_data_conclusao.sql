-- Verifica se há dados na coluna data_conclusao
-- Execute no SQL Editor do Supabase

SELECT id, nome, status, data_conclusao 
FROM clientes 
WHERE status = '🟢 Concluido' 
ORDER BY id DESC 
LIMIT 10;
