(function () {
  // Shift+click range selection for the inline "Remove" checkboxes
  let last = null;

  function isTarget(el) {
    return el.matches("fieldset.module .inline-related input[type='checkbox'][name$='-remove']");
  }

  document.addEventListener("click", function (e) {
    const t = e.target;
    if (!isTarget(t)) return;

    if (e.shiftKey && last && last !== t) {
      const boxes = Array.from(
        document.querySelectorAll("fieldset.module .inline-related input[type='checkbox'][name$='-remove']")
      );
      const i1 = boxes.indexOf(last);
      const i2 = boxes.indexOf(t);
      if (i1 !== -1 && i2 !== -1) {
        const start = Math.min(i1, i2);
        const end = Math.max(i1, i2);
        for (let i = start; i <= end; i++) {
          boxes[i].checked = t.checked;
        }
      }
    }

    last = t;
  });
})();

