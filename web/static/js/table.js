/**
 * 自治体ランキングテーブル描画
 */

const BADGE_CLASS = {
  "食品コスパ型": "badge-food-cheap",
  "食品プレミアム型": "badge-food-prem",
  "家電・高額品特化型": "badge-elec",
  "大規模総合型": "badge-large",
  "汎用・小規模型": "badge-small",
};

// 星評価HTML（例: 4.5 → ★★★★½）
function starHTML(rating) {
  if (!rating) return '<span style="color:#ccc">—</span>';
  const full = Math.floor(rating);
  const half = rating - full >= 0.4 ? 1 : 0;
  return `<span style="color:#f39c12">${"★".repeat(full)}${half ? "½" : ""}</span> ${rating.toFixed(1)}`;
}

function renderMunicipalityTable() {
  const munis = filteredMunicipalities()
    .filter((m) => m.total_reviews > 0)
    .sort((a, b) => b.total_reviews - a.total_reviews)
    .slice(0, 50);

  const tbody = document.getElementById("muni-tbody");
  tbody.innerHTML = "";

  munis.forEach((m, i) => {
    const tr = document.createElement("tr");
    const badgeClass = BADGE_CLASS[m.cluster_label] || "badge-small";
    const donationStr = m.donation_amount_oku > 0
      ? `${m.donation_amount_oku.toFixed(1)}億円`
      : "—";

    tr.innerHTML = `
      <td style="text-align:center;color:#999">${i + 1}</td>
      <td><strong>${m.shop_name}</strong></td>
      <td style="text-align:right">${m.product_count.toLocaleString()}</td>
      <td style="text-align:right">¥${m.median_price.toLocaleString()}</td>
      <td style="text-align:right">${m.total_reviews.toLocaleString()}</td>
      <td>${starHTML(m.avg_rating)}</td>
      <td>${m.main_category || "—"}</td>
      <td><span class="badge ${badgeClass}">${m.cluster_label}</span></td>
      <td style="text-align:right">${donationStr}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("muni-count").textContent = `（上位50件 / 全${filteredMunicipalities().length.toLocaleString()}自治体）`;
}
