const API = "http://127.0.0.1:8000/api";

let chart;

// INIT
async function init() {
  await loadCompanies();
  await loadStock("RELIANCE");
  await loadMovers();
}

// LOAD COMPANIES
async function loadCompanies() {
  const res = await fetch(`${API}/companies`);
  const data = await res.json();

  const list = document.getElementById("company-list");
  const c1 = document.getElementById("compare1");
  const c2 = document.getElementById("compare2");

  list.innerHTML = "";
  c1.innerHTML = "";
  c2.innerHTML = "";

  data.forEach(c => {
    if (c.symbol === "TATAMOTORS") return;

    // Sidebar
    const btn = document.createElement("button");
    btn.className = "company";
    btn.innerHTML = `
      <div>
        <div class="sym">${c.symbol}</div>
        <div class="name">${c.ticker}</div>
      </div>
    `;
    btn.onclick = () => loadStock(c.symbol);
    list.appendChild(btn);

    // Dropdown
    c1.innerHTML += `<option value="${c.symbol}">${c.symbol}</option>`;
    c2.innerHTML += `<option value="${c.symbol}">${c.symbol}</option>`;
  });
}

// LOAD STOCK
async function loadStock(symbol) {
  const res = await fetch(`${API}/data/${symbol}?days=30`);
  const data = await res.json();

  const labels = data.map(d => d.date);
  const prices = data.map(d => d.close);
  const ma7 = data.map(d => d.ma_7);

  drawChart(labels, prices, ma7);
  updateHeader(symbol, prices);
  loadInsights(symbol);
}

// COMPARE
async function compareStocks() {
  const s1 = document.getElementById("compare1").value;
  const s2 = document.getElementById("compare2").value;

  const res = await fetch(`${API}/compare?symbol1=${s1}&symbol2=${s2}`);
  const data = await res.json();

  const labels = data.data1.map(d => d.date);

  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("stock-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: s1, data: data.data1.map(d => d.close) },
        { label: s2, data: data.data2.map(d => d.close) }
      ]
    }
  });

  document.getElementById("chart-symbol").innerText =
    `${s1} vs ${s2} (Corr: ${data.correlation})`;
}

// DRAW CHART
function drawChart(labels, prices, ma7) {
  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("stock-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Price", data: prices },
        { label: "MA7", data: ma7 }
      ]
    }
  });
}

// HEADER
function updateHeader(symbol, prices) {
  const last = prices[prices.length - 1];
  const prev = prices[prices.length - 2];

  const change = last - prev;
  const pct = ((change / prev) * 100).toFixed(2);

  document.getElementById("chart-symbol").innerText = symbol;
  document.getElementById("chart-price").innerText = `₹${last.toFixed(2)}`;

  const el = document.getElementById("chart-change");
  el.innerText = `${pct}%`;
  el.className = change >= 0 ? "change up" : "change down";
}

// INSIGHTS
async function loadInsights(symbol) {
  const res = await fetch(`${API}/summary/${symbol}`);
  const s = await res.json();

  document.getElementById("insights-grid").innerHTML = `
    <div class="insight"><div class="ilabel">HIGH</div><div class="ival">${s.high_52w}</div></div>
    <div class="insight"><div class="ilabel">LOW</div><div class="ival">${s.low_52w}</div></div>
    <div class="insight"><div class="ilabel">AVG</div><div class="ival">${s.avg_close}</div></div>
    <div class="insight"><div class="ilabel">VOL</div><div class="ival">${s.avg_volatility}</div></div>
  `;
}

// MOVERS
async function loadMovers() {
  const res = await fetch(`${API}/top-movers`);
  const data = await res.json();

  const el = document.getElementById("movers");
  el.innerHTML = "";

  [...data.gainers, ...data.losers].forEach(m => {
    const div = document.createElement("div");
    div.className = "mover";

    const up = m.daily_return >= 0;

    div.innerHTML = `
      <div>${m.symbol}</div>
      <div class="${up ? "up" : "down"}">${m.daily_return}%</div>
    `;

    el.appendChild(div);
  });
}

// RUN
init();