/* knowai markdown editor — Write/Preview tabs + toolbar.
   Loads Marked from CDN for preview; degrades to <pre> if blocked. */

(function () {
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function renderMarkdown(text) {
    if (window.marked && typeof window.marked.parse === "function") {
      try {
        return window.marked.parse(text, { mangle: false, headerIds: false, breaks: false });
      } catch (e) {
        // fall through
      }
    }
    // Fallback: show raw markdown in a pre block
    var pre = document.createElement("pre");
    pre.className = "mono";
    pre.textContent = text;
    return pre.outerHTML;
  }

  function setTab(editor, which) {
    editor.querySelectorAll(".md-tab").forEach(function (t) {
      t.classList.toggle("on", t.dataset.tab === which);
    });
    var write   = editor.querySelector(".md-write");
    var preview = editor.querySelector(".md-preview");
    var ta      = editor.querySelector("[data-md-input]");
    if (which === "preview") {
      var text = ta.value.trim();
      if (!text) {
        preview.innerHTML = '<div class="md-preview-empty muted">Nothing to preview yet.</div>';
      } else {
        preview.innerHTML = renderMarkdown(ta.value);
      }
      write.hidden = true;
      preview.hidden = false;
    } else {
      preview.hidden = true;
      write.hidden = false;
      ta.focus();
    }
  }

  // Insert markdown syntax around the current selection (or at cursor).
  function wrap(ta, before, after, placeholder) {
    after = after || "";
    placeholder = placeholder || "";
    var start = ta.selectionStart;
    var end   = ta.selectionEnd;
    var sel   = ta.value.substring(start, end);
    var insert = sel || placeholder;
    var out = before + insert + after;
    ta.setRangeText(out, start, end, "end");
    if (!sel && placeholder) {
      // select the placeholder so user can overwrite immediately
      ta.selectionStart = start + before.length;
      ta.selectionEnd   = start + before.length + placeholder.length;
    }
    ta.focus();
  }

  // Prefix each selected line with `prefix` (function or string).
  function prefixLines(ta, prefix) {
    var start = ta.selectionStart;
    var end   = ta.selectionEnd;
    var text  = ta.value;
    var lineStart = text.lastIndexOf("\n", start - 1) + 1;
    var lineEnd   = end;
    var block = text.substring(lineStart, lineEnd) || "item";
    var lines = block.split("\n");
    var out = lines.map(function (l, i) {
      var p = typeof prefix === "function" ? prefix(i) : prefix;
      return p + l;
    }).join("\n");
    ta.setRangeText(out, lineStart, lineEnd, "end");
    ta.focus();
  }

  function applyTool(ta, tool) {
    switch (tool) {
      case "bold":      return wrap(ta, "**", "**", "bold");
      case "italic":    return wrap(ta, "*", "*", "italic");
      case "code":      return wrap(ta, "`", "`", "code");
      case "codeblock": return wrap(ta, "\n```\n", "\n```\n", "code");
      case "link":      return wrap(ta, "[", "](https://)", "text");
      case "heading":   return prefixLines(ta, "## ");
      case "ul":        return prefixLines(ta, "- ");
      case "ol":        return prefixLines(ta, function (i) { return (i + 1) + ". "; });
      case "quote":     return prefixLines(ta, "> ");
    }
  }

  function bindEditor(editor) {
    var ta = editor.querySelector("[data-md-input]");
    if (!ta) return;

    editor.querySelectorAll(".md-tab").forEach(function (t) {
      t.addEventListener("click", function () { setTab(editor, t.dataset.tab); });
    });

    editor.querySelectorAll(".md-tools button").forEach(function (b) {
      b.addEventListener("click", function () { applyTool(ta, b.dataset.md); });
    });

    // Keyboard shortcuts on the textarea
    ta.addEventListener("keydown", function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      if (e.key === "b" || e.key === "B") { e.preventDefault(); applyTool(ta, "bold"); }
      else if (e.key === "i" || e.key === "I") { e.preventDefault(); applyTool(ta, "italic"); }
      else if (e.key === "k" || e.key === "K") { e.preventDefault(); applyTool(ta, "link"); }
      else if (e.key === "Enter") { /* allow Ctrl+Enter to submit form */
        var form = ta.closest("form");
        if (form) { e.preventDefault(); form.requestSubmit(); }
      }
    });
  }

  ready(function () {
    document.querySelectorAll("[data-editor]").forEach(bindEditor);
  });
})();
