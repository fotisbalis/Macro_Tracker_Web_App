import { test } from "node:test";
import assert from "node:assert/strict";
import { formatDate, parseDate } from "../frontend/js/diary-date.js";

test("dates display day first and round-trip to ISO for API requests", () => {
    assert.equal(formatDate("2026-09-15"), "15/09/2026");
    assert.equal(parseDate("03/04/2026"), "2026-04-03");
    for (const date of ["2026-01-05", "2024-02-29", "2000-02-29", "0001-01-01"]) {
        assert.equal(parseDate(formatDate(date)), date);
    }
});

test("invalid, incomplete and non-day-first dates are rejected", () => {
    for (const value of ["", "1/2/2026", "2026-09-15", "09/15/2026", "31/04/2026",
        "29/02/2025", "29/02/1900", "00/01/2026", "01/00/2026", "01/13/2026", "01/01/0000"]) {
        assert.equal(parseDate(value), null, value);
    }
});
