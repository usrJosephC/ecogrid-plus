/**
 * Lógica principal da aplicação frontend
 */

// Charts
let loadChart = null;
let predictionChart = null;

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

// ==================== SYSTEM ACTIONS ====================

async function initializeSystem() {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading"></span> Inicializando...';

  try {
    const result = await api.initialize(20, false);

    if (result.success) {
      showNotification("Sistema inicializado com sucesso!", "success");
      await refreshData();
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

      // Atualiza métricas de eficiência
      updateEfficiencyMetrics(result);
      await refreshData();
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
      const accuracy = (
        result.training_result.validation.accuracy * 100
      ).toFixed(1);
      showNotification(`Modelo treinado! Acurácia: ${accuracy}%`, "success");
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

    showNotification("Dados atualizados!", "info");
  } catch (error) {
    console.error("Erro ao atualizar dados:", error);
  }
}

// ==================== UI UPDATES ====================

function updateStats(stats) {
  document.getElementById("total-nodes").textContent =
    stats.network.node_count || "-";
  document.getElementById("total-load").textContent = stats.network.total_load
    ? stats.network.total_load.toFixed(1)
    : "-";
  document.getElementById("utilization").textContent = stats.network.utilization
    ? (stats.network.utilization * 100).toFixed(1)
    : "-";
  document.getElementById("overloaded-nodes").textContent =
    stats.network.overloaded_nodes || "0";
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

    if (eventsData.count === 0) {
      container.innerHTML = "<p>Nenhum evento crítico no momento.</p>";
      return;
    }

    container.innerHTML = eventsData.events
      .map(
        (event) => `
            <div class="event-item ${
              event.priority <= 2 ? "critical" : "high"
            }">
                <div class="event-title">${event.type.toUpperCase()} - Nó: ${
          event.node_id
        }</div>
                <div class="event-details">Prioridade: ${
                  event.priority
                } | ${JSON.stringify(event.data)}</div>
            </div>
        `
      )
      .join("");
  } catch (error) {
    console.error("Erro ao atualizar eventos:", error);
  }
}

function updateEfficiencyMetrics(data) {
    // Eficiência Global
    const efficiency = data.efficiency || data.balancing?.efficiency;
    document.getElementById('global-efficiency').textContent = 
        efficiency?.global_efficiency ? efficiency.global_efficiency.toFixed(2) : '-';
    
    // Perdas Totais
    document.getElementById('total-losses').textContent = 
        efficiency?.total_losses ? efficiency.total_losses.toFixed(2) + ' kW' : '-';
    
    // Pegada de Carbono
    document.getElementById('carbon-footprint').textContent = 
        data.carbon_footprint?.total_co2_kg ? data.carbon_footprint.total_co2_kg.toFixed(2) + ' kg' : '-';
    
    // Classificação
    document.getElementById('efficiency-class').textContent = 
        data.carbon_footprint?.efficiency_class || '-';
    
    // Sugestões de energia renovável
    const suggestionsDiv = document.getElementById('renewable-suggestions');
    if (data.renewable_suggestions && data.renewable_suggestions.length > 0) {
        suggestionsDiv.innerHTML = data.renewable_suggestions.map(s => `
            <div class="metric">
                <span class="metric-label">Nó ${s.node_id}:</span>
                <span class="metric-value">${s.recommended_source}</span>
            </div>
        `).join('');
    } else {
        suggestionsDiv.innerHTML = '<p>Nenhuma sugestão disponível no momento.</p>';
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

    // Atualiza gráfico de previsão
    if (top10.length > 0) {
      const prediction = await api.predictDemand(top10[0].key, 24);

      predictionChart.data.labels = prediction.predictions.map(
        (p, i) => `+${i + 1}h`
      );
      predictionChart.data.datasets[0].data = prediction.predictions.map(
        (p) => p.predicted_load
      );
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
    const source = document.getElementById('route-source').value;
    const destination = document.getElementById('route-destination').value;
    const algorithm = document.getElementById('route-algorithm').value;
    
    if (!source || !destination) {
        showNotification('Preencha origem e destino', 'error');
        return;
    }
    
    try {
        const result = await api.findRoute(source, destination, algorithm);
        
        const resultDiv = document.getElementById('route-result');
        
        // Verifica se encontrou rota
        if (result.success && result.route.path && result.route.path.length > 0) {
            // Formata custo (pode ser null se Infinity)
            const costText = result.route.cost !== null ? result.route.cost.toFixed(4) : 'Infinito (sem rota direta)';
            const lossText = result.route.power_loss ? result.route.power_loss.toFixed(2) : 'N/A';
            
            resultDiv.innerHTML = `
                <h4>✅ Rota Encontrada</h4>
                <p><strong>Caminho:</strong> ${result.route.path.join(' → ')}</p>
                <p><strong>Custo:</strong> ${costText}</p>
                <p><strong>Saltos:</strong> ${result.route.hops}</p>
                <p><strong>Perda de Potência:</strong> ${lossText} kW</p>
                <p><strong>Tempo de Execução:</strong> ${(result.route.execution_time * 1000).toFixed(2)} ms</p>
            `;
        } else {
            resultDiv.innerHTML = '<p class="error">❌ Rota não encontrada ou nós desconectados</p>';
        }
    } catch (error) {
        console.error('Erro completo:', error);
        showNotification('Erro ao buscar rota: ' + error.message, 'error');
        document.getElementById('route-result').innerHTML = '<p class="error">❌ Erro ao buscar rota</p>';
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
  event.target.classList.add("active");
  document.getElementById(`tab-${tabName}`).classList.add("active");
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = "info") {
  // Implementação simples com alert
  // Em produção, usar biblioteca como Toastify
  console.log(`[${type.toUpperCase()}] ${message}`);

  // Você pode implementar um sistema de toast aqui
  alert(message);
}
