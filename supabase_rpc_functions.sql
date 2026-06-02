-- =========================================================
-- FUNÇÕES RPC PARA SUPABASE (evita cache do PostgREST)
-- =========================================================

-- Função: Listar todos os clientes
CREATE OR REPLACE FUNCTION listar_clientes_rpc()
RETURNS SETOF clientes
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * FROM clientes ORDER BY id;
$$;

-- Função: Buscar cliente por ID
CREATE OR REPLACE FUNCTION buscar_cliente_por_id_rpc(p_id INTEGER)
RETURNS SETOF clientes
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * FROM clientes WHERE id = p_id;
$$;

-- Função: Buscar cliente por chassi
CREATE OR REPLACE FUNCTION buscar_cliente_por_chassi_rpc(p_chassi TEXT)
RETURNS SETOF clientes
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * FROM clientes WHERE chassi = p_chassi;
$$;

-- Função: Salvar cliente (INSERT)
CREATE OR REPLACE FUNCTION salvar_cliente_rpc(
  p_nome TEXT,
  p_contato TEXT DEFAULT NULL,
  p_shaken_vencimento DATE DEFAULT NULL,
  p_veiculo TEXT DEFAULT NULL,
  p_placa TEXT DEFAULT NULL,
  p_chassi TEXT DEFAULT NULL,
  p_fabricante TEXT DEFAULT NULL,
  p_modelo_katashiki TEXT DEFAULT NULL,
  p_chassi_completo TEXT DEFAULT NULL,
  p_data_registro DATE DEFAULT NULL,
  p_data_conclusao DATE DEFAULT NULL,
  p_status TEXT DEFAULT 'Pendente',
  p_observacao TEXT DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_id INTEGER;
BEGIN
  INSERT INTO clientes (
    nome, contato, shaken_vencimento, veiculo, placa, chassi,
    fabricante, modelo_katashiki, chassi_completo, data_registro,
    data_conclusao, status, observacao
  ) VALUES (
    p_nome, p_contato, p_shaken_vencimento, p_veiculo, p_placa, p_chassi,
    p_fabricante, p_modelo_katashiki, p_chassi_completo, p_data_registro,
    p_data_conclusao, p_status, p_observacao
  ) RETURNING id INTO v_id;
  
  RETURN v_id;
END;
$$;

-- Função: Atualizar cliente
CREATE OR REPLACE FUNCTION atualizar_cliente_rpc(
  p_id INTEGER,
  p_nome TEXT,
  p_contato TEXT DEFAULT NULL,
  p_shaken_vencimento DATE DEFAULT NULL,
  p_veiculo TEXT DEFAULT NULL,
  p_placa TEXT DEFAULT NULL,
  p_chassi TEXT DEFAULT NULL,
  p_fabricante TEXT DEFAULT NULL,
  p_modelo_katashiki TEXT DEFAULT NULL,
  p_chassi_completo TEXT DEFAULT NULL,
  p_data_registro DATE DEFAULT NULL,
  p_data_conclusao DATE DEFAULT NULL,
  p_status TEXT DEFAULT 'Pendente',
  p_observacao TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE clientes SET
    nome = p_nome,
    contato = p_contato,
    shaken_vencimento = p_shaken_vencimento,
    veiculo = p_veiculo,
    placa = p_placa,
    chassi = p_chassi,
    fabricante = p_fabricante,
    modelo_katashiki = p_modelo_katashiki,
    chassi_completo = p_chassi_completo,
    data_registro = p_data_registro,
    data_conclusao = p_data_conclusao,
    status = p_status,
    observacao = p_observacao
  WHERE id = p_id;

  RETURN FOUND;
END;
$$;

-- Função: Deletar cliente
CREATE OR REPLACE FUNCTION deletar_cliente_rpc(p_id INTEGER)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Primeiro salva no histórico
  INSERT INTO historico_exclusoes (
    cliente_id, nome, contato, shaken_vencimento, veiculo,
    placa, chassi, fabricante, modelo_katashiki, chassi_completo,
    data_registro
  )
  SELECT 
    id, nome, contato, shaken_vencimento, veiculo,
    placa, chassi, fabricante, modelo_katashiki, chassi_completo,
    data_registro
  FROM clientes WHERE id = p_id;
  
  -- Depois deleta
  DELETE FROM clientes WHERE id = p_id;
  
  RETURN FOUND;
END;
$$;

-- Função: Salvar histórico de ação
CREATE OR REPLACE FUNCTION salvar_historico_rpc(
  p_cliente_id INTEGER,
  p_acao TEXT,
  p_dados_anteriores JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO historico_acoes (cliente_id, acao, dados_anteriores)
  VALUES (p_cliente_id, p_acao, p_dados_anteriores);
END;
$$;

-- Função: Obter última ação (para desfazer)
CREATE OR REPLACE FUNCTION obter_ultima_acao_rpc()
RETURNS TABLE (
  id INTEGER,
  cliente_id INTEGER,
  acao TEXT,
  dados_anteriores JSONB,
  criado_em TIMESTAMP WITH TIME ZONE
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * FROM historico_acoes 
  ORDER BY criado_em DESC 
  LIMIT 1;
$$;

-- Função: Deletar do histórico
CREATE OR REPLACE FUNCTION deletar_historico_rpc(p_id INTEGER)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  DELETE FROM historico_acoes WHERE id = p_id;
END;
$$;

-- Função: Restaurar cliente do histórico de exclusões
CREATE OR REPLACE FUNCTION restaurar_cliente_excluido_rpc(p_historico_id INTEGER)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_cliente_id INTEGER;
BEGIN
  -- Insere o cliente de volta
  INSERT INTO clientes (
    nome, contato, shaken_vencimento, veiculo, placa, chassi,
    fabricante, modelo_katashiki, chassi_completo, data_registro,
    data_conclusao, status, observacao
  )
  SELECT 
    nome, contato, shaken_vencimento, veiculo, placa, chassi,
    fabricante, modelo_katashiki, chassi_completo, data_registro,
    data_conclusao, 'Restaurado', 'Cliente restaurado da exclusão'
  FROM historico_exclusoes WHERE id = p_historico_id
  RETURNING id INTO v_cliente_id;
  
  -- Marca como restaurado no histórico
  UPDATE historico_exclusoes SET restaurado = TRUE WHERE id = p_historico_id;
  
  RETURN v_cliente_id;
END;
$$;

-- Função: Obter última exclusão
CREATE OR REPLACE FUNCTION obter_ultima_exclusao_rpc()
RETURNS TABLE (
  id INTEGER,
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
  data_exclusao TIMESTAMP WITH TIME ZONE,
  restaurado BOOLEAN
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * FROM historico_exclusoes 
  WHERE restaurado = FALSE
  ORDER BY data_exclusao DESC 
  LIMIT 1;
$$;

-- Dar permissões para as funções
GRANT EXECUTE ON FUNCTION listar_clientes_rpc() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION buscar_cliente_por_id_rpc(INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION buscar_cliente_por_chassi_rpc(TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION salvar_cliente_rpc(TEXT, TEXT, DATE, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, DATE, DATE, TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION atualizar_cliente_rpc(INTEGER, TEXT, TEXT, DATE, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, DATE, DATE, TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION deletar_cliente_rpc(INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION salvar_historico_rpc(INTEGER, TEXT, JSONB) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION obter_ultima_acao_rpc() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION deletar_historico_rpc(INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION restaurar_cliente_excluido_rpc(INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION obter_ultima_exclusao_rpc() TO anon, authenticated;
