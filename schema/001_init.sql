create extension if not exists pgcrypto;
create table if not exists public.cofres (
 id uuid primary key, nome text not null check (length(nome) between 1 and 120),
 kdf_sal text not null, kdf_iteracoes integer not null check (kdf_iteracoes >= 100000),
 verificador_nonce text not null, verificador_criptograma text not null, verificador_etiqueta text not null,
 criado_em timestamptz not null default now()
);
create table if not exists public.segredos (
 id uuid primary key, cofre_id uuid not null references public.cofres(id) on delete cascade,
 titulo text not null, usuario text, url text, nonce text not null, criptograma text not null, etiqueta text not null,
 criado_em timestamptz not null default now(), atualizado_em timestamptz
);
create index if not exists segredos_cofre_idx on public.segredos(cofre_id);
