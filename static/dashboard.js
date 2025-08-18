// Unified Dashboard JavaScript for Excalibur ERP
// Combines both provided scripts with optimizations and improvements

// Check if Chart.js is loaded
document.addEventListener("DOMContentLoaded", function () {
  if (typeof Chart === "undefined") {
    console.error("❌ Chart.js is not loaded! Charts will not work.");
  } else {
    console.log("✅ Chart.js loaded successfully:", Chart.version);
    // Register the datalabels plugin if available
    if (typeof ChartDataLabels !== "undefined") {
      Chart.register(ChartDataLabels);
      console.log("✅ Chart.js DataLabels plugin registered");
    } else {
      console.warn("⚠️ Chart.js DataLabels plugin not found");
    }
  }
});

// Global State Management
const AppState = {
  currentTab: "of-en-cours",
  currentViewMode: "overview",
  filters: {
    dateDebut: null,
    dateFin: null,
  },
  data: {
    ofEnCours: null,
    ofHistorique: null,
    ofCombined: null,
    alerts: null,
    kpis: null,
    filterOptions: null,
  },
  charts: {}, // Store chart instances for proper cleanup
  lastUpdate: null,
  isLoading: false,
};

// API Configuration
const API_BASE = "";
const API_ENDPOINTS = {
  config: "/api/config",
  dashboard: "/api/dashboard-data",
  kpis: "/api/kpis",
  filters: "/api/filters/options",
  alerts: "/api/alerts/",
  of: {
    en_cours: "/api/of/en_cours", // Use the correct endpoint
    histo: "/api/of/histo", // Use the correct endpoint
    all: "/api/of/all-ofs", // Use the correct endpoint
    current: "/api/of/current",
    filtered: "/api/of/filtered",
  },
  export: {
    csv: "/api/export/csv",
    excel: "/api/export/excel",
    txt: "/api/export/txt-resume",
    comprehensive_csv: "/api/export/comprehensive-csv",
    comprehensive_txt: "/api/export/comprehensive-txt",
    tab: "/api/export/tab",
  },
  health: {
    database: "/api/health/database",
  },
};

// Utility Functions
const Utils = {
  formatDate: (date) => {
    if (!date) return "";
    return new Date(date).toLocaleDateString("fr-FR");
  },

  formatNumber: (num) => {
    if (num === null || num === undefined) return "0";
    return new Intl.NumberFormat("fr-FR").format(num);
  },

  formatPercentage: (num) => {
    if (num === null || num === undefined) return "0%";
    return `${parseFloat(num).toFixed(1)}%`;
  },

  showAlert: (message, type = "info") => {
    const alertElement = document.getElementById(`${type}Alert`);
    const messageElement = document.getElementById(`${type}Message`);

    if (alertElement && messageElement) {
      messageElement.textContent = message;
      alertElement.style.display = "block";

      if (type !== "error" && type !== "connection") {
        setTimeout(() => {
          alertElement.style.display = "none";
        }, 5000);
      }
    }
  },

  hideAllAlerts: () => {
    ["info", "error", "connection"].forEach((type) => {
      const alert = document.getElementById(`${type}Alert`);
      if (alert) alert.style.display = "none";
    });
  },

  setLoading: (isLoading) => {
    AppState.isLoading = isLoading;
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (loadingIndicator) {
      loadingIndicator.style.display = isLoading ? "block" : "none";
    }
  },

  updateConnectionStatus: (isConnected) => {
    const connectedStatus = document.getElementById("connectionStatus");
    const errorStatus = document.getElementById("errorStatus");

    if (isConnected) {
      if (connectedStatus) connectedStatus.style.display = "inline-flex";
      if (errorStatus) errorStatus.style.display = "none";
    } else {
      if (connectedStatus) connectedStatus.style.display = "none";
      if (errorStatus) errorStatus.style.display = "inline-flex";
    }
  },

  getStatusClass: (status) => {
    const statusMap = {
      C: "primary", // En cours
      T: "success", // Terminé
      A: "warning", // Arrêté
      P: "info", // Planifié
      E: "danger", // Erreur
    };
    return statusMap[status] || "secondary";
  },

  getChargeBadgeClass: (percentage) => {
    const pct = parseFloat(percentage) || 0;
    if (pct > 100) return "danger";
    if (pct > 80) return "warning";
    if (pct > 60) return "info";
    return "success";
  },

  getPriorityBadgeClass: (priority) => {
    switch (priority) {
      case "URGENT":
        return "danger";
      case "PRIORITAIRE":
        return "warning";
      case "NORMAL":
        return "success";
      default:
        return "secondary";
    }
  },

  getPriorityRowClass: (priority) => {
    switch (priority) {
      case "URGENT":
        return "table-danger";
      case "PRIORITAIRE":
        return "table-warning";
      default:
        return "";
    }
  },
};

// API Service
const ApiService = {
  async makeRequest(url, options = {}) {
    try {
      const response = await fetch(API_BASE + url, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      Utils.updateConnectionStatus(true);
      return data;
    } catch (error) {
      console.error("API Request failed:", error);
      Utils.updateConnectionStatus(false);
      throw error;
    }
  },

  async getDashboardData(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        params.append(key, value);
      }
    });

    const url = `${API_ENDPOINTS.dashboard}?${params.toString()}`;
    return await this.makeRequest(url);
  },

  async getKPIs(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        params.append(key, value);
      }
    });

    const url = `${API_ENDPOINTS.kpis}?${params.toString()}`;
    return await this.makeRequest(url);
  },

  async getFilterOptions() {
    return await this.makeRequest(API_ENDPOINTS.filters);
  },

  async getAlerts() {
    return await this.makeRequest(API_ENDPOINTS.alerts);
  },

  async sendTestAlert(
    title = "Test Alert",
    message = "This is a test alert",
    severity = "medium"
  ) {
    const params = new URLSearchParams({
      title: title,
      message: message,
      severity: severity,
      send_email: "true",
    });
    return await this.makeRequest(`${API_ENDPOINTS.alerts}test/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });
  },

  async checkProductionAlerts() {
    return await this.makeRequest(`${API_ENDPOINTS.alerts}check`, {
      method: "POST",
    });
  },

  async getOFData(type = "all", filters = {}) {
    const endpoint = API_ENDPOINTS.of[type] || API_ENDPOINTS.of.all;
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        params.append(key, value);
      }
    });

    const url = `${endpoint}?${params.toString()}`;
    return await this.makeRequest(url);
  },
};

// Filter Management
const FilterManager = {
  init() {
    this.setupEventListeners();
    this.loadFilterOptions();
    this.setDefaultDates();
  },

  setupEventListeners() {
    // Date filters
    document
      .getElementById("dateDebut")
      ?.addEventListener("change", this.onFilterChange.bind(this));
    document
      .getElementById("dateFin")
      ?.addEventListener("change", this.onFilterChange.bind(this));

    // Date range toggle
    const enableDateRange = document.getElementById("enableDateRange");
    const dateRangeContainer = document.getElementById("dateRangeContainer");

    if (enableDateRange && dateRangeContainer) {
      enableDateRange.addEventListener("change", function () {
        if (this.checked) {
          dateRangeContainer.style.display = "block";
          FilterManager.setDefaultDates();
        } else {
          dateRangeContainer.style.display = "none";
          document.getElementById("dateDebut").value = "";
          document.getElementById("dateFin").value = "";
          AppState.filters.dateDebut = null;
          AppState.filters.dateFin = null;
          DataManager.refreshCurrentView();
        }
      });
    }
  },

  async loadFilterOptions() {
    // No longer needed since we only have date filters
    console.log("Filter options loading skipped - only date filters are used");
  },

  populateFilterDropdowns(options) {
    // No longer needed since we removed all dropdown filters
    console.log(
      "Filter dropdown population skipped - only date filters are used"
    );
  },

  setDefaultDates() {
    const today = new Date();
    const threeMonthsAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);

    const dateDebut = document.getElementById("dateDebut");
    const dateFin = document.getElementById("dateFin");

    if (dateDebut) {
      dateDebut.value = threeMonthsAgo.toISOString().split("T")[0];
      AppState.filters.dateDebut = dateDebut.value;
    }

    if (dateFin) {
      dateFin.value = today.toISOString().split("T")[0];
      AppState.filters.dateFin = dateFin.value;
    }
  },

  onFilterChange() {
    this.updateFiltersFromUI();
    DataManager.refreshCurrentView();
  },

  updateFiltersFromUI() {
    AppState.filters.dateDebut =
      document.getElementById("dateDebut")?.value || null;
    AppState.filters.dateFin =
      document.getElementById("dateFin")?.value || null;
  },

  getActiveFilters() {
    return { ...AppState.filters };
  },

  clearAllFilters() {
    document.getElementById("dateDebut").value = "";
    document.getElementById("dateFin").value = "";

    AppState.filters = {
      dateDebut: null,
      dateFin: null,
    };

    this.setDefaultDates();
    DataManager.refreshCurrentView();
  },
};

// Data Management
const DataManager = {
  // Chart management functions
  destroyChart(chartId) {
    if (AppState.charts[chartId]) {
      AppState.charts[chartId].destroy();
      delete AppState.charts[chartId];
      console.log(`🗑️ Destroyed chart: ${chartId}`);
    }
  },

  destroyAllCharts() {
    Object.keys(AppState.charts).forEach((chartId) => {
      this.destroyChart(chartId);
    });
    console.log("🗑️ All charts destroyed");
  },

  createChart(canvasId, config) {
    // Destroy existing chart if it exists
    this.destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.error(`❌ Canvas not found: ${canvasId}`);
      return null;
    }

    try {
      const chart = new Chart(canvas, config);
      AppState.charts[canvasId] = chart;
      console.log(`✅ Created chart: ${canvasId}`);
      return chart;
    } catch (error) {
      console.error(`❌ Failed to create chart ${canvasId}:`, error);
      return null;
    }
  },

  async loadInitialData() {
    Utils.setLoading(true);

    try {
      await this.loadConfiguration();
      await this.loadOFEnCoursData();
      await this.loadAlerts();
      Utils.showAlert("Données chargées avec succès", "connection");
      AppState.lastUpdate = new Date();
      this.updateLastRefreshTime();
    } catch (error) {
      console.error("Failed to load initial data:", error);
      Utils.showAlert("Erreur lors du chargement des données", "error");
    } finally {
      Utils.setLoading(false);
    }
  },

  async loadConfiguration() {
    try {
      const response = await ApiService.makeRequest(API_ENDPOINTS.config);
      if (response.success) {
        console.log("Configuration loaded:", response.data);
      }
    } catch (error) {
      console.warn("Failed to load configuration:", error);
    }
  },

  async loadOFEnCoursData() {
    try {
      console.log("🔄 Loading OF En Cours data...");
      const filters = FilterManager.getActiveFilters();
      console.log("📊 Active filters:", filters);

      const response = await ApiService.getOFData("en_cours", filters);
      console.log("📥 API Response:", response);

      if (response && response.success) {
        // Extract the actual data array from the response
        const actualData = response.data?.of_list || response.data || [];
        AppState.data.ofEnCours = actualData;
        console.log(
          "✅ Data loaded successfully:",
          actualData?.length || 0,
          "records"
        );
        this.renderOFTable("enCours", actualData);
        this.renderKPICards("enCours", actualData);
      } else {
        console.warn("⚠️ API response indicates failure:", response);
        this.renderTableError("enCours", "No data received from server");
      }
    } catch (error) {
      console.error("❌ Failed to load OF En Cours data:", error);
      this.renderTableError("enCours", error.message);
    }
  },

  async loadOFHistoriqueData() {
    try {
      console.log("🔄 Loading OF Historique data...");
      const filters = FilterManager.getActiveFilters();
      const response = await ApiService.getOFData("histo", filters);
      console.log("📥 Historique API Response:", response);

      if (response && response.success) {
        // Extract the actual data array from the response
        const actualData = response.data?.of_list || response.data || [];
        AppState.data.ofHistorique = actualData;
        console.log(
          "✅ Historique data loaded successfully:",
          actualData?.length || 0,
          "records"
        );
        this.renderOFTable("historique", actualData);
        this.renderKPICards("historique", actualData);
      } else {
        console.warn("⚠️ Historique API response indicates failure:", response);
        this.renderTableError(
          "historique",
          "No historical data received from server"
        );
      }
    } catch (error) {
      console.error("❌ Failed to load OF Historique data:", error);
      this.renderTableError("historique", error.message);
    }
  },

  async loadOFCombinedData() {
    try {
      console.log("🔄 Loading OF Combined data...");
      const filters = FilterManager.getActiveFilters();
      // Add enable_date_filter parameter for combined view
      filters.enable_date_filter = "true";
      const response = await ApiService.getOFData("all", filters);
      console.log("📥 Combined API Response:", response);

      if (response && response.success) {
        // Extract the actual data array from the response
        const actualData = response.data?.of_list || response.data || [];
        AppState.data.ofCombined = actualData;
        console.log(
          "✅ Combined data loaded successfully:",
          actualData?.length || 0,
          "records"
        );
        this.renderOFTable("combined", actualData);
        this.renderKPICards("combined", actualData);
      } else {
        console.warn("⚠️ Combined API response indicates failure:", response);
        this.renderTableError(
          "combined",
          "No combined data received from server"
        );
      }
    } catch (error) {
      console.error("❌ Failed to load OF Combined data:", error);
      this.renderTableError("combined", error.message);
    }
  },

  async loadAlerts() {
    try {
      const response = await ApiService.getAlerts();
      if (response.success) {
        AppState.data.alerts = response.data;
        this.renderAlerts();
      }
    } catch (error) {
      console.error("Failed to load alerts:", error);
    }
  },

  renderKPICards(type, data) {
    console.log(`📊 Rendering KPI cards for type: ${type}, data:`, data);

    const containerId = `${type}KpiCards`;
    const container = document.getElementById(containerId);

    console.log(`🔍 Looking for KPI container: ${containerId}`);
    console.log(`📍 Container element:`, container);

    if (!container) {
      console.error(`❌ KPI container not found: ${containerId}`);
      return;
    }

    if (!data) {
      console.warn(`⚠️ No data provided for KPI rendering`);
      return;
    }

    // Calculate KPIs based on data
    const totalOrders = Array.isArray(data) ? data.length : 0;
    let activeOrders = 0;
    let completedOrders = 0;
    let avgProgress = 0;
    let alertsCount = 0;
    let avgEfficiency = 0;

    if (Array.isArray(data) && data.length > 0) {
      if (type === "historique") {
        completedOrders = totalOrders;
        avgEfficiency =
          data.reduce(
            (sum, item) => sum + (parseFloat(item.EFFICACITE) || 0),
            0
          ) / data.length;
      } else {
        activeOrders = data.filter((item) => item.STATUT === "C").length;
        completedOrders = data.filter((item) => item.STATUT === "T").length;
        alertsCount = data.filter((item) => item.Alerte_temps).length;
      }

      avgProgress =
        data.reduce(
          (sum, item) => sum + (parseFloat(item.Avancement_PROD) || 0),
          0
        ) / data.length;
    }

    const completionRate =
      totalOrders > 0 ? (completedOrders / totalOrders) * 100 : 0;

    // Enhanced KPI cards with icons and better styling
    let kpiHtml = "";

    if (type === "enCours") {
 kpiHtml = `
  <div class="row">
    <div class="col-md-4">
      <div class="kpi-card primary">
        <i class="fas fa-clipboard-list kpi-icon"></i>
        <div class="kpi-value">${Utils.formatNumber(totalOrders)}</div>
        <div class="kpi-label">Total OF En Cours</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="kpi-card warning">
        <i class="fas fa-play kpi-icon"></i>
        <div class="kpi-value">${Utils.formatNumber(activeOrders)}</div>
        <div class="kpi-label">Actifs</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="kpi-card info">
        <i class="fas fa-chart-line kpi-icon"></i>
        <div class="kpi-value">${Utils.formatPercentage(avgProgress * 100)}</div>
        <div class="kpi-label">Avancement Moyen</div>
      </div>
    </div>
  </div>
`;

    } else if (type === "historique") {
      kpiHtml = `
        <div class="col-md-3">
          <div class="kpi-card success">
            <i class="fas fa-check-circle kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(totalOrders)}</div>
            <div class="kpi-label">OF Terminés</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card info">
            <i class="fas fa-percentage kpi-icon"></i>
            <div class="kpi-value">${Utils.formatPercentage(
              avgEfficiency * 100
            )}</div>
            <div class="kpi-label">Efficacité Moyenne</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card primary">
            <i class="fas fa-chart-bar kpi-icon"></i>
            <div class="kpi-value">${Utils.formatPercentage(
              completionRate
            )}</div>
            <div class="kpi-label">Taux Complétion</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card warning">
            <i class="fas fa-clock kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(
              Math.round(avgProgress * 100)
            )}%</div>
            <div class="kpi-label">Performance</div>
          </div>
        </div>
      `;
    } else {
      // combined
      kpiHtml = `
        <div class="col-md-3">
          <div class="kpi-card primary">
            <i class="fas fa-list kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(totalOrders)}</div>
            <div class="kpi-label">Total OF</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card warning">
            <i class="fas fa-play kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(activeOrders)}</div>
            <div class="kpi-label">En Cours</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card success">
            <i class="fas fa-check kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(completedOrders)}</div>
            <div class="kpi-label">Terminés</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="kpi-card ${alertsCount > 0 ? "danger" : "info"}">
            <i class="fas fa-bell kpi-icon"></i>
            <div class="kpi-value">${Utils.formatNumber(alertsCount)}</div>
            <div class="kpi-label">Alertes</div>
          </div>
        </div>
      `;
    }

    container.innerHTML = `<div class="row g-3">${kpiHtml}</div>`;

    // Render charts after KPI cards
    this.renderCharts(type, data);
  },

  renderCharts(type, data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn(`⚠️ No data available for charts: ${type}`);
      return;
    }

    console.log(`📊 Rendering charts for type: ${type}`);

    // Chart.js default configuration
    Chart.defaults.font.family =
      "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.position = "bottom";
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;

    switch (type) {
      case "enCours":
        this.renderEnCoursCharts(data);
        break;
      case "historique":
        this.renderHistoriqueCharts(data);
        break;
      case "combined":
        this.renderCombinedCharts(data);
        break;
    }
  },

  renderEnCoursCharts(data) {
    // Status Distribution Chart
    this.renderStatusChart("enCoursStatusChart", data);

    // Progress Distribution Chart
    this.renderProgressChart("enCoursProgressChart", data);

    // Priority Distribution Chart
    this.renderPriorityChart("enCoursPriorityChart", data);

    // Timeline Chart
    this.renderTimelineChart("enCoursTimelineChart", data);
  },

  renderHistoriqueCharts(data) {
    // Efficiency Trend Chart
    this.renderEfficiencyChart("historiqueEfficiencyChart", data);

    // Completion Rate Chart
    this.renderCompletionChart("historiqueCompletionChart", data);

    // Duration vs Planned Chart
    this.renderDurationChart("historiqueDurationChart", data);

    // Volume by Month Chart
    this.renderVolumeChart("historiqueVolumeChart", data);
  },

  renderCombinedCharts(data) {
    // Source Distribution Chart
    this.renderSourceChart("combinedSourceChart", data);

    // Timeline Distribution Chart
    this.renderTimelineChart("combinedTimelineChart", data);

    // Global Status Chart
    this.renderStatusChart("combinedStatusChart", data);

    // Client Distribution Chart
    this.renderClientChart("combinedClientChart", data);

    // Family Distribution Chart
    this.renderFamilyChart("combinedFamilyChart", data);
  },

  renderStatusChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const statusCounts = {};
    data.forEach((item) => {
      const status = item.STATUT || "Unknown";
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });

    const statusLabels = {
      C: "En Cours",
      T: "Terminé",
      A: "Arrêté",
      P: "Planifié",
      E: "Erreur",
    };

    const labels = Object.keys(statusCounts).map(
      (key) => statusLabels[key] || key
    );
    const values = Object.values(statusCounts);
    const colors = ["#3498db", "#27ae60", "#e74c3c", "#f39c12", "#9b59b6"];

    DataManager.createChart(canvas.id, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors,
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return `${context.label}: ${context.parsed} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  },

  renderProgressChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const progressRanges = {
      "0-25%": 0,
      "25-50%": 0,
      "50-75%": 0,
      "75-100%": 0,
      Terminé: 0,
    };

    data.forEach((item) => {
      const progress = parseFloat(item.Avancement_PROD) || 0;
      if (progress === 1) {
        progressRanges["Terminé"]++;
      } else if (progress >= 0.75) {
        progressRanges["75-100%"]++;
      } else if (progress >= 0.5) {
        progressRanges["50-75%"]++;
      } else if (progress >= 0.25) {
        progressRanges["25-50%"]++;
      } else {
        progressRanges["0-25%"]++;
      }
    });

    DataManager.createChart(canvas.id, {
      type: "bar",
      data: {
        labels: Object.keys(progressRanges),
        datasets: [
          {
            label: "Nombre d'OF",
            data: Object.values(progressRanges),
            backgroundColor: [
              "#e74c3c",
              "#f39c12",
              "#3498db",
              "#27ae60",
              "#2ecc71",
            ],
            borderWidth: 1,
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
  },

  renderPriorityChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const priorityCounts = {};
    data.forEach((item) => {
      const priority = item.PRIORITE || "NORMAL";
      priorityCounts[priority] = (priorityCounts[priority] || 0) + 1;
    });

    const labels = Object.keys(priorityCounts);
    const values = Object.values(priorityCounts);
    const colors = labels.map((label) => {
      switch (label) {
        case "URGENT":
          return "#e74c3c";
        case "PRIORITAIRE":
          return "#f39c12";
        case "NORMAL":
          return "#27ae60";
        default:
          return "#95a5a6";
      }
    });

    DataManager.createChart(canvas.id, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors,
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  },

  renderTimelineChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Group data by month
    const monthCounts = {};
    data.forEach((item) => {
      const date = new Date(item.LANCEMENT_AU_PLUS_TARD || item.DATE_FIN);
      if (!isNaN(date.getTime())) {
        const monthKey = `${date.getFullYear()}-${String(
          date.getMonth() + 1
        ).padStart(2, "0")}`;
        monthCounts[monthKey] = (monthCounts[monthKey] || 0) + 1;
      }
    });

    const sortedMonths = Object.keys(monthCounts).sort();
    const labels = sortedMonths.map((month) => {
      const [year, monthNum] = month.split("-");
      return new Date(year, monthNum - 1).toLocaleDateString("fr-FR", {
        month: "short",
        year: "numeric",
      });
    });
    const values = sortedMonths.map((month) => monthCounts[month]);

    DataManager.createChart(canvas.id, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Nombre d'OF",
            data: values,
            borderColor: "#3498db",
            backgroundColor: "rgba(52, 152, 219, 0.1)",
            borderWidth: 3,
            fill: true,
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
            },
          },
        },
      },
    });
  },

  renderEfficiencyChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Group efficiency by month
    const monthlyEfficiency = {};
    data.forEach((item) => {
      const date = new Date(item.DATE_FIN);
      const efficiency = parseFloat(item.EFFICACITE) || 0;
      if (!isNaN(date.getTime()) && efficiency > 0) {
        const monthKey = `${date.getFullYear()}-${String(
          date.getMonth() + 1
        ).padStart(2, "0")}`;
        if (!monthlyEfficiency[monthKey]) {
          monthlyEfficiency[monthKey] = { total: 0, count: 0 };
        }
        monthlyEfficiency[monthKey].total += efficiency;
        monthlyEfficiency[monthKey].count += 1;
      }
    });

    const sortedMonths = Object.keys(monthlyEfficiency).sort();
    const labels = sortedMonths.map((month) => {
      const [year, monthNum] = month.split("-");
      return new Date(year, monthNum - 1).toLocaleDateString("fr-FR", {
        month: "short",
        year: "numeric",
      });
    });
    const avgEfficiency = sortedMonths.map((month) =>
      (
        (monthlyEfficiency[month].total / monthlyEfficiency[month].count) *
        100
      ).toFixed(1)
    );

    DataManager.createChart(canvas.id, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Efficacité Moyenne (%)",
            data: avgEfficiency,
            borderColor: "#27ae60",
            backgroundColor: "rgba(39, 174, 96, 0.1)",
            borderWidth: 3,
            fill: true,
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 120,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
  },

  renderCompletionChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const completionData = {
      "Terminé à 100%": 0,
      "Partiellement terminé": 0,
      "Non terminé": 0,
    };

    data.forEach((item) => {
      const qtyDemanded = parseFloat(item.QUANTITE_DEMANDEE) || 0;
      const qtyProduced = parseFloat(item.CUMUL_ENTREES) || 0;

      if (qtyProduced >= qtyDemanded && qtyDemanded > 0) {
        completionData["Terminé à 100%"]++;
      } else if (qtyProduced > 0) {
        completionData["Partiellement terminé"]++;
      } else {
        completionData["Non terminé"]++;
      }
    });

    DataManager.createChart(canvas.id, {
      type: "doughnut",
      data: {
        labels: Object.keys(completionData),
        datasets: [
          {
            data: Object.values(completionData),
            backgroundColor: ["#27ae60", "#f39c12", "#e74c3c"],
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  },

  renderDurationChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const durationData = data
      .map((item) => {
        const planned = parseFloat(item.DUREE_PREVUE) || 0;
        const actual = parseFloat(item.DUREE_REELLE) || 0;
        return {
          of: item.OF,
          planned: planned,
          actual: actual,
          variance: actual - planned,
        };
      })
      .filter((item) => item.planned > 0 && item.actual > 0)
      .slice(0, 10); // Top 10

    DataManager.createChart(canvas.id, {
      type: "bar",
      data: {
        labels: durationData.map((item) => item.of),
        datasets: [
          {
            label: "Durée Prévue (h)",
            data: durationData.map((item) => item.planned),
            backgroundColor: "#3498db",
            borderWidth: 1,
          },
          {
            label: "Durée Réelle (h)",
            data: durationData.map((item) => item.actual),
            backgroundColor: "#e74c3c",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  },

  renderVolumeChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Group volume by month
    const monthlyVolume = {};
    data.forEach((item) => {
      const date = new Date(item.DATE_FIN);
      const quantity = parseFloat(item.QUANTITE_DEMANDEE) || 0;
      if (!isNaN(date.getTime()) && quantity > 0) {
        const monthKey = `${date.getFullYear()}-${String(
          date.getMonth() + 1
        ).padStart(2, "0")}`;
        monthlyVolume[monthKey] = (monthlyVolume[monthKey] || 0) + quantity;
      }
    });

    const sortedMonths = Object.keys(monthlyVolume).sort();
    const labels = sortedMonths.map((month) => {
      const [year, monthNum] = month.split("-");
      return new Date(year, monthNum - 1).toLocaleDateString("fr-FR", {
        month: "short",
        year: "numeric",
      });
    });
    const volumes = sortedMonths.map((month) => monthlyVolume[month]);

    DataManager.createChart(canvas.id, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Volume Produit",
            data: volumes,
            backgroundColor: "rgba(52, 152, 219, 0.8)",
            borderColor: "#3498db",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  },

  renderSourceChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Determine source based on data structure
    const sourceCounts = {
      "OF En Cours": 0,
      "OF Historique": 0,
    };

    data.forEach((item) => {
      if (item.STATUT === "T" || item.DATE_FIN) {
        sourceCounts["OF Historique"]++;
      } else {
        sourceCounts["OF En Cours"]++;
      }
    });

    DataManager.createChart(canvas.id, {
      type: "pie",
      data: {
        labels: Object.keys(sourceCounts),
        datasets: [
          {
            data: Object.values(sourceCounts),
            backgroundColor: ["#3498db", "#27ae60"],
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  },

  renderClientChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const clientCounts = {};
    data.forEach((item) => {
      const client = item.CLIENT || "Non spécifié";
      clientCounts[client] = (clientCounts[client] || 0) + 1;
    });

    // Get top 5 clients
    const sortedClients = Object.entries(clientCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);

    const labels = sortedClients.map(([client]) => client);
    const values = sortedClients.map(([, count]) => count);
    const colors = ["#3498db", "#27ae60", "#f39c12", "#e74c3c", "#9b59b6"];

    DataManager.createChart(canvas.id, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors,
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  },

  renderFamilyChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const familyCounts = {};
    data.forEach((item) => {
      const family = item.FAMILLE_TECHNIQUE || "Non classé";
      familyCounts[family] = (familyCounts[family] || 0) + 1;
    });

    const labels = Object.keys(familyCounts);
    const values = Object.values(familyCounts);

    DataManager.createChart(canvas.id, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Nombre d'OF",
            data: values,
            backgroundColor: "rgba(155, 89, 182, 0.8)",
            borderColor: "#9b59b6",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
  },

  renderOFTable(type, data) {
    console.log(`🎨 Rendering table for type: ${type}, data:`, data);

    const headerId = `${type}Header`;
    const bodyId = `${type}Body`;
    const headerElement = document.getElementById(headerId);
    const bodyElement = document.getElementById(bodyId);

    console.log(`🔍 Looking for elements: ${headerId}, ${bodyId}`);
    console.log(`📍 Header element:`, headerElement);
    console.log(`📍 Body element:`, bodyElement);

    if (!headerElement || !bodyElement) {
      console.error(`❌ Table elements not found for type: ${type}`);
      return;
    }

    // Define columns
    const columns = [
      { key: "NUMERO_OFDA", label: "N° OF" },
      { key: "PRODUIT", label: "Produit" },
      { key: "DESIGNATION", label: "Désignation" },
      { key: "STATUT", label: "Statut" },
      { key: "LANCEMENT_AU_PLUS_TARD", label: "Lancement" },
      { key: "DUREE_PREVUE", label: "DUREE PREVUE" },
      { key: "CUMUL_TEMPS_PASSES", label: "C.TEMPS.PASSES" },
      { key: "QUANTITE_DEMANDEE", label: "Qté Demandée" },
      { key: "CUMUL_ENTREES", label: "Qté Produite" },
      { key: "Avancement_PROD", label: "Avancement Prod" },
      { key: "Avancement_temps", label: "Avancement Temp" },

    ];

    // Add source column for combined view
    if (type === "combined") {
      columns.push({ key: "SOURCE_TABLE", label: "Source" });
    }

    // Render header
    headerElement.innerHTML = `
      <tr>
        ${columns.map((col) => `<th>${col.label}</th>`).join("")}
        <th>Actions</th>
      </tr>
    `;

    // Render body
    if (!data || !Array.isArray(data) || data.length === 0) {
      bodyElement.innerHTML = `
        <tr>
          <td colspan="${columns.length + 1}" class="text-center text-muted">
            <i class="fas fa-spinner fa-spin"></i> Aucune donnée disponible
          </td>
        </tr>
      `;
      return;
    }

    const rowsHtml = data
      .slice(0, 100)
      .map((row) => {
        const statusClass = Utils.getStatusClass(row.STATUT);
        const progressPercentage = Math.round(
          (parseFloat(row.Avancement_PROD) || 0) * 100
        );
 const progressTempPercentage = Math.round(
          (parseFloat(row.Avancement_temps) || 0) * 100
        );
        return `
        <tr>
          ${columns
            .map((col) => {
              let value = row[col.key];

              if (col.key === "Avancement_PROD") {
                value = `
                <div class="progress" style="height: 20px;">
                  <div class="progress-bar bg-${statusClass}"
                       role="progressbar"
                       style="width: ${progressPercentage}%"
                       aria-valuenow="${progressPercentage}"
                       aria-valuemin="0"
                       aria-valuemax="100">
                    ${progressPercentage}%
                  </div>
                </div>
              `;
              }else if (col.key === "Avancement_temps") {
                value = `
                <div class="progress" style="height: 20px;">
                  <div class="progress-bar bg-${statusClass}"
                       role="progressbar"
                       style="width: ${progressTempPercentage}%"
                       aria-valuenow="${progressTempPercentage}"
                       aria-valuemin="0"
                       aria-valuemax="100">
                    ${progressTempPercentage}%
                  </div>
                </div>
              `;
              } else if (col.key === "STATUT") {
                value = `<span class="badge bg-${statusClass}">${
                  value || "N/A"
                }</span>`;
              } else if (col.key === "LANCEMENT_AU_PLUS_TARD") {
                value = Utils.formatDate(value);
              } else if (col.key === "SOURCE_TABLE") {
                value = value === "OF_DA" ? "En Cours" : "Historique";
              } else if (typeof value === "number") {
                value = Utils.formatNumber(value);
              } else {
                value = value || "N/A";
              }

              return `<td>${value}</td>`;
            })
            .join("")}
          <td>
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-outline-primary btn-sm"
                      onclick="DataManager.showOrderDetails('${
                        row.NUMERO_OFDA
                      }')"
                      title="Voir détails">
                <i class="fas fa-eye"></i>
              </button>
              <button class="btn btn-outline-secondary btn-sm"
                      onclick="ExportManager.exportSingleOrder('${
                        row.NUMERO_OFDA
                      }')"
                      title="Exporter">
                <i class="fas fa-download"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
      })
      .join("");

    bodyElement.innerHTML = rowsHtml;

    // Add enhanced table classes
    const tableElement = headerElement.closest("table");
    if (tableElement) {
      tableElement.classList.add("table-enhanced");
      tableElement.classList.remove("table-striped", "table-hover");
    }

    console.log(
      `✅ Table rendered successfully for ${type} with ${data.length} rows`
    );
  },

  renderTableError(type, errorMessage) {
    const bodyId = `${type}Body`;
    const bodyElement = document.getElementById(bodyId);

    if (bodyElement) {
      bodyElement.innerHTML = `
        <tr>
          <td colspan="10" class="text-center">
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-triangle me-2"></i>
              Erreur: ${errorMessage}
              <button class="btn btn-sm btn-outline-danger ms-2"
                      onclick="DataManager.refreshCurrentView()">
                Réessayer
              </button>
            </div>
          </td>
        </tr>
      `;
    }
  },

  renderAlerts() {
    const alertsContainer = document.getElementById("alertsContainer");
    if (!alertsContainer) return;

    const alerts = AppState.data.alerts || [];

    if (alerts.length === 0) {
      alertsContainer.innerHTML = `
        <div class="text-center text-muted">
          <i class="fas fa-check-circle text-success me-2"></i>
          Aucune alerte active
        </div>
      `;
      return;
    }

    const alertsHtml = alerts
      .slice(0, 5)
      .map((alert) => {
        const severityClass =
          {
            critical: "danger",
            high: "warning",
            medium: "info",
            low: "secondary",
          }[alert.severity] || "secondary";

        return `
        <div class="alert alert-${severityClass} alert-dismissible fade show mb-2" role="alert">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <strong>${alert.title}</strong>
              <div class="small">${alert.message}</div>
              <div class="small text-muted">
                ${Utils.formatDate(alert.created_at)} - ${alert.category}
              </div>
            </div>
            <div class="ms-3">
              <span class="badge bg-${severityClass}">${alert.severity.toUpperCase()}</span>
            </div>
          </div>
        </div>
      `;
      })
      .join("");

    alertsContainer.innerHTML = alertsHtml;
  },

  updateDataSummary() {
    const dataCount = document.getElementById("dataCount");
    const lastRefresh = document.getElementById("lastRefresh");
    const systemStatus = document.getElementById("systemStatus");
    const responseTime = document.getElementById("responseTime");

    if (dataCount) {
      const totalRecords =
        (AppState.data.ofEnCours?.length || 0) +
        (AppState.data.ofHistorique?.length || 0) +
        (AppState.data.ofCombined?.length || 0);
      dataCount.textContent = Utils.formatNumber(totalRecords);
    }

    if (lastRefresh && AppState.lastUpdate) {
      lastRefresh.textContent = Utils.formatDate(AppState.lastUpdate);
    }

    if (systemStatus) {
      systemStatus.textContent = AppState.isLoading
        ? "Chargement..."
        : "Opérationnel";
    }

    if (responseTime) {
      responseTime.textContent = "< 1s"; // Simulated
    }
  },

  updateLastRefreshTime() {
    const lastUpdateElement = document.getElementById("lastUpdateTime");
    if (lastUpdateElement && AppState.lastUpdate) {
      lastUpdateElement.textContent = `Dernière mise à jour: ${AppState.lastUpdate.toLocaleTimeString(
        "fr-FR"
      )}`;
    }
  },

  showOrderDetails(orderId) {
    console.log("Show details for order:", orderId);
    Utils.showAlert(`Détails pour la commande ${orderId}`, "info");
  },

  async refreshCurrentView() {
    Utils.setLoading(true);

    try {
      switch (AppState.currentTab) {
        case "of-en-cours":
          await this.loadOFEnCoursData();
          break;
        case "of-historique":
          await this.loadOFHistoriqueData();
          break;
        case "of-combined":
          await this.loadOFCombinedData();
          break;
      }

      AppState.lastUpdate = new Date();
      this.updateLastRefreshTime();
      Utils.showAlert("Données actualisées", "connection");
    } catch (error) {
      console.error("Failed to refresh data:", error);
      Utils.showAlert("Erreur lors de l'actualisation", "error");
    } finally {
      Utils.setLoading(false);
    }
  },
};

// Tab Management
const TabManager = {
  currentTab: "of-en-cours",
  tabConfigs: {
    "of-en-cours": {
      endpoint: API_ENDPOINTS.of.en_cours,
      kpiContainerId: "enCoursKpiCards",
      tableId: "enCoursTable",
      headerId: "enCoursHeader",
      bodyId: "enCoursBody",
      columns: [
        { field: "NUMERO_OFDA", label: "N° OF" },
        { field: "PRODUIT", label: "Produit" },
        { field: "DESIGNATION", label: "Désignation" },
        { field: "STATUT", label: "Statut" },
        { key: "DUREE_PREVUE", label: "DUREE PREVUE" },
        { key: "CUMUL_TEMPS_PASSES", label: "C.TEMPS.PASSES" },
        { field: "Avancement_PROD", label: "Avanc. Prod" },
        { field: "Avancement_temps", label: "Avanc. Temps" },
        { field: "EFFICACITE", label: "Efficacité" },
      ],
    },
    "of-historique": {
      endpoint: API_ENDPOINTS.of.histo,
      kpiContainerId: "historiqueKpiCards",
      tableId: "historiqueTable",
      headerId: "historiqueHeader",
      bodyId: "historiqueBody",
      columns: [
        { field: "NUMERO_OFDA", label: "N° OF" },
        { field: "PRODUIT", label: "Produit" },
        { key: "DUREE_PREVUE", label: "DUREE PREVUE" },
        { key: "CUMUL_TEMPS_PASSES", label: "C.TEMPS.PASSES" },
        { field: "DUREE_TOTALE", label: "Durée" },
        { field: "EFFICACITE", label: "Efficacité" },
      ],
    },
    "of-combined": {
      endpoint: API_ENDPOINTS.of.all,
      kpiContainerId: "combinedKpiCards",
      tableId: "combinedTable",
      headerId: "combinedHeader",
      bodyId: "combinedBody",
      columns: [
        { field: "NUMERO_OFDA", label: "N° OF" },
        { field: "PRODUIT", label: "Produit" },
        { field: "STATUT", label: "Statut" },
        { key: "DUREE_PREVUE", label: "DUREE PREVUE" },
        { key: "CUMUL_TEMPS_PASSES", label: "C.TEMPS.PASSES" },
        { field: "Avancement_PROD", label: "Avanc. Prod" },
        { field: "Avancement_temps", label: "Avanc. Temps" },
        { field: "EFFICACITE", label: "Efficacité" },
      ],
    },
  },

  async switchMainTab(tabId) {
    this.currentTab = tabId;
    AppState.currentTab = tabId;

    // Destroy existing charts before switching tabs
    DataManager.destroyAllCharts();

    // Load data for the selected tab
    switch (tabId) {
      case "of-en-cours":
        await DataManager.loadOFEnCoursData();
        break;
      case "of-historique":
        await DataManager.loadOFHistoriqueData();
        break;
      case "of-combined":
        await DataManager.loadOFCombinedData();
        break;
    }
  },

  getTabConfig() {
    return this.tabConfigs[this.currentTab];
  },
};

// Update dataManager with new methods
Object.assign(DataManager, {
  async updateUI(data) {
    const tabConfig = TabManager.getTabConfig();
    if (!tabConfig) return;

    // Update KPIs for current tab
    this.updateKPIs(data.kpis, tabConfig.kpiContainerId);

    // Update table for current tab
    this.updateTable(data.data, tabConfig);

    // Update filters if needed
    if (data.filters) {
      this.updateFilters(data.filters);
    }

    // Update system status
    this.updateSystemStatus(data.status);
  },

  updateKPIs(kpis, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !kpis) return;

    // Use the existing renderKPICards method instead
    const type = containerId.replace("KpiCards", "").toLowerCase();
    this.renderKPICards(type, kpis);
  },

  updateTable(data, tabConfig) {
    if (!data || !tabConfig) return;

    // Update header
    const headerElement = document.getElementById(tabConfig.headerId);
    if (headerElement) {
      headerElement.innerHTML = this.generateTableHeader(tabConfig.columns);
    }

    // Update body
    const bodyElement = document.getElementById(tabConfig.bodyId);
    if (bodyElement) {
      bodyElement.innerHTML = this.generateTableRows(data, tabConfig.columns);
    }
  },

  generateTableHeader(columns) {
    return `<tr>${columns.map((col) => `<th>${col.label}</th>`).join("")}</tr>`;
  },

  generateTableRows(data, columns) {
    return data
      .map(
        (row) => `
            <tr>
                ${columns
                  .map((col) => {
                    const value = row[col.field];
                    if (col.field === "STATUT") {
                      const statusClass = Utils.getStatusClass(value);
                      return `<td><span class="badge bg-${statusClass}">${
                        value || "N/A"
                      }</span></td>`;
                    }
                    if (col.field.includes("Avancement")) {
                      return `<td>${Utils.formatPercentage(value)}</td>`;
                    }
                    if (col.field === "EFFICACITE") {
                      return `<td>${
                        value ? parseFloat(value).toFixed(2) : "-"
                      }</td>`;
                    }
                    return `<td>${value || "-"}</td>`;
                  })
                  .join("")}
            </tr>
        `
      )
      .join("");
  },

  updateFilters(filterData) {
    // Update famille filter
    const familleSelect = document.getElementById("familleFilter");
    if (familleSelect && filterData.familles) {
      this.populateSelect(
        familleSelect,
        filterData.familles,
        "Toutes les familles"
      );
    }

    // Update client filter
    const clientSelect = document.getElementById("clientFilter");
    if (clientSelect && filterData.clients) {
      this.populateSelect(clientSelect, filterData.clients, "Tous les clients");
    }

    // Update secteur filter
    const secteurSelect = document.getElementById("secteurFilter");
    if (secteurSelect && filterData.secteurs) {
      this.populateSelect(
        secteurSelect,
        filterData.secteurs,
        "Tous les secteurs"
      );
    }
  },

  populateSelect(selectElement, options, defaultLabel) {
    const currentValue = selectElement.value;
    selectElement.innerHTML = `<option value="">${defaultLabel}</option>`;
    options.forEach((option) => {
      const optElement = document.createElement("option");
      optElement.value = option;
      optElement.textContent = option;
      selectElement.appendChild(optElement);
    });
    if (currentValue && options.includes(currentValue)) {
      selectElement.value = currentValue;
    }
  },

  updateSystemStatus(status) {
    if (!status) return;

    document.getElementById("systemStatus").textContent = status.message || "-";
    document.getElementById("responseTime").textContent = status.responseTime
      ? `${status.responseTime}ms`
      : "-";
    document.getElementById("dataCount").textContent =
      status.totalRecords || "0";
    document.getElementById("lastRefresh").textContent =
      new Date().toLocaleTimeString();
  },
});

// Add alert management
const alertManager = {
  async refreshAlerts() {
    try {
      const response = await ApiService.getAlerts();
      if (response.success) {
        this.updateAlertsUI(response.data || []);
      }
    } catch (error) {
      console.error("Error refreshing alerts:", error);
      Utils.showAlert("Failed to refresh alerts", "error");
    }
  },

  updateAlertsUI(alerts) {
    const container = document.getElementById("alertsContainer");
    if (!container) return;

    if (alerts.length === 0) {
      container.innerHTML =
        '<div class="alert alert-success">No alerts at this time</div>';
      return;
    }

    container.innerHTML = alerts
      .map(
        (alert) => `
            <div class="alert alert-${this.getAlertLevel(alert)}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alert.NUMERO_OFDA}</strong> - ${alert.PRODUIT}
                        <br>
                        <small class="text-muted">
                            Client: ${alert.CLIENT} |
                            Retard: ${alert.RETARD_JOURS} jours
                        </small>
                    </div>
                    <div>
                        ${this.getAlertBadge(alert)}
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  },

  getAlertLevel(alert) {
    if (alert.RETARD_JOURS > 30) return "danger";
    if (alert.RETARD_JOURS > 15) return "warning";
    return "info";
  },

  getAlertBadge(alert) {
    const priority = alert.PRIORITE || "NORMAL";
    const badgeClass = Utils.getPriorityBadgeClass(priority);
    return `<span class="badge bg-${badgeClass}">${priority}</span>`;
  },
};

// Initialize dashboard with enhanced functionality
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Dashboard initializing...");

  // Initialize components
  FilterManager.init();
  DataManager.loadInitialData();

  // Set up tab switching
  setupTabSwitching();

  // Set up auto-refresh (every 30 seconds)
  setInterval(() => {
    DataManager.refreshCurrentView();
  }, 30000);

  console.log("✅ Dashboard initialized successfully");
});

// Setup tab switching functionality
function setupTabSwitching() {
  const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');

  tabButtons.forEach((button) => {
    button.addEventListener("shown.bs.tab", function (event) {
      const targetTab = event.target.getAttribute("data-bs-target");

      // Destroy existing charts before switching tabs
      DataManager.destroyAllCharts();

      if (targetTab === "#of-en-cours-content") {
        AppState.currentTab = "of-en-cours";
        DataManager.loadOFEnCoursData();
      } else if (targetTab === "#of-historique-content") {
        AppState.currentTab = "of-historique";
        DataManager.loadOFHistoriqueData();
      } else if (targetTab === "#of-combined-content") {
        AppState.currentTab = "of-combined";
        DataManager.loadOFCombinedData();
      }
    });
  });
}

// Global functions referenced in HTML
function refreshAlerts() {
  alertManager.refreshAlerts();
}

function checkAlerts() {
  DataManager.loadAlerts();
}

async function sendTestAlert() {
  try {
    const response = await ApiService.sendTestAlert(
      "Test Alert from Dashboard",
      "This is a test alert sent from the production dashboard to verify the alert system is working correctly.",
      "medium"
    );

    if (response.success) {
      Utils.showAlert(
        "Test alert sent successfully! Check your email.",
        "connection"
      );
      // Refresh alerts to show the new one
      setTimeout(() => {
        refreshAlerts();
      }, 1000);
    } else {
      Utils.showAlert("Failed to send test alert", "error");
    }
  } catch (error) {
    console.error("Error sending test alert:", error);
    Utils.showAlert("Error sending test alert", "error");
  }
}

function refreshData() {
  DataManager.refreshCurrentView();
}

function clearFilters() {
  FilterManager.clearAllFilters();
}

// Export Manager (referenced in HTML)
const ExportManager = {
  exportSingleOrder(orderId) {
    console.log("Export order:", orderId);
    Utils.showAlert(`Export pour commande ${orderId} en cours...`, "info");
  },

  // Get current date filter parameters
  getCurrentDateFilters() {
    const dateDebut = document.getElementById("dateDebut")?.value || null;
    const dateFin = document.getElementById("dateFin")?.value || null;

    const params = new URLSearchParams();
    if (dateDebut) params.append("dateDebut", dateDebut);
    if (dateFin) params.append("dateFin", dateFin);

    return params.toString();
  },

  // Download file from response
  async downloadFile(response, defaultFilename) {
    try {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;

      // Try to get filename from Content-Disposition header
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = defaultFilename;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(
          /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
        );
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, "");
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading file:", error);
      throw error;
    }
  },

  async exportComprehensiveCSV() {
    try {
      Utils.showAlert("Génération de l'export CSV complet en cours...", "info");

      const dateParams = this.getCurrentDateFilters();
      const url = `${API_ENDPOINTS.export.comprehensive_csv}${
        dateParams ? "?" + dateParams : ""
      }`;

      const response = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await this.downloadFile(response, "export_complet_dashboard.csv");
      Utils.showAlert("Export CSV complet généré avec succès", "success");
    } catch (error) {
      console.error("Error exporting comprehensive CSV:", error);
      Utils.showAlert("Erreur lors de l'export CSV complet", "error");
    }
  },

  async exportComprehensiveTXT() {
    try {
      Utils.showAlert("Génération du rapport détaillé en cours...", "info");

      const dateParams = this.getCurrentDateFilters();
      const url = `${API_ENDPOINTS.export.comprehensive_txt}${
        dateParams ? "?" + dateParams : ""
      }`;

      const response = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await this.downloadFile(response, "rapport_detaille_production.txt");
      Utils.showAlert("Rapport détaillé généré avec succès", "success");
    } catch (error) {
      console.error("Error exporting comprehensive TXT:", error);
      Utils.showAlert(
        "Erreur lors de la génération du rapport détaillé",
        "error"
      );
    }
  },

  async exportTabData(tabName, format = "csv") {
    try {
      const formatLabel = format.toUpperCase();
      Utils.showAlert(
        `Génération de l'export ${formatLabel} pour l'onglet en cours...`,
        "info"
      );

      const dateParams = this.getCurrentDateFilters();
      const baseUrl = `${API_ENDPOINTS.export.tab}/${tabName}`;
      const url = `${baseUrl}?format=${format}${
        dateParams ? "&" + dateParams : ""
      }`;

      const response = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const extension = format === "excel" ? "xlsx" : "csv";
      await this.downloadFile(response, `${tabName}_export.${extension}`);
      Utils.showAlert(
        `Export ${formatLabel} de l'onglet généré avec succès`,
        "success"
      );
    } catch (error) {
      console.error(`Error exporting tab data (${format}):`, error);
      Utils.showAlert(
        `Erreur lors de l'export ${format.toUpperCase()} de l'onglet`,
        "error"
      );
    }
  },

  // Legacy methods for backward compatibility
  async exportCSV() {
    await this.exportComprehensiveCSV();
  },

  async exportExcel() {
    await this.exportTabData("all", "excel");
  },

  async exportTXT() {
    await this.exportComprehensiveTXT();
  },
};
