/**
 * ダッシュボード状態管理・初期化
 *
 * フィルター対象（★）: 価格帯構成比 / 価格×レビュー散布図 /
 *                      レビュー×評価散布図 / 自治体散布図 / 自治体テーブル
 * フィルター非対象: カテゴリ別商品件数 / 自治体タイプ棒グラフ
 */

const DATA_BASE = "./static/data/";

const state = {
  categories: [],
  priceSegments: [],
  municipalities: [],
  scatter: [],
  summary: {},
  filter: {
    category: "all",       // カテゴリ名 or "all"
    ratings: [],           // チェック済み評価点の配列（空=すべて）
    clusterLabel: "all",   // 自治体タイプ or "all"
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
  // カテゴリ
  const catSel = document.getElementById("filter-category");
  state.categories.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.category;
    opt.textContent = `${c.category}（${c.count.toLocaleString()}件）`;
    catSel.appendChild(opt);
  });

  // 自治体タイプ
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
  state.filter.clusterLabel = document.getElementById("filter-cluster").value;
  state.filter.ratings = [...document.querySelectorAll(".rating-check:checked")]
    .map((cb) => parseInt(cb.value));
  renderAll();
}

// 全チャート再描画
function renderAll() {
  renderCategoryBar();         // フィルター非対象
  renderPriceBar();            // ★
  renderScatter();             // ★ 価格×レビュー
  renderMunicipalityScatter(); // ★ 自治体散布図
  renderClusterBar();          // フィルター非対象
  renderMunicipalityTable();   // ★
}

// ★ フィルター適用: scatter.json（商品レベル）
//   カテゴリ・評価点でフィルタリング
function filteredScatter() {
  const { category, ratings } = state.filter;
  return state.scatter.filter((d) => {
    if (category !== "all" && d.category !== category) return false;
    if (ratings.length > 0) {
      if (!d.rating) return false;
      if (!ratings.includes(Math.floor(d.rating))) return false;
    }
    return true;
  });
}

// ★ フィルター適用: municipalities.json（自治体レベル）
//   カテゴリ（主力カテゴリで絞り込み）・自治体タイプ・評価点でフィルタリング
function filteredMunicipalities() {
  const { category, clusterLabel, ratings } = state.filter;
  return state.municipalities.filter((m) => {
    if (category !== "all" && m.main_category !== category) return false;
    if (clusterLabel !== "all" && m.cluster_label !== clusterLabel) return false;
    if (ratings.length > 0) {
      if (!m.avg_rating) return false;
      if (!ratings.includes(Math.floor(m.avg_rating))) return false;
    }
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
    `平均レビュースコア ${s.avg_review_score.toFixed(2)} ／5.0 — レビュー数とスコアを両立する自治体が高付加価値戦略の鍵`,
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

    // フィルターイベント
    document.getElementById("filter-category").addEventListener("change", onFilterChange);
    document.getElementById("filter-cluster").addEventListener("change", onFilterChange);
    document.querySelectorAll(".rating-check").forEach((cb) =>
      cb.addEventListener("change", onFilterChange)
    );

    // リセット
    document.getElementById("btn-reset").addEventListener("click", () => {
      document.getElementById("filter-category").value = "all";
      document.getElementById("filter-cluster").value = "all";
      document.querySelectorAll(".rating-check").forEach((cb) => (cb.checked = false));
      state.filter = { category: "all", ratings: [], clusterLabel: "all" };
      renderAll();
    });

    const loadingMsg = document.getElementById("loading-msg");
    if (loadingMsg) loadingMsg.style.display = "none";
  } catch (e) {
    console.error("データ読み込みエラー:", e);
    const loadingMsg = document.getElementById("loading-msg");
    if (loadingMsg) loadingMsg.textContent = "データの読み込みに失敗しました。";
  }
}

document.addEventListener("DOMContentLoaded", init);
