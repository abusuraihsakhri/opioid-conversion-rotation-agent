"use strict";

// CDC 2022 Table of Morphine Milligram Equivalent Doses (not rotation factors).
const MME_FACTORS = Object.freeze({
  morphine_po: { label: "Morphine, oral", factor: 1, unit: "mg/day" },
  oxycodone_po: { label: "Oxycodone, oral", factor: 1.5, unit: "mg/day" },
  hydromorphone_po: { label: "Hydromorphone, oral", factor: 5, unit: "mg/day" },
  hydrocodone_po: { label: "Hydrocodone, oral", factor: 1, unit: "mg/day" },
  codeine_po: { label: "Codeine, oral", factor: 0.15, unit: "mg/day" },
  tramadol_po: { label: "Tramadol, oral", factor: 0.2, unit: "mg/day" },
  fentanyl_patch: { label: "Fentanyl, transdermal", factor: 2.4, unit: "mcg/hour" }
});

function calculateDailyMME(drug, dose) {
  if (!Object.prototype.hasOwnProperty.call(MME_FACTORS, drug)) {
    throw new RangeError("Unsupported opioid or route.");
  }
  if (typeof dose !== "number" || !Number.isFinite(dose) || dose <= 0 || dose > 1000000) {
    throw new RangeError("Enter a finite, positive daily dose or patch delivery rate.");
  }
  const result = dose * MME_FACTORS[drug].factor;
  if (!Number.isFinite(result)) throw new RangeError("MME result is out of range.");
  return result;
}

function totalMME(regimens) {
  if (!Array.isArray(regimens)) throw new TypeError("Regimens must be an array.");
  const total = regimens.reduce((acc, item) => acc + calculateDailyMME(item.drug, item.dose), 0);
  if (!Number.isFinite(total)) throw new RangeError("Total MME exceeds numeric range.");
  return total;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { MME_FACTORS, calculateDailyMME, totalMME };
}

if (typeof document !== "undefined") {
  const regimens = [];
  const drug = document.getElementById("drug");
  const input = document.getElementById("daily-dose");
  const doseLabel = document.getElementById("dose-label");
  const error = document.getElementById("error");
  const rows = document.getElementById("regimen-rows");
  const totalEl = document.getElementById("total-mme");
  const format = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

  function setError(message) {
    error.textContent = message;
  }

  function updateDoseLabel() {
    doseLabel.textContent = drug.value === "fentanyl_patch"
      ? "Patch delivery rate (mcg/hour)"
      : "Total daily dose (mg/day)";
  }

  function render() {
    rows.replaceChildren();
    if (!regimens.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 5;
      cell.textContent = "No regimen entered.";
      row.appendChild(cell);
      rows.appendChild(row);
    }
    regimens.forEach((item, index) => {
      const info = MME_FACTORS[item.drug];
      const row = document.createElement("tr");
      const fields = [
        info.label,
        format.format(item.dose) + " " + info.unit,
        String(info.factor),
        format.format(calculateDailyMME(item.drug, item.dose))
      ];
      fields.forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });
      const action = document.createElement("td");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "secondary";
      remove.textContent = "Remove";
      remove.setAttribute("aria-label", "Remove " + info.label + " regimen");
      remove.addEventListener("click", () => {
        regimens.splice(index, 1);
        render();
      });
      action.appendChild(remove);
      row.appendChild(action);
      rows.appendChild(row);
    });
    totalEl.textContent = format.format(totalMME(regimens));
  }

  drug.addEventListener("change", updateDoseLabel);
  document.getElementById("dose-form").addEventListener("submit", event => {
    event.preventDefault();
    setError("");
    try {
      if (!input.value.trim()) throw new RangeError("Enter the daily dose or rate.");
      const dose = Number(input.value);
      calculateDailyMME(drug.value, dose);
      if (regimens.length >= 30) throw new RangeError("At most 30 regimens are supported.");
      regimens.push({ drug: drug.value, dose });
      render();
      input.value = "";
      input.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid input.");
    }
  });
  document.getElementById("clear").addEventListener("click", () => {
    regimens.length = 0;
    setError("");
    render();
  });
  updateDoseLabel();
  render();
}
