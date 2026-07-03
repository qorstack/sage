/* Sage Docs — shared zoom/pan for inline SVG diagrams (canonical source).
   Lives in agents/sage/docs/ alongside the template + CSS.
   Reference from any generated docs/*.html via (at end of <body>):
   <script src="../agents/sage/docs/sage-docs.js"></script>

   Auto-discovers EVERY .svg-diagram on the page and wires each one
   independently — no hardcoded IDs, no per-diagram duplication.

   Each diagram needs only:
   - a wrapper:        <div class="svg-diagram"> … </div>
   - controls buttons: <button data-zoom="in|out|fit">
   - an <svg> whose pannable content sits in a <g> (id starting "svg-content"
     if present, else the first <g>). Size is auto-measured via getBBox(); you
     can override with data-w / data-h on the .svg-diagram element. */

(function () {
  function initDiagram(container) {
    var svg = container.querySelector("svg");
    var group =
      container.querySelector('[id^="svg-content"]') ||
      (svg && svg.querySelector("g"));
    var label = container.querySelector(".zoom-level");
    if (!svg || !group) return;

    var scale = 1,
      tx = 0,
      ty = 0;
    var dragging = false,
      sx = 0,
      sy = 0,
      stx = 0,
      sty = 0;

    /* Returns the content's true bounding box {x, y, w, h}. x/y matter:
       content rarely starts at 0,0, so centering must subtract the origin. */
    function box() {
      if (container.dataset.w && container.dataset.h) {
        return { x: 0, y: 0, w: +container.dataset.w, h: +container.dataset.h };
      }
      try {
        var b = group.getBBox();
        if (b.width && b.height)
          return { x: b.x, y: b.y, w: b.width, h: b.height };
      } catch (e) {
        /* getBBox throws if not rendered yet */
      }
      var vb = (svg.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number);
      if (vb.length === 4 && vb[2] && vb[3])
        return { x: vb[0] || 0, y: vb[1] || 0, w: vb[2], h: vb[3] };
      return {
        x: 0,
        y: 0,
        w: container.clientWidth || 1,
        h: container.clientHeight || 1,
      };
    }

    function apply() {
      group.setAttribute(
        "transform",
        "translate(" + tx + "," + ty + ") scale(" + scale + ")",
      );
      if (label) label.textContent = Math.round(scale * 100) + "%";
    }

    function fit() {
      var b = box();
      var cw = container.clientWidth,
        ch = container.clientHeight;
      scale = Math.min((cw - 40) / b.w, (ch - 40) / b.h, 1.6);
      if (!isFinite(scale) || scale <= 0) scale = 1;
      /* center the content's own box, then offset by its origin (b.x, b.y) so a
         diagram that starts at e.g. x=10,y=9 still lands dead-center, not skewed */
      tx = (cw - b.w * scale) / 2 - b.x * scale;
      ty = (ch - b.h * scale) / 2 - b.y * scale;
      apply();
    }

    function zoomAt(factor, cx, cy) {
      var prev = scale;
      scale = Math.min(Math.max(scale * factor, 0.1), 8);
      if (cx == null) {
        cx = container.clientWidth / 2;
        cy = container.clientHeight / 2;
      }
      tx = cx - (cx - tx) * (scale / prev);
      ty = cy - (cy - ty) * (scale / prev);
      apply();
    }

    container.querySelectorAll("[data-zoom]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var a = btn.getAttribute("data-zoom");
        if (a === "in") zoomAt(1.3);
        else if (a === "out") zoomAt(1 / 1.3);
        else fit();
      });
    });

    container.addEventListener(
      "wheel",
      function (e) {
        e.preventDefault();
        var r = container.getBoundingClientRect();
        zoomAt(
          e.deltaY > 0 ? 0.88 : 1.14,
          e.clientX - r.left,
          e.clientY - r.top,
        );
      },
      { passive: false },
    );

    container.addEventListener("mousedown", function (e) {
      dragging = true;
      sx = e.clientX;
      sy = e.clientY;
      stx = tx;
      sty = ty;
      container.classList.add("is-dragging");
    });
    window.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      tx = stx + (e.clientX - sx);
      ty = sty + (e.clientY - sy);
      apply();
    });
    window.addEventListener("mouseup", function () {
      dragging = false;
      container.classList.remove("is-dragging");
    });

    var lastDist = null;
    container.addEventListener(
      "touchstart",
      function (e) {
        if (e.touches.length === 2) {
          var a = e.touches[0],
            b = e.touches[1];
          lastDist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
        } else if (e.touches.length === 1) {
          dragging = true;
          sx = e.touches[0].clientX;
          sy = e.touches[0].clientY;
          stx = tx;
          sty = ty;
        }
      },
      { passive: true },
    );
    container.addEventListener(
      "touchmove",
      function (e) {
        if (e.touches.length === 2) {
          e.preventDefault();
          var a = e.touches[0],
            b = e.touches[1];
          var dist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
          var r = container.getBoundingClientRect();
          if (lastDist) {
            zoomAt(
              dist / lastDist,
              (a.clientX + b.clientX) / 2 - r.left,
              (a.clientY + b.clientY) / 2 - r.top,
            );
          }
          lastDist = dist;
        } else if (e.touches.length === 1 && dragging) {
          tx = stx + (e.touches[0].clientX - sx);
          ty = sty + (e.touches[0].clientY - sy);
          apply();
        }
      },
      { passive: false },
    );
    container.addEventListener("touchend", function () {
      dragging = false;
      lastDist = null;
    });

    fit();
    window.addEventListener("resize", fit);
  }

  function initAll() {
    document.querySelectorAll(".svg-diagram").forEach(initDiagram);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
