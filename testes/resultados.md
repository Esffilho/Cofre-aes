# Resultados dos testes oficiais

Data: 2026-09-16

- `python -m pytest testes -q`: **5 passed**.
- `python -m compileall -q app testes`: **OK**.
- Rotas FastAPI carregadas e frontend `/` servido: **OK**.

Os testes cobrem criptografia/AAD/nonce, criação e abertura (401/422), CRUD e autorização, adulteração de criptograma/falha GCM (500), estrutura KDF inválida (500) e ausência de vazamento na listagem/persistência. As evidências reproduzíveis ficam neste arquivo e no código em `testes/test_oficiais.py`; nenhum segredo real é incluído.

## Roteiro oficial — correspondência das evidências

| Teste obrigatório | Implementação | Resultado observado |
|---|---|---|
| 1. Nonces distintos | `test_01_nonces_e_criptogramas_distintos` cadastra duas vezes a mesma senha e compara os registros em memória equivalentes à tabela `segredos`. | `nonce` e `criptograma` diferentes. |
| 2. Senha-mestra incorreta | `test_02_senha_mestra_incorreta` tenta ler um segredo com senha errada. | HTTP `401`; o corpo não contém a senha clara. |
| 3. O que o invasor enxerga | `test_03_invasor_enxerga_apenas_base64` consulta `titulo, usuario, nonce, criptograma, etiqueta` no armazenamento de teste. | Nenhuma senha legível; campos criptográficos permanecem como strings Base64. |
| 4. Registro adulterado | `test_04_integridade_invalida_500` altera o criptograma e também verifica estrutura KDF inválida. | HTTP `500`; nenhum texto claro é devolvido. |
| 5. Troca de criptogramas entre registros | `test_05_troca_de_criptogramas_recusada_por_aad` copia `nonce`, `criptograma` e `etiqueta` da origem para o destino. | HTTP `500` por falha de autenticação GCM/AAD; senha de origem não é devolvida. |

Esses testes reproduzem as propriedades criptográficas sem depender de uma
instância externa do Supabase. O roteiro manual equivalente usa a consulta SQL
e o `UPDATE` descritos na especificação, diretamente no SQL Editor do
Supabase, e pode ser registrado em capturas de tela adicionais.

## Capturas de evidência

As capturas manuais estão organizadas em `testes/evidencias/`:

| Arquivo | Evidência |
|---|---|
| `01_nonces_distintos.png` | Dois registros com nonce e criptograma diferentes. |
| `02_senha_mestra_incorreta.png` | Mensagem de senha-mestra incorreta. |
| `02_status_http_401.png` | Requisição de leitura recusada com HTTP 401. |
| `03_visao_invasor_supabase.png` | Consulta direta sem senha clara. |
| `04_registro_adulterado_500.png` | Registro adulterado recusado pela interface. |
| `05a_antes_da_troca.png` | Registros de origem e destino antes da troca. |
| `05b_depois_da_troca.png` | Dados criptográficos copiados para o destino. |
| `05_status_http_500_aad.png` | Leitura do destino recusada pelo AAD com HTTP 500. |

As saídas automatizadas foram verificadas durante a execução e podem ser
reproduzidas com `python -m pytest testes -vv` e
`python -m compileall -q app testes`; o resultado foi `5 passed` e compilação
sem erros. Os arquivos de texto temporários dessas execuções foram removidos
para manter a pasta focada nas capturas e na documentação.
