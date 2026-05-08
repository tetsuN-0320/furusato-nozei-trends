/**
 * Plotly チャート描画
 */

const CATEGORY_COLORS = {
  "魚介類":           "#1a6496",
  "牛肉":             "#c0392b",
  "果物":             "#e67e22",
  "旅行・体験":       "#8e44ad",
  "その他":           "#95a5a6",
  "家電・電気製品":   "#2980b9",
  "米・穀物":         "#f1c40f",
  "日用品・生活雑貨": "#27ae60",
  "鶏肉":             "#e74c3c",
  "酒・飲料":         "#6c3483",
  "野菜":             "#2ecc71",
  "豚肉":             "#e8a87c",
  "加工食品・惣菜":   "#d35400",
  "スイーツ・菓子":   "#fd79a8",
};

const CLUSTER_COLORS = {
  "食品コスパ型":       "#27ae60",
  "食品プレミアム型":   "#f39c12",
  "家電・高額品特化型": "#2980b9",
  "大規模総合型":       "#c0392b",
  "汎用・小規模型":     "#7f8c8d",
};

const PLOTLY_CONFIG = { displayModeBar: false, responsive: true };

const LAYOUT_BASE = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  margin: { t: 10, r: 20, b: 60, l: 60 },
  font: { family: "'Noto Sans JP', sans-serif", size: 12 },
  showlegend: false,
};

// ─── カテゴリ別棒グラフ（フィルター非対象） ───
function renderCategoryBar() {
  const sorted = [...state.categories].sort((a, b) => b.count - a.count);
  const trace = {
    type: "bar",
    x: sorted.map((c) => c.count),
    y: sorted.map((c) => c.category),
    orientation: "h",
    marker: { color: sorted.map((c) => CATEGORY_COLORS[c.category] || "#95a5a6") },
    hovertemplate: "<b>%{y}</b><br>件数: %{x:,}<extra></extra>",
  };
  Plotly.react("chart-category", [trace], {
    ...LAYOUT_BASE,
    margin: { t: 10, r: 40, b: 40, l: 110 },
    xaxis: { title: "商品件数", gridcolor: "#eee" },
    yaxis: { autorange: "reversed" },
    height: 340,
  }, PLOTLY_CONFIG);
}

// ─── 価格帯別構成比 ★（フィルター時は scatter データで再集計） ───
const PRICE_BINS = [
  { label: "〜5千円",    min: 0,      max: 5000 },
  { label: "5千〜1万円", min: 5000,   max: 10000 },
  { label: "1〜2万円",   min: 10000,  max: 20000 },
  { label: "2〜3万円",   min: 20000,  max: 30000 },
  { label: "3〜5万円",   min: 30000,  max: 50000 },
  { label: "5〜10万円",  min: 50000,  max: 100000 },
  { label: "10万円〜",   min: 100000, max: Infinity },
];

function renderPriceBar() {
  const isFiltered = state.filter.category !== "all" || state.filter.ratings.length > 0;

  let segments, labels;
  if (!isFiltered) {
    segments = state.priceSegments.map((p) => p.share_pct);
    labels   = state.priceSegments.map((p) => p.segment);
  } else {
    const data = filteredScatter();
    const total = data.length || 1;
    labels   = PRICE_BINS.map((b) => b.label);
    segments = PRICE_BINS.map((bin) => {
      const n = data.filter((d) => d.price >= bin.min && d.price < bin.max).length;
      return (n / total) * 100;
    });
  }

  Plotly.react("chart-price", [{
    type: "bar",
    x: labels,
    y: segments,
    marker: { color: "#e85d04", opacity: 0.85 },
    hovertemplate: "<b>%{x}</b><br>構成比: %{y:.1f}%<extra></extra>",
  }], {
    ...LAYOUT_BASE,
    xaxis: { title: "" },
    yaxis: { title: "構成比（%）", gridcolor: "#eee" },
    height: 300,
  }, PLOTLY_CONFIG);
}

// ─── 価格 × レビュー数（カテゴリ別）★ ───
function renderScatter() {
  const data = filteredScatter();
  const catGroups = {};
  data.forEach((d) => { (catGroups[d.category] = catGroups[d.category] || []).push(d); });

  const traces = Object.entries(catGroups).map(([cat, pts]) => ({
    type: "scatter", mode: "markers", name: cat,
    x: pts.map((p) => p.price),
    y: pts.map((p) => p.reviews),
    marker: { color: CATEGORY_COLORS[cat] || "#95a5a6", size: 6, opacity: 0.65 },
    hovertemplate: `<b>${cat}</b><br>価格: ¥%{x:,}<br>レビュー数: %{y:,}<extra></extra>`,
  }));

  Plotly.react("chart-scatter", traces, {
    ...LAYOUT_BASE,
    showlegend: true,
    legend: { orientation: "h", x: 0, y: -0.25, font: { size: 11 } },
    margin: { t: 10, r: 20, b: 110, l: 70 },
    xaxis: { title: "価格（円）", type: "log", gridcolor: "#eee" },
    yaxis: { title: "レビュー数", type: "log", gridcolor: "#eee" },
    height: 380,
  }, PLOTLY_CONFIG);
}

// ─── 自治体別 レビュー数 × 平均評価 ★ ───
function renderMunicipalityScatter() {
  const munis = filteredMunicipalities().filter((m) => m.avg_rating && m.total_reviews > 0);
  const clusterGroups = {};
  munis.forEach((m) => { (clusterGroups[m.cluster_label] = clusterGroups[m.cluster_label] || []).push(m); });

  const traces = Object.entries(clusterGroups).map(([label, pts]) => ({
    type: "scatter", mode: "markers", name: label,
    x: pts.map((p) => p.total_reviews),
    y: pts.map((p) => p.avg_rating),
    text: pts.map((p) => p.shop_name),
    marker: {
      color: CLUSTER_COLORS[label] || "#95a5a6",
      size: pts.map((p) => Math.max(6, Math.min(28, Math.sqrt(p.product_count) * 1.5))),
      opacity: 0.72,
      sizemode: "diameter",
    },
    hovertemplate: "<b>%{text}</b><br>レビュー数: %{x:,}<br>平均評価: %{y:.2f}<extra></extra>",
  }));

  Plotly.react("chart-muni-scatter", traces, {
    ...LAYOUT_BASE,
    showlegend: true,
    legend: { orientation: "h", x: 0, y: -0.25, font: { size: 11 } },
    margin: { t: 10, r: 20, b: 110, l: 60 },
    xaxis: { title: "レビュー数合計（人気度）", type: "log", gridcolor: "#eee" },
    yaxis: { title: "平均評価（満足度）", range: [2.5, 5.5], gridcolor: "#eee" },
    height: 400,
    shapes: [{ type: "line", x0: 0, x1: 1, y0: 4.0, y1: 4.0,
               xref: "paper", yref: "y", line: { color: "#e85d04", width: 1, dash: "dot" } }],
    annotations: [{ x: 1, y: 4.12, xref: "paper", yref: "y",
                    text: "評価4.0以上", showarrow: false,
                    font: { color: "#e85d04", size: 11 }, xanchor: "right" }],
  }, PLOTLY_CONFIG);
}

// ─── 自治体タイプ別棒グラフ（フィルター非対象） ───
function renderClusterBar() {
  const counts = {};
  state.municipalities.forEach((m) => { counts[m.cluster_label] = (counts[m.cluster_label] || 0) + 1; });
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  Plotly.react("chart-cluster", [{
    type: "bar",
    x: sorted.map(([l]) => l),
    y: sorted.map(([, c]) => c),
    marker: { color: sorted.map(([l]) => CLUSTER_COLORS[l] || "#95a5a6") },
    hovertemplate: "<b>%{x}</b><br>自治体数: %{y}<extra></extra>",
  }], {
    ...LAYOUT_BASE,
    xaxis: { tickangle: -20 },
    yaxis: { title: "自治体数", gridcolor: "#eee" },
    height: 300,
  }, PLOTLY_CONFIG);
}
