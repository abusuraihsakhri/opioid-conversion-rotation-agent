"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { MME_FACTORS, calculateDailyMME, totalMME } = require("../web/app.js");

test("CDC 2022 examples and units", () => {
  assert.equal(calculateDailyMME("morphine_po", 30), 30);
  assert.equal(calculateDailyMME("oxycodone_po", 20), 30);
  assert.equal(calculateDailyMME("hydromorphone_po", 12), 60);
  assert.equal(calculateDailyMME("tramadol_po", 100), 20);
  assert.equal(calculateDailyMME("fentanyl_patch", 25), 60);
  assert.equal(MME_FACTORS.fentanyl_patch.unit, "mcg/hour");
});

test("Multiple opioid regimens sum without premature rounding", () => {
  assert.equal(totalMME([{ drug: "morphine_po", dose: 10 }, { drug: "oxycodone_po", dose: 20 }]), 40);
  assert.equal(totalMME([]), 0);
});

test("Reject invalid doses, unsupported drugs and unsafe coercions", () => {
  for (const value of [0, -1, NaN, Infinity, -Infinity, "20", true, null, 1000001]) {
    assert.throws(() => calculateDailyMME("morphine_po", value), RangeError);
  }
  assert.throws(() => calculateDailyMME("methadone_po", 10), RangeError);
  assert.throws(() => calculateDailyMME("__proto__", 10), RangeError);
  assert.throws(() => totalMME(null), TypeError);
});
