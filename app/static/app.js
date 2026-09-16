const $ = (selector) => document.querySelector(selector);
let cofreId = "";
let senhaMestra = "";

function mostrarStatus(mensagem, tipo = "info") {
  const elemento = $("#status");
  elemento.textContent = mensagem;
  elemento.className = `status ${tipo}`;
}

async function api(url, options = {}) {
  const resposta = await fetch(url, options);
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    const erro = new Error(dados.detail || `Erro HTTP ${resposta.status}`);
    erro.status = resposta.status;
    throw erro;
  }
  return dados;
}

document.querySelectorAll(".toggle-password").forEach((botao) => {
  botao.addEventListener("click", () => {
    const campo = document.getElementById(botao.dataset.target);
    const mostrar = campo.type === "password";
    campo.type = mostrar ? "text" : "password";
    botao.textContent = mostrar ? "Ocultar" : "Mostrar";
    botao.setAttribute("aria-label", `${mostrar ? "Ocultar" : "Mostrar"} senha`);
  });
});

$("#criar").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = Object.fromEntries(new FormData(evento.target));
  try {
    const cofre = await api("/cofres", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(dados),
    });
    $("#cofre-id").value = cofre.id;
    $("#senha-abrir").value = dados.senha_mestra;
    mostrarStatus(`Cofre criado. ID: ${cofre.id} — confira a senha e clique em “Abrir cofre”.`, "success");
    $("#abrir").scrollIntoView({behavior: "smooth", block: "center"});
  } catch (erro) {
    mostrarStatus(erro.message, "error");
  }
});

$("#abrir").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = Object.fromEntries(new FormData(evento.target));
  cofreId = dados.id.trim();
  senhaMestra = dados.senha;
  try {
    await api(`/cofres/${encodeURIComponent(cofreId)}/abrir`, {
      method: "POST",
      headers: {"X-Senha-Mestra": senhaMestra},
    });
    $("#conteudo").hidden = false;
    await listar();
    mostrarStatus("Senha-mestra correta. Cofre aberto com sucesso.", "success");
    $("#conteudo").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (erro) {
    senhaMestra = "";
    $("#conteudo").hidden = true;
    if (erro.status === 404) {
      mostrarStatus("Cofre não encontrado. Confira se o ID foi copiado corretamente.", "error");
    } else if (erro.status === 401) {
      mostrarStatus("Senha-mestra incorreta. Confira a senha usada na criação do cofre.", "error");
    } else {
      mostrarStatus(erro.message, "error");
    }
  }
});

async function listar() {
  const registros = await api(`/cofres/${encodeURIComponent(cofreId)}/segredos`, {
    headers: {"X-Senha-Mestra": senhaMestra},
  });
  const lista = $("#lista");
  lista.replaceChildren();
  if (!registros.length) {
    const vazio = document.createElement("li");
    vazio.className = "empty";
    vazio.textContent = "Nenhum segredo cadastrado ainda.";
    lista.appendChild(vazio);
    return;
  }
  registros.forEach((registro) => {
    const item = document.createElement("li");
    item.className = "secret-item";
    const texto = document.createElement("span");
    texto.textContent = `${registro.titulo}${registro.usuario ? ` — ${registro.usuario}` : ""}`;
    const ver = document.createElement("button");
    ver.type = "button";
    ver.className = "secondary";
    ver.textContent = "Ver";
    ver.addEventListener("click", () => verSegredo(registro.id));
    item.append(texto, ver);
    lista.appendChild(item);
  });
}

async function verSegredo(segredoId) {
  try {
    const registro = await api(
      `/cofres/${encodeURIComponent(cofreId)}/segredos/${encodeURIComponent(segredoId)}`,
      {headers: {"X-Senha-Mestra": senhaMestra}},
    );
    window.alert(`Título: ${registro.titulo}\nUsuário: ${registro.usuario || "(não informado)"}\nSenha: ${registro.senha}`);
  } catch (erro) {
    mostrarStatus(erro.message, "error");
  }
}

$("#novo").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = Object.fromEntries(new FormData(evento.target));
  try {
    await api(`/cofres/${encodeURIComponent(cofreId)}/segredos`, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Senha-Mestra": senhaMestra},
      body: JSON.stringify(dados),
    });
    evento.target.reset();
    await listar();
    mostrarStatus("Segredo salvo com segurança.", "success");
  } catch (erro) {
    mostrarStatus(erro.message, "error");
  }
});

$("#atualizar").addEventListener("click", async () => {
  try {
    await listar();
    mostrarStatus("Lista atualizada.", "success");
  } catch (erro) {
    mostrarStatus(erro.message, "error");
  }
});
