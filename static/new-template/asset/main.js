(function () {
  "use strict";

  function initializePublicPage() {
// --- Victim memorial gallery count ---
      const memorialResultsCount = document.getElementById(
        "memorialResultsCount"
      );
      const memorialItems = () =>
        Array.from(document.querySelectorAll("#memorialGrid .memorial-item"));

      function updateMemorialCount() {
        if (!memorialResultsCount) return;
        const visible = memorialItems().filter(
          (el) => el.style.display !== "none"
        ).length;
        memorialResultsCount.textContent = `Showing ${visible} victim${
          visible === 1 ? "" : "s"
        }`;
      }

      function parseChartValues(raw, fallbackValues) {
        if (!raw) return fallbackValues;
        const values = String(raw).split(",").map((item) => Number(item.trim())).filter((item) => Number.isFinite(item));
        return values.length ? values : fallbackValues;
      }

      function formatChartPercent(value, total) {
        if (!total) return "0%";
        return `${((value * 100) / total).toFixed(2).replace(/\.?0+$/, "")}%`;
      }

      function hydrateChartLegends() {
        document.querySelectorAll("[data-chart-legend-for]").forEach((legend) => {
          const canvas = document.getElementById(legend.dataset.chartLegendFor);
          if (!canvas) return;

          const values = parseChartValues(canvas.dataset.values, []);
          const total = values.reduce((sum, value) => sum + value, 0);
          legend.querySelectorAll("[data-chart-stat]").forEach((stat, index) => {
            const value = values[index] || 0;
            stat.textContent = `(${value.toLocaleString()} / ${formatChartPercent(value, total)})`;
          });
        });
      }

      // --- Canvas analytics charts ---
      function fitCanvasDpr(canvas) {
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.floor(rect.width * dpr));
        canvas.height = Math.max(1, Math.floor(rect.height * dpr));
        const ctx = canvas.getContext("2d");
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        return { ctx, width: rect.width, height: rect.height };
      }

      function drawZoneChart() {
        const canvas = document.getElementById("zoneChart");
        const fit = fitCanvasDpr(canvas);
        if (!fit) return;
        const { ctx, width, height } = fit;

        const labels = [
          "West",
          "East",
          "Central",
          "North West",
          "South",
          "South East",
          "Mekelle",
          "Other",
        ];
        const fallbackValues = [281, 985, 1729, 688, 192, 481, 38, 36];
        const values = parseChartValues(canvas.dataset.values, fallbackValues);
        const data = labels.map((label, i) => ({
          label,
          value: values[i] || 0,
        }));

        const margin = { top: 54, right: 60, bottom: 26, left: 120 };
        const plotW = width - margin.left - margin.right;
        const plotH = height - margin.top - margin.bottom;
        const rawMax = Math.max(...data.map((d) => d.value), 1);
        const max = Math.ceil(rawMax / 500) * 500;
        const step = Math.max(100, Math.ceil(max / 5 / 100) * 100);
        const rowH = plotH / data.length;

        ctx.clearRect(0, 0, width, height);
        ctx.font = "700 10px Inter, Arial, sans-serif";
        ctx.fillStyle = "rgba(26, 24, 24, .75)";
        ctx.textAlign = "center";
        ctx.fillText("Number of Civilian Victims", margin.left + plotW / 2, 22);

        for (let x = 0; x <= max; x += step) {
          const px = margin.left + (x / max) * plotW;
          ctx.strokeStyle =
            x % (step * 2) === 0
              ? "rgba(140,164,177,.35)"
              : "rgba(140,164,177,.2)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(px, margin.top);
          ctx.lineTo(px, margin.top + plotH);
          ctx.stroke();

          ctx.fillStyle = "rgba(26, 24, 24, .78)";
          ctx.textAlign = "center";
          ctx.font = "600 8.5px Inter, Arial, sans-serif";
          ctx.fillText(x.toLocaleString(), px, margin.top - 10);
        }

        ctx.fillStyle = "rgba(26, 24, 24, .86)";
        ctx.textAlign = "center";
        ctx.save();
        ctx.translate(18, margin.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.font = "700 9px Inter, Arial, sans-serif";
        ctx.fillText("Tigray Zone", 0, 0);
        ctx.restore();

        data.forEach((item, i) => {
          const y = margin.top + i * rowH + rowH * 0.15;
          const barH = rowH * 0.7;
          const barW = (item.value / max) * plotW;

          ctx.fillStyle = "#0a5a72";
          ctx.fillRect(margin.left, y, barW, barH);

          ctx.fillStyle = "rgba(26,24,24,.9)";
          ctx.textAlign = "right";
          ctx.font = "600 8.8px Inter, Arial, sans-serif";
          ctx.fillText(item.label, margin.left - 8, y + barH * 0.68);

          ctx.textAlign = "left";
          ctx.font = "700 9px Inter, Arial, sans-serif";
          ctx.fillText(
            item.value.toLocaleString(),
            margin.left + barW + 6,
            y + barH * 0.68
          );
        });
      }

      function drawAgeChart() {
        const canvas = document.getElementById("ageChart");
        const fit = fitCanvasDpr(canvas);
        if (!fit) return;
        const { ctx, width, height } = fit;

        const labels = [
          "< 10",
          "10-18",
          "18-33",
          "33-49",
          "49-64",
          "64-80",
          "80-95",
          "Unknown",
        ];
        const colors = [
          "#6d79b5",
          "#4fc19a",
          "#d8746a",
          "#539ba0",
          "#a57896",
          "#baca56",
          "#5b8ea7",
          "#d68549",
        ];
        const fallbackValues = [36, 76, 551, 495, 296, 232, 80, 1736];
        const values = parseChartValues(canvas.dataset.values, fallbackValues);
        const data = labels.map((label, i) => ({
          label,
          value: values[i] || 0,
          color: colors[i],
        }));

        const margin = { top: 26, right: 16, bottom: 64, left: 56 };
        const plotW = width - margin.left - margin.right;
        const plotH = height - margin.top - margin.bottom;
        const rawMax = Math.max(...data.map((d) => d.value), 1);
        const max = Math.ceil(rawMax / 500) * 500;
        const gap = 6;
        const barW = (plotW - gap * (data.length - 1)) / data.length;

        ctx.clearRect(0, 0, width, height);

        [0, Math.round(max / 2), max].forEach((v) => {
          const y = margin.top + plotH - (v / max) * plotH;
          ctx.strokeStyle = "rgba(24,24,24,.14)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(margin.left, y);
          ctx.lineTo(margin.left + plotW, y);
          ctx.stroke();

          ctx.fillStyle = "rgba(26,24,24,.72)";
          ctx.textAlign = "right";
          ctx.font = "600 8.5px Inter, Arial, sans-serif";
          ctx.fillText(v.toLocaleString(), margin.left - 6, y + 3);
        });

        data.forEach((item, i) => {
          const x = margin.left + i * (barW + gap);
          const h = (item.value / max) * plotH;
          const y = margin.top + plotH - h;

          ctx.fillStyle = item.color;
          ctx.fillRect(x, y, barW, h);

          ctx.fillStyle = "rgba(26,24,24,.85)";
          ctx.textAlign = "center";
          ctx.font = "700 9px Inter, Arial, sans-serif";
          ctx.fillText(item.value.toLocaleString(), x + barW / 2, y - 6);

          ctx.font = "600 8.4px Inter, Arial, sans-serif";
          ctx.fillText(item.label, x + barW / 2, margin.top + plotH + 16);
        });

        ctx.fillStyle = "rgba(26,24,24,.8)";
        ctx.textAlign = "center";
        ctx.font = "700 9px Inter, Arial, sans-serif";
        ctx.fillText("Age of victims", margin.left + plotW / 2, height - 8);

        ctx.save();
        ctx.translate(13, margin.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText("Number of Civilian Victims", 0, 0);
        ctx.restore();
      }

      function drawCasualtyPieChart() {
        const canvas = document.getElementById("casualtyPieChart");
        const fit = fitCanvasDpr(canvas);
        if (!fit) return;
        const { ctx, width, height } = fit;

        const labels = [
          "Died from lack of food",
          "Killed by Eritrean forces",
          "Died from lack of medicine",
          "Killed by Ethiopian forces",
          "Killed by Ethiopian and Eritrean forces",
          "Killed by Amhara militia and Fano",
        ];
        const colors = [
          "#1f6da3",
          "#28734c",
          "#2f9c34",
          "#e02429",
          "#7f2bbf",
          "#7d3326",
        ];
        const fallbackValues = [31, 2344, 49, 842, 892, 286];
        const values = parseChartValues(canvas.dataset.values, fallbackValues);
        const data = values.map((value, i) => ({
          label: labels[i] || `Category ${i + 1}`,
          value,
          color: colors[i] || "#666",
        }));

        const total = data.reduce((s, d) => s + d.value, 0);
        if (!total) return;

        const cx = width / 2;
        const cy = height / 2 + 8;
        const radius = Math.min(width, height) * 0.33;

        ctx.clearRect(0, 0, width, height);
        let start = -Math.PI / 2;

        data.forEach((item) => {
          const angle = (item.value / total) * Math.PI * 2;
          const end = start + angle;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.arc(cx, cy, radius, start, end);
          ctx.closePath();
          ctx.fillStyle = item.color;
          ctx.fill();

          const pct = (item.value / total) * 100;
          if (pct >= 5) {
            const mid = (start + end) / 2;
            const tx = cx + Math.cos(mid) * (radius * 0.56);
            const ty = cy + Math.sin(mid) * (radius * 0.56);
            ctx.fillStyle = "#ffffff";
            ctx.textAlign = "center";
            ctx.font = "700 10px Inter, Arial, sans-serif";
            ctx.fillText(item.value.toLocaleString(), tx, ty - 3);
            ctx.font = "700 9px Inter, Arial, sans-serif";
            ctx.fillText(`${pct.toFixed(1)}%`, tx, ty + 10);
          }

          start = end;
        });
      }

      function drawGenderDonutChart() {
        const canvas = document.getElementById("genderDonutChart");
        const fit = fitCanvasDpr(canvas);
        if (!fit) return;
        const { ctx, width, height } = fit;

        const labels = ["Male", "Female", "Unknown"];
        const colors = ["#7b5828", "#de262a", "#2f9c34"];
        const fallbackValues = [3233, 273, 0];
        const values = parseChartValues(canvas.dataset.values, fallbackValues);
        const data = values
          .map((value, i) => ({
            label: labels[i] || `Group ${i + 1}`,
            value,
            color: colors[i] || "#666",
          }))
          .filter((d) => d.value > 0);

        const total = data.reduce((s, d) => s + d.value, 0);
        if (!total) return;

        const cx = width / 2;
        const cy = height / 2 + 8;
        const outer = Math.min(width, height) * 0.33;
        const inner = outer * 0.5;

        ctx.clearRect(0, 0, width, height);
        let start = -Math.PI / 2;

        data.forEach((item) => {
          const angle = (item.value / total) * Math.PI * 2;
          const end = start + angle;
          ctx.beginPath();
          ctx.arc(cx, cy, outer, start, end);
          ctx.arc(cx, cy, inner, end, start, true);
          ctx.closePath();
          ctx.fillStyle = item.color;
          ctx.fill();

          const pct = (item.value / total) * 100;
          const mid = (start + end) / 2;
          const tx = cx + Math.cos(mid) * ((outer + inner) / 2);
          const ty = cy + Math.sin(mid) * ((outer + inner) / 2);
          ctx.fillStyle = "#ffffff";
          ctx.textAlign = "center";
          ctx.font = "700 10px Inter, Arial, sans-serif";
          ctx.fillText(item.value.toLocaleString(), tx, ty - 3);
          ctx.font = "700 9px Inter, Arial, sans-serif";
          ctx.fillText(`${pct.toFixed(2)}%`, tx, ty + 10);

          start = end;
        });
      }

      function renderAnalyticsCharts() {
        drawZoneChart();
        drawAgeChart();
        drawCasualtyPieChart();
        drawGenderDonutChart();
        hydrateChartLegends();
      }

      // --- Init ---
      if (window.AOS) AOS.init({ duration: 650, easing: "ease-out", once: true, offset: 80 });

      updateMemorialCount();
      renderAnalyticsCharts();
      if (window.publicChartsResizeHandler) {
        window.removeEventListener("resize", window.publicChartsResizeHandler);
      }
      window.publicChartsResizeHandler = renderAnalyticsCharts;
      window.addEventListener("resize", window.publicChartsResizeHandler);

      const footerYearEl = document.getElementById("footerYear");
      if (footerYearEl) footerYearEl.textContent = new Date().getFullYear();

const memorialSearch = document.getElementById("memorialSearch");
      const zoneFilter = document.getElementById("zoneFilter");
      function filterMemorials() {
        const query = (memorialSearch?.value || "").trim().toLowerCase();
        const zone = (zoneFilter?.value || "").trim().toLowerCase();
        document.querySelectorAll("#memorialGrid .memorial-item").forEach((item) => {
          const haystack = item.dataset.search || "";
          const itemZone = item.dataset.zone || "";
          const show = (!query || haystack.includes(query)) && (!zone || itemZone === zone);
          item.style.display = show ? "" : "none";
        });
        updateMemorialCount();
      }
      if (memorialSearch && !memorialSearch.dataset.publicInitialized) {
        memorialSearch.addEventListener("input", filterMemorials);
        memorialSearch.dataset.publicInitialized = "true";
      }
      if (zoneFilter && !zoneFilter.dataset.publicInitialized) {
        zoneFilter.addEventListener("change", filterMemorials);
        zoneFilter.dataset.publicInitialized = "true";
      }
      filterMemorials();

// --- Django public forms and table filters ---
window.attachAjaxForm = function attachAjaxForm(formId, buttonId, statusId, successMessage, errorMessage) {
  const form = document.getElementById(formId);
  const button = document.getElementById(buttonId);
  const status = document.getElementById(statusId);
  if (!form || !button || !status) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const parsleyForm = window.jQuery?.fn?.parsley
      ? window.jQuery(form).parsley()
      : null;
    if (parsleyForm && !parsleyForm.validate()) return;
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Sending...";
    status.hidden = true;
    status.className = "form-status";

    try {
      const response = await fetch(form.action || window.location.href, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error("Request failed");
      status.textContent = successMessage;
      status.classList.add("success");
      status.hidden = false;
      form.reset();
    } catch (error) {
      status.textContent = errorMessage;
      status.classList.add("error");
      status.hidden = false;
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  });
};

document.querySelectorAll(".filter-controls").forEach((controls) => {
  if (controls.dataset.publicInitialized) return;
  const table = document.querySelector(controls.dataset.target);
  if (!table) return;
  controls.dataset.publicInitialized = "true";
  const inputs = Array.from(controls.querySelectorAll("[data-filter]"));
  const rows = Array.from(table.querySelectorAll("tbody tr"));

  function applyFilters() {
    const filters = Object.fromEntries(
      inputs.map((input) => [input.dataset.filter, (input.value || "").trim().toLowerCase()])
    );
    rows.forEach((row) => {
      const visible = Object.entries(filters).every(([key, value]) => {
        if (!value) return true;
        return (row.dataset[key] || "").includes(value);
      });
      row.classList.toggle("filter-hidden", !visible);
    });
  }

  inputs.forEach((input) => input.addEventListener("input", applyFilters));
  inputs.forEach((input) => input.addEventListener("change", applyFilters));
  controls.querySelector("[data-reset-filters]")?.addEventListener("click", () => {
    inputs.forEach((input) => {
      input.value = "";
    });
    applyFilters();
  });
});
  }

  function isPublicPageLink(link) {
    if (!link || link.dataset.noHtmx !== undefined) return false;
    if (link.hasAttribute("download") || link.target === "_blank") return false;
    if (link.hasAttribute("hx-get") || link.hasAttribute("hx-post")) return false;
    if (link.matches("[data-async-page], [data-async-reset], .dropdown-toggle")) return false;

    const rawHref = link.getAttribute("href");
    if (!rawHref || rawHref === "#" || rawHref.startsWith("#")) return false;

    let url;
    try {
      url = new URL(link.href, window.location.href);
    } catch (error) {
      return false;
    }

    if (url.origin !== window.location.origin) return false;
    if (!["http:", "https:"].includes(url.protocol)) return false;
    return !url.pathname.startsWith("/static/") &&
      !url.pathname.startsWith("/media/") &&
      !url.pathname.startsWith("/admin/") &&
      !url.pathname.startsWith("/Admin");
  }

  function enhancePublicNavigation(root) {
    if (!window.htmx) return;
    const links = [];
    if (root?.matches?.("a[href]")) links.push(root);
    root?.querySelectorAll?.("a[href]").forEach((link) => links.push(link));

    links.forEach((link) => {
      if (!isPublicPageLink(link) || link.dataset.publicNavigation) return;
      link.dataset.publicNavigation = "true";
      link.setAttribute("hx-boost", "true");
      link.setAttribute("hx-target", "#page-content");
      link.setAttribute("hx-select", "#page-content");
      link.setAttribute("hx-select-oob", "#page-assets:outerHTML");
      link.setAttribute("hx-swap", "outerHTML transition:true show:top");
      link.setAttribute("hx-push-url", "true");
      link.setAttribute("hx-indicator", "#page-navigation-indicator");
      window.htmx.process(link);
    });
  }

  window.publicNavigate = function publicNavigate(url) {
    const link = document.createElement("a");
    link.href = url;
    link.hidden = true;
    document.body.appendChild(link);
    enhancePublicNavigation(link);
    link.click();
    window.setTimeout(() => link.remove(), 0);
  };

  function updateBodyClassForNavigation() {
    const homePaths = ["/", "/index.html"];
    const path = window.location.pathname.replace(/\/+$|^\//g, "").toLowerCase();
    const normalized = path ? `/${path}` : "/";
    document.body.classList.toggle("home-page", homePaths.includes(normalized));
  }

  initializePublicPage();

  function initializeHtmxNavigation() {
    if (!window.htmx) return;
    enhancePublicNavigation(document);
    updateBodyClassForNavigation();

    document.body.addEventListener("htmx:load", (event) => {
      initializePublicPage();
      enhancePublicNavigation(event.detail?.elt || document);
      updateBodyClassForNavigation();

      const navigation = document.getElementById("navMain");
      if (navigation?.classList.contains("show") && window.bootstrap) {
        window.bootstrap.Collapse.getOrCreateInstance(navigation).hide();
      }
    });

    document.body.addEventListener("htmx:responseError", () => {
      document.getElementById("page-navigation-indicator")?.classList.remove("htmx-request");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeHtmxNavigation, { once: true });
  } else {
    initializeHtmxNavigation();
  }
})();
