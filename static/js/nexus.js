// Nexus Social: melhorias progressivas. Tudo funciona sem JavaScript (formulários comuns);
// com ele, curtir e seguir acontecem sem recarregar a página.
(() => {
  "use strict";

  const enviar = async (form) => {
    const resposta = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    return resposta.json();
  };

  document.addEventListener("submit", async (evento) => {
    const form = evento.target;
    if (!(form instanceof HTMLFormElement)) return;

    const confirmacao = form.dataset.confirmar;
    if (confirmacao && !window.confirm(confirmacao)) {
      evento.preventDefault();
      return;
    }

    const tipo = form.dataset.js;
    if (tipo !== "curtir" && tipo !== "seguir") return;
    evento.preventDefault();
    const botao = form.querySelector("button");
    botao.disabled = true;
    try {
      const dados = await enviar(form);
      if (tipo === "curtir") {
        botao.classList.toggle("ativo", dados.curtida);
        botao.setAttribute("aria-pressed", String(dados.curtida));
        botao.querySelector("[data-total]").textContent = dados.total;
        botao.classList.remove("pulsar");
        void botao.offsetWidth;
        if (dados.curtida) botao.classList.add("pulsar");
      } else {
        botao.classList.toggle("botao--contorno", dados.seguindo);
        botao.textContent = dados.seguindo ? botao.dataset.seguindo : botao.dataset.seguir;
        const contador = document.querySelector("[data-seguidores]");
        if (contador && form.closest(".perfil")) contador.textContent = dados.seguidores;
      }
    } catch {
      form.submit();
    } finally {
      botao.disabled = false;
    }
  });

  // Contador de caracteres e prévia da imagem no compositor.
  document.querySelectorAll("[data-contador]").forEach((campo) => {
    const limite = Number(campo.dataset.contador);
    const saida = campo.closest("form")?.querySelector("[data-contador-saida]");
    if (!saida) return;
    const atualizar = () => {
      saida.textContent = `${campo.value.length}/${limite}`;
      saida.classList.toggle("limite", campo.value.length >= limite);
    };
    campo.addEventListener("input", atualizar);
    atualizar();
  });

  document.querySelectorAll('#compositor input[type="file"]').forEach((entrada) => {
    const previa = entrada.closest("form").querySelector("[data-previa]");
    entrada.addEventListener("change", () => {
      const arquivo = entrada.files?.[0];
      if (!arquivo) return previa.classList.remove("visivel");
      previa.querySelector("img").src = URL.createObjectURL(arquivo);
      previa.classList.add("visivel");
    });
  });

  // Os avisos somem sozinhos depois de alguns segundos.
  setTimeout(() => document.querySelector(".avisos")?.remove(), 4000);
})();
