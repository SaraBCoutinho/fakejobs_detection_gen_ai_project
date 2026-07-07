const state = {
  analyses: [],
  reports: [],
};

const verdictLabel = {
  provavel_golpe: "Provavel golpe",
  atencao: "Atencao",
  provavel_legitima: "Provavel legitima",
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.erro || "Falha na requisicao");
  return payload;
};

const toast = (message) => {
  const element = document.querySelector("#toast");
  element.textContent = message;
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 2800);
};

const switchView = async (view) => {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `view-${view}`);
  });
  if (view === "historico") await loadHistory();
  if (view === "denuncias") await loadReports();
  if (view === "dashboard") await loadDashboard();
};

const formToJson = (form) => {
  const data = Object.fromEntries(new FormData(form).entries());
  form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    data[checkbox.name] = checkbox.checked;
  });
  return data;
};

const renderResult = (analysis) => {
  const flags = analysis.red_flags || [];
  document.querySelector("#analysis-result").innerHTML = `
    <div class="score-ring" style="--score: ${analysis.score_risco}">
      <strong>${analysis.score_risco}</strong>
    </div>
    <div class="verdict ${analysis.veredito}">${verdictLabel[analysis.veredito]}</div>
    <p class="muted" style="margin-top: 12px">Confianca ${analysis.confianca}. ${flags.length} sinal(is) encontrado(s).</p>
    <h2>Sinais identificados</h2>
    ${
      flags.length
        ? flags
            .map(
              (flag) => `
                <div class="flag">
                  <strong>${flag.codigo} <span>+${flag.peso}</span></strong>
                  <p>${flag.descricao}</p>
                  ${flag.trecho_evidencia ? `<span>Evidencia: ${flag.trecho_evidencia}</span>` : ""}
                </div>
              `,
            )
            .join("")
        : '<p class="muted">Nenhuma red flag forte foi disparada.</p>'
    }
  `;
};

const loadHistory = async () => {
  const payload = await api("/api/analises");
  state.analyses = payload.items;
  const body = document.querySelector("#history-body");
  body.innerHTML = state.analyses.length
    ? state.analyses
        .map(
          (item) => `
          <tr>
            <td>${item.title || "Vaga sem titulo"}</td>
            <td>${item.fonte}</td>
            <td><strong>${item.score_risco}</strong></td>
            <td>${verdictLabel[item.veredito]}</td>
            <td>${item.confianca}</td>
            <td><button class="link-button" data-analysis="${item.id}">Ver</button></td>
          </tr>
        `,
        )
        .join("")
    : '<tr><td colspan="6">Nenhuma analise registrada ainda.</td></tr>';
};

const loadReports = async () => {
  const analyses = await api("/api/analises");
  state.analyses = analyses.items;
  const select = document.querySelector("#report-vaga-select");
  select.innerHTML = state.analyses.length
    ? state.analyses.map((item) => `<option value="${item.vaga_id}">${item.title || item.vaga_id}</option>`).join("")
    : '<option value="">Analise uma vaga primeiro</option>';

  const reports = await api("/api/denuncias");
  state.reports = reports.items;
  document.querySelector("#reports-list").innerHTML = state.reports.length
    ? state.reports
        .map(
          (item) => `
          <article class="mini-card">
            <strong>${item.title}</strong>
            <p>${item.motivo}</p>
            <span class="muted">${item.status} - score ${item.score_risco ?? "n/a"}</span>
          </article>
        `,
        )
        .join("")
    : '<p class="muted">Nenhuma sinalizacao registrada.</p>';
};

const loadDashboard = async () => {
  const data = await api("/api/dashboard");
  document.querySelector("#metrics").innerHTML = `
    <div class="metric"><span>Analises</span><strong>${data.total_analises}</strong></div>
    <div class="metric"><span>Score medio</span><strong>${data.score_medio}</strong></div>
    <div class="metric"><span>Sinalizacoes</span><strong>${data.denuncias}</strong></div>
  `;
  const total = Math.max(data.total_analises, 1);
  document.querySelector("#verdict-bars").innerHTML = Object.entries(data.vereditos)
    .map(([key, value]) => {
      const pct = Math.round((value / total) * 100);
      return `
        <div>
          <div class="bar-label"><strong>${verdictLabel[key]}</strong><span>${value}</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
        </div>
      `;
    })
    .join("");
};

document.querySelectorAll(".nav-button").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});

document.querySelector("#analysis-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formToJson(event.currentTarget);
  const result = await api("/api/analisar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  renderResult(result);
  toast("Analise salva no historico");
});

document.querySelector("#history-body").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-analysis]");
  if (!button) return;
  const analysis = await api(`/api/analises/${button.dataset.analysis}`);
  renderResult(analysis);
  switchView("analisar");
});

document.querySelector("#report-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formToJson(event.currentTarget);
  if (!payload.vaga_id) {
    toast("Analise uma vaga antes de sinalizar");
    return;
  }
  await api("/api/denuncias", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  event.currentTarget.reset();
  await loadReports();
  toast("Sinalizacao registrada");
});

loadHistory().catch(() => {});
