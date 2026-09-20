export function attachEditor(textarea) {
  textarea.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    e.preventDefault();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    const indent = "    ";

    if (start === end) {
      if (e.shiftKey) {
        const lineStart = value.lastIndexOf("\n", start - 1) + 1;
        if (value.slice(lineStart, lineStart + 4) === indent) {
          textarea.value = value.slice(0, lineStart) + value.slice(lineStart + 4);
          textarea.selectionStart = textarea.selectionEnd = start - 4;
        } else if (value.slice(lineStart, lineStart + 1) === "\t") {
          textarea.value = value.slice(0, lineStart) + value.slice(lineStart + 1);
          textarea.selectionStart = textarea.selectionEnd = start - 1;
        }
      } else {
        textarea.value = value.slice(0, start) + indent + value.slice(end);
        textarea.selectionStart = textarea.selectionEnd = start + indent.length;
      }
      return;
    }

    const lineStart = value.lastIndexOf("\n", start - 1) + 1;
    const block = value.slice(lineStart, end);
    const lines = block.split("\n");
    const next = e.shiftKey
      ? lines.map((l) => (l.startsWith(indent) ? l.slice(4) : l.startsWith("\t") ? l.slice(1) : l))
      : lines.map((l) => indent + l);
    textarea.value = value.slice(0, lineStart) + next.join("\n") + value.slice(end);
  });
}
