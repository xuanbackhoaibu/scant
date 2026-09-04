import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildSheetDataSignals } from "../excelSheetSignals.js";

describe("excel sheet data signals", () => {
  it("uses visual workbook data before a sheet has been analyzed", () => {
    const signals = buildSheetDataSignals(
      ["Bang_luong", "Tong_hop"],
      {},
      {
        sheets: [
          {
            name: "Bang_luong",
            max_row: 3,
            max_column: 2,
            cells: [
              [{ display_value: "Tên" }, { display_value: "Lương" }],
              [{ display_value: "A" }, { display_value: "10" }],
              [{ display_value: "" }, { display_value: null }],
            ],
          },
          { name: "Tong_hop", max_row: 0, max_column: 0, cells: [] },
        ],
      }
    );

    assert.equal(signals[0].isRead, false);
    assert.equal(signals[0].hasData, true);
    assert.equal(signals[0].populatedCells, 4);
    assert.equal(signals[1].hasData, false);
  });

  it("prefers analyzed overview and quality issue counts once available", () => {
    const signals = buildSheetDataSignals(
      ["Tong_hop"],
      {
        Tong_hop: {
          overview: {
            total_rows: 8,
            total_columns: 6,
            populated_cells: 43,
            empty_cells: 5,
          },
          data_quality_issues: [{ id: "missing" }, { id: "duplicate" }],
        },
      },
      null
    );

    assert.equal(signals[0].isRead, true);
    assert.equal(signals[0].totalRows, 8);
    assert.equal(signals[0].totalColumns, 6);
    assert.equal(signals[0].emptyCells, 5);
    assert.equal(signals[0].issueCount, 2);
  });
});
