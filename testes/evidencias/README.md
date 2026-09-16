# Evidências dos testes

Os testes oficiais são determinísticos e usam um banco em memória via
`monkeypatch`, portanto não exigem credenciais Supabase nem persistem segredos.

As saídas automatizadas podem ser reproduzidas com os comandos abaixo e estão
resumidas em `resultado_testes.md`:

```text
5 passed, 2 warnings
compileall: OK
```

As capturas visuais desta pasta são:

- `01_nonces_distintos.png`: dois registros com nonce e criptograma distintos.
- `02_senha_mestra_incorreta.png`: mensagem de senha incorreta.
- `02_status_http_401.png`: requisição recusada com HTTP 401.
- `03_visao_invasor_supabase.png`: consulta direta sem senha legível.
- `04_registro_adulterado_500.png`: adulteração detectada pela interface.
- `05a_antes_da_troca.png`: registros íntegros antes da troca.
- `05b_depois_da_troca.png`: campos criptográficos trocados no destino.
- `05_status_http_500_aad.png`: troca recusada com HTTP 500.

Os arquivos `resultado_testes.md` e `roteiro_manual_supabase.md` explicam,
respectivamente, a correspondência com os requisitos e como reproduzir os
testes no Supabase.
- `resultado_testes.md`: correspondência entre cada teste obrigatório e seu
  teste automatizado.
- `roteiro_manual_supabase.md`: comandos para produzir evidências adicionais
  diretamente no SQL Editor do Supabase e pela API.

Para reproduzir:

```powershell
python -m pytest testes -q
python -m compileall -q app testes
```
