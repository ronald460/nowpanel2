// Configuración y estado
const APP_STATE = {
  currentView: "inbox",
  selectedEmails: [],
  emailData: {},
  currentPage: 1,
  pageSize: 20,
  totalEmails: 0,
  quillEditor: null,
  draftData: null,
};

// Inicialización del editor Quill para redactar
document.addEventListener("DOMContentLoaded", function () {
  // Inicializar Quill
  APP_STATE.quillEditor = new Quill("#editorContainer", {
    theme: "snow",
    placeholder: "Escribe tu mensaje aquí...",
    modules: {
      toolbar: [
        ["bold", "italic", "underline", "strike"],
        ["blockquote", "code-block"],
        [{ list: "ordered" }, { list: "bullet" }],
        [{ script: "sub" }, { script: "super" }],
        [{ indent: "-1" }, { indent: "+1" }],
        ["link", "image", "video"],
        ["clean"],
      ],
    },
  });

  // Configurar eventos
  setupEventListeners();

  // Cargar la bandeja de entrada inicial
  loadView("inbox");
});

// Configuración de event listeners
function setupEventListeners() {
  // Navegación
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", function (e) {
      e.preventDefault();
      const view = this.dataset.view;
      loadView(view);

      // Actualizar clase activa
      document
        .querySelectorAll(".nav-item")
        .forEach((nav) => nav.classList.remove("active"));
      this.classList.add("active");
    });
  });

  // Redactar
  document
    .getElementById("composeBtn")
    .addEventListener("click", openComposeModal);
  document
    .getElementById("closeCompose")
    .addEventListener("click", closeComposeModal);
  document
    .getElementById("discardBtn")
    .addEventListener("click", closeComposeModal);

  // Envío de correo
  document.getElementById("composeForm").addEventListener("submit", sendEmail);
  document.getElementById("saveDraftBtn").addEventListener("click", saveDraft);

  // Cc y Bcc
  document.getElementById("ccToggle").addEventListener("click", function () {
    const container = document.getElementById("ccContainer");
    container.style.display =
      container.style.display === "none" ? "block" : "none";
  });

  document.getElementById("bccToggle").addEventListener("click", function () {
    const container = document.getElementById("bccContainer");
    container.style.display =
      container.style.display === "none" ? "block" : "none";
  });

  // Seleccionar todos
  document.getElementById("selectAll").addEventListener("change", function () {
    const checkboxes = document.querySelectorAll(".email-checkbox");
    checkboxes.forEach((cb) => (cb.checked = this.checked));
    updateSelectedEmails();
  });

  // Refresh
  document.getElementById("refreshBtn").addEventListener("click", function () {
    loadView(APP_STATE.currentView);
  });

  // Acciones masivas
  document
    .getElementById("archiveSelected")
    .addEventListener("click", function () {
      performBulkAction("archive");
    });

  document
    .getElementById("deleteSelected")
    .addEventListener("click", function () {
      if (confirm("¿Mover los correos seleccionados a la papelera?")) {
        performBulkAction("delete");
      }
    });

  document
    .getElementById("markReadSelected")
    .addEventListener("click", function () {
      performBulkAction("mark_read");
    });

  document
    .getElementById("markUnreadSelected")
    .addEventListener("click", function () {
      performBulkAction("mark_unread");
    });
}

// Funciones de carga de vistas
function loadView(view) {
  APP_STATE.currentView = view;
  const contentArea = document.getElementById("contentArea");

  // Mostrar loading
  contentArea.innerHTML = `
        <div class="loading-container">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Cargando correos...</p>
        </div>
    `;

  // Cargar correos desde la API
  const url = `/api/emails/${
    view === "inbox"
      ? "inbox"
      : view === "sent"
        ? "sent"
        : view === "drafts"
          ? "drafts"
          : view === "archived"
            ? "archived"
            : view
  }/`;

  fetch(url, {
    headers: {
      Authorization: `Token ${getCSRFToken()}`,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      renderEmailList(data, view);
      updateBadgeCounts();
    })
    .catch((error) => {
      console.error("Error cargando correos:", error);
      contentArea.innerHTML = `
            <div class="error-container">
                <i class="fas fa-exclamation-circle"></i>
                <p>Error al cargar los correos. Intenta de nuevo.</p>
                <button onclick="loadView('${view}')">Reintentar</button>
            </div>
        `;
    });
}

function renderEmailList(emails, view) {
  const contentArea = document.getElementById("contentArea");

  if (emails.length === 0) {
    contentArea.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>No hay correos</h3>
                <p>Tu bandeja de entrada está vacía</p>
                <button class="compose-btn" id="emptyComposeBtn">
                    <i class="fas fa-pen"></i> Redactar
                </button>
            </div>
        `;

    document
      .getElementById("emptyComposeBtn")
      ?.addEventListener("click", openComposeModal);
    return;
  }

  let html = `
        <div class="toolbar">
            <div class="toolbar-left">
                <input type="checkbox" id="selectAll">
                <button class="toolbar-btn" id="refreshBtn">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button class="toolbar-btn" id="archiveSelected">
                    <i class="fas fa-archive"></i>
                </button>
                <button class="toolbar-btn" id="deleteSelected">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="toolbar-right">
                <button class="toolbar-btn" id="markReadSelected">
                    <i class="fas fa-check-double"></i>
                </button>
                <button class="toolbar-btn" id="markUnreadSelected">
                    <i class="fas fa-envelope"></i>
                </button>
            </div>
        </div>
        <div class="email-list">
    `;

  emails.forEach((email) => {
    const isRead = email.is_read ? "read" : "unread";
    const hasAttachments = email.attachments && email.attachments.length > 0;
    const isImportant = email.is_starred || false;

    html += `
            <div class="email-item ${isRead}" data-id="${email.id}" onclick="openEmailDetail(${email.id})">
                <div class="email-select" onclick="event.stopPropagation();">
                    <input type="checkbox" class="email-checkbox" data-id="${email.id}">
                </div>
                <div class="email-star" onclick="event.stopPropagation(); toggleStar(${email.id})">
                    <i class="fas fa-star ${isImportant ? "starred" : ""}"></i>
                </div>
                <div class="email-sender">${email.sender_name || email.sender}</div>
                <div class="email-subject-preview">
                    <span class="email-subject">${email.subject || "Sin asunto"}</span>
                    <span class="email-preview">${email.summary || ""}</span>
                </div>
                ${hasAttachments ? '<div class="email-attachment-indicator"><i class="fas fa-paperclip"></i></div>' : ""}
                <div class="email-date">${formatDate(email.sent_at)}</div>
            </div>
        `;
  });

  html += "</div>";
  contentArea.innerHTML = html;

  // Reconfigurar event listeners para la nueva lista
  document.getElementById("selectAll")?.addEventListener("change", function () {
    const checkboxes = document.querySelectorAll(".email-checkbox");
    checkboxes.forEach((cb) => (cb.checked = this.checked));
    updateSelectedEmails();
  });

  document.querySelectorAll(".email-checkbox").forEach((cb) => {
    cb.addEventListener("change", updateSelectedEmails);
  });

  // Configurar acciones de toolbar
  document.getElementById("refreshBtn")?.addEventListener("click", function () {
    loadView(APP_STATE.currentView);
  });

  document
    .getElementById("archiveSelected")
    ?.addEventListener("click", function () {
      performBulkAction("archive");
    });

  document
    .getElementById("deleteSelected")
    ?.addEventListener("click", function () {
      if (confirm("¿Mover los correos seleccionados a la papelera?")) {
        performBulkAction("delete");
      }
    });

  document
    .getElementById("markReadSelected")
    ?.addEventListener("click", function () {
      performBulkAction("mark_read");
    });

  document
    .getElementById("markUnreadSelected")
    ?.addEventListener("click", function () {
      performBulkAction("mark_unread");
    });
}

// Funciones de acciones
function openEmailDetail(emailId) {
  fetch(`/api/emails/${emailId}/`)
    .then((response) => response.json())
    .then((email) => {
      renderEmailDetail(email);
    })
    .catch((error) => {
      console.error("Error cargando detalle del correo:", error);
    });
}

function renderEmailDetail(email) {
  const contentArea = document.getElementById("contentArea");

  let html = `
        <div class="email-detail-container">
            <div class="email-detail-header">
                <button class="back-btn" onclick="loadView('${APP_STATE.currentView}')">
                    <i class="fas fa-arrow-left"></i>
                </button>
                <div class="email-actions">
                    <button class="action-btn" onclick="replyEmail(${email.id})">
                        <i class="fas fa-reply"></i> Responder
                    </button>
                    <button class="action-btn" onclick="replyAllEmail(${email.id})">
                        <i class="fas fa-reply-all"></i>
                    </button>
                    <button class="action-btn" onclick="forwardEmail(${email.id})">
                        <i class="fas fa-forward"></i>
                    </button>
                    <button class="action-btn" onclick="archiveEmail(${email.id})">
                        <i class="fas fa-archive"></i>
                    </button>
                    <button class="action-btn" onclick="deleteEmail(${email.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <div class="email-detail-body">
                <div class="email-header-info">
                    <div class="email-sender">
                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(email.sender)}&background=4285f4&color=fff" alt="Sender">
                        <div>
                            <strong>${email.sender_name || email.sender}</strong>
                            <span>${formatDate(email.sent_at)}</span>
                        </div>
                    </div>
                    <div class="email-subject">
                        <h2>${email.subject || "Sin asunto"}</h2>
                    </div>
                    <div class="email-recipients">
                        <span><strong>Para:</strong> ${email.recipients.join(", ")}</span>
                        ${email.cc && email.cc.length ? `<span><strong>Cc:</strong> ${email.cc.join(", ")}</span>` : ""}
                    </div>
                </div>
                
                <div class="email-body-content">
                    ${email.body_html || `<pre>${email.body_text || ""}</pre>`}
                </div>
                
                ${
                  email.attachments && email.attachments.length
                    ? `
                <div class="email-attachments">
                    <h4>Adjuntos</h4>
                    <ul>
                        ${email.attachments
                          .map(
                            (att) => `
                            <li>
                                <i class="fas fa-paperclip"></i>
                                <a href="#">${att.name}</a>
                                <span>(${formatFileSize(att.size)})</span>
                            </li>
                        `,
                          )
                          .join("")}
                    </ul>
                </div>`
                    : ""
                }
            </div>
        </div>
    `;

  contentArea.innerHTML = html;

  // Marcar como leído automáticamente
  if (!email.is_read) {
    fetch(`/api/emails/${email.id}/mark_read/`, {
      method: "POST",
      headers: {
        Authorization: `Token ${getCSRFToken()}`,
      },
    });
    email.is_read = true;
  }
}

// Funciones de utilidad
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;

  if (diff < 86400000) {
    // Menos de 24 horas
    return date.toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } else if (diff < 604800000) {
    // Menos de 7 días
    return date.toLocaleDateString("es-ES", { weekday: "short" });
  } else {
    return date.toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
    });
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function getCSRFToken() {
  return (
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1]
  );
}

function updateSelectedEmails() {
  const checkboxes = document.querySelectorAll(".email-checkbox:checked");
  APP_STATE.selectedEmails = Array.from(checkboxes).map((cb) =>
    parseInt(cb.dataset.id),
  );
}

// Funciones de acciones masivas
function performBulkAction(action) {
  if (APP_STATE.selectedEmails.length === 0) {
    alert("Selecciona al menos un correo");
    return;
  }

  const promises = APP_STATE.selectedEmails.map((id) => {
    return fetch(`/api/emails/${id}/${action}/`, {
      method: "POST",
      headers: {
        Authorization: `Token ${getCSRFToken()}`,
      },
    });
  });

  Promise.all(promises)
    .then(() => {
      loadView(APP_STATE.currentView);
    })
    .catch((error) => {
      console.error("Error realizando acción:", error);
      alert("Ocurrió un error. Intenta de nuevo.");
    });
}

// Funciones de redacción
function openComposeModal() {
  const modal = document.getElementById("composeModal");
  modal.classList.add("active");

  // Resetear el formulario
  document.getElementById("toInput").value = "";
  document.getElementById("subjectInput").value = "";
  APP_STATE.quillEditor.setText("");
}

function closeComposeModal() {
  document.getElementById("composeModal").classList.remove("active");
}

function sendEmail(event) {
  event.preventDefault();

  const to = document.getElementById("toInput").value;
  const subject = document.getElementById("subjectInput").value;
  const body = APP_STATE.quillEditor.getText() || "";
  const htmlBody = APP_STATE.quillEditor.getContents();

  console.log("=== ENVIANDO CORREO DESDE EL NAVEGADOR ===");
  console.log("Destinatarios:", to);
  console.log("Asunto:", subject);
  console.log("Cuerpo (texto):", body);
  console.log("Cuerpo (HTML):", htmlBody);

  if (!to) {
    alert("Por favor, ingresa al menos un destinatario");
    return;
  }

  const emailData = {
    recipients: to.split(",").map((email) => email.trim()),
    subject: subject,
    body_text: body,
    body_html: JSON.stringify(htmlBody),
  };

  console.log("Datos a enviar al backend:", emailData);

  // Obtener el token CSRF
  const csrftoken =
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1];

  console.log("CSRF Token:", csrftoken);

  fetch("/api/emails/send/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
      Authorization: `Token ${getCSRFToken()}`,
    },
    body: JSON.stringify(emailData),
  })
    .then((response) => {
      console.log("Respuesta del servidor - Status:", response.status);
      return response.json();
    })
    .then((data) => {
      console.log("Datos de respuesta:", data);

      if (data.status === "sent") {
        console.log("✅ Correo enviado exitosamente");
        closeComposeModal();
        loadView(APP_STATE.currentView);
      } else {
        console.error("❌ Error del servidor:", data);
        alert(
          "Error al enviar: " +
            (data.message || data.detail || "Error desconocido"),
        );
      }
    })
    .catch((error) => {
      console.error("❌ Error en la petición fetch:", error);
      console.error("Stack trace:", error.stack);
      alert("Error al enviar el correo. Revisa la consola para más detalles.");
    });
}

function saveDraft() {
  const to = document.getElementById("toInput").value;
  const subject = document.getElementById("subjectInput").value;
  const body = APP_STATE.quillEditor.getText() || "";
  const htmlBody = APP_STATE.quillEditor.getContents();

  const draftData = {
    recipients: to.split(",").map((email) => email.trim()),
    subject: subject,
    body_text: body,
    body_html: JSON.stringify(htmlBody),
  };

  fetch("/api/emails/save_draft/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${getCSRFToken()}`,
    },
    body: JSON.stringify(draftData),
  })
    .then((response) => response.json())
    .then((data) => {
      alert("Borrador guardado exitosamente");
      closeComposeModal();
      loadView("drafts");
    })
    .catch((error) => {
      console.error("Error guardando borrador:", error);
      alert("Error al guardar el borrador");
    });
}

// Funciones de actualización de badges
function updateBadgeCounts() {
  fetch("/api/emails/inbox/", {
    headers: {
      Authorization: `Token ${getCSRFToken()}`,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const unreadCount = data.filter((email) => !email.is_read).length;
      document.getElementById("inboxCount").textContent = unreadCount;
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener("DOMContentLoaded", function () {
  // Actualizar contadores cada 30 segundos
  setInterval(updateBadgeCounts, 30000);
});
