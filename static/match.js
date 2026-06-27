// Matching game: tap a Vietnamese word, then its meaning/number.
// Correct matches lock in green and (if enabled) play the Southern audio;
// mistakes flash red. When the board is cleared we POST FSRS grades derived
// from how many tries each word took.
(function () {
  const root = document.getElementById("match-game");
  const pairs = JSON.parse(document.getElementById("pairs-data").textContent);
  const audioBase = root.dataset.audioBase;   // e.g. "/audio/0/"
  const gradeUrl = root.dataset.gradeUrl;
  const replayUrl = root.dataset.replayUrl;
  const backUrl = root.dataset.backUrl;

  const audioOn = pairs.some((p) => p.audio);
  const mistakes = {};
  pairs.forEach((p) => (mistakes[p.id] = 0));
  const matched = new Set();
  let selLeft = null, selRight = null, locked = false;

  const shuffle = (a) => {
    for (let i = a.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  const audioUrl = (id) => audioBase.replace(/0\/$/, id + "/");
  const play = (id) => { if (audioOn) new Audio(audioUrl(id)).play().catch(() => {}); };

  const left = shuffle(pairs.map((p) => ({ id: p.id, text: p.vietnamese })));
  const right = shuffle(pairs.map((p) => ({ id: p.id, text: p.target })));

  function makeTile(item, side) {
    const b = document.createElement("button");
    b.className = "tile";
    b.textContent = item.text;
    b.dataset.id = item.id;
    if (matched.has(item.id)) { b.classList.add("matched"); b.disabled = true; }
    b.addEventListener("click", () => onPick(b, item, side));
    return b;
  }

  function render() {
    const board = document.createElement("div");
    board.className = "match-board";
    const colL = document.createElement("div"); colL.className = "col";
    const colR = document.createElement("div"); colR.className = "col";
    left.forEach((i) => colL.appendChild(makeTile(i, "left")));
    right.forEach((i) => colR.appendChild(makeTile(i, "right")));
    board.append(colL, colR);
    root.replaceChildren(board);
  }

  function onPick(el, item, side) {
    if (locked || el.disabled) return;
    if (side === "left") {
      if (selLeft) selLeft.el.classList.remove("sel");
      selLeft = { el, id: item.id };
      el.classList.add("sel");
      play(item.id);
    } else {
      if (selRight) selRight.el.classList.remove("sel");
      selRight = { el, id: item.id };
      el.classList.add("sel");
    }
    if (selLeft && selRight) evaluate();
  }

  function evaluate() {
    const l = selLeft, r = selRight;
    if (l.id === r.id) {
      [l.el, r.el].forEach((e) => {
        e.classList.remove("sel"); e.classList.add("matched"); e.disabled = true;
      });
      matched.add(l.id);
      selLeft = selRight = null;
      play(l.id);
      if (matched.size === pairs.length) finish();
    } else {
      mistakes[l.id] += 1;
      locked = true;
      l.el.classList.add("wrong"); r.el.classList.add("wrong");
      setTimeout(() => {
        [l.el, r.el].forEach((e) => e.classList.remove("wrong", "sel"));
        selLeft = selRight = null; locked = false;
      }, 600);
    }
  }

  const ratingFor = (id) => (mistakes[id] === 0 ? 3 : mistakes[id] === 1 ? 2 : 1);

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  function finish() {
    const results = pairs.map((p) => ({ card_id: p.id, rating: ratingFor(p.id) }));
    fetch(gradeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ results }),
    }).catch(() => {});

    const total = Object.values(mistakes).reduce((a, b) => a + b, 0);
    root.innerHTML =
      '<div class="match-done">' +
      '<div class="big">🎉 Hoàn thành!</div>' +
      `<p>${pairs.length} matched · ${total} mistake${total === 1 ? "" : "s"}</p>` +
      '<div class="actions">' +
      `<a class="btn" href="${replayUrl}">Play again</a>` +
      `<a class="btn ghost" href="${backUrl}">Back to decks</a>` +
      "</div></div>";
  }

  render();
})();
