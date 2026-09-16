import base64
import binascii

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes


ITERACOES_PADRAO = 210_000
TAMANHO_CHAVE = 32
TAMANHO_SAL = 16
TAMANHO_NONCE = 12

FRASE_VERIFICADORA = "cofre-ok"

def para_b64(dados: bytes) -> str:
    """Converte bytes em texto Base64, para gravar no banco."""
    return base64.b64encode(dados).decode("ascii")


def de_b64(texto: str) -> bytes:
    """Decodifica Base64 estrito; registros inválidos são tratados como corrupção."""
    if not isinstance(texto, str) or not texto:
        raise ValueError("Base64 inválido")
    try:
        return base64.b64decode(texto.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("Base64 inválido") from exc

def derivar_chave(
    senha_mestra: str,
    sal: bytes,
    iteracoes: int
) -> bytes:
    """Transforma a senha-mestra em uma chave de 32 bytes."""
    if not isinstance(senha_mestra, str) or not senha_mestra:
        raise ValueError("senha-mestra inválida")
    if not isinstance(sal, bytes) or len(sal) != TAMANHO_SAL:
        raise ValueError("sal inválido")
    if not isinstance(iteracoes, int) or iteracoes < 100_000:
        raise ValueError("iterações inválidas")
    return PBKDF2(
        senha_mestra,
        sal,
        dkLen=TAMANHO_CHAVE,
        count=iteracoes,
        hmac_hash_module=SHA256,
    )

def gerar_sal() -> bytes:
    """Sorteia um sal novo para um cofre."""
    return get_random_bytes(TAMANHO_SAL)

def cifrar(
    chave: bytes,
    texto_claro: str,
    aad: bytes
) -> tuple[str, str, str]:
    """Cifra e devolve (nonce, criptograma, etiqueta) em Base64."""

    nonce = get_random_bytes(TAMANHO_NONCE)

    cifra = AES.new(
        chave,
        AES.MODE_GCM,
        nonce=nonce
    )

    cifra.update(aad)

    texto_bytes = texto_claro.encode("utf-8")

    criptograma, etiqueta = cifra.encrypt_and_digest(texto_bytes)

    return (
        para_b64(nonce),
        para_b64(criptograma),
        para_b64(etiqueta),
    )
def decifrar(
    chave: bytes,
    nonce_b64: str,
    cripto_b64: str,
    etiqueta_b64: str,
    aad: bytes
) -> str:
    """Decifra e verifica a etiqueta. Lança ValueError na falha."""

    nonce = de_b64(nonce_b64)
    criptograma = de_b64(cripto_b64)
    etiqueta = de_b64(etiqueta_b64)
    if len(nonce) != TAMANHO_NONCE or len(etiqueta) != 16:
        raise ValueError("nonce ou etiqueta inválidos")
    if not isinstance(chave, bytes) or len(chave) != TAMANHO_CHAVE:
        raise ValueError("chave inválida")

    cifra = AES.new(
        chave,
        AES.MODE_GCM,
        nonce=nonce
    )

    cifra.update(aad)

    texto_bytes = cifra.decrypt_and_verify(
        criptograma,
        etiqueta
    )

    return texto_bytes.decode("utf-8")

def criar_verificador(
    chave: bytes,
    cofre_id: str
) -> tuple[str, str, str]:
    """Cifra a frase fixa, gravada no registro."""
    return cifrar(
        chave,
        FRASE_VERIFICADORA,
        cofre_id.encode()
    )

def senha_mestra_correta(
    chave: bytes,
    nonce: str,
    cripto: str,
    etiqueta: str,
    cofre_id: str
) -> bool:
    """Tenta decifrar o verificador. Devolve True ou False."""

    try:
        texto = decifrar(
            chave,
            nonce,
            cripto,
            etiqueta,
            cofre_id.encode()
        )

        return texto == FRASE_VERIFICADORA

    except (ValueError, KeyError, TypeError):
        return False