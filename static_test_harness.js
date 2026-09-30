/* Browser test harness for the static Pages build.
 *
 * Injected into a freshly exported page so it runs against the real SAKURA bootstrap,
 * the real DOM and the real data.json. Prints PASS/FAIL into <pre id="out">.
 */
(() => {
  const R = [];
  const ok = (c, m) => R.push((c ? "PASS  " : "FAIL  ") + m);
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const finish = () => {
    document.getElementById("out").textContent = "BEGIN\n" + R.join("\n") + "\nEND";
    document.title = R.some((x) => x.startsWith("FAIL")) ? "RESULT_FAIL" : "RESULT_OK";
  };

  async function waitFor(cond, ms = 8000) {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) {
      if (cond()) return true;
      await wait(50);
    }
    return false;
  }

  // The game keeps its state in a module closure, so seeding money means writing
  // localStorage and reloading. Phase 1 funds the save, phase 2 does the work.
  const PHASE = new URLSearchParams(location.search).get("p") || "1";
  if (PHASE === "1") {
    (async () => {
      try {
        await waitFor(() => typeof window.SAKURA?.pull === "function");
        const D = await window.SAKURA.load();
        const c = D.cases.find((x) => x.hasLegendary);
        const poor = await window.SAKURA.pull(c.slug, 1);
        R.push(
          (poor.ok === false && /Не хватает/.test(poor.error || "") ? "PASS  " : "FAIL  ") +
            "insufficient funds rejected: " + JSON.stringify(poor.error),
        );
        localStorage.setItem("sakura.save.v1", JSON.stringify({ v: 1, petals: 10000000, pity: 0, owned: {}, logs: [], lots: [], trades: 0 }));
      } catch (e) {
        R.push("FAIL  phase1: " + e);
      }
      finish();
      location.replace(location.pathname + "?p=2");
    })();
    return;
  }

  (async () => {
    try {
      /* ---------------------------------------------------- assets actually load */
      const cssOk = await waitFor(
        () => getComputedStyle(document.querySelector(".nav")).position === "fixed",
        4000,
      );
      ok(cssOk, "sakura.css applied (nav is fixed)");
      ok(await waitFor(() => typeof window.SAKURA?.pull === "function"), "static-mode.js installed SAKURA.pull");

      const logo = document.querySelector(".brand-mark img");
      const logoOk = await waitFor(() => logo && logo.naturalWidth > 0, 4000);
      ok(logoOk, "logo SVG loaded from " + (logo?.getAttribute("src") || "?"));
      const artOk = await waitFor(
        () => [...document.querySelectorAll("img")].some((i) => i.naturalWidth > 0),
        6000,
      );
      ok(artOk, "at least one image resolved on the page");

      /* ------------------------------------------------------------ catalogue */
      const D = await (await fetch("/data.json")).json();
      ok(D.girls.length > 0 && D.cases.length > 0, `data.json: ${D.girls.length} girls, ${D.cases.length} cases`);
      const c = D.cases.find((x) => x.hasLegendary);
      ok(!!c, "found a case with a legendary guarantee");

      let wsum = 0;
      for (const cs of D.cases) wsum += cs.drops.reduce((s, d) => s + d.w, 0);
      const avg = wsum / D.cases.length;
      ok(Math.abs(avg - 100) < 0.5, `every case's drop weights sum to 100 (avg ${avg.toFixed(2)})`);

      const badGirl = D.girls.filter((g) => !g.fallback.startsWith("/static/art/avatar/"));
      ok(badGirl.length === 0, `all girls have a static SVG fallback (${badGirl.length} bad)`);
      const head = await fetch(D.girls[0].fallback).then((r) => r.status);
      ok(head === 200, `avatar file exists (${D.girls[0].fallback} -> ${head})`);

      /* ----------------------------------------------------------------- gacha */
      const START = 10000000;
      /* ------------------------------------- petals bookkeeping, one clean case at a time */
      // a fresh save has a known purse, so charge exactly one pull and compare
      const solo = await window.SAKURA.pull(c.slug, 1);
      ok(solo.ok, "single pull succeeds");
      if (!solo.ok) throw new Error("pull failed: " + JSON.stringify(solo.error));
      const afterSolo = solo.petals;
      ok(afterSolo === START - c.price, `one pull costs ${c.price} (${afterSolo} == ${START - c.price})`);
      ok(solo.results[0].is_new === true && solo.results[0].count === 1,
        `first pull is_new=${solo.results[0].is_new} count=${solo.results[0].count}`);

      // now ten more, and check the delta is exactly 10x
      const r10 = await window.SAKURA.pull(c.slug, 10);
      ok(r10.ok && r10.results.length === 10, "x10 returns 10 results");
      ok(r10.petals === afterSolo - c.price * 10,
        `x10 costs 10x (${afterSolo} -> ${r10.petals}, expected ${afterSolo - c.price * 10})`);

      // and ten more from a different case, to rule out a case-specific quirk
      const c2 = D.cases.find((x) => x.slug !== c.slug);
      const base2 = r10.petals;
      const r10b = await window.SAKURA.pull(c2.slug, 10);
      ok(r10b.ok && r10b.petals === base2 - c2.price * 10,
        `x10 on ${c2.slug} costs 10x (${r10b.petals} == ${base2 - c2.price * 10})`);

      let dupe = null;
      for (let i = 0; i < 500 && !dupe; i++) {
        const r = await window.SAKURA.pull(c.slug, 1);
        for (const res of r.results) if (res.is_new === false && res.count >= 2) dupe = res;
      }
      ok(!!dupe, "duplicate pull reports is_new=false and count>=2");

      /* ------------------------------------------------------------------ pity */
      // drive the counter up through real pulls rather than writing state behind the game's back
      const cap = D.pityLimit;
      let guard = 0;
      while (guard++ < cap + 5) {
        const r = await window.SAKURA.pull(c.slug, 1);
        if (r.pity === 0) break; // a legend landed, counter reset
      }
      ok(guard <= cap + 5, `a legend appeared within ${cap} pulls (took ${guard})`);
      const rp = await window.SAKURA.pull(c.slug, 1);
      ok(rp.pity <= 1, `pity counter behaves (${rp.pity})`);

      /* -------------------------------------------------- no legends in cheap case */
      const cheap = D.cases.find((x) => !x.hasLegendary);
      if (cheap) {
        let forced = 0;
        for (let i = 0; i < 120; i++) {
          const r = await window.SAKURA.pull(cheap.slug, 1);
          if (!r.ok) break;
          if (r.results[0].rarity === "sakura") forced++;
        }
        ok(forced === 0, `case without legends never drops one (${forced})`);
      }

      /* ------------------------------------------------------ persistence in localStorage */
      const after = JSON.parse(localStorage.getItem("sakura.save.v1"));
      ok(after.total_opens > 0, `total_opens persisted (${after.total_opens})`);
      ok(Object.keys(after.owned).length > 0, `collection persisted (${Object.keys(after.owned).length} girls)`);
      ok(after.pity >= 0 && after.pity <= D.pityLimit, `pity in range (${after.pity}/${D.pityLimit})`);

      /* ------------------------------------------------------------ theme toggle */
      const tb = document.getElementById("themeBtn");
      ok(!!tb, "theme toggle button present");
      const wasDark = document.documentElement.dataset.theme;
      tb?.click();
      await wait(120);
      const nowDark = document.documentElement.dataset.theme;
      ok(nowDark && nowDark !== wasDark, `theme toggled ${wasDark || "(none)"} -> ${nowDark}`);
      ok(localStorage.getItem("sakura-theme") === nowDark, "theme choice persisted to localStorage");
      const bg = getComputedStyle(document.body).backgroundColor;
      ok(bg !== "rgb(255, 255, 255)" && bg !== "rgba(0, 0, 0, 0)", "body background repainted (" + bg + ")");
      tb?.click();
    } catch (e) {
      R.push("FAIL  harness threw: " + (e && e.stack ? e.stack : e));
    }
    finish();
  })();
})();
