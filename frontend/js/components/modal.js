export function openModal({ title, bodyHtml, onClose }) {
  closeModal();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.setAttribute("role", "presentation");
  backdrop.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-head">
        <h2 id="modal-title">${title}</h2>
        <button type="button" class="btn btn-secondary" data-close>Close</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
    </div>
  `;
  function close() {
    backdrop.remove();
    document.removeEventListener("keydown", onKey);
    onClose?.();
  }
  function onKey(e) {
    if (e.key === "Escape") close();
  }
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });
  backdrop.querySelector("[data-close]").addEventListener("click", close);
  document.addEventListener("keydown", onKey);
  document.body.appendChild(backdrop);
  backdrop.querySelector("[data-close]").focus();
  return { close };
}

export function closeModal() {
  document.querySelector(".modal-backdrop")?.remove();
}
