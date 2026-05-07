/**
 * ダッシュボード状態管理・初期化
 */

const DATA_BASE = "./static/data/";

// グローバル状態
const state = {
  categories: [],
  priceSegments: [],
  municipalities: [],
  scatter: [],
  summary: {},
  filter: {
    category: "all",
    priceSegment: "all",
    clusterLabel: "all",
  },
};

// データ読み込み
async function loadAll() {
  const [summary, categories, priceSegments, municipalities, scatter] = await Promise.all([
    fetch(`${DATA_BASE}summary.json`).then((r) => r.json()),
    fetch(`${DATA_BASE}categories.json`).then((r) => r.json()),
    fetch(`${DATA_BASE}price_segments.json`).then((r) => r.json()),
    fetch(`${DATA_BASE}municipalities.json`).then((r) => r.json()),
    fetch(`${DATA_BASE}scatter.json`).then((r) => r.json()),
  ]);
  state.summary = summary;
  state.categories = categories;
  state.priceSegments = priceSegments;
  state.municipalities = municipalities;
  state.scatter = scatter;
}

// KPIカード描画
function renderKPIs() {
  const s = state.summary;
  document.getElementById("kpi-products").textContent = s.total_products.toLocaleString();
  document.getElementById("kpi-municipalities").textContent = s.total_municipalities.toLocaleString();
  document.getElementById("kpi-categories").textContent = s.total_categories;
  document.getElementById("kpi-rating").textContent = s.avg_review_score.toFixed(2);
  document.getElementById("kpi-median-price").textContent = "¥" + s.median_price.toLocaleString();
}

// フィルター選択肢を生成
function populateFilters() {
  const catSel = document.getElementById("filter-category");
  state.categories.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.category;
    opt.textContent = `${c.category}（${c.count.toLocaleString()}件）`;
    catSel.appendChild(opt);
  });

  const priceSel = document.getElementById("filter-price");
  state.priceSegments.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.segment;
    opt.textContent = p.segment;
    priceSel.appendChild(opt);
  });

  const clusterSel = document.getElementById("filter-cluster");
  const labels = [...new Set(state.municipalities.map((m) => m.cluster_label))].sort();
  labels.forEach((l) => {
    const opt = document.createElement("option");
    opt.value = l;
    opt.textContent = l;
    clusterSel.appendChild(opt);
  });
}

// フィルター変更ハンドラー
function onFilterChange() {
  state.filter.category = document.getElementById("filter-category").value;
  state.filter.priceSegment = document.getElementById("filter-price").value;
  state.filter.clusterLabel = document.getElementById("filter-cluster").value;
  renderAll();
}

// 全チャート再描画
function renderAll() {
  renderCategoryBar();
  renderPriceBar();
  renderScatter();
  renderClusterBar();
  renderMunicipalityTable();
}

// フィルター適用済み散布図データ取得
function filteredScatter() {
  return state.scatter.filter((d) => {
    if (state.filter.category !== "all" && d.category !== state.filter.category) return false;
    return true;
  });
}

// フィルター適用済み自治体データ取得
function filteredMunicipalities() {
  return state.municipalities.filter((m) => {
    if (state.filter.clusterLabel !== "all" && m.cluster_label !== state.filter.clusterLabel) return false;
    return true;
  });
}

// インサイトバナー（静的）
function renderInsights() {
  const s = state.summary;
  const top = state.categories[0];
  const items = [
    `最多カテゴリは「${top.category}」で全体の${top.share_pct}%（${top.count.toLocaleString()}件）を占める`,
    `返礼品の中央価格は ¥${s.median_price.toLocaleString()}。楽天市場全体より高単価な傾向`,
    `全1,497自治体のうち「食品コスパ型」が最多（62%）、次いで「家電・高額品特化型」（37%）`,
    `平均レビュースコア ${s.avg_review_score.toFixed(2)} ／5.0 — 購入満足度は高水準`,
  ];
  const ul = document.getElementById("insights-list");
  items.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    ul.appendChild(li);
  });
}

// メイン初期化
async function init() {
  try {
    await loadAll();
    renderKPIs();
    populateFilters();
    renderInsights();
    renderAll();

    document.getElementById("filter-category").addEventListener("change", onFilterChange);
    document.getElementById("filter-price").addEventListener("change", onFilterChange);
    document.getElementById("filter-cluster").addEventListener("change", onFilterChange);
    document.getElementById("btn-reset").addEventListener("click", () => {
      document.getElementById("filter-category").value = "all";
      document.getElementById("filter-price").value = "all";
      document.getElementById("filter-cluster").value = "all";
      state.filter = { category: "all", priceSegment: "all", clusterLabel: "all" };
      renderAll();
    });
    // ローディング表示を非表示にする
    const loadingMsg = document.getElementById("loading-msg");
    if (loadingMsg) loadingMsg.style.display = "none";
  } catch (e) {
    console.error("データ読み込みエラー:", e);
    const loadingMsg = document.getElementById("loading-msg");
    if (loadingMsg) loadingMsg.textContent = "データの読み込みに失敗しました。";
  }
}

document.addEventListener("DOMContentLoaded", init);
