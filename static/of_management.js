// OF Management JavaScript functionality
let currentOFData = {
  en_cours: null,
  histo: null,
  all: null,
};

// API Endpoints
const API_ENDPOINTS = {
  of: {
    en_cours: "/api/of/en_cours",
    histo: "/api/of/histo",
    all: "/api/of/all",
    by_status: "/api/of/by_status",
  },
  export: {
    csv: "/api/export/csv",
    excel: "/api/export/excel",
  },
};

// Initialize page on load
document.addEventListener("DOMContentLoaded", function () {
  loadAllOFData();
  setupEventListeners();
});

function setupEventListeners() {
  // Tab change events
  document
    .getElementById("en-cours-tab")
    .addEventListener("click", () => loadOFData("en_cours"));
  document
    .getElementById("histo-tab")
    .addEventListener("click", () => loadOFData("histo"));
  document
    .getElementById("all-tab")
    .addEventListener("click", () => loadOFData("all"));

  // Filter events
  document
    .getElementById("statusFilter")
    .addEventListener("change", applyFilters);
  document
    .getElementById("searchInput")
    .addEventListener("input", applyFilters);
}

function showLoading() {
  document.getElementById("loadingIndicator").style.display = "block";
  document.getElementById("errorAlert").style.display = "none";
  document.getElementById("successAlert").style.display = "none";
}

function hideLoading() {
  document.getElementById("loadingIndicator").style.display = "none";
}

function showSuccess(message) {
  document.getElementById("successMessage").textContent = message;
  document.getElementById("successAlert").style.display = "block";
  setTimeout(() => {
    document.getElementById("successAlert").style.display = "none";
  }, 5000);
}

function showError(message) {
  document.getElementById("errorMessage").textContent = message;
  document.getElementById("errorAlert").style.display = "block";
  hideLoading();
}

async function loadAllOFData() {
  showLoading();
  try {
    // Load EN_COURS data first (default tab)
    await loadOFData("en_cours");
    hideLoading();
    showSuccess("Données OF chargées avec succès");
  } catch (error) {
    console.error("Error loading OF data:", error);
    showError("Erreur lors du chargement des données: " + error.message);
  }
}

async function loadOFData(type) {
  try {
    if (currentOFData[type]) {
      // Data already loaded, just display it
      displayOFData(type, currentOFData[type]);
      updateQuickStats(type, currentOFData[type]);
      return;
    }

    showLoading();

    const response = await fetch(API_ENDPOINTS.of[type]);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (data.success) {
      // Extract the of_list from the data structure
      const ofList = data.data.of_list || data.data || [];
      currentOFData[type] = ofList;
      displayOFData(type, ofList);
      updateQuickStats(type, ofList);
      hideLoading();
    } else {
      throw new Error(data.message || "Failed to fetch OF data");
    }
  } catch (error) {
    console.error(`Error loading ${type} data:`, error);
    showError(`Erreur lors du chargement ${type}: ${error.message}`);
  }
}

function displayOFData(type, data) {
  const headerId = `${type === "en_cours" ? "enCours" : type}Header`;
  const bodyId = `${type === "en_cours" ? "enCours" : type}Body`;

  const headerElement = document.getElementById(headerId);
  const bodyElement = document.getElementById(bodyId);

  if (!headerElement || !bodyElement) {
    console.error(`Elements not found for type: ${type}`);
    return;
  }

  // Generate table header based on data structure
  headerElement.innerHTML = generateTableHeader(type, data);

  // Generate table body
  bodyElement.innerHTML = generateTableBody(type, data);
}

function generateTableHeader(type, data) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return "<tr><th>Aucune donnée</th></tr>";
  }

  const firstRow = data[0];
  if (!firstRow || typeof firstRow !== "object") {
    return "<tr><th>Données invalides</th></tr>";
  }

  const headers = Object.keys(firstRow);

  return `
    <tr>
      ${headers
        .map((header) => `<th>${formatHeaderName(header)}</th>`)
        .join("")}
    </tr>
  `;
}

function generateTableBody(type, data) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return '<tr><td colspan="100%" class="text-center">Aucune donnée disponible</td></tr>';
  }

  return data
    .slice(0, 100)
    .map((row) => {
      const cells = Object.values(row).map((value) => {
        if (value === null || value === undefined) return "";
        if (typeof value === "string" && value.includes("T")) {
          // Likely a date, format it
          try {
            return new Date(value).toLocaleDateString("fr-FR");
          } catch {
            return value;
          }
        }
        return value;
      });

      return `<tr>${cells.map((cell) => `<td>${cell}</td>`).join("")}</tr>`;
    })
    .join("");
}

function formatHeaderName(header) {
  // Convert database column names to readable French labels
  const headerMap = {
    NUMERO_OFDA: "N° OF",
    PRODUIT: "Produit",
    STATUT: "Statut",
    DESIGNATION: "Désignation",
    AFFAIRE: "Affaire",
    LANCEMENT_AU_PLUS_TARD: "Lancement",
    QUANTITE_DEMANDEE: "Qté Demandée",
    CUMUL_ENTREES: "Qté Produite",
    DUREE_PREVUE: "Durée Prévue",
    CUMUL_TEMPS_PASSES: "Temps Passé",
    LANCE_LE: "Lancé le",
    CATEGORIE: "Catégorie",
  };

  return headerMap[header] || header;
}

function updateQuickStats(type, data) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    document.getElementById("quickStats").innerHTML = `
      <div class="col-12">
        <div class="alert alert-info">
          <i class="fas fa-info-circle me-2"></i>
          Aucune donnée disponible pour ${type}
        </div>
      </div>
    `;
    return;
  }

  const stats = calculateStats(data);

  document.getElementById("quickStats").innerHTML = `
    <div class="col-md-3">
      <div class="metric-card" style="background: linear-gradient(135deg, #74c0fc 0%, #339af0 100%);">
        <div class="metric-value">${stats.total}</div>
        <div class="metric-label">Total OF</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="metric-card" style="background: linear-gradient(135deg, #ffd43b 0%, #fab005 100%);">
        <div class="metric-value">${stats.en_cours}</div>
        <div class="metric-label">En Cours</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="metric-card" style="background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);">
        <div class="metric-value">${stats.termines}</div>
        <div class="metric-label">Terminés</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="metric-card" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);">
        <div class="metric-value">${stats.arretes}</div>
        <div class="metric-label">Arrêtés</div>
      </div>
    </div>
  `;
}

function calculateStats(data) {
  if (!data || !Array.isArray(data)) {
    return {
      total: 0,
      en_cours: 0,
      termines: 0,
      arretes: 0,
    };
  }

  return {
    total: data.length,
    en_cours: data.filter((row) => row.STATUT === "C").length,
    termines: data.filter((row) => row.STATUT === "T").length,
    arretes: data.filter((row) => row.STATUT === "A").length,
  };
}

function applyFilters() {
  const statusFilter = document.getElementById("statusFilter").value;
  const searchInput = document
    .getElementById("searchInput")
    .value.toLowerCase();

  // Get current active tab
  const activeTab = document
    .querySelector(".nav-link.active")
    .id.replace("-tab", "");
  const dataType = activeTab === "en-cours" ? "en_cours" : activeTab;

  if (!currentOFData[dataType]) return;

  let filteredData = currentOFData[dataType];

  // Apply status filter
  if (statusFilter) {
    filteredData = filteredData.filter((row) => row.STATUT === statusFilter);
  }

  // Apply search filter
  if (searchInput) {
    filteredData = filteredData.filter((row) =>
      Object.values(row).some(
        (value) => value && value.toString().toLowerCase().includes(searchInput)
      )
    );
  }

  displayOFData(dataType, filteredData);
  updateQuickStats(dataType, filteredData);
}

async function exportOFData(format) {
  try {
    showLoading();

    const activeTab = document
      .querySelector(".nav-link.active")
      .id.replace("-tab", "");
    const dataType = activeTab === "en-cours" ? "en_cours" : activeTab;

    let endpoint;
    if (format === "csv") {
      endpoint = `${API_ENDPOINTS.export.csv}/of_${dataType}`;
    } else if (format === "excel") {
      endpoint = `${API_ENDPOINTS.export.excel}/of_${dataType}`;
    }

    const response = await fetch(endpoint);
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `of_${dataType}_${
        new Date().toISOString().split("T")[0]
      }.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      hideLoading();
      showSuccess(`Export ${format.toUpperCase()} téléchargé avec succès`);
    } else {
      throw new Error(`Export failed: ${response.status}`);
    }
  } catch (error) {
    console.error("Export error:", error);
    showError(`Erreur lors de l'export: ${error.message}`);
  }
}
