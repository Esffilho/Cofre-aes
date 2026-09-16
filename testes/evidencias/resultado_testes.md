# Prova dos testes oficiais

## Pytest

Comando executado:

```powershell
python -m pytest testes -q
```

Resultado:

```text
5 passed, 2 warnings
```

A saída integral está em `pytest_saida.txt`. Para visualizar cada teste pelo
nome, consulte também `pytest_verbose_saida.txt`, gerado com `pytest -vv`.
Os dois avisos são depreciações das dependências `starlette/httpx` e não
falhas do projeto.

## Correspondência com os cinco testes obrigatórios

Os cinco testes obrigatórios estão implementados individualmente em
`testes/test_oficiais.py` e descritos em detalhes na tabela de
`testes/resultados.md`:

1. `test_01_nonces_e_criptogramas_distintos`
2. `test_02_senha_mestra_incorreta`
3. `test_03_invasor_enxerga_apenas_base64`
4. `test_04_integridade_invalida_500`
5. `test_05_troca_de_criptogramas_recusada_por_aad`

Assim, o `5 passed` corresponde exatamente aos cinco requisitos experimentais,
e não apenas a um teste genérico de compilação ou de integração.

A saída detalhada confirma individualmente:

```text
test_01_nonces_e_criptogramas_distintos PASSED
test_02_senha_mestra_incorreta PASSED
test_03_invasor_enxerga_apenas_base64 PASSED
test_04_integridade_invalida_500 PASSED
test_05_troca_de_criptogramas_recusada_por_aad PASSED
```

## Compilação

Comando executado:

```powershell
python -m compileall -q app testes
```

Resultado: código de saída `0`, registrado em `status_execucao.txt`. Como o
comando usa `-q`, não há texto de sucesso; qualquer erro faria o código de
saída ser diferente de zero e produziria saída em `compileall_saida.txt`.
