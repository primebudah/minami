# Relatorio: Problema Registro Manual

## Problema
No formulario de registro manual, ao clicar "Adicionar a fila" com chassi fora do padrao:
1. Aparece aviso "Chassi fora do padrao"
2. Ao clicar "Adicionar mesmo assim", NAO vai para a fila

## Causa
Streamlit faz rerun quando clica no botao, e as variaveis do formulario se perdem.

## Solucao Proposta
Adicionar direto na fila sem validacao. A validacao ja existe na tela de conferencia.

## Arquivo
pages/1_Registros.py - linhas 434-524

## Codigo Atual Problema
if submitted or _ja_confirmou:
    # Validacao bloqueia mesmo com confirmacao
    if _erros: ...
    elif _avisos: ...  # Mostra botoes
    else:  # Adiciona

## Solucao
if submitted:
    # Adiciona direto na fila sem validacao
