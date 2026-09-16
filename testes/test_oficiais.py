import pytest
from fastapi.testclient import TestClient
from app import banco
from app.main import app

@pytest.fixture
def client(monkeypatch):
    cofres, segredos = {}, {}
    monkeypatch.setattr(banco, 'buscar_cofre', lambda i: cofres.get(i))
    monkeypatch.setattr(banco, 'inserir_cofre', lambda x: cofres.setdefault(x['id'], x))
    monkeypatch.setattr(banco, 'buscar_segredo', lambda i: segredos.get(i))
    monkeypatch.setattr(banco, 'inserir_segredo', lambda x: segredos.setdefault(x['id'], x))
    monkeypatch.setattr(banco, 'listar_segredos', lambda c: [{k:v for k,v in x.items() if k in ('id','titulo','usuario','url','criado_em')} for x in segredos.values() if x['cofre_id']==c])
    monkeypatch.setattr(banco, 'atualizar_segredo', lambda i,x: segredos[i].update(x))
    monkeypatch.setattr(banco, 'remover_segredo', lambda i: segredos.pop(i, None))
    return TestClient(app), cofres, segredos

def test_01_nonces_e_criptogramas_distintos(client):
    c,_,segredos=client
    cid=c.post('/cofres',json={'nome':'Teste','senha_mestra':'senha-segura'}).json()['id']
    h={'X-Senha-Mestra':'senha-segura'}
    for titulo in ('Primeiro','Segundo'):
        assert c.post(
            f'/cofres/{cid}/segredos',
            json={'titulo':titulo,'senha':'mesma-senha'},
            headers=h,
        ).status_code == 201
    registros=list(segredos.values())
    assert registros[0]['nonce'] != registros[1]['nonce']
    assert registros[0]['criptograma'] != registros[1]['criptograma']

def test_02_senha_mestra_incorreta(client):
    c,_,_=client
    cid=c.post('/cofres',json={'nome':'Teste','senha_mestra':'senha-segura'}).json()['id']
    h={'X-Senha-Mestra':'senha-segura'}
    sid=c.post(
        f'/cofres/{cid}/segredos',
        json={'titulo':'Privado','senha':'nao-vazar'},
        headers=h,
    ).json()['id']
    resposta=c.get(
        f'/cofres/{cid}/segredos/{sid}',
        headers={'X-Senha-Mestra':'senha-errada'},
    )
    assert resposta.status_code == 401
    assert 'nao-vazar' not in resposta.text

def test_03_invasor_enxerga_apenas_base64(client):
    c,_,segredos=client
    cid=c.post('/cofres',json={'nome':'Teste','senha_mestra':'senha-segura'}).json()['id']
    h={'X-Senha-Mestra':'senha-segura'}
    c.post(
        f'/cofres/{cid}/segredos',
        json={'titulo':'Email','usuario':'alguem','senha':'plaintext-secreto'},
        headers=h,
    )
    campos={'titulo','usuario','nonce','criptograma','etiqueta'}
    consulta=[{campo:registro[campo] for campo in campos} for registro in segredos.values()]
    assert consulta
    assert all('plaintext-secreto' not in str(registro) for registro in consulta)
    assert all(isinstance(registro['nonce'], str) for registro in consulta)
    assert all(isinstance(registro['criptograma'], str) for registro in consulta)
    assert all(isinstance(registro['etiqueta'], str) for registro in consulta)

def test_04_integridade_invalida_500(client):
    c,cofres,segredos=client
    cid=c.post('/cofres',json={'nome':'Teste','senha_mestra':'senha-segura'}).json()['id']
    h={'X-Senha-Mestra':'senha-segura'}
    sid=c.post(
        f'/cofres/{cid}/segredos',
        json={'titulo':'Adulterado','senha':'original'},
        headers=h,
    ).json()['id']
    segredos[sid]['criptograma'] = 'AAAA'
    assert c.get(f'/cofres/{cid}/segredos/{sid}',headers=h).status_code==500
    cofres[cid]['kdf_sal']='!!!'
    assert c.post(f'/cofres/{cid}/abrir',headers=h).status_code==500
    
def test_05_troca_de_criptogramas_recusada_por_aad(client):
    c,_,segredos=client
    cid=c.post('/cofres',json={'nome':'Teste','senha_mestra':'senha-segura'}).json()['id']
    h={'X-Senha-Mestra':'senha-segura'}
    ids=[
        c.post(
            f'/cofres/{cid}/segredos',
            json={'titulo':titulo,'senha':senha},
            headers=h,
        ).json()['id']
        for titulo,senha in (('Origem','senha-origem'),('Destino','senha-destino'))
    ]
    origem, destino = (segredos[segredo_id] for segredo_id in ids)
    for campo in ('nonce','criptograma','etiqueta'):
        segredos[ids[1]][campo] = origem[campo]
    resposta=c.get(f'/cofres/{cid}/segredos/{ids[1]}',headers=h)
    assert resposta.status_code == 500
    assert 'senha-origem' not in resposta.text
