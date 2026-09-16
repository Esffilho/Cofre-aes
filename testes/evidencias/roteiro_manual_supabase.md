# Roteiro manual no Supabase

Este roteiro produz evidências complementares usando a instância PostgreSQL/
Supabase configurada em `.env`. Execute as consultas no SQL Editor e capture a
tela com os resultados. Não inclua a URL, a chave ou outros segredos na
captura.

## Teste 1 — nonces distintos

Cadastre duas vezes a mesma senha pela API, com títulos diferentes, e execute:

```sql
select id, titulo, nonce, criptograma, etiqueta
from public.segredos
order by criado_em desc
limit 2;
```

Observe que `nonce` e `criptograma` são diferentes.

## Teste 2 — senha-mestra incorreta

Leia um dos IDs retornados pela consulta usando uma senha-mestra errada:

```powershell
$h = @{"X-Senha-Mestra" = "senha-incorreta"}
Invoke-WebRequest -Method Get `
  -Uri "http://127.0.0.1:8000/cofres/ID_DO_COFRE/segredos/ID_DO_SEGREDO" `
  -Headers $h
```

O resultado esperado é HTTP `401`, sem a senha clara no corpo.

## Teste 3 — visão do invasor

```sql
select titulo, usuario, nonce, criptograma, etiqueta
from public.segredos;
```

Os campos criptográficos aparecem como Base64; a senha não aparece em
formato legível.

## Teste 4 — registro adulterado

```sql
update public.segredos
set criptograma = 'X' || substring(criptograma from 2)
where id = 'ID_DO_SEGREDO';
```

Tente ler o segredo pela API com a senha correta. O resultado esperado é HTTP
`500` com indicação de registro adulterado, sem texto claro.

## Teste 5 — troca de criptogramas

Substitua os campos do segredo de destino pelos do segredo de origem:

```sql
update public.segredos as destino
set nonce = origem.nonce,
    criptograma = origem.criptograma,
    etiqueta = origem.etiqueta
from public.segredos as origem
where destino.id = 'ID_DESTINO'
  and origem.id = 'ID_ORIGEM';
```

Leia o segredo de destino pela API. O resultado esperado é HTTP `500`: o AAD
inclui o identificador do registro e impede a reutilização dos dados de
origem.
