/**
 * Plotly チャート描画
 */

const CATEGORY_COLORS = {
  "魚介類": "#1a6496",
  "牛肉": "#c0392b",
  "果物": "#e67e22",
  "旅行・体験": "#8e44ad",
  "その他": "#95a5a6",
  "家電・電気製品": "#2980b9",
  "米・穀物": "#f1c40f",
  "日用品・生活雑貨": "#27ae60",
  "鶏肉": "#e74c3c",
  "酒・飲料": "#6c3483",
  "野菜": "#2ecc71",
  "豚肉": "#e8a87c",
  "加工食品・惣菜": "#d35400",
  "スイーツ・菓子": "#fd79a8",
};

const CLUSTER_COLORS = {
  "食品コスパ型": "#27ae60",
  "食品プレミアム型": "#f39c12",
  "家電・高額品特化型": "#2980b9",
  "大規模総合型": "#c0392b",
  "汎用・小規模型": "#7f8c8d",
};

const PLOTLY_CONFIG = {
  displayModeBar: false,
  responsive: true,
  locale: "ja",
};

const LAYOUT_BASE = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  margin: { t: 10, r: 20, b: 60, l: 60 },
  font: { family: "'Noto Sans JP', sans-serif", size: 12 },
  showlegend: false,
};

// カテゴリ別棒グラフ
function renderCategoryBar() {
  const cats = state.categories.filter(
    (c) => state.filter.category === "all" || c.category === state.filter.category
  );
  const sorted = [...cats].sort((a, b) => b.count - a.count);

  const trace = {
    type: "bar",
    x: sorted.map((c) => c.count),
    y: sorted.map((c) => c.category),
    orientation: "h",
    marker: { color: sorted.map((c) => CATEGORY_COLORS[c.category] || "#95a5a6") },
    hovertemplate: "<b>%{y}</b><br>件数: %{x:,}<extra></extra>",
  };

  const layout = {
    ...LAYOUT_BASE,
    margin: { t: 10, r: 40, b: 40, l: 110 },
    xaxis: { title: "商品件数", gridcolor: "#eee" },
    yaxis: { autorange: "reversed" },
    height: 340,
  };

  Plotly.react("chart-category", [trace], layout, PLOTLY_CONFIG);
}

// 価格帯別棒グラフ
function renderPriceBar() {
  const segs = state.priceSegments.filter(
    (p) => state.filter.priceSegment === "all" || p.segment === state.filter.priceSegment
  );

  const trace = {
    type: "bar",
    x: segs.map((p) => p.segment),
    y: segs.map((p) => p.share_pct),
    marker: { color: "#e85d04", opacity: 0.85 },
    hovertemplate: "<b>%{x}</b><br>構成比: %{y:.1f}%<br>件数: %{customdata:,}<extra></extra>",
    customdata: segs.map((p) => p.count),
  };

  const layout = {
    ...LAYOUT_BASE,
    xaxis: { title: "" },
    yaxis: { title: "構成比（%）", gridcolor: "#eee" },
    height: 300,
  };

  Plotly.react("chart-price", [trace], layout, PLOTLY_CONFIG);
}

// 散布図: 価格 × レビュー数
function renderScatter() {
  const data = filteredScatter();

  // カテゴリごとにトレースを分ける（凡例に表示するため）
  const catGroups = {};
  data.forEach((d) => {
    if (!catGroups[d.category]) catGroups[d.category] = [];
    catGroups[d.category].push(d);
  });

  const traces = Object.entries(catGroups).map(([cat, pts]) => ({
    type: "scatter",
    mode: "markers",
    name: cat,
    x: pts.map((p) => p.price),
    y: pts.map((p) => p.reviews),
    marker: {
      color: CATEGORY_COLORS[cat] || "#95a5a6",
      size: 6,
      opacity: 0.65,
    },
    hovertemplate: `<b>${cat}</b><br>価格: ¥%{x:,}<br>レビュー数: %{y:,}<extra></extra>`,
  }));

  const layout = {
    ...LAYOUT_BASE,
    showlegend: true,
    legend: { orientation: "h", x: 0, y: -0.2, font: { size: 11 } },
    margin: { t: 10, r: 20, b: 100, l: 70 },
    xaxis: { title: "価格（円）", type: "log", gridcolor: "#eee" },
    yaxis: { title: "レビュー数", type: "log", gridcolor: "#eee" },
    height: 380,
  };

  Plotly.react("chart-scatter", traces, layout, PLOTLY_CONFIG);
}

// 自治体クラスター別棒グラフ
function renderClusterBar() {
  const munis = filteredMunicipalities();
  const counts = {};
  munis.forEach((m) => {
    counts[m.cluster_label] = (counts[m.cluster_label] || 0) + 1;
  });

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  const trace = {
    type: "bar",
    x: sorted.map(([l]) => l),
    y: sorted.map(([, c]) => c),
    marker: { color: sorted.map(([l]) => CLUSTER_COLORS[l] || "#95a5a6") },
    hovertemplate: "<b>%{x}</b><br>自治体数: %{y}<extra></extra>",
  };

  const layout = {
    ...LAYOUT_BASE,
    xaxis: { tickangle: -20 },
    yaxis: { title: "自治体数", gridcolor: "#eee" },
    height: 300,
  };

  Plotly.react("chart-cluster", [trace], layout, PLOTLY_CONFIG);
}
