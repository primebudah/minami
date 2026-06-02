-- Atualiza a função RPC atualizar_cliente_rpc para remover referência à coluna atualizado_em
-- Execute no SQL Editor do Supabase

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
