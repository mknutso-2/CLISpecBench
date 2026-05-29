const DATA_URL = "test-results-published.json";
const MATRIX_ALL_COLUMN_KEY = "__all_selected_results__";
const OUTCOME_ORDER = ["failed", "passed", "skipped", "unknown"];
const OUTCOME_LABELS = {
  failed: "Failed",
  passed: "Passed",
  skipped: "Skipped",
  unknown: "Unknown",
};
const OUTCOME_SHORT = {
  failed: "F",
  passed: "P",
  skipped: "S",
  unknown: "?",
};
const AGENT_SHORT_NAMES = {
  "claude-code": "CC",
  "codex-cli": "C",
  codex: "C",
};
const AGENT_FULL_NAMES = {
  "claude-code": "Claude Code",
  "codex-cli": "Codex CLI",
  codex: "Codex",
};
const MODEL_SHORT_NAMES = {
  "claude-opus-4-7": "O-4.7",
};
const MODEL_FULL_NAMES = {
  "claude-opus-4-7": "Claude Opus 4.7",
};

const state = {
  rows: [],
  runs: [],
  evalOptions: [],
  pairOptions: [],
  outcomeOptions: [],
  selectedEvalLanguages: new Set(),
  selectedEvalVersions: new Map(),
  expandedVersionEvals: new Set(),
  selectedPairs: new Set(),
  selectedOutcomes: new Set(),
  viewMode: "matrix",
  columnMode: "pair",
  rowMode: "eval_language",
  onlyDisagreements: false,
  searchText: "",
  matrixSortKey: "",
  matrixSortDirection: "asc",
  tableSortKey: "",
  tableSortDirection: "asc",
  detailRows: [],
  detailTitle: "",
};

const elements = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  cacheElements();
  bindStaticControls();
  await loadData();
}

function cacheElements() {
  [
    "column-mode",
    "controls-toggle",
    "dashboard-layout",
    "detail-panel",
    "error-banner",
    "eval-clear",
    "eval-list",
    "eval-select-all",
    "matrix-count",
    "matrix-empty",
    "matrix-panel",
    "only-disagreements",
    "outcome-list",
    "pair-clear",
    "pair-list",
    "pair-select-all",
    "row-mode",
    "status",
    "table-count",
    "table-empty",
    "table-panel",
    "test-matrix-table",
    "test-results-table",
    "test-search",
    "version-list",
    "view-mode",
  ].forEach((id) => {
    elements[toCamelCase(id)] = document.getElementById(id);
  });
}

function bindStaticControls() {
  elements.controlsToggle.addEventListener("click", () => {
    const collapsed = !elements.dashboardLayout.classList.contains("controls-collapsed");
    elements.dashboardLayout.classList.toggle("controls-collapsed", collapsed);
    elements.controlsToggle.textContent = collapsed ? "Show controls" : "Hide controls";
    elements.controlsToggle.setAttribute("aria-expanded", String(!collapsed));
  });

  elements.viewMode.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-view-mode]");
    if (!button) {
      return;
    }
    state.viewMode = button.dataset.viewMode;
    render();
  });

  elements.columnMode.addEventListener("change", () => {
    state.columnMode = elements.columnMode.value;
    render();
  });

  elements.rowMode.addEventListener("change", () => {
    state.rowMode = elements.rowMode.value;
    render();
  });

  elements.onlyDisagreements.addEventListener("change", () => {
    state.onlyDisagreements = elements.onlyDisagreements.checked;
    render();
  });

  elements.testSearch.addEventListener("input", () => {
    state.searchText = elements.testSearch.value.trim().toLowerCase();
    render();
  });

  elements.pairList.addEventListener("change", (event) => {
    updateSelectionFromCheckbox(event, state.selectedPairs);
  });
  elements.evalList.addEventListener("change", (event) => {
    updateSelectionFromCheckbox(event, state.selectedEvalLanguages);
  });
  elements.versionList.addEventListener("click", (event) => {
    const button = event.target.closest('button[data-action="toggle-versions"]');
    if (!button) {
      return;
    }
    const evalName = button.dataset.eval || "";
    if (!evalName) {
      return;
    }
    if (state.expandedVersionEvals.has(evalName)) {
      state.expandedVersionEvals.delete(evalName);
    } else {
      state.expandedVersionEvals.add(evalName);
    }
    renderVersionFilters();
  });
  elements.versionList.addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || input.dataset.group !== "eval-version") {
      return;
    }
    const evalName = input.dataset.eval || "";
    if (!state.selectedEvalVersions.has(evalName)) {
      state.selectedEvalVersions.set(evalName, new Set());
    }
    const selectedVersions = state.selectedEvalVersions.get(evalName);
    if (input.checked) {
      selectedVersions.add(versionKey(input.value));
    } else {
      selectedVersions.delete(versionKey(input.value));
    }
    renderVersionFilters();
    render();
  });
  elements.outcomeList.addEventListener("change", (event) => {
    updateSelectionFromCheckbox(event, state.selectedOutcomes);
  });

  elements.pairSelectAll.addEventListener("click", () => {
    state.selectedPairs = new Set(state.pairOptions);
    renderFilters();
    render();
  });
  elements.pairClear.addEventListener("click", () => {
    state.selectedPairs.clear();
    renderFilters();
    render();
  });
  elements.evalSelectAll.addEventListener("click", () => {
    state.selectedEvalLanguages = new Set(state.evalOptions);
    renderFilters();
    render();
  });
  elements.evalClear.addEventListener("click", () => {
    state.selectedEvalLanguages.clear();
    renderFilters();
    render();
  });
}

async function loadData() {
  try {
    setStatus("Loading per-test results...");
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(localPerTestDataHelp());
      }
      throw new Error(`HTTP ${response.status} while loading ${DATA_URL}`);
    }
    const data = await response.json();
    state.rows = Array.isArray(data.rows) ? data.rows : [];
    state.runs = Array.isArray(data.runs) ? data.runs : [];
    state.evalOptions = uniqueSorted(state.rows.map((row) => row.eval_language));
    state.pairOptions = uniqueSorted(state.rows.map((row) => row.pair));
    state.outcomeOptions = OUTCOME_ORDER.filter((outcome) =>
      state.rows.some((row) => normalizedOutcome(row.outcome) === outcome),
    );
    state.selectedEvalLanguages = new Set(state.evalOptions);
    state.selectedEvalVersions = getDefaultEvalVersionSelections();
    state.expandedVersionEvals = new Set();
    state.selectedPairs = new Set(state.pairOptions);
    state.selectedOutcomes = new Set(state.outcomeOptions);
    renderFilters();
    render();
    setStatus(
      `Loaded ${formatInteger(state.rows.length)} test results across ${formatInteger(
        state.runs.length,
      )} published runs.`,
    );
  } catch (error) {
    const message = error.message || String(error);
    showError(shouldAppendLocalPerTestHelp(message) ? `${message}\n\n${localPerTestDataHelp()}` : message);
    setStatus("Unable to load per-test results.");
  }
}

function shouldAppendLocalPerTestHelp(message) {
  const normalized = String(message || "").toLowerCase();
  return (
    !normalized.includes("clispecbench rebuild-dashboard") &&
    (normalized.includes(DATA_URL.toLowerCase()) ||
      normalized.includes("failed to fetch") ||
      normalized.includes("load failed") ||
      normalized.includes("networkerror"))
  );
}

function localPerTestDataHelp() {
  return [
    "Per-test data is local-only and is not included in the raw checkout or public static site.",
    "",
    "To use this explorer locally, generate the aggregate and launch the dashboard:",
    "  clispecbench rebuild-dashboard",
    "  python published_results/start-dashboard.py",
    "",
    `Expected local file: published_results/web/${DATA_URL}`,
  ].join("\n");
}

function renderFilters() {
  renderCheckboxList(elements.pairList, state.pairOptions, state.selectedPairs, {
    className: "pair-filter",
    label: (pair) => formatPairShortFromPair(pair),
    title: (pair) => formatPairFullFromPair(pair),
  });
  renderCheckboxList(elements.evalList, state.evalOptions, state.selectedEvalLanguages, {
    className: "eval-filter",
  });
  renderVersionFilters();
  renderCheckboxList(elements.outcomeList, state.outcomeOptions, state.selectedOutcomes, {
    className: "outcome-filter",
    label: (outcome) => OUTCOME_LABELS[outcome] || outcome,
  });
}

function renderVersionFilters() {
  elements.versionList.replaceChildren();
  getEvals().forEach((evalName) => {
    const item = document.createElement("div");
    item.className = "eval-filter-item";

    const main = document.createElement("div");
    main.className = "eval-filter-main";
    const title = createTextCell("span", evalName, "eval-version-title");
    const versions = getEvalVersions(evalName);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "version-toggle";
    toggle.dataset.action = "toggle-versions";
    toggle.dataset.eval = evalName;
    toggle.textContent = formatVersionSummary(evalName);
    toggle.title = `Choose ${evalName} versions`;
    toggle.setAttribute("aria-expanded", state.expandedVersionEvals.has(evalName) ? "true" : "false");
    toggle.disabled = versions.length <= 1;
    main.append(title, toggle);
    item.append(main);

    if (versions.length > 1) {
      const versionList = document.createElement("div");
      versionList.className = "version-list";
      if (!state.expandedVersionEvals.has(evalName)) {
        versionList.classList.add("hidden");
      }
      versions.forEach((version) => {
        const label = document.createElement("label");
        label.className = "version-option";
        const input = document.createElement("input");
        input.type = "checkbox";
        input.dataset.group = "eval-version";
        input.dataset.eval = evalName;
        input.value = version;
        input.checked = isEvalVersionSelected(evalName, version);
        label.append(input, document.createTextNode(formatVersionLabel(version)));
        versionList.append(label);
      });
      item.append(versionList);
    }

    elements.versionList.append(item);
  });
}

function renderCheckboxList(container, items, selectedSet, options = {}) {
  container.replaceChildren();
  items.forEach((item) => {
    const label = document.createElement("label");
    if (options.title) {
      label.title = options.title(item);
    }
    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = options.className || "";
    input.value = item;
    input.checked = selectedSet.has(item);
    const span = document.createElement("span");
    span.textContent = options.label ? options.label(item) : item;
    label.append(input, span);
    container.append(label);
  });
}

function updateSelectionFromCheckbox(event, selectedSet) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) || input.type !== "checkbox") {
    return;
  }
  if (input.checked) {
    selectedSet.add(input.value);
  } else {
    selectedSet.delete(input.value);
  }
  render();
}

function render() {
  renderViewMode();
  const filteredRows = getFilteredRows();
  if (state.viewMode === "matrix") {
    renderMatrix(filteredRows);
  } else {
    renderTable(filteredRows);
  }
  renderDetail();
}

function renderViewMode() {
  elements.viewMode.querySelectorAll("button[data-view-mode]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.viewMode === state.viewMode));
  });
  const matrixActive = state.viewMode === "matrix";
  elements.matrixPanel.classList.toggle("hidden", !matrixActive);
  elements.tablePanel.classList.toggle("hidden", matrixActive);
  document.querySelectorAll(".matrix-control").forEach((control) => {
    control.classList.toggle("hidden", !matrixActive);
  });
}

function getFilteredRows() {
  const query = state.searchText;
  return state.rows.filter((row) => {
    if (!state.selectedEvalLanguages.has(row.eval_language)) {
      return false;
    }
    if (!isRowVersionSelected(row)) {
      return false;
    }
    if (!state.selectedPairs.has(row.pair)) {
      return false;
    }
    if (!state.selectedOutcomes.has(normalizedOutcome(row.outcome))) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      row.test_id,
      row.test_file,
      row.test_name,
      row.message,
      row.eval_language,
      row.pair,
      row.outcome,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderMatrix(filteredRows) {
  const columns = getMatrixColumns();
  const rowGroups = getMatrixRowGroups(filteredRows, columns);
  const unsortedVisibleGroups = state.onlyDisagreements
    ? rowGroups.filter((group) => hasDisagreement(group.cells))
    : rowGroups;
  const visibleGroups = sortMatrixGroups(unsortedVisibleGroups);

  elements.matrixCount.textContent = `${formatInteger(visibleGroups.length)} tests, ${formatInteger(
    filteredRows.length,
  )} test results`;
  elements.matrixEmpty.classList.toggle("hidden", visibleGroups.length > 0);
  elements.testMatrixTable.classList.toggle("hidden", visibleGroups.length === 0);
  elements.testMatrixTable.replaceChildren();

  if (visibleGroups.length === 0) {
    return;
  }

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerRow.append(
    createMatrixHeader({
      key: "__scope__",
      label: state.rowMode === "eval" ? "Eval" : "Eval-Lang",
      title: state.rowMode === "eval" ? "Sort by eval" : "Sort by eval-language",
    }),
  );
  headerRow.append(createMatrixHeader({ key: "__test__", label: "Test", title: "Sort by test" }));
  columns.forEach((column) => {
    headerRow.append(createMatrixHeader(column));
  });
  thead.append(headerRow);

  const tbody = document.createElement("tbody");
  visibleGroups.forEach((group) => {
    const tr = document.createElement("tr");
    tr.append(createTextCell("td", group.scopeLabel, "table-muted nowrap"));
    const testCell = createTextCell("td", group.testId, "test-id-cell");
    testCell.title = group.testId;
    tr.append(testCell);
    group.cells.forEach((cell) => {
      tr.append(createMatrixCell(cell, group));
    });
    tbody.append(tr);
  });

  elements.testMatrixTable.append(thead, tbody);
}

function getMatrixColumns() {
  const allColumn = {
    key: MATRIX_ALL_COLUMN_KEY,
    label: "All",
    title: "All selected agent/model/effort results",
    isSummary: true,
  };

  if (state.columnMode === "run") {
    const runColumns = state.runs
      .filter(
        (run) =>
          state.selectedEvalLanguages.has(run.eval_language) &&
          state.selectedPairs.has(run.pair) &&
          isRunVersionSelected(run),
      )
      .map((run) => ({
        key: run.run_key,
        label: `${run.eval_language} ${formatPairShort(run)} #${run.run_id}`,
        title: `${run.eval_language} ${formatPairFull(run)} run ${run.run_id} (${formatVersionLabel(run.eval_version)})`,
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
    return [allColumn, ...runColumns];
  }

  const pairColumns = state.pairOptions
    .filter((pair) => state.selectedPairs.has(pair))
    .map((pair) => ({
      key: pair,
      label: formatPairShortFromPair(pair),
      title: formatPairFullFromPair(pair),
    }));
  return [allColumn, ...pairColumns];
}

function createMatrixHeader(column) {
  const th = document.createElement("th");
  th.title = column.title || column.label;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "table-sort-button matrix-sort-button";
  button.addEventListener("click", () => cycleMatrixSort(column.key));
  const label = document.createElement("span");
  label.textContent = column.label;
  const indicator = document.createElement("span");
  indicator.className = "sort-indicator";
  indicator.textContent = matrixSortIndicator(column.key);
  button.append(label, indicator);
  th.append(button);
  return th;
}

function getMatrixRowGroups(filteredRows, columns) {
  const groups = new Map();
  filteredRows.forEach((row) => {
    const scopeLabel = getMatrixScopeLabel(row);
    const key = `${scopeLabel}\u0000${row.test_id}`;
    if (!groups.has(key)) {
      groups.set(key, {
        scopeLabel,
        testId: row.test_id,
        rows: [],
      });
    }
    groups.get(key).rows.push(row);
  });

  return Array.from(groups.values())
    .sort((a, b) =>
      a.scopeLabel.localeCompare(b.scopeLabel) || a.testId.localeCompare(b.testId),
    )
    .map((group) => {
      const columnRows = new Map(columns.map((column) => [column.key, []]));
      group.rows.forEach((row) => {
        if (columnRows.has(MATRIX_ALL_COLUMN_KEY)) {
          columnRows.get(MATRIX_ALL_COLUMN_KEY).push(row);
        }
        const columnKey = state.columnMode === "run" ? row.run_key : row.pair;
        if (columnRows.has(columnKey)) {
          columnRows.get(columnKey).push(row);
        }
      });
      return {
        ...group,
        cells: columns.map((column) => ({
          column,
          rows: columnRows.get(column.key) || [],
          summary: summarizeCellRows(columnRows.get(column.key) || [], {
            forceRatio: column.isSummary,
          }),
        })),
      };
    });
}

function getMatrixScopeLabel(row) {
  return state.rowMode === "eval" ? row.eval : row.eval_language;
}

function summarizeCellRows(rows, options = {}) {
  if (rows.length === 0) {
    return {
      status: "empty",
      label: "",
      title: "No matching result",
      counts: {},
    };
  }

  const counts = {};
  rows.forEach((row) => {
    const outcome = normalizedOutcome(row.outcome);
    counts[outcome] = (counts[outcome] || 0) + 1;
  });
  const total = rows.length;
  const passed = counts.passed || 0;
  const failed = counts.failed || 0;
  const skipped = counts.skipped || 0;
  let status = "mixed";
  if (passed === total) {
    status = "passed";
  } else if (failed === total) {
    status = "failed";
  } else if (skipped === total) {
    status = "skipped";
  } else if (failed > 0) {
    status = "mixed";
  }

  const label =
    options.forceRatio || (state.columnMode === "pair" && total > 1)
      ? `${passed}/${total}`
      : OUTCOME_SHORT[status] || OUTCOME_SHORT[normalizedOutcome(rows[0].outcome)] || "?";
  const parts = OUTCOME_ORDER.filter((outcome) => counts[outcome]).map(
    (outcome) => `${counts[outcome]} ${OUTCOME_LABELS[outcome].toLowerCase()}`,
  );
  return {
    status,
    label,
    title: parts.join(", "),
    counts,
  };
}

function hasDisagreement(cells) {
  const statuses = cells
    .filter((cell) => !cell.column.isSummary)
    .map((cell) => cell.summary.status)
    .filter((status) => status !== "empty");
  if (statuses.includes("mixed")) {
    return true;
  }
  return new Set(statuses).size > 1;
}

function sortMatrixGroups(groups) {
  const sorted = [...groups];
  const key = state.matrixSortKey;
  if (!key) {
    return sorted;
  }
  const direction = state.matrixSortDirection === "desc" ? -1 : 1;
  return sorted.sort((a, b) => compareMatrixGroups(a, b, key, direction));
}

function compareMatrixGroups(a, b, key, direction) {
  let comparison = 0;
  if (key === "__scope__") {
    comparison = a.scopeLabel.localeCompare(b.scopeLabel);
  } else if (key === "__test__") {
    comparison = a.testId.localeCompare(b.testId);
  } else {
    comparison = compareMatrixCells(getMatrixCell(a, key), getMatrixCell(b, key), direction);
  }

  if (comparison !== 0) {
    return comparison * direction;
  }
  return a.scopeLabel.localeCompare(b.scopeLabel) || a.testId.localeCompare(b.testId);
}

function getMatrixCell(group, key) {
  return group.cells.find((cell) => cell.column.key === key);
}

function compareMatrixCells(a, b, direction) {
  const aRows = a?.rows.length || 0;
  const bRows = b?.rows.length || 0;
  if (aRows === 0 && bRows === 0) {
    return 0;
  }
  if (aRows === 0) {
    return direction;
  }
  if (bRows === 0) {
    return -direction;
  }

  const aScore = matrixCellScore(a);
  const bScore = matrixCellScore(b);
  if (aScore !== bScore) {
    return aScore - bScore;
  }
  return aRows - bRows;
}

function matrixCellScore(cell) {
  const total = cell.rows.length;
  if (total === 0) {
    return Number.NaN;
  }
  return (cell.summary.counts.passed || 0) / total;
}

function cycleMatrixSort(key) {
  if (state.matrixSortKey !== key) {
    state.matrixSortKey = key;
    state.matrixSortDirection = "asc";
  } else if (state.matrixSortDirection === "asc") {
    state.matrixSortDirection = "desc";
  } else {
    state.matrixSortKey = "";
    state.matrixSortDirection = "asc";
  }
  renderMatrix(getFilteredRows());
}

function matrixSortIndicator(key) {
  if (state.matrixSortKey !== key) {
    return "";
  }
  return state.matrixSortDirection === "asc" ? "asc" : "desc";
}

function createMatrixCell(cell, group) {
  const classes = ["matrix-cell", cell.summary.status];
  if (cell.column.isSummary) {
    classes.push("summary-cell");
  }
  const td = createTextCell("td", cell.summary.label, classes.join(" "));
  td.title = cell.summary.title;
  if (cell.rows.length > 0) {
    td.tabIndex = 0;
    td.setAttribute("role", "button");
    td.addEventListener("click", () => {
      state.detailRows = cell.rows;
      state.detailTitle = `${group.scopeLabel} ${group.testId} - ${cell.column.title}`;
      renderDetail();
    });
    td.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        td.click();
      }
    });
  }
  return td;
}

function renderTable(filteredRows) {
  const rows = sortRows(filteredRows);
  elements.tableCount.textContent = `${formatInteger(rows.length)} test results`;
  elements.tableEmpty.classList.toggle("hidden", rows.length > 0);
  elements.testResultsTable.classList.toggle("hidden", rows.length === 0);
  elements.testResultsTable.replaceChildren();

  if (rows.length === 0) {
    return;
  }

  const columns = getTableColumns();
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    if (column.numeric) {
      th.classList.add("numeric");
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "table-sort-button";
    button.addEventListener("click", () => cycleSort(column.key));
    const label = document.createElement("span");
    label.textContent = column.label;
    const indicator = document.createElement("span");
    indicator.className = "sort-indicator";
    indicator.textContent = sortIndicator(column.key);
    button.append(label, indicator);
    th.append(button);
    headerRow.append(th);
  });
  thead.append(headerRow);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.addEventListener("click", () => {
      state.detailRows = [row];
      state.detailTitle = `${row.eval_language} ${row.test_id} - ${formatPairFull(row)} run ${row.run_id}`;
      renderDetail();
    });
    columns.forEach((column) => {
      const td = document.createElement("td");
      if (column.numeric) {
        td.classList.add("numeric");
      }
      if (column.className) {
        td.classList.add(column.className);
      }
      column.render(td, row);
      tr.append(td);
    });
    tbody.append(tr);
  });

  elements.testResultsTable.append(thead, tbody);
}

function getTableColumns() {
  return [
    {
      key: "eval_language",
      label: "Eval-Lang",
      render: (td, row) => {
        td.textContent = row.eval_language;
      },
    },
    {
      key: "pair",
      label: "Agent/Model/Effort",
      render: (td, row) => {
        td.textContent = formatPairShort(row);
        td.title = formatPairFull(row);
      },
    },
    {
      key: "run_id",
      label: "Run",
      render: (td, row) => {
        td.textContent = row.run_id;
      },
    },
    {
      key: "eval_version",
      label: "Version",
      render: (td, row) => {
        td.textContent = formatVersionLabel(row.eval_version);
      },
    },
    {
      key: "outcome",
      label: "Outcome",
      render: (td, row) => {
        const pill = document.createElement("span");
        const outcome = normalizedOutcome(row.outcome);
        pill.className = `outcome-pill ${outcome}`;
        pill.textContent = OUTCOME_LABELS[outcome] || row.outcome || "Unknown";
        td.append(pill);
      },
    },
    {
      key: "duration_seconds",
      label: "Duration",
      numeric: true,
      render: (td, row) => {
        td.textContent = formatDuration(row.duration_seconds);
      },
    },
    {
      key: "test_id",
      label: "Test",
      className: "test-id-cell",
      render: (td, row) => {
        td.textContent = row.test_id;
        td.title = row.test_id;
      },
    },
    {
      key: "message",
      label: "Message",
      className: "test-message",
      render: (td, row) => {
        td.textContent = formatMessageSummary(row.message);
        if (row.message) {
          td.title = row.message;
        }
      },
    },
    {
      key: "result_link",
      label: "Result",
      render: (td, row) => {
        const link = document.createElement("a");
        link.className = "table-link";
        link.href = row.result_link;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = "JSON";
        link.addEventListener("click", (event) => event.stopPropagation());
        td.append(link);
      },
    },
  ];
}

function sortRows(rows) {
  const sorted = [...rows];
  const key = state.tableSortKey;
  if (!key) {
    return sorted.sort(
      (a, b) =>
        a.eval_language.localeCompare(b.eval_language) ||
        a.test_id.localeCompare(b.test_id) ||
        a.pair.localeCompare(b.pair) ||
        String(a.run_id).localeCompare(String(b.run_id), undefined, { numeric: true }),
    );
  }
  const direction = state.tableSortDirection === "desc" ? -1 : 1;
  return sorted.sort((a, b) => compareTableValues(a, b, key) * direction);
}

function compareTableValues(a, b, key) {
  if (key === "duration_seconds") {
    return numericValue(a.duration_seconds) - numericValue(b.duration_seconds);
  }
  if (key === "run_id") {
    return String(a.run_id).localeCompare(String(b.run_id), undefined, { numeric: true });
  }
  return String(a[key] || "").localeCompare(String(b[key] || ""), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function cycleSort(key) {
  if (state.tableSortKey !== key) {
    state.tableSortKey = key;
    state.tableSortDirection = "asc";
  } else if (state.tableSortDirection === "asc") {
    state.tableSortDirection = "desc";
  } else {
    state.tableSortKey = "";
    state.tableSortDirection = "asc";
  }
  renderTable(getFilteredRows());
}

function sortIndicator(key) {
  if (state.tableSortKey !== key) {
    return "";
  }
  return state.tableSortDirection === "asc" ? "asc" : "desc";
}

function renderDetail() {
  elements.detailPanel.replaceChildren();
  elements.detailPanel.append(createTextCell("h2", "Test Detail"));
  if (state.detailRows.length === 0) {
    elements.detailPanel.append(
      createTextCell("p", "Select a matrix cell or table row to inspect the exact result message.", "hint"),
    );
    return;
  }

  elements.detailPanel.append(createTextCell("p", state.detailTitle, "detail-title"));
  const summary = document.createElement("div");
  summary.className = "detail-grid";
  const counts = summarizeCellRows(state.detailRows).counts;
  addDetailItem(summary, "Rows", formatInteger(state.detailRows.length));
  OUTCOME_ORDER.forEach((outcome) => {
    if (counts[outcome]) {
      addDetailItem(summary, OUTCOME_LABELS[outcome], formatInteger(counts[outcome]));
    }
  });
  elements.detailPanel.append(summary);

  const list = document.createElement("div");
  list.className = "test-detail-list";
  state.detailRows.forEach((row) => {
    const item = document.createElement("section");
    item.className = "test-detail-item";
    const heading = createTextCell(
      "h3",
      `${row.eval_language} ${formatPairFull(row)} run ${row.run_id} - ${
        OUTCOME_LABELS[normalizedOutcome(row.outcome)] || row.outcome
      }`,
    );
    item.append(heading);
    const meta = createTextCell("p", `${row.test_id} | ${formatDuration(row.duration_seconds)}`, "hint");
    item.append(meta);
    if (row.message) {
      const pre = document.createElement("pre");
      pre.className = "detail-message";
      pre.textContent = row.message;
      item.append(pre);
    } else {
      item.append(createTextCell("p", "No message reported.", "hint"));
    }
    const link = document.createElement("a");
    link.className = "table-link";
    link.href = row.result_link;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "Open run JSON";
    item.append(link);
    list.append(item);
  });
  elements.detailPanel.append(list);
}

function addDetailItem(container, label, value) {
  const item = document.createElement("div");
  const labelEl = createTextCell("span", label, "detail-label");
  const valueEl = createTextCell("strong", value);
  item.append(labelEl, valueEl);
  container.append(item);
}

function createTextCell(tagName, text, className = "") {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  element.textContent = text;
  return element;
}

function normalizedOutcome(outcome) {
  const value = String(outcome || "unknown").toLowerCase();
  return OUTCOME_LABELS[value] ? value : "unknown";
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function versionKey(version) {
  return String(version ?? "");
}

function formatVersionLabel(version) {
  return versionKey(version) || "n/a";
}

function parseVersionParts(version) {
  return versionKey(version)
    .split(/[^0-9]+/)
    .filter(Boolean)
    .map((part) => Number(part));
}

function compareVersions(a, b) {
  const aParts = parseVersionParts(a);
  const bParts = parseVersionParts(b);
  const maxLength = Math.max(aParts.length, bParts.length);
  for (let index = 0; index < maxLength; index += 1) {
    const diff = (aParts[index] || 0) - (bParts[index] || 0);
    if (diff) {
      return diff;
    }
  }
  return versionKey(a).localeCompare(versionKey(b), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function versionMajorKey(version) {
  const parts = parseVersionParts(version);
  if (parts.length) {
    return String(parts[0]);
  }
  return versionKey(version) || "__unversioned__";
}

function getEvals() {
  return uniqueSorted(state.rows.map((row) => row.eval));
}

function getEvalVersions(evalName) {
  const versionSet = new Set();
  state.rows.forEach((row) => {
    if (row.eval === evalName) {
      versionSet.add(versionKey(row.eval_version));
    }
  });
  return Array.from(versionSet).sort((a, b) => compareVersions(b, a));
}

function getDefaultEvalVersionSelections() {
  const selections = new Map();
  getEvals().forEach((evalName) => {
    const versions = getEvalVersions(evalName);
    if (!versions.length) {
      selections.set(evalName, new Set());
      return;
    }
    const newestMajor = versionMajorKey(versions[0]);
    selections.set(
      evalName,
      new Set(versions.filter((version) => versionMajorKey(version) === newestMajor)),
    );
  });
  return selections;
}

function isEvalVersionSelected(evalName, version) {
  const selectedVersions = state.selectedEvalVersions.get(evalName);
  return Boolean(selectedVersions && selectedVersions.has(versionKey(version)));
}

function isRowVersionSelected(row) {
  return isEvalVersionSelected(row.eval, row.eval_version);
}

function isRunVersionSelected(run) {
  return isEvalVersionSelected(run.eval, run.eval_version);
}

function formatVersionSummary(evalName) {
  const versions = getEvalVersions(evalName);
  if (versions.length <= 1) {
    return `Version: ${formatVersionLabel(versions[0])}`;
  }
  const selectedVersions = versions.filter((version) => isEvalVersionSelected(evalName, version));
  if (!selectedVersions.length) {
    return "Versions: none";
  }
  if (selectedVersions.length === versions.length) {
    return "Versions: all";
  }
  const selectedMajors = new Set(selectedVersions.map(versionMajorKey));
  const selectedMajor = Array.from(selectedMajors)[0];
  const allMajorVersionsSelected =
    selectedMajors.size === 1 &&
    versions
      .filter((version) => versionMajorKey(version) === selectedMajor)
      .every((version) => selectedVersions.includes(version));
  if (allMajorVersionsSelected) {
    return `Versions: ${selectedMajor}.x`;
  }
  return `Versions: ${selectedVersions.map(formatVersionLabel).join(", ")}`;
}

function formatPairShort(row) {
  return `${formatAgentShort(row.agent)} / ${formatModelShort(modelWithEffort(row.model, row.effort))}`;
}

function formatPairShortFromPair(pair) {
  const { agent, model } = splitPair(pair);
  return `${formatAgentShort(agent)} / ${formatModelShort(model)}`;
}

function formatPairFull(row) {
  return `${formatAgentFull(row.agent)} / ${formatModelFull(modelWithEffort(row.model, row.effort))}`;
}

function formatPairFullFromPair(pair) {
  const { agent, model } = splitPair(pair);
  return `${formatAgentFull(agent)} / ${formatModelFull(model)}`;
}

function splitPair(pair) {
  const parts = String(pair || "").split(" / ");
  const agent = parts.shift() || "";
  const model = parts.join(" / ");
  return { agent, model };
}

function modelWithEffort(model, effort) {
  const level = String(effort || "").trim();
  return level ? `${model} (${level})` : String(model || "");
}

function formatAgentShort(agent) {
  return AGENT_SHORT_NAMES[agent] || titleCaseIdentifier(agent);
}

function formatAgentFull(agent) {
  return AGENT_FULL_NAMES[agent] || titleCaseIdentifier(agent);
}

function formatModelShort(model) {
  const { baseModel, effort } = splitModelEffortLabel(model);
  const normalized = baseModel.toLowerCase();
  const withEffort = (label) => (effort ? `${label} (${abbreviateEffort(effort)})` : label);
  const gptMatch = normalized.match(/^gpt-(\d+(?:\.\d+)?)(?:-(mini|codex))?/);
  if (gptMatch) {
    const suffix = gptMatch[2] === "mini" ? "-m" : gptMatch[2] === "codex" ? "-c" : "";
    return withEffort(`${gptMatch[1]}${suffix}`);
  }
  return withEffort(MODEL_SHORT_NAMES[baseModel] || baseModel.toUpperCase());
}

function formatModelFull(model) {
  const { baseModel, effort } = splitModelEffortLabel(model);
  const normalized = baseModel.toLowerCase();
  const withEffort = (label) => (effort ? `${label} (${effort})` : label);
  const gptMatch = normalized.match(/^gpt-(\d+(?:\.\d+)?)(?:-(mini|codex))?/);
  if (gptMatch) {
    const suffix = gptMatch[2] === "mini" ? " Mini" : gptMatch[2] === "codex" ? " Codex" : "";
    return withEffort(`GPT-${gptMatch[1]}${suffix}`);
  }
  return withEffort(MODEL_FULL_NAMES[baseModel] || titleCaseIdentifier(baseModel));
}

function splitModelEffortLabel(model) {
  const value = String(model || "").trim();
  const match = value.match(/^(.*)\s+\(([^()]+)\)$/);
  if (!match) return { baseModel: value, effort: "" };
  return { baseModel: match[1], effort: match[2] };
}

function abbreviateEffort(effort) {
  const normalized = String(effort || "").toLowerCase();
  const labels = {
    low: "low",
    medium: "med",
    high: "high",
    max: "max",
    xhigh: "xhigh",
  };
  return labels[normalized] || effort;
}

function titleCaseIdentifier(value) {
  return String(value || "")
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatDuration(value) {
  const number = numericValue(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  if (number < 1) {
    return `${(number * 1000).toFixed(0)} ms`;
  }
  return `${number.toFixed(number < 10 ? 2 : 1)} s`;
}

function formatInteger(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function formatMessageSummary(message) {
  if (!message) {
    return "-";
  }
  return String(message).replace(/\s+/g, " ").trim();
}

function numericValue(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number.NaN;
}

function setStatus(message) {
  elements.status.textContent = message;
}

function showError(message) {
  elements.errorBanner.textContent = message;
  elements.errorBanner.classList.remove("hidden");
}

function toCamelCase(id) {
  return id.replace(/-([a-z])/g, (_, char) => char.toUpperCase());
}
