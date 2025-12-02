/**
 * Lógica principal da aplicação frontend
 */

// Charts
let loadChart = null;
let predictionChart = null;
let benchmarkChart = null;

// ==================== INITIALIZATION ====================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🌐 EcoGrid+ Frontend carregado");

  // Inicializa visualização da rede
  networkViz = new NetworkVisualization("network-viz");

  // Inicializa charts
  initCharts();

  // Verifica status inicial
  checkHealth();
});

async function checkHealth() {
  try {
    const health = await api.getHealth();
    updateStatusIndicator(health.status === "healthy");

    if (health.initialized) {
      await refreshData();
    }
  } catch (error) {
    updateStatusIndicator(false);
    console.error("Sistema não está respondendo");
  }
}

function updateStatusIndicator(isHealthy) {
  const indicator = document.getElementById("status-indicator");
  const text = document.getElementById("status-text");
  const dot = indicator.querySelector(".status-dot");

  if (isHealthy) {
    text.textContent = "Sistema Online";
    dot.style.background = "#10b981";
  } else {
    text.textContent = "Sistema Offline";
    dot.style.background = "#ef4444";
  }
}

function setNetworkMode(mode) {
  if (window.networkViz) {
    networkViz.setMode(mode);
  }
}

// ==================== SYSTEM ACTIONS ====================

async function initializeSystem() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Inicializando...';

  try {
    // Chama inicialização
    const result = await api.initialize(20, false);

    if (result.success) {
      showNotification("Sistema inicializado com sucesso!", "success");

      // Atualiza IMEDIATAMENTE com os dados que vieram do /api/init
      if (result.network_stats) {
        updateStats({
          network: result.network_stats,
          avl_tree: result.avl_stats,
        });
      }

      // Depois atualiza novamente para garantir dados frescos do banco
      setTimeout(async () => {
        await refreshData();
      }, 3000);

      setTimeout(async () => {
        await refreshData();
        showNotification("Dados carregados!", "info");
      }, 5000);
    }
  } catch (error) {
    showNotification("Erro ao inicializar sistema: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🚀 Inicializar Sistema";
  }
}

async function balanceNetwork() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Balanceando...';

  try {
    const result = await api.balanceNetwork();

    if (result.success) {
      showNotification(
        `Balanceamento concluído! ${result.balancing.balanced} nós rebalanceados.`,
        "success"
      );
      await refreshData();
    }
  } catch (error) {
    showNotification("Erro no balanceamento: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "⚖️ Balancear Rede";
  }
}

async function optimizeNetwork() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Otimizando...';

  try {
    const result = await api.optimizeEfficiency();

    if (result.success) {
      showNotification(
        `Otimização concluída! ${result.optimization.optimizations_performed} operações realizadas.`,
        "success"
      );

      updateEfficiencyMetrics(result);
      await refreshData();
      await updateMLPanel();
    }
  } catch (error) {
    showNotification("Erro na otimização: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔧 Otimizar Eficiência";
  }
}

async function trainML() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Treinando...';

  try {
    const result = await api.trainML(50);

    if (result.success) {
      const tr = result.training_result || {};
      const val = tr.validation || {};

      const samples = tr.train_samples ?? 0;
      const epochs = tr.epochs ?? 50;
      const acc =
        val.accuracy !== undefined
          ? (val.accuracy * 100).toFixed(1) + "%"
          : "-";
      const loss = val.loss !== undefined ? val.loss.toFixed(1) + " kW" : "-";

      let msg = `Modelo treinado!\nAmostras: ${samples}\nÉpocas: ${epochs}\nAcurácia: ${acc}\nLoss: ${loss}`;
      showNotification(msg, "success");

      await updateMLPanel();
    } else if (result.error) {
      showNotification("Erro no treinamento: " + result.error, "error");
    }
  } catch (error) {
    showNotification("Erro no treinamento: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🤖 Treinar ML";
  }
}

async function refreshData() {
  try {
    // Atualiza estatísticas
    const stats = await api.getStats();
    updateStats(stats.stats);

    // Atualiza visualização da rede
    await networkViz.update();

    // Atualiza tabela de nós
    await updateNodesTable();

    // Atualiza eventos
    await updateEvents();

    // Atualiza charts
    await updateCharts();

    // Atualiza métricas de eficiência (se estiver na aba)
    if (
      document.getElementById("tab-efficiency").classList.contains("active")
    ) {
      updateEfficiencyTab();
    }

    showNotification("Dados atualizados!", "info");
  } catch (error) {
    console.error("Erro ao atualizar dados:", error);
  }
}

async function updateMLPanel() {
  try {
    const stats = await api.request("/ml/stats", { method: "GET" });
    if (!stats.success) return;

    const m = stats.ml_stats;

    document.getElementById("ml-samples").textContent =
      m.train_samples !== undefined ? m.train_samples : "-";

    document.getElementById("ml-accuracy").textContent =
      m.train_accuracy !== undefined
        ? (m.train_accuracy * 100).toFixed(1) + "%"
        : "-";

    document.getElementById("ml-loss").textContent =
      m.train_loss !== undefined ? m.train_loss.toFixed(1) + " kW" : "-";

    document.getElementById("ml-last-train").textContent =
      m.last_train_time || "-";
  } catch (e) {
    console.warn("ML stats não disponíveis:", e.message);
  }
}

async function simulateOverload() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Simulando...';

  try {
    const result = await api.request("/simulate-overload", {
      method: "POST",
      body: JSON.stringify({ num_nodes: 3 }),
    });

    if (result.success) {
      showNotification(
        `Sobrecarga simulada em ${result.nodes.length} nós!`,
        "success"
      );

      // AGUARDA 1 segundo e atualiza DUAS vezes
      setTimeout(async () => {
        await refreshData();
        setTimeout(async () => {
          await refreshData();
        }, 1000);
      }, 1000);
    }
  } catch (error) {
    showNotification("Erro ao simular: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "⚠️ Simular Sobrecarga";
  }
}

// ==================== UI UPDATES ====================

function updateStats(stats) {
  console.log("Atualizando stats:", stats); // Debug

  // Total de nós
  const nodeCount = stats.network?.node_count || stats.avl_tree?.size || 0;
  document.getElementById("total-nodes").textContent = nodeCount;

  // Carga Total
  const totalLoad = stats.network?.total_load;
  if (totalLoad !== undefined && totalLoad !== null) {
    document.getElementById("total-load").textContent = totalLoad.toFixed(1);
  } else {
    document.getElementById("total-load").textContent = "-";
  }

  // Utilização
  const utilization = stats.network?.utilization;
  if (utilization !== undefined) {
    document.getElementById("utilization").textContent = (
      utilization * 100
    ).toFixed(1);
  } else {
    document.getElementById("utilization").textContent = "-";
  }

  // Nós Sobrecarregados
  const overloaded = stats.network?.overloaded_nodes || 0;
  document.getElementById("overloaded-nodes").textContent = overloaded;

  // Atualiza métricas de eficiência se estiverem disponíveis
  if (stats.efficiency) {
    document.getElementById("global-efficiency").textContent =
      stats.efficiency.global_efficiency?.toFixed(2) || "-";

    document.getElementById("total-losses").textContent = stats.efficiency
      .total_losses
      ? stats.efficiency.total_losses.toFixed(2) + " kW"
      : "-";
  }

  // Métricas de sobrecarga
  if (stats.overload_metrics) {
    document.getElementById("overload-detected").textContent =
      stats.overload_metrics.overloads_detected;
    document.getElementById("overload-resolved").textContent =
      stats.overload_metrics.overloads_resolved;
    document.getElementById("overload-avg-time").textContent =
      stats.overload_metrics.avg_overload_response_ms.toFixed(1) + " ms";
  }
}

async function updateNodesTable() {
  try {
    const nodesData = await api.getNodes();
    const tbody = document.getElementById("nodes-tbody");

    tbody.innerHTML = nodesData.nodes
      .map((node) => {
        const data = node.data;
        const utilization = ((data.current_load / data.capacity) * 100).toFixed(
          1
        );
        const status =
          utilization > 90
            ? "overloaded"
            : utilization > 70
            ? "warning"
            : "active";

        return `
                <tr>
                    <td><strong>${node.key}</strong></td>
                    <td>${data.type}</td>
                    <td>${data.capacity.toFixed(1)}</td>
                    <td>${data.current_load.toFixed(1)}</td>
                    <td>${utilization}%</td>
                    <td>${(data.efficiency * 100).toFixed(0)}%</td>
                    <td><span class="status-badge status-${status}">${status}</span></td>
                </tr>
            `;
      })
      .join("");
  } catch (error) {
    console.error("Erro ao atualizar tabela:", error);
  }
}

async function updateEvents() {
  try {
    const eventsData = await api.getCriticalEvents();
    const container = document.getElementById("events-list");

    if (!eventsData.events || eventsData.count === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #6b7280;">
          <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
          <h3 style="margin: 0; color: #374151;">Nenhum Evento Crítico</h3>
          <p style="margin: 8px 0 0 0; font-size: 14px;">A rede está operando normalmente.</p>
        </div>
      `;
      return;
    }

    const critical = eventsData.events.filter((e) => e.priority <= 2);
    const high = eventsData.events.filter((e) => e.priority === 3);
    const medium = eventsData.events.filter((e) => e.priority >= 4);

    let html = "";

    // Críticos
    if (critical.length > 0) {
      html +=
        '<h4 style="color: #ef4444; margin: 0 0 12px 0;">🔴 Críticos</h4>';
      critical.forEach((event) => {
        const d = event.data || {};
        const cap = d.capacity !== undefined ? d.capacity.toFixed(2) : "-";
        const load = d.load !== undefined ? d.load.toFixed(2) : "-";
        const util =
          d.utilization !== undefined
            ? (d.utilization * 100).toFixed(1) + "%"
            : "-";

        html += `
          <div class="event-item critical" style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 12px; margin-bottom: 8px; border-radius: 6px;">
            <div style="font-weight: 600; color: #991b1b; margin-bottom: 4px;">
              ${event.type.toUpperCase()} - Nó: ${event.node_id}
            </div>
            <div style="font-size: 13px; color: #7f1d1d;">
              Prioridade: ${event.priority} |
              Capacidade: ${cap} kW |
              Carga: ${load} kW |
              Utilização: ${util}
            </div>
          </div>
        `;
      });
    }

    // Altos
    if (high.length > 0) {
      html +=
        '<h4 style="color: #f59e0b; margin: 16px 0 12px 0;">🟠 Altos</h4>';
      high.forEach((event) => {
        html += `
          <div class="event-item high" style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 8px; border-radius: 6px;">
            <div style="font-weight: 600; color: #92400e; margin-bottom: 4px;">
              ${event.type.toUpperCase()} - Nó: ${event.node_id}
            </div>
            <div style="font-size: 13px; color: #78350f;">
              Prioridade: ${event.priority} | ${JSON.stringify(event.data)}
            </div>
          </div>
        `;
      });
    }

    // Médios
    if (medium.length > 0) {
      html +=
        '<h4 style="color: #3b82f6; margin: 16px 0 12px 0;">🟡 Médios</h4>';
      medium.forEach((event) => {
        html += `
          <div class="event-item medium" style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 12px; margin-bottom: 8px; border-radius: 6px;">
            <div style="font-weight: 600; color: #1e40af; margin-bottom: 4px;">
              ${event.type.toUpperCase()} - Nó: ${event.node_id}
            </div>
            <div style="font-size: 13px; color: #1e3a8a;">
              Prioridade: ${event.priority} | ${JSON.stringify(event.data)}
            </div>
          </div>
        `;
      });
    }

    container.innerHTML = html;
  } catch (error) {
    console.error("Erro ao atualizar eventos:", error);
    document.getElementById("events-list").innerHTML = `
      <div style="text-align: center; padding: 40px; color: #ef4444;">
        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
        <h3 style="margin: 0;">Erro ao Carregar Eventos</h3>
        <p style="margin: 8px 0 0 0; font-size: 14px;">${error.message}</p>
      </div>
    `;
  }
}

function updateEfficiencyMetrics(data) {
  // Eficiência Global
  const efficiency = data.efficiency || data.balancing?.efficiency;
  document.getElementById("global-efficiency").textContent =
    efficiency?.global_efficiency
      ? efficiency.global_efficiency.toFixed(2)
      : "-";

  // Perdas Totais
  document.getElementById("total-losses").textContent = efficiency?.total_losses
    ? efficiency.total_losses.toFixed(2) + " kW"
    : "-";

  // Pegada de Carbono
  document.getElementById("carbon-footprint").textContent = data
    .carbon_footprint?.total_co2_kg
    ? data.carbon_footprint.total_co2_kg.toFixed(2) + " kg"
    : "-";

  // Classificação
  document.getElementById("efficiency-class").textContent =
    data.carbon_footprint?.efficiency_class || "-";

  // Sugestões de energia renovável - VERSÃO COMPLETA
  const suggestionsDiv = document.getElementById("renewable-suggestions");
  const suggestions = data.renewable_suggestions;

  if (suggestions && suggestions.length > 0) {
    suggestionsDiv.innerHTML = suggestions
      .map(
        (s) => `
            <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 12px; color: #6b7280; font-weight: 500;">
                            Nó ${s.node_id}
                        </div>
                        <div style="font-size: 18px; font-weight: 700; color: #10b981; text-transform: uppercase;">
                            ${s.recommended_source.replace("_", " ")}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 14px; color: #059669; font-weight: 600;">
                            Score: ${(s.score * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding-top: 10px; border-top: 1px solid #e5e7eb;">
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #6b7280;">Carga Atual</div>
                        <div style="font-size: 14px; font-weight: 600; color: #374151;">${s.current_load.toFixed(
                          0
                        )} kW</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #6b7280;">Eficiência</div>
                        <div style="font-size: 14px; font-weight: 600; color: #374151;">${(
                          s.efficiency * 100
                        ).toFixed(0)}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #6b7280;">Redução CO₂</div>
                        <div style="font-size: 14px; font-weight: 600; color: #059669;">~${s.estimated_reduction_co2_kg.toFixed(
                          0
                        )} kg</div>
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  } else {
    suggestionsDiv.innerHTML =
      '<p style="color: #6b7280; font-size: 14px; padding: 20px; text-align: center; background: #f9fafb; border-radius: 8px;">Nenhuma sugestão disponível. Execute "Otimizar Eficiência" primeiro.</p>';
  }
}

async function updateEfficiencyTab() {
  try {
    const stats = await api.getStats();

    if (!stats.stats || !stats.stats.efficiency) {
      console.warn("Sem dados de eficiência");
      return;
    }

    const efficiency = stats.stats.efficiency;

    // Eficiência Global
    document.getElementById("global-efficiency").textContent =
      efficiency.global_efficiency
        ? efficiency.global_efficiency.toFixed(2)
        : "-";

    // Perdas Totais
    document.getElementById("total-losses").textContent =
      efficiency.total_losses
        ? efficiency.total_losses.toFixed(2) + " kW"
        : "-";

    // Pegada de Carbono - via endpoint de otimização
    const optimizeData = await api.optimizeEfficiency();

    if (optimizeData.success && optimizeData.carbon_footprint) {
      document.getElementById("carbon-footprint").textContent =
        optimizeData.carbon_footprint.total_co2_kg.toFixed(2) + " kg";

      document.getElementById("efficiency-class").textContent =
        optimizeData.carbon_footprint.efficiency_class || "-";

      // Sugestões renováveis
      const suggestionsDiv = document.getElementById("renewable-suggestions");
      if (
        optimizeData.renewable_suggestions &&
        optimizeData.renewable_suggestions.length > 0
      ) {
        suggestionsDiv.innerHTML = optimizeData.renewable_suggestions
          .slice(0, 5)
          .map(
            (s) => `
                    <div class="metric">
                        <span class="metric-label">Nó ${s.node_id}:</span>
                        <span class="metric-value">${s.recommended_source.replace(
                          "_",
                          " "
                        )}</span>
                    </div>
                `
          )
          .join("");
      }
    }
  } catch (error) {
    console.error("Erro ao atualizar aba de eficiência:", error);
  }
}

// ==================== CHARTS ====================

function initCharts() {
  // Load Chart
  const loadCtx = document.getElementById("load-chart").getContext("2d");
  loadChart = new Chart(loadCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Carga Atual (kW)",
          data: [],
          backgroundColor: "rgba(102, 126, 234, 0.5)",
          borderColor: "rgba(102, 126, 234, 1)",
          borderWidth: 2,
        },
        {
          label: "Capacidade (kW)",
          data: [],
          backgroundColor: "rgba(16, 185, 129, 0.5)",
          borderColor: "rgba(16, 185, 129, 1)",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true },
      },
    },
  });

  // Prediction Chart
  const predCtx = document.getElementById("prediction-chart").getContext("2d");
  predictionChart = new Chart(predCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Demanda Prevista (kW)",
          data: [],
          borderColor: "rgba(102, 126, 234, 1)",
          backgroundColor: "rgba(102, 126, 234, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

async function updateCharts() {
  try {
    // Atualiza gráfico de carga
    const nodesData = await api.getNodes();
    const top10 = nodesData.nodes.slice(0, 10);

    loadChart.data.labels = top10.map((n) => n.key);
    loadChart.data.datasets[0].data = top10.map((n) => n.data.current_load);
    loadChart.data.datasets[1].data = top10.map((n) => n.data.capacity);
    loadChart.update();

    // Atualiza gráfico de previsão com DADOS SINTÉTICOS
    if (top10.length > 0) {
      const baseLoad = top10[0].data.current_load;
      const predictions = [];

      // Gera curva de demanda típica (sobe durante o dia, desce à noite)
      for (let h = 1; h <= 24; h++) {
        let factor = 1.0;

        // Padrão de consumo: pico às 18h, mínimo às 3h
        if (h >= 6 && h <= 9) factor = 1.3; // Manhã: +30%
        else if (h >= 12 && h <= 14) factor = 1.2; // Almoço: +20%
        else if (h >= 18 && h <= 21) factor = 1.5; // Noite: +50% (pico)
        else if (h >= 22 || h <= 5) factor = 0.7; // Madrugada: -30%

        predictions.push(baseLoad * factor);
      }

      predictionChart.data.labels = Array.from(
        { length: 24 },
        (_, i) => `+${i + 1}h`
      );
      predictionChart.data.datasets[0].data = predictions;
      predictionChart.update();
    }
  } catch (error) {
    console.error("Erro ao atualizar gráficos:", error);
  }
}

// ==================== ROUTING ====================

async function resetSystem() {
  if (
    !confirm(
      "Tem certeza que deseja resetar o sistema? Todos os dados serão perdidos."
    )
  ) {
    return;
  }

  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Resetando...';

  try {
    const result = await api.request("/reset", { method: "POST" });

    if (result.success) {
      showNotification(
        "Sistema resetado! Pode inicializar novamente.",
        "success"
      );

      // Limpa a interface
      document.getElementById("total-nodes").textContent = "-";
      document.getElementById("total-load").textContent = "-";
      document.getElementById("utilization").textContent = "-";
      document.getElementById("overloaded-nodes").textContent = "-";
    }
  } catch (error) {
    showNotification("Erro ao resetar: " + error.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔄 Resetar Sistema";
  }
}

async function findRoute() {
  const source = document.getElementById("route-source").value;
  const destination = document.getElementById("route-destination").value;
  const algorithm = document.getElementById("route-algorithm").value;

  if (!source || !destination) {
    showNotification("Preencha origem e destino", "error");
    return;
  }

  try {
    const result = await api.findRoute(source, destination, algorithm);

    const resultDiv = document.getElementById("route-result");

    // Comparação de algoritmos, se vier do backend
    let comparisonHtml = "";
    if (result.comparison) {
      const dTime = result.comparison.dijkstra ?? null;
      const aTime = result.comparison.astar ?? null;

      if (dTime !== null || aTime !== null) {
        comparisonHtml = `
          <h5>Comparativo de Algoritmos</h5>
          <p><strong>Dijkstra:</strong> ${
            dTime !== null ? dTime.toFixed(3) + " ms" : "N/A"
          }</p>
          <p><strong>A*:</strong> ${
            aTime !== null ? aTime.toFixed(3) + " ms" : "N/A"
          }</p>
        `;
      }
    }

    // Verifica se encontrou rota
    if (result.success && result.route.path && result.route.path.length > 0) {
      // Formata custo (pode ser null se Infinity)
      const costText =
        result.route.cost !== null
          ? result.route.cost.toFixed(4)
          : "Infinito (sem rota direta)";
      const lossText = result.route.power_loss
        ? result.route.power_loss.toFixed(2)
        : "N/A";

      resultDiv.innerHTML = `
                <h4>✅ Rota Encontrada</h4>
                <p><strong>Caminho:</strong> ${result.route.path.join(
                  " → "
                )}</p>
                <p><strong>Custo:</strong> ${costText}</p>
                <p><strong>Saltos:</strong> ${result.route.hops}</p>
                <p><strong>Perda de Potência:</strong> ${lossText} kW</p>
                <p><strong>Tempo de Execução (${
                  result.route.algorithm
                }):</strong> ${(result.route.execution_time * 1000).toFixed(
        2
      )} ms</p>
                ${comparisonHtml}
            `;
    } else {
      resultDiv.innerHTML =
        '<p class="error">❌ Rota não encontrada ou nós desconectados</p>' +
        comparisonHtml;
    }

    // Atualiza painel de benchmark com novos tempos
    await updateBenchmarkPanel();
  } catch (error) {
    console.error("Erro completo:", error);
    showNotification("Erro ao buscar rota: " + error.message, "error");
    document.getElementById("route-result").innerHTML =
      '<p class="error">❌ Erro ao buscar rota</p>';
  }
}

// ==================== TABS ====================

function showTab(tabName) {
  // Remove active de todos
  document
    .querySelectorAll(".tab-btn")
    .forEach((btn) => btn.classList.remove("active"));
  document
    .querySelectorAll(".tab-content")
    .forEach((content) => content.classList.remove("active"));

  // Adiciona active no selecionado
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    const onclick = btn.getAttribute("onclick") || "";
    if (onclick.includes(`'${tabName}'`)) {
      btn.classList.add("active");
    }
  });

  document.getElementById(`tab-${tabName}`).classList.add("active");

  // Atualizações específicas por aba
  if (tabName === "efficiency") {
    updateEfficiencyTab(); 
  } else if (tabName === "ml") {
    updateMLPanel();
  } else if (tabName === "events") {
    updateEvents();
  } else if (tabName === "nodes") {
    updateNodesTable();
  }
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = "info") {
  console.log(`[${type.toUpperCase()}] ${message}`);
  alert(message);
}
