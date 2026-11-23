// InventarioPro: navegación, filtros y acciones de demostración.
// Este archivo controla el prototipo visual; no guarda datos en una base de datos.

"use strict";

const pageNames = {
  dashboard: "Dashboard",
  inventario: "Inventario",
  movimientos: "Movimientos",
  alertas: "Alertas",
  reportes: "Reportes",
  acerca: "Acerca del sistema"
};

const sections = document.querySelectorAll(".page-section");
const breadcrumbCurrent = document.getElementById("breadcrumbCurrent");
const sidebar = document.getElementById("sidebar");
const statusFilter = document.getElementById("statusFilter");
const productSearch = document.getElementById("productSearch");
const inventoryTableBody = document.querySelector("#inventoryTable tbody");
const noProductsRow = document.getElementById("noProductsRow");

function showPage(page, options = {}) {
  if (!pageNames[page]) return;

  sections.forEach(section => {
    section.classList.toggle("active", section.id === `page-${page}`);
  });

  document.querySelectorAll(".side-nav .nav-link").forEach(button => {
    button.classList.toggle("active", button.dataset.page === page);
  });

  if (breadcrumbCurrent) breadcrumbCurrent.textContent = pageNames[page];
  if (sidebar) sidebar.classList.remove("open");

  // Mantiene la navegación compatible con Atrás y Adelante del navegador.
  if (!options.fromHistory && location.hash !== `#${page}`) {
    history.pushState({ page }, "", `#${page}`);
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-page]").forEach(button => {
  button.addEventListener("click", () => {
    const page = button.dataset.page;
    if (page) showPage(page);
  });
});

window.addEventListener("popstate", () => {
  const page = location.hash.slice(1);
  showPage(pageNames[page] ? page : "dashboard", { fromHistory: true });
});

window.addEventListener("hashchange", () => {
  const page = location.hash.slice(1);
  showPage(pageNames[page] ? page : "dashboard", { fromHistory: true });
});

// Abre la sección indicada en la URL o el Dashboard por defecto.
const initialPage = location.hash.slice(1);
showPage(pageNames[initialPage] ? initialPage : "dashboard", { fromHistory: true });

// Menú lateral para pantallas pequeñas.
const mobileMenu = document.getElementById("mobileMenu");
if (mobileMenu && sidebar) {
  mobileMenu.addEventListener("click", () => sidebar.classList.toggle("open"));
}

// Mensaje pequeño de confirmación.
function showToast(message) {
  const toast = document.getElementById("toastMessage");
  if (!toast) return;

  const messageElement = toast.querySelector("span");
  if (messageElement) messageElement.textContent = message;

  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2800);
}

// Ventana modal de demostración.
const modal = document.getElementById("demoModal");
const modalTitle = document.getElementById("modalTitle");
const modalText = document.getElementById("modalText");

function openDemoModal(title, description = "") {
  if (!modal) return;
  if (modalTitle) modalTitle.textContent = title;
  if (modalText) {
    modalText.textContent = description ||
      "Esta es una vista de demostración del prototipo navegable. No se guardan ni modifican datos reales.";
  }
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeDemoModal() {
  if (!modal) return;
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

document.querySelectorAll("[data-demo]").forEach(button => {
  button.addEventListener("click", () => {
    const code = button.dataset.productCode;
    if (code) {
      const row = document.querySelector(`#inventoryTable tbody tr[data-code="${code}"]`);
      if (row) {
        const productName = row.querySelector(".table-product")?.textContent.trim() || "Producto";
        const cells = row.querySelectorAll("td");
        const stock = cells[2]?.textContent.trim() || "No disponible";
        const minimum = cells[3]?.textContent.trim() || "No disponible";
        openDemoModal(button.dataset.demo, `${productName}. Código: ${code}. Existencias: ${stock}. Stock mínimo: ${minimum}. Esta demostración no modifica el inventario.`);
        return;
      }
    }
    openDemoModal(button.dataset.demo);
  });
});

document.getElementById("closeModal")?.addEventListener("click", closeDemoModal);
document.getElementById("modalOk")?.addEventListener("click", closeDemoModal);
modal?.addEventListener("click", event => {
  if (event.target === modal) closeDemoModal();
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeDemoModal();
});

// Búsqueda y filtros de inventario.
function filterProducts() {
  if (!inventoryTableBody) return;

  const query = (productSearch?.value || "").trim().toLocaleLowerCase("es");
  const selectedStatus = statusFilter?.value || "todos";
  let visibleCount = 0;

  inventoryTableBody.querySelectorAll("tr[data-code]").forEach(row => {
    const productName = (row.dataset.name || "").toLocaleLowerCase("es");
    const productCode = (row.dataset.code || "").toLocaleLowerCase("es");
    const matchesText = productName.includes(query) || productCode.includes(query);
    const matchesStatus = selectedStatus === "todos" || row.dataset.status === selectedStatus;
    const isVisible = matchesText && matchesStatus;

    row.hidden = !isVisible;
    if (isVisible) visibleCount += 1;
  });

  if (noProductsRow) noProductsRow.hidden = visibleCount !== 0;
}

productSearch?.addEventListener("input", filterProducts);
statusFilter?.addEventListener("change", filterProducts);

// Hace clicables las tarjetas del Dashboard y los resúmenes de Alertas.
// Al hacer clic, abre Inventario con el filtro correspondiente aplicado.
function openInventoryWithFilter(status) {
  if (!statusFilter) return;

  showPage("inventario");
  statusFilter.value = status;
  if (productSearch) productSearch.value = "";
  filterProducts();

  const statusLabels = {
    todos: "todos los productos",
    optimo: "productos con stock óptimo",
    regular: "productos con stock regular",
    critico: "productos con stock crítico"
  };
  showToast(`Mostrando ${statusLabels[status] || "productos"}.`);
}

document.querySelectorAll("[data-stock-filter]").forEach(card => {
  const activateCard = () => openInventoryWithFilter(card.dataset.stockFilter || "todos");

  card.addEventListener("click", activateCard);
  card.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activateCard();
    }
  });
});

// Selector visual de entrada/salida.
document.querySelectorAll(".movement-choice").forEach(choice => {
  choice.addEventListener("click", () => {
    document.querySelectorAll(".movement-choice").forEach(item => {
      item.classList.remove("selected");
    });
    choice.classList.add("selected");

    const radio = choice.querySelector('input[type="radio"]');
    if (radio) radio.checked = true;
  });
});

// Vista previa del formulario; no actualiza ni guarda existencias.
const movementForm = document.getElementById("movementForm");
movementForm?.addEventListener("submit", event => {
  event.preventDefault();

  const product = document.getElementById("movementProduct")?.value || "Producto";
  const quantity = document.getElementById("movementQuantity")?.value;
  const type = document.querySelector('input[name="movementType"]:checked')?.value || "Entrada";
  const note = document.getElementById("movementNote")?.value.trim();

  if (!quantity || Number(quantity) <= 0 || !Number.isFinite(Number(quantity))) {
    showToast("Ingresa una cantidad válida para ver la vista previa.");
    document.getElementById("movementQuantity")?.focus();
    return;
  }

  const noteText = note ? ` Observaciones: ${note}.` : "";
  openDemoModal(
    `Vista previa: ${type} de ${quantity} unidades`,
    `Producto: ${product}. Tipo: ${type}. Cantidad: ${quantity}.${noteText} Esta demostración no guarda ni modifica el inventario.`
  );
});

// Imprimir la vista de reportes.
document.getElementById("printReport")?.addEventListener("click", () => window.print());

// Fecha de la cabecera.
const todayDate = document.getElementById("todayDate");
if (todayDate) {
  todayDate.textContent = new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric"
  }).format(new Date());
}

// Inicializa la tabla con todos los productos visibles.
filterProducts();
