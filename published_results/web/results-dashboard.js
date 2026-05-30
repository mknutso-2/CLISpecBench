const DATA_PATH = 'results-published.json';
const PER_TEST_DATA_PATH = 'test-results-published.json';

const AXIS_OPTIONS = [
  { id: 'percent', label: 'Pass rate' },
  { id: 'tokens_input', label: 'Tokens Input' },
  { id: 'tokens_output', label: 'Tokens Output' },
  { id: 'tokens_total', label: 'Tokens Total' },
  { id: 'cost', label: 'Cost (USD)' },
  { id: 'wall', label: 'Wall Clock Time' },
  { id: 'tools', label: 'Tools Used' },
  { id: 'loc', label: 'LOC' },
  { id: 'language', label: 'Language', axisOnly: true, selectionLabel: 'languages' },
  { id: 'eval', label: 'Eval', axisOnly: true, selectionLabel: 'evals' },
];

const COLOR_MODE_OPTIONS = [
  { id: 'pair', label: 'Agent / Model / Effort' },
  { id: 'language', label: 'Language' },
  { id: 'agent', label: 'Agent' },
];

const LABEL_MODE_OPTIONS = [
  { id: 'all', label: 'All' },
  { id: 'none', label: 'None' },
  { id: 'pareto', label: 'Pareto' },
];

const NAME_MODE_OPTIONS = [
  { id: 'short', label: 'Abbreviations' },
  { id: 'full', label: 'Full names' },
];

const REPORT_TYPE_OPTIONS = [
  { id: 'worst', label: 'Worst' },
  { id: 'best', label: 'Best' },
  { id: 'median', label: 'Median' },
  { id: 'mean', label: 'Mean' },
];

const ERROR_BAR_OPTIONS = [
  { id: 'range', label: 'Range' },
  { id: 'std', label: 'Std Dev.' },
  { id: 'none', label: 'None' },
];

const TABLE_SORT_OPTIONS = {
  summary: [
    { id: '', label: 'No ordering' },
    { id: 'pair', label: 'Agent/model/effort' },
    { id: 'eval_language', label: 'Eval-Lang' },
    { id: 'runs', label: 'Runs' },
    { id: 'percent', label: 'Pass rate' },
    { id: 'cost', label: 'Cost' },
    { id: 'wall', label: 'Wall time' },
    { id: 'tokens', label: 'Tokens' },
    { id: 'tools', label: 'Tools' },
    { id: 'loc', label: 'LOC' },
  ],
  runs: [
    { id: '', label: 'No ordering' },
    { id: 'eval_language', label: 'Eval-Lang' },
    { id: 'pair', label: 'Agent/model/effort' },
    { id: 'run', label: 'Run' },
    { id: 'version', label: 'Version' },
    { id: 'status', label: 'Agent stop' },
    { id: 'percent', label: 'Pass rate' },
    { id: 'cost', label: 'Cost' },
    { id: 'wall', label: 'Wall time' },
    { id: 'tokens', label: 'Tokens' },
    { id: 'tools', label: 'Tools' },
    { id: 'files', label: 'Files' },
    { id: 'loc', label: 'LOC' },
    { id: 'last_message', label: 'Last Message' },
  ],
};

const METRICS = {
  percent: {
    label: 'Pass rate',
    parse: (row) => row.score_pct,
    formatMean: (value) => `${value.toFixed(1)}%`,
    formatSummary: (s) => `${s.mean.toFixed(1)}% (min ${s.min.toFixed(1)}%, max ${s.max.toFixed(1)}%)`,
    isPercent: true,
    forceMin: 0,
    forceMax: 100,
    minClamp: 0,
    higherIsBetter: true,
  },
  tokens_input: {
    label: 'Tokens Input',
    parse: (row) => row.input_tokens,
    formatMean: (value) => formatTokenCount(value),
    formatSummary: (s) =>
      `${formatTokenCount(s.mean)} (min ${formatTokenCount(s.min)}, max ${formatTokenCount(s.max)})`,
    minClamp: 0,
  },
  tokens_output: {
    label: 'Tokens Output',
    parse: (row) => row.output_tokens,
    formatMean: (value) => formatTokenCount(value),
    formatSummary: (s) =>
      `${formatTokenCount(s.mean)} (min ${formatTokenCount(s.min)}, max ${formatTokenCount(s.max)})`,
    minClamp: 0,
  },
  tokens_total: {
    label: 'Tokens Total',
    parse: (row) => row.input_tokens + row.output_tokens,
    parseInput: (row) => row.input_tokens,
    parseOutput: (row) => row.output_tokens,
    formatMean: (value) => formatTokenCount(value),
    formatSummary: (s) =>
      `${formatTokenCount(s.mean)} total (input ${formatTokenCount(s.meanInput)} + output ${formatTokenCount(s.meanOutput)})`,
    stacked: true,
    minClamp: 0,
  },
  cost: {
    label: 'Cost (USD)',
    parse: (row) => row.cost_usd,
    formatMean: (value) => formatMoney(value),
    formatSummary: (s) => `${formatMoney(s.mean)} (min ${formatMoney(s.min)}, max ${formatMoney(s.max)})`,
    minClamp: 0,
    minTickStep: 0.01,
  },
  wall: {
    label: 'Wall Clock Time',
    parse: (row) => row.wall_min,
    formatMean: (value) => formatWallTime(value),
    formatSummary: (s) => `${formatWallTime(s.mean)} (min ${formatWallTime(s.min)}, max ${formatWallTime(s.max)})`,
    minClamp: 0,
    minTickStep: 0.1,
  },
  tools: {
    label: 'Tools Used',
    parse: (row) => row.tools,
    formatMean: (value) => formatCount(value),
    formatSummary: (s) => `${formatCount(s.mean)} (min ${formatCount(s.min)}, max ${formatCount(s.max)})`,
    minClamp: 0,
  },
  loc: {
    label: 'LOC',
    parse: (row) => row.loc,
    formatMean: (value) => formatLocCount(value),
    formatSummary: (s) => `${formatLocCount(s.mean)} (min ${formatLocCount(s.min)}, max ${formatLocCount(s.max)})`,
    minClamp: 0,
  },
  files: {
    label: 'Files',
    parse: (row) => row.files,
    formatMean: (value) => formatCount(value),
    formatSummary: (s) => `${formatCount(s.mean)} (min ${formatCount(s.min)}, max ${formatCount(s.max)})`,
    minClamp: 0,
  },
};

const EVAL_COMBINED_METRIC_MODES = {
  percent: 'average',
  cost: 'sum',
  wall: 'sum',
};

const DETAIL_METRIC_IDS = [
  'percent',
  'tools',
  'tokens_input',
  'tokens_output',
  'tokens_total',
  'cost',
  'wall',
  'loc',
  'files',
];

const AXIS_PADDING = {
  left: 16,
  right: 16,
  top: 12,
  bottom: 12,
};
const CATEGORY_AXIS_X_PADDING = 24;
const AXIS_TICK_SEGMENTS = 5;
const AXIS_DOMAIN_PADDING_FRACTION = 0.06;
const AXIS_DOMAIN_MIN_PADDING = 0.5;
const POINT_LABEL_WRAP_LENGTH = 34;
const LABEL_LINE_CLEARANCE = 7;
const LEADER_ERROR_BAR_PENALTY = 240;
const LABEL_LEADER_PENALTY = 700;
const LEADER_LABEL_PENALTY = 900;
const LEADER_CROSSING_PENALTY = 180;

const PALETTE = [
  '#4c6ef5',
  '#22a06b',
  '#e76f51',
  '#7c3aed',
  '#0ea5e9',
  '#f97316',
  '#db2777',
  '#0891b2',
];

const LAST_MESSAGE_CACHE = new Map();

const STATE = {
  rows: [],
  selectedPairs: new Set(),
  selectedLanguages: new Set(),
  selectedEvals: new Set(),
  selectedEvalVersions: new Map(),
  expandedVersionEvals: new Set(),
  viewMode: 'graph',
  xAxis: 'cost',
  yAxis: 'percent',
  colorMode: 'pair',
  labelMode: 'all',
  nameMode: 'short',
  reportType: 'mean',
  errorBarMode: 'std',
  tableMode: 'summary',
  tableGroupBy: 'pair',
  tableSortBy: '',
  tableSortDirection: 'asc',
  controlsCollapsed: false,
  hiddenColorKeys: new Set(),
};

const dashboardLayout = document.getElementById('dashboard-layout');
const controlsToggleButton = document.getElementById('controls-toggle');
const viewModeEl = document.getElementById('view-mode');
const pairListEl = document.getElementById('pair-list');
const pairUnavailableHintEl = document.getElementById('pair-unavailable-hint');
const pairSelectAllButton = document.getElementById('pair-select-all');
const pairUnselectAllButton = document.getElementById('pair-unselect-all');
const languageListEl = document.getElementById('language-list');
const evalListEl = document.getElementById('eval-list');
const evalSelectAllButton = document.getElementById('eval-select-all');
const evalClearButton = document.getElementById('eval-clear');
const xAxisSelect = document.getElementById('x-axis');
const yAxisSelect = document.getElementById('y-axis');
const reportTypeSelect = document.getElementById('report-type');
const errorBarsSelect = document.getElementById('error-bars');
const colorModeSelect = document.getElementById('color-mode');
const labelModeSelect = document.getElementById('label-mode');
const nameModeSelect = document.getElementById('name-mode');
const tableModeSelect = document.getElementById('table-mode');
const tableGroupBySelect = document.getElementById('table-group-by');
const tableSortBySelect = document.getElementById('table-sort-by');
const tableSortDirectionSelect = document.getElementById('table-sort-direction');
const graphControls = Array.from(document.querySelectorAll('.graph-control'));
const tableControls = Array.from(document.querySelectorAll('.table-control'));
const tableSummaryControls = Array.from(document.querySelectorAll('.table-summary-control'));
const tableRunsControls = Array.from(document.querySelectorAll('.table-runs-control'));
const validationEl = document.getElementById('validation-message');
const statusEl = document.getElementById('status');
const errorBanner = document.getElementById('error-banner');
const chartSvg = document.getElementById('scatter-svg');
const chartEmpty = document.getElementById('chart-empty');
const graphTitleEl = document.getElementById('graph-title');
const graphPanel = document.getElementById('graph-panel');
const tablePanel = document.getElementById('table-panel');
const tableTitleEl = document.getElementById('table-title');
const tableEl = document.getElementById('results-table');
const tableEmpty = document.getElementById('table-empty');
const tableCountEl = document.getElementById('table-count');
const legendEl = document.getElementById('legend');
const tooltip = document.getElementById('tooltip');

document.addEventListener('DOMContentLoaded', () => {
  if (
    !viewModeEl ||
    !dashboardLayout ||
    !controlsToggleButton ||
    !pairListEl ||
    !pairSelectAllButton ||
    !pairUnselectAllButton ||
    !languageListEl ||
    !evalListEl ||
    !evalSelectAllButton ||
    !evalClearButton ||
    !xAxisSelect ||
    !yAxisSelect ||
    !reportTypeSelect ||
    !errorBarsSelect ||
    !colorModeSelect ||
    !labelModeSelect ||
    !nameModeSelect ||
    !tableModeSelect ||
    !tableGroupBySelect ||
    !tableSortBySelect ||
    !tableSortDirectionSelect ||
    !graphTitleEl ||
    !graphPanel ||
    !tablePanel ||
    !tableTitleEl ||
    !tableEl ||
    !tableEmpty ||
    !tableCountEl
  ) {
    console.error('Dashboard initialization failed: expected UI elements are missing.');
    return;
  }

  attachEvents();

  (async () => {
    try {
      const dataset = await loadRows();
      initializeDashboard(dataset, DATA_PATH);
    } catch (error) {
      const message =
        window.location.protocol === 'file:'
          ? `Unable to load ${DATA_PATH} from file://. Serve this page from a local server (for example: python -m http.server 8000 from published_results/web).`
          : `Unable to load ${DATA_PATH}: ${error.message}. Open this page through a local web server and refresh (for example: python -m http.server 8000 from published_results/web).`;
      setError(message);
      return;
    }
  })();
});

function initializeDashboard(data, sourceName, { preserveView = false } = {}) {
  const dataset = normalizeDataset(data);
  if (!dataset.rows.length) {
    throw new Error('No result rows were found in the data source.');
  }
  STATE.rows = dataset.rows;
  LAST_MESSAGE_CACHE.clear();
  initSelectionDefaults({ preserveView });
  buildControls();
  render();
  statusEl.textContent = `Loaded ${STATE.rows.length} official runs from ${sourceName || DATA_PATH}.`;
  clearError();
}

function initSelectionDefaults({ preserveView = false } = {}) {
  const previousView = preserveView
    ? {
        xAxis: STATE.xAxis,
        yAxis: STATE.yAxis,
        colorMode: STATE.colorMode,
        labelMode: STATE.labelMode,
        nameMode: STATE.nameMode,
        reportType: STATE.reportType,
        errorBarMode: STATE.errorBarMode,
        selectedEvals: new Set(STATE.selectedEvals),
        selectedEvalVersions: cloneVersionSelection(STATE.selectedEvalVersions),
        expandedVersionEvals: new Set(STATE.expandedVersionEvals),
        viewMode: STATE.viewMode,
        tableMode: STATE.tableMode,
        tableGroupBy: STATE.tableGroupBy,
        tableSortBy: STATE.tableSortBy,
        tableSortDirection: STATE.tableSortDirection,
        controlsCollapsed: STATE.controlsCollapsed,
      }
    : null;

  STATE.selectedPairs = new Set();
  STATE.selectedLanguages = new Set();
  STATE.selectedEvals = new Set();
  STATE.selectedEvalVersions = getDefaultEvalVersionSelections();
  STATE.expandedVersionEvals = new Set();
  STATE.hiddenColorKeys = new Set();
  const pairs = getPairs();
  const languages = getLanguages();
  const evals = getEvals();

  if (!pairs.length || !languages.length || !evals.length) {
    throw new Error(
      'The data source loaded but did not contain expected pair/language/eval rows for the controls.',
    );
  }

  const defaultSelectedEvals = getDefaultSelectedEvals(evals);
  const defaultSelectedLanguages = languages;
  getDefaultSelectedPairs(pairs, defaultSelectedEvals, defaultSelectedLanguages).forEach((id) =>
    STATE.selectedPairs.add(id),
  );
  defaultSelectedLanguages.forEach((lang) => STATE.selectedLanguages.add(lang));
  defaultSelectedEvals.forEach((evalName) => STATE.selectedEvals.add(evalName));
  STATE.pairEligibilitySyncKey = getEvalLanguageSelectionKey(
    defaultSelectedEvals,
    defaultSelectedLanguages,
  );

  if (previousView) {
    const preservedEvals = evals.filter((evalName) => previousView.selectedEvals.has(evalName));
    STATE.selectedEvals = new Set(
      preservedEvals.length ? preservedEvals : getDefaultSelectedEvals(evals),
    );
    STATE.selectedEvalVersions = mergeVersionSelectionWithDefaults(previousView.selectedEvalVersions);
    STATE.expandedVersionEvals = new Set(
      Array.from(previousView.expandedVersionEvals).filter((evalName) => evals.includes(evalName)),
    );
    STATE.xAxis = previousView.xAxis;
    STATE.yAxis = previousView.yAxis;
    STATE.colorMode = previousView.colorMode;
    STATE.labelMode = previousView.labelMode;
    STATE.nameMode = previousView.nameMode;
    STATE.reportType = previousView.reportType;
    STATE.errorBarMode = previousView.errorBarMode;
    STATE.viewMode = previousView.viewMode;
    STATE.tableMode = previousView.tableMode;
    STATE.tableGroupBy = previousView.tableGroupBy;
    STATE.tableSortBy = previousView.tableSortBy;
    STATE.tableSortDirection = previousView.tableSortDirection;
    STATE.controlsCollapsed = previousView.controlsCollapsed;
  } else {
    STATE.viewMode = 'graph';
    STATE.xAxis = 'cost';
    STATE.yAxis = 'percent';
    STATE.colorMode = 'agent';
    STATE.labelMode = 'all';
    STATE.nameMode = 'short';
    STATE.reportType = 'mean';
    STATE.errorBarMode = getDefaultErrorBarMode();
    STATE.tableMode = 'summary';
    STATE.tableGroupBy = 'pair';
    STATE.tableSortBy = '';
    STATE.tableSortDirection = 'asc';
    STATE.controlsCollapsed = false;
  }
}

function getDefaultSelectedEvals(evals) {
  return evals.includes('RS274') ? ['RS274'] : evals;
}

function getDefaultSelectedPairs(pairs, selectedEvals, selectedLanguages) {
  return getEligiblePairsForEvalLanguages(pairs, selectedEvals, selectedLanguages);
}

function getEligiblePairsForEvalLanguages(pairs, selectedEvals, selectedLanguages) {
  if (!selectedEvals.length || !selectedLanguages.length) return [];

  const requiredCount = 3;
  const selectedEvalSet = new Set(selectedEvals);
  const selectedLanguageSet = new Set(selectedLanguages);
  const countsByPairEvalLanguage = new Map();
  STATE.rows.forEach((row) => {
    if (!selectedEvalSet.has(row.eval) || !selectedLanguageSet.has(row.language)) return;
    if (!isRowVersionSelected(row)) return;
    const pairId = rowPairId(row);
    const key = getPairEvalLanguageKey(pairId, row.eval, row.language);
    countsByPairEvalLanguage.set(key, (countsByPairEvalLanguage.get(key) || 0) + 1);
  });

  return pairs.filter((pairId) =>
    selectedEvals.every((evalName) =>
      selectedLanguages.every(
        (language) =>
          (countsByPairEvalLanguage.get(getPairEvalLanguageKey(pairId, evalName, language)) || 0) >=
          requiredCount,
      ),
    ),
  );
}

function syncSelectedPairsForCurrentEvalLanguages() {
  const selectedEvals = getSelectedEvalNames();
  const selectedLanguages = getLanguages().filter((language) => STATE.selectedLanguages.has(language));
  const nextKey = getEvalLanguageSelectionKey(selectedEvals, selectedLanguages);
  if (STATE.pairEligibilitySyncKey === nextKey) return false;

  const nextSelectedPairs = new Set(
    getEligiblePairsForEvalLanguages(getPairs(), selectedEvals, selectedLanguages),
  );
  const changed = !setsHaveSameMembers(STATE.selectedPairs, nextSelectedPairs);
  STATE.selectedPairs = nextSelectedPairs;
  STATE.pairEligibilitySyncKey = nextKey;
  return changed;
}

function getEvalLanguageSelectionKey(selectedEvals, selectedLanguages) {
  return JSON.stringify({
    evals: [...selectedEvals].sort(),
    languages: [...selectedLanguages].sort(),
    versions: getSelectedEvalVersionsByEval(selectedEvals),
  });
}

function getSelectedEvalVersionsByEval(selectedEvals) {
  const versionsByEval = {};
  [...selectedEvals].sort().forEach((evalName) => {
    versionsByEval[evalName] = Array.from(STATE.selectedEvalVersions.get(evalName) || []).sort();
  });
  return versionsByEval;
}

function getPairEvalLanguageKey(pairId, evalName, language) {
  return JSON.stringify([pairId, evalName, language]);
}

function setsHaveSameMembers(left, right) {
  if (left.size !== right.size) return false;
  for (const item of left) {
    if (!right.has(item)) return false;
  }
  return true;
}

function buildControls() {
  renderPairList();
  renderLanguageList();
  renderEvalList();
  renderColorModeSelector();
  renderLabelModeSelector();
  renderNameModeSelector();
  renderReportTypeSelector();
  renderErrorBarSelector();
  renderTableControls();
  updateAxisSelectors();
  syncViewModeControls();
  syncControlsColumn();
}

function attachEvents() {
  controlsToggleButton.addEventListener('click', () => {
    STATE.controlsCollapsed = !STATE.controlsCollapsed;
    syncControlsColumn();
    if (STATE.rows.length) {
      window.requestAnimationFrame(() => render());
    }
  });

  viewModeEl.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-view-mode]');
    if (!button) return;
    STATE.viewMode = button.dataset.viewMode === 'table' ? 'table' : 'graph';
    syncViewModeControls();
    render();
  });

  if (pairSelectAllButton) {
    pairSelectAllButton.addEventListener('click', () => {
      const selectablePairInputs = Array.from(
        pairListEl.querySelectorAll('input[data-group="pair"]:not(:disabled)'),
      );
      STATE.selectedPairs = new Set(selectablePairInputs.map((input) => input.value));
      selectablePairInputs.forEach((input) => {
        input.checked = true;
      });
      render();
    });
  }

  if (pairUnselectAllButton) {
    pairUnselectAllButton.addEventListener('click', () => {
      STATE.selectedPairs = new Set();
      const allPairInputs = Array.from(pairListEl.querySelectorAll('input[data-group="pair"]'));
      allPairInputs.forEach((input) => {
        input.checked = false;
      });
      render();
    });
  }

  pairListEl.addEventListener('change', () => {
    const selected = getCheckedValues(pairListEl, 'pair');
    STATE.selectedPairs = new Set(selected);
    render();
  });

  languageListEl.addEventListener('change', () => {
    const selected = getCheckedValues(languageListEl, 'language');
    STATE.selectedLanguages = new Set(selected);
    if (STATE.selectedLanguages.size === 0) {
      const fallback = getLanguages()[0];
      if (fallback) STATE.selectedLanguages.add(fallback);
      const fallbackInput = Array.from(
        languageListEl.querySelectorAll('input[data-group="language"]'),
      ).find((input) => input.value === fallback);
      if (fallbackInput) fallbackInput.checked = true;
    }
    updateAxisSelectors();
    syncErrorBarModeWithDefaults();
    render();
  });

  if (evalSelectAllButton) {
    evalSelectAllButton.addEventListener('click', () => {
      const evals = getEvals();
      STATE.selectedEvals = new Set(evals);
      renderEvalList();
      updateAxisSelectors();
      syncErrorBarModeWithDefaults();
      render();
    });
  }

  if (evalClearButton) {
    evalClearButton.addEventListener('click', () => {
      STATE.selectedEvals = new Set();
      renderEvalList();
      updateAxisSelectors();
      syncErrorBarModeWithDefaults();
      render();
    });
  }

  evalListEl.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action="toggle-versions"]');
    if (!button) return;
    const evalName = button.dataset.eval || '';
    if (!evalName) return;
    if (STATE.expandedVersionEvals.has(evalName)) {
      STATE.expandedVersionEvals.delete(evalName);
    } else {
      STATE.expandedVersionEvals.add(evalName);
    }
    renderEvalList();
  });

  evalListEl.addEventListener('change', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement)) return;
    if (input.dataset.group === 'eval') {
      const selected = getCheckedValues(evalListEl, 'eval');
      STATE.selectedEvals = new Set(selected);
      renderEvalList();
    } else if (input.dataset.group === 'eval-version') {
      const evalName = input.dataset.eval || '';
      if (!STATE.selectedEvalVersions.has(evalName)) {
        STATE.selectedEvalVersions.set(evalName, new Set());
      }
      const selectedVersions = STATE.selectedEvalVersions.get(evalName);
      if (input.checked) {
        selectedVersions.add(versionKey(input.value));
      } else {
        selectedVersions.delete(versionKey(input.value));
      }
      renderEvalList();
    }
    updateAxisSelectors();
    syncErrorBarModeWithDefaults();
    render();
  });

  xAxisSelect.addEventListener('change', () => {
    STATE.xAxis = xAxisSelect.value;
    syncErrorBarModeWithDefaults();
    renderColorModeSelector();
    render();
  });
  yAxisSelect.addEventListener('change', () => {
    STATE.yAxis = yAxisSelect.value;
    render();
  });
  reportTypeSelect.addEventListener('change', () => {
    STATE.reportType = normalizeReportType(reportTypeSelect.value);
    render();
  });
  errorBarsSelect.addEventListener('change', () => {
    STATE.errorBarMode = errorBarsSelect.value;
    render();
  });

  colorModeSelect.addEventListener('change', () => {
    STATE.colorMode = colorModeSelect.value;
    STATE.hiddenColorKeys.clear();
    render();
  });

  labelModeSelect.addEventListener('change', () => {
    STATE.labelMode = normalizeLabelMode(labelModeSelect.value);
    render();
  });

  nameModeSelect.addEventListener('change', () => {
    STATE.nameMode = normalizeNameMode(nameModeSelect.value);
    render();
  });

  tableModeSelect.addEventListener('change', () => {
    STATE.tableMode = tableModeSelect.value === 'runs' ? 'runs' : 'summary';
    if (!getTableSortOptions(STATE.tableMode).some((option) => option.id === STATE.tableSortBy)) {
      STATE.tableSortBy = '';
    }
    renderTableControls();
    render();
  });

  tableGroupBySelect.addEventListener('change', () => {
    STATE.tableGroupBy = tableGroupBySelect.value;
    render();
  });

  tableSortBySelect.addEventListener('change', () => {
    STATE.tableSortBy = tableSortBySelect.value;
    if (!STATE.tableSortBy) {
      STATE.tableSortDirection = 'asc';
      renderTableControls();
    }
    render();
  });

  tableSortDirectionSelect.addEventListener('change', () => {
    STATE.tableSortDirection = tableSortDirectionSelect.value === 'asc' ? 'asc' : 'desc';
    render();
  });

  let resizeTimer = null;
  const requestRerender = () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (STATE.rows.length) render();
    }, 120);
  };
  window.addEventListener('resize', requestRerender);
  if (typeof ResizeObserver !== 'undefined') {
    const chartObserver = new ResizeObserver(requestRerender);
    chartObserver.observe(chartSvg);
  }
}

function renderPairList(canRenderPairById) {
  pairListEl.replaceChildren();
  const rowsByPair = getRowsByPairForCurrentSelection();
  const availabilityMap = canRenderPairById || getPairAvailability(rowsByPair);
  const unavailableLabels = [];
  getPairs().forEach((pairId) => {
    const isSelectable = availabilityMap.get(pairId) ?? true;
    const { agent, model } = splitPairId(pairId);

    if (!isSelectable && STATE.selectedPairs.has(pairId)) {
      unavailableLabels.push(`${agent} / ${model}`);
    }

    const row = document.createElement('label');
    row.classList.toggle('unavailable-option', !isSelectable);
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.dataset.group = 'pair';
    cb.value = pairId;
    cb.checked = STATE.selectedPairs.has(pairId);
    cb.disabled = !isSelectable;
    row.appendChild(cb);
    row.appendChild(document.createTextNode(`${agent} / ${model}`));
    pairListEl.appendChild(row);
  });

  if (pairUnavailableHintEl) {
    if (unavailableLabels.length) {
      const noun = unavailableLabels.length === 1 ? 'pair has' : 'pairs have';
      pairUnavailableHintEl.textContent =
        `${unavailableLabels.length} ${noun} no data for this view: ${unavailableLabels.join(', ')}.`;
    } else {
      pairUnavailableHintEl.textContent = '';
    }
  }

  return availabilityMap;
}

function renderLanguageList() {
  languageListEl.replaceChildren();
  getLanguages().forEach((language) => {
    const row = document.createElement('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.dataset.group = 'language';
    cb.value = language;
    cb.checked = STATE.selectedLanguages.has(language);
    row.appendChild(cb);
    row.appendChild(document.createTextNode(language));
    languageListEl.appendChild(row);
  });
}

function renderEvalList() {
  evalListEl.replaceChildren();
  getEvals().forEach((evalName) => {
    const item = document.createElement('div');
    item.className = 'eval-filter-item';

    const row = document.createElement('div');
    row.className = 'eval-filter-main';
    const label = document.createElement('label');
    label.className = 'eval-filter-label';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.dataset.group = 'eval';
    cb.value = evalName;
    cb.checked = STATE.selectedEvals.has(evalName);
    label.appendChild(cb);
    label.appendChild(document.createTextNode(evalName));

    const versions = getEvalVersions(evalName);
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'version-toggle';
    toggle.dataset.action = 'toggle-versions';
    toggle.dataset.eval = evalName;
    toggle.textContent = formatVersionSummary(evalName);
    toggle.title = `Choose ${evalName} versions`;
    toggle.setAttribute('aria-expanded', STATE.expandedVersionEvals.has(evalName) ? 'true' : 'false');
    toggle.disabled = versions.length <= 1;

    row.append(label, toggle);
    item.appendChild(row);

    if (versions.length > 1) {
      const versionList = document.createElement('div');
      versionList.className = 'version-list';
      if (!STATE.expandedVersionEvals.has(evalName)) {
        versionList.classList.add('hidden');
      }
      versionList.dataset.eval = evalName;
      versions.forEach((version) => {
        const versionLabel = document.createElement('label');
        versionLabel.className = 'version-option';
        const versionInput = document.createElement('input');
        versionInput.type = 'checkbox';
        versionInput.dataset.group = 'eval-version';
        versionInput.dataset.eval = evalName;
        versionInput.value = version;
        versionInput.checked = isEvalVersionSelected(evalName, version);
        versionInput.disabled = !STATE.selectedEvals.has(evalName);
        versionLabel.appendChild(versionInput);
        versionLabel.appendChild(document.createTextNode(formatVersionLabel(version)));
        versionList.appendChild(versionLabel);
      });
      item.appendChild(versionList);
    }

    evalListEl.appendChild(item);
  });
}

function updateAxisSelectors() {
  xAxisSelect.replaceChildren();
  AXIS_OPTIONS.forEach((axis) => {
    const option = document.createElement('option');
    option.value = axis.id;
    option.textContent = axis.label;
    const categoryCount = getSelectedAxisCategories(axis.id).length;
    if (axis.axisOnly && categoryCount < 2) {
      option.disabled = true;
      option.textContent = `${axis.label} (select 2+ ${axis.selectionLabel || 'values'})`;
    }
    xAxisSelect.appendChild(option);
  });
  if (isCategoricalXAxis(STATE.xAxis) && getSelectedAxisCategories(STATE.xAxis).length < 2) {
    STATE.xAxis = 'cost';
  } else if (!xAxisSelect.querySelector(`option[value="${STATE.xAxis}"]`)) {
    STATE.xAxis = 'cost';
  }
  xAxisSelect.value = STATE.xAxis;

  yAxisSelect.replaceChildren();
  AXIS_OPTIONS.forEach((axis) => {
    if (axis.axisOnly) return;
    const option = document.createElement('option');
    option.value = axis.id;
    option.textContent = axis.label;
    yAxisSelect.appendChild(option);
  });
  if (!yAxisSelect.querySelector(`option[value="${STATE.yAxis}"]`)) {
    STATE.yAxis = 'percent';
  }
  yAxisSelect.value = STATE.yAxis;
}

function renderColorModeSelector() {
  colorModeSelect.replaceChildren();
  COLOR_MODE_OPTIONS.forEach((mode) => {
    const option = document.createElement('option');
    option.value = mode.id;
    option.textContent = mode.label;
    colorModeSelect.appendChild(option);
  });

  const selectedOption = colorModeSelect.querySelector(`option[value="${STATE.colorMode}"]`);
  if (!selectedOption || selectedOption.disabled) {
    STATE.colorMode = 'pair';
  }
  colorModeSelect.value = STATE.colorMode;
}

function renderLabelModeSelector() {
  labelModeSelect.replaceChildren();
  LABEL_MODE_OPTIONS.forEach((mode) => {
    const option = document.createElement('option');
    option.value = mode.id;
    option.textContent = mode.label;
    labelModeSelect.appendChild(option);
  });

  STATE.labelMode = normalizeLabelMode(STATE.labelMode);
  labelModeSelect.value = STATE.labelMode;
}

function normalizeLabelMode(mode) {
  const normalized = String(mode || '').trim().toLowerCase();
  return LABEL_MODE_OPTIONS.some((option) => option.id === normalized)
    ? normalized
    : 'all';
}

function renderNameModeSelector() {
  nameModeSelect.replaceChildren();
  NAME_MODE_OPTIONS.forEach((mode) => {
    const option = document.createElement('option');
    option.value = mode.id;
    option.textContent = mode.label;
    nameModeSelect.appendChild(option);
  });

  STATE.nameMode = normalizeNameMode(STATE.nameMode);
  nameModeSelect.value = STATE.nameMode;
}

function normalizeNameMode(mode) {
  const normalized = String(mode || '').trim().toLowerCase();
  return NAME_MODE_OPTIONS.some((option) => option.id === normalized)
    ? normalized
    : 'short';
}

function renderReportTypeSelector() {
  const normalizedReportType = normalizeReportType(STATE.reportType);
  STATE.reportType = normalizedReportType || 'mean';

  reportTypeSelect.replaceChildren();
  REPORT_TYPE_OPTIONS.forEach((type) => {
    const option = document.createElement('option');
    option.value = type.id;
    option.textContent = type.label;
    reportTypeSelect.appendChild(option);
  });

  const selectedOption = reportTypeSelect.querySelector(`option[value="${STATE.reportType}"]`);
  if (!selectedOption) {
    STATE.reportType = 'mean';
  }
  reportTypeSelect.value = STATE.reportType;
}

function renderErrorBarSelector() {
  errorBarsSelect.replaceChildren();
  ERROR_BAR_OPTIONS.forEach((type) => {
    const option = document.createElement('option');
    option.value = type.id;
    option.textContent = type.label;
    errorBarsSelect.appendChild(option);
  });

  const selectedOption = errorBarsSelect.querySelector(`option[value="${STATE.errorBarMode}"]`);
  if (!selectedOption) {
    STATE.errorBarMode = getDefaultErrorBarMode();
  }
  errorBarsSelect.value = STATE.errorBarMode;
}

function renderTableControls() {
  tableModeSelect.value = STATE.tableMode;
  tableGroupBySelect.value = STATE.tableGroupBy;
  tableSortDirectionSelect.value = STATE.tableSortDirection;
  tableSortBySelect.replaceChildren();
  const sortOptions = getTableSortOptions(STATE.tableMode);
  sortOptions.forEach((optionDef) => {
    const option = document.createElement('option');
    option.value = optionDef.id;
    option.textContent = optionDef.label;
    tableSortBySelect.appendChild(option);
  });
  if (!sortOptions.some((option) => option.id === STATE.tableSortBy)) {
    STATE.tableSortBy = '';
  }
  tableSortBySelect.value = STATE.tableSortBy;
  tableSortDirectionSelect.disabled = !STATE.tableSortBy;

  tableSummaryControls.forEach((el) => {
    el.classList.toggle('hidden', STATE.tableMode !== 'summary');
  });
  tableRunsControls.forEach((el) => {
    el.classList.toggle('hidden', STATE.tableMode !== 'runs');
  });
}

function getTableSortOptions(tableMode = STATE.tableMode) {
  return (TABLE_SORT_OPTIONS[tableMode] || []).filter(
    (option) => !(shouldHideEvalLanguageColumn() && option.id === 'eval_language'),
  );
}

function syncViewModeControls() {
  document.body.classList.toggle('table-view-active', STATE.viewMode === 'table');
  viewModeEl.querySelectorAll('button[data-view-mode]').forEach((button) => {
    const pressed = button.dataset.viewMode === STATE.viewMode;
    button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
  });
  graphControls.forEach((el) => {
    el.classList.toggle('hidden', STATE.viewMode !== 'graph');
  });
  tableControls.forEach((el) => {
    el.classList.toggle('hidden', STATE.viewMode !== 'table');
  });
  graphPanel.classList.toggle('hidden', STATE.viewMode !== 'graph');
  tablePanel.classList.toggle('hidden', STATE.viewMode !== 'table');
}

function syncControlsColumn() {
  dashboardLayout.classList.toggle('controls-collapsed', STATE.controlsCollapsed);
  controlsToggleButton.setAttribute('aria-expanded', STATE.controlsCollapsed ? 'false' : 'true');
  controlsToggleButton.textContent = STATE.controlsCollapsed ? 'Show controls' : 'Hide controls';
}

function getDefaultErrorBarMode() {
  if (STATE.selectedLanguages.size > 1 && !isCategoricalXAxis(STATE.xAxis)) {
    return 'std';
  }
  return 'range';
}

function syncErrorBarModeWithDefaults() {
  const defaultMode = getDefaultErrorBarMode();
  if (STATE.errorBarMode === 'std' || STATE.errorBarMode === 'range') {
    STATE.errorBarMode = defaultMode;
    if (errorBarsSelect) {
      errorBarsSelect.value = STATE.errorBarMode;
    }
  }
}

function render() {
  if (syncSelectedPairsForCurrentEvalLanguages()) {
    renderPairList();
  }

  clearError();
  syncViewModeControls();
  syncGraphTitle();
  syncTableTitle();
  renderTableControls();
  const validation = validateSelection();
  if (!validation.ok) {
    showNoData(validation.message);
    return;
  }

  const colorMap = getColorMap();
  const rowsByPair = getRowsByPairForCurrentSelection();
  const canRenderPairById =
    STATE.viewMode === 'table'
      ? getPairAvailabilityForRows(rowsByPair)
      : getPairAvailability(rowsByPair);
  renderPairList(canRenderPairById);

  if (STATE.viewMode === 'table') {
    renderTableView();
    return;
  }

  const points = buildPoints(colorMap, rowsByPair);
  if (!points.length) {
    showNoData('No matching results for the current filters.');
    return;
  }

  const visiblePoints = points.filter(
    (p) => !STATE.hiddenColorKeys.has(p.colorModeKey),
  );

  legendEl.innerHTML = '';
  clearChart();
  renderLegend(points, colorMap);
  if (!visiblePoints.length) {
    chartEmpty.textContent =
      'All series in this view are hidden. Click a legend entry to re-enable one.';
    chartEmpty.classList.remove('hidden');
    validationEl.textContent = '';
    return;
  }
  renderPlot(visiblePoints);
  chartEmpty.classList.add('hidden');
  validationEl.textContent = '';
}

function syncGraphTitle() {
  if (!graphTitleEl) return;
  const title = buildGraphTitle();
  graphTitleEl.textContent = title;
  graphTitleEl.title = title;
}

function syncTableTitle() {
  if (!tableTitleEl) return;
  const title = buildTableTitle();
  tableTitleEl.textContent = title;
  tableTitleEl.title = title;
}

function buildGraphTitle() {
  const selectedEvals = getSelectedEvalNames();
  const selectedLanguages = getSelectedLanguageNames();
  if (!selectedEvals.length || !selectedLanguages.length) return 'XY Scatter Plot';

  if (areAllLanguagesSelected()) {
    return selectedEvals.join(', ');
  }

  return selectedEvals
    .flatMap((evalName) =>
      selectedLanguages.map((language) => formatEvalLanguageLabel(evalName, language)),
    )
    .join(', ');
}

function buildTableTitle() {
  const selectedEvals = getSelectedEvalNames();
  if (shouldHideEvalLanguageColumn() && selectedEvals.length === 1) {
    return `${selectedEvals[0]} Results Table`;
  }
  return 'Results Table';
}

function shouldHideEvalLanguageColumn() {
  return getSelectedEvalNames().length === 1 && areExactlyFourLanguagesSelected();
}

function getSelectedEvalNames() {
  return getEvals().filter((evalName) => STATE.selectedEvals.has(evalName));
}

function getSelectedLanguageNames() {
  return getLanguages().filter((language) => STATE.selectedLanguages.has(language));
}

function areAllLanguagesSelected() {
  const languages = getLanguages();
  return languages.length > 0 && languages.every((language) => STATE.selectedLanguages.has(language));
}

function areExactlyFourLanguagesSelected() {
  const languages = getLanguages();
  return (
    languages.length === 4 &&
    STATE.selectedLanguages.size === 4 &&
    languages.every((language) => STATE.selectedLanguages.has(language))
  );
}

function getColorMap() {
  let colorKeys = [];

  if (STATE.colorMode === 'language') {
    colorKeys = Array.from(STATE.selectedLanguages).sort();
  } else if (STATE.colorMode === 'agent') {
    const agentSet = new Set();
    Array.from(STATE.selectedPairs).forEach((pairId) => {
      const { agent } = splitPairId(pairId);
      agentSet.add(agent || 'Unknown Agent');
    });
    colorKeys = Array.from(agentSet).sort();
  } else {
    colorKeys = Array.from(STATE.selectedPairs).sort();
  }

  const map = new Map();
  colorKeys.forEach((colorKey, index) => {
    map.set(colorKey, PALETTE[index % PALETTE.length]);
  });
  return map;
}

function validateSelection() {
  if (!STATE.selectedEvals.size) {
    return { ok: false, message: 'Choose at least one eval.' };
  }
  if (!getSelectedEvalVersionCount()) {
    return { ok: false, message: 'Choose at least one version for the selected evals.' };
  }
  if (!STATE.selectedPairs.size) {
    return { ok: false, message: 'Choose at least one agent/model/effort pair.' };
  }
  if (!STATE.selectedLanguages.size) {
    return { ok: false, message: 'Choose at least one language.' };
  }
  if (STATE.viewMode === 'graph' && isCategoricalXAxis(STATE.xAxis)) {
    const categories = getSelectedAxisCategories(STATE.xAxis);
    const axis = AXIS_OPTIONS.find((option) => option.id === STATE.xAxis);
    if (categories.length < 2) {
      return {
        ok: false,
        message: `${axis?.label || STATE.xAxis} is available when at least two ${axis?.selectionLabel || 'values'} are selected.`,
      };
    }
  }
  return { ok: true };
}

function showNoData(message) {
  clearChart();
  chartEmpty.textContent = message;
  chartEmpty.classList.remove('hidden');
  legendEl.innerHTML = '';
  tableEl.replaceChildren();
  tableEmpty.textContent = message;
  tableEmpty.classList.remove('hidden');
  tableCountEl.textContent = '';
  validationEl.textContent = message;
}

function getChartSize() {
  const rect = chartSvg.getBoundingClientRect();
  const width = rect.width > 0 ? Math.round(rect.width) : 980;
  const height = rect.height > 0 ? Math.round(rect.height) : 560;
  return { width: Math.max(480, width), height: Math.max(320, height) };
}

function clearChart() {
  chartSvg.innerHTML = '';
}

function renderTableView() {
  clearChart();
  legendEl.innerHTML = '';
  chartEmpty.classList.add('hidden');
  validationEl.textContent = '';

  const rows = STATE.tableMode === 'runs' ? buildRunTableRows() : buildSummaryTableRows();
  const columns = STATE.tableMode === 'runs' ? getRunTableColumns() : getSummaryTableColumns();
  const sortedRows = sortTableRows(rows);
  renderResultsTable(columns, sortedRows);
  if (STATE.tableMode === 'runs') {
    primeLastMessageTooltips(sortedRows);
  }

  if (!sortedRows.length) {
    tableEmpty.textContent = 'No matching rows for the current filters.';
    tableEmpty.classList.remove('hidden');
    tableCountEl.textContent = '';
    return;
  }

  tableEmpty.classList.add('hidden');
  const noun = sortedRows.length === 1 ? 'row' : 'rows';
  tableCountEl.textContent = `${sortedRows.length} ${noun}`;
}

function buildSummaryTableRows() {
  const groups = new Map();
  getRowsForCurrentSelection(STATE.rows).forEach((row) => {
    const group = getSummaryGroup(row);
    if (!groups.has(group.key)) {
      groups.set(group.key, { ...group, rows: [] });
    }
    groups.get(group.key).rows.push(row);
  });

  return Array.from(groups.values()).map((group) => {
    const summaries = summarizePointDetails(group.rows);
    const evals = Array.from(new Set(group.rows.map((row) => row.eval).filter(Boolean))).sort();
    const languages = Array.from(new Set(group.rows.map((row) => row.language).filter(Boolean))).sort();
    const evalLabel = group.evalLabel || formatListLabel(evals, 'All selected');
    const languageLabel = group.languageLabel || formatListLabel(languages, 'All selected');
    const evalLanguageLabel = formatEvalLanguageLabel(evalLabel, languageLabel);
    return {
      type: 'summary',
      pairId: group.pairId,
      evalLabel,
      languageLabel,
      evalLanguageLabel,
      runs: group.rows.length,
      evals,
      languages,
      summaries,
      sortValues: {
        pair: group.pairId,
        eval_language: evalLanguageLabel,
        runs: group.rows.length,
        percent: summaries.percent?.mean,
        cost: summaries.cost?.mean,
        wall: summaries.wall?.mean,
        tokens: summaries.tokens_total?.mean,
        tools: summaries.tools?.mean,
        loc: summaries.loc?.mean,
      },
    };
  });
}

function getSummaryGroup(row) {
  const pairId = rowPairId(row);
  const parts = [pairId];
  const group = { key: '', pairId, evalLabel: '', languageLabel: '' };
  if (STATE.tableGroupBy === 'pair_eval' || STATE.tableGroupBy === 'pair_eval_language') {
    group.evalLabel = row.eval || 'Unknown';
    parts.push(group.evalLabel);
  }
  if (STATE.tableGroupBy === 'pair_language' || STATE.tableGroupBy === 'pair_eval_language') {
    group.languageLabel = row.language || 'Unknown';
    parts.push(group.languageLabel);
  }
  group.key = parts.join('\u001f');
  return group;
}

function buildRunTableRows() {
  return getRowsForCurrentSelection(STATE.rows).map((row) => ({
    ...row,
    sortValues: getRunSortValues(row),
  }));
}

function getRunSortValues(row) {
  return {
    eval_language: formatEvalLanguageLabel(row.eval || 'Unknown', row.language || 'n/a'),
    pair: rowPairId(row),
    run: toNumber(row.run_id),
    version: row.eval_version || '',
    percent: row.score_pct,
    cost: row.cost_usd,
    wall: row.wall_min,
    tokens: row.input_tokens + row.output_tokens,
    tools: row.tools,
    files: row.files,
    loc: row.loc,
    link: row.result_link || '',
    status: getRunStatusLabel(row),
    last_message: getLastMessageDisplay(row),
  };
}

function getRunStatusLabel(row) {
  const stopLabel = firstPresent(row.agent_stop_label, '');
  if (stopLabel) return stopLabel;
  const exitReason = firstPresent(row.exit_reason, 'completed');
  if (exitReason === 'completed') return 'Finished';
  return firstPresent(
    row.status,
    row.failure_class,
    exitReason,
    'completed',
  );
}

function getRunStatusTitle(row) {
  const stopLabel = getRunStatusLabel(row);
  const exitReason = firstPresent(row.exit_reason, 'completed');
  const failureClass = firstPresent(row.failure_class, '');
  const stopReason = firstPresent(row.agent_stop_reason, '');
  const stopMessage = firstPresent(row.agent_stop_message, '');
  const notes = firstPresent(row.notes, '');
  const lastMessage = firstPresent(row.last_message, '');
  const parts = [`Agent stop: ${stopLabel}`];
  if (stopReason && stopReason !== stopLabel) parts.push(`Reason: ${stopReason}`);
  if (stopMessage) parts.push(`Stop message: ${stopMessage}`);
  if (exitReason) parts.push(`Harness exit: ${exitReason}`);
  if (failureClass && failureClass !== stopLabel && failureClass !== exitReason) parts.push(`Class: ${failureClass}`);
  if (Number.isFinite(row.score_count) && Number.isFinite(row.score_total) && row.score_total > 0) {
    parts.push(`Score: ${formatCount(row.score_count)}/${formatCount(row.score_total)} (${formatAxisValue('percent', row.score_pct)})`);
  }
  if (lastMessage) parts.push(`Last Message: ${lastMessage}`);
  if (notes) parts.push(`Notes: ${notes}`);
  return parts.join('\n');
}

function getRowsForCurrentSelection(rows) {
  return rows.filter((row) => {
    if (!STATE.selectedEvals.has(row.eval)) return false;
    if (!isRowVersionSelected(row)) return false;
    if (!STATE.selectedLanguages.has(row.language)) return false;
    if (!STATE.selectedPairs.has(rowPairId(row))) return false;
    return true;
  });
}

function getSummaryTableColumns() {
  const columns = [
    {
      key: 'pair',
      label: 'Agent / Model / Effort',
      render: (row) => formatAgentModelDisplay(row.pairId),
      title: (row) => row.pairId,
    },
    {
      key: 'eval_language',
      label: 'Eval-Lang',
      render: (row) => row.evalLanguageLabel,
      title: (row) => `${row.evalLabel} / ${row.languageLabel}`,
    },
    { key: 'runs', label: 'Runs', numeric: true, render: (row) => formatCount(row.runs) },
    {
      key: 'percent',
      label: 'Pass rate',
      numeric: true,
      render: (row) => formatSummaryMetric('percent', row.summaries.percent),
    },
    {
      key: 'cost',
      label: 'Cost',
      numeric: true,
      render: (row) => formatSummaryMetric('cost', row.summaries.cost),
    },
    {
      key: 'wall',
      label: 'Wall',
      numeric: true,
      render: (row) => formatSummaryMetric('wall', row.summaries.wall),
    },
    {
      key: 'tokens',
      label: 'Tokens',
      numeric: true,
      render: (row) => formatSummaryMetric('tokens_total', row.summaries.tokens_total),
    },
    {
      key: 'tools',
      label: 'Tools',
      numeric: true,
      render: (row) => formatSummaryMetric('tools', row.summaries.tools),
    },
    {
      key: 'loc',
      label: 'LOC',
      numeric: true,
      render: (row) => formatSummaryMetric('loc', row.summaries.loc),
    },
  ];
  return filterVisibleTableColumns(columns);
}

function getRunTableColumns() {
  const columns = [
    {
      key: 'eval_language',
      label: 'Eval-Lang',
      render: (row) => formatEvalLanguageLabel(row.eval || 'Unknown', row.language || 'n/a'),
      title: (row) => `${row.eval || 'Unknown'} / ${row.language || 'n/a'}`,
    },
    {
      key: 'pair',
      label: 'Agent / Model / Effort',
      render: (row) => formatAgentModelDisplay(rowPairId(row)),
      title: (row) => rowPairId(row),
    },
    { key: 'run', label: 'Run', numeric: true, render: (row) => row.run_id || 'n/a' },
    { key: 'version', label: 'Version', render: (row) => row.eval_version || 'n/a' },
    {
      key: 'status',
      label: 'Agent Stop',
      className: 'table-status',
      render: (row) => getRunStatusLabel(row),
      title: (row) => getRunStatusTitle(row),
    },
    { key: 'score', sortKey: 'percent', label: 'Score', numeric: true, render: (row) => formatScore(row) },
    { key: 'cost', label: 'Cost', numeric: true, render: (row) => formatAxisValue('cost', row.cost_usd) },
    { key: 'wall', label: 'Wall', numeric: true, render: (row) => formatAxisValue('wall', row.wall_min) },
    { key: 'tokens', label: 'Tokens', numeric: true, render: (row) => formatRunTokens(row) },
    { key: 'tools', label: 'Tools', numeric: true, render: (row) => formatAxisValue('tools', row.tools) },
    { key: 'files', label: 'Files', numeric: true, render: (row) => formatAxisValue('files', row.files) },
    { key: 'loc', label: 'LOC', numeric: true, render: (row) => formatAxisValue('loc', row.loc) },
    { key: 'link', label: 'Link', render: (row) => buildResultLink(row) },
    {
      key: 'last_message',
      label: 'Last Message',
      className: 'table-message',
      render: (row) => getLastMessageDisplay(row),
      title: (row) => getLastMessageTooltip(row),
    },
  ];
  return filterVisibleTableColumns(columns);
}

function filterVisibleTableColumns(columns) {
  if (!shouldHideEvalLanguageColumn()) return columns;
  return columns.filter((column) => column.key !== 'eval_language');
}

function renderResultsTable(columns, rows) {
  tableEl.replaceChildren();
  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  columns.forEach((column) => {
    const th = document.createElement('th');
    if (column.numeric) th.classList.add('numeric');
    const sortKey = column.sortKey ?? column.key;
    th.setAttribute('aria-sort', getHeaderAriaSort(sortKey));
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'table-sort-button';
    button.title = `Sort by ${column.label}`;
    button.addEventListener('click', () => cycleTableSort(sortKey));
    const label = document.createElement('span');
    label.textContent = column.label;
    button.appendChild(label);
    const indicator = document.createElement('span');
    indicator.className = 'sort-indicator';
    indicator.textContent = getHeaderSortIndicator(sortKey);
    button.appendChild(indicator);
    th.appendChild(button);
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  tableEl.appendChild(thead);

  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    columns.forEach((column) => {
      const td = document.createElement('td');
      if (column.numeric) td.classList.add('numeric');
      if (column.className) td.classList.add(column.className);
      const title = column.title ? column.title(row) : '';
      if (title && title !== 'n/a') td.title = title;
      if (column.key === 'last_message' && row.result_link) {
        td.dataset.resultLink = row.result_link;
      }
      const value = column.render(row);
      if (value instanceof Node) {
        td.appendChild(value);
      } else {
        td.textContent = value;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tableEl.appendChild(tbody);
}

function cycleTableSort(sortKey) {
  if (!sortKey) return;
  if (STATE.tableSortBy !== sortKey) {
    STATE.tableSortBy = sortKey;
    STATE.tableSortDirection = 'asc';
  } else if (STATE.tableSortDirection === 'asc') {
    STATE.tableSortDirection = 'desc';
  } else {
    STATE.tableSortBy = '';
    STATE.tableSortDirection = 'asc';
  }
  renderTableControls();
  render();
}

function getHeaderAriaSort(sortKey) {
  if (!sortKey || STATE.tableSortBy !== sortKey) return 'none';
  return STATE.tableSortDirection === 'desc' ? 'descending' : 'ascending';
}

function getHeaderSortIndicator(sortKey) {
  if (!sortKey || STATE.tableSortBy !== sortKey) return '';
  return STATE.tableSortDirection === 'desc' ? 'desc' : 'asc';
}

function getLastMessageDisplay(row) {
  return firstPresent(row.last_message, row.failure_class, 'n/a');
}

function getLastMessageTooltip(row) {
  return firstPresent(
    row.last_message_verbatim,
    row.result_link ? LAST_MESSAGE_CACHE.get(row.result_link) : '',
    row.last_message,
    row.failure_class,
    '',
  );
}

function primeLastMessageTooltips(rows) {
  const links = Array.from(new Set(
    rows
      .map((row) => row.result_link)
      .filter((link) => link && !LAST_MESSAGE_CACHE.has(link)),
  ));
  if (!links.length) {
    updateLastMessageTooltips();
    return;
  }

  Promise.all(links.map(async (link) => {
    try {
      const response = await fetch(link);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      LAST_MESSAGE_CACHE.set(link, firstPresent(payload?.metadata?.agent_last_message, null));
    } catch {
      LAST_MESSAGE_CACHE.set(link, null);
    }
  })).then(updateLastMessageTooltips);
}

function updateLastMessageTooltips() {
  tableEl.querySelectorAll('td.table-message[data-result-link]').forEach((cell) => {
    const link = cell.dataset.resultLink;
    const cachedMessage = link ? LAST_MESSAGE_CACHE.get(link) : '';
    if (cachedMessage) cell.title = cachedMessage;
  });
}

function sortTableRows(rows) {
  if (!STATE.tableSortBy) return [...rows];
  const direction = STATE.tableSortDirection === 'asc' ? 1 : -1;
  return [...rows].sort((a, b) => {
    const aValue = a.sortValues?.[STATE.tableSortBy];
    const bValue = b.sortValues?.[STATE.tableSortBy];
    const aMissing = isMissingSortValue(aValue);
    const bMissing = isMissingSortValue(bValue);
    if (aMissing && bMissing) return 0;
    if (aMissing) return 1;
    if (bMissing) return -1;
    const result = compareTableValues(aValue, bValue);
    return result * direction;
  });
}

function compareTableValues(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b));
}

function isMissingSortValue(value) {
  return value === undefined || value === null || value === '' ||
    (typeof value === 'number' && !Number.isFinite(value));
}

function formatSummaryMetric(metricId, summary) {
  if (!summary?.hasData) return 'n/a';
  if (!Number.isFinite(summary.stdDev) || summary.stdDev <= 0) {
    return formatAxisValue(metricId, summary.mean);
  }
  const precision = getMeasuredValuePrecision(summary.stdDev);
  const useLocThousands =
    metricId === 'loc' &&
    (Math.abs(summary.mean) >= 1000 || Math.abs(summary.stdDev) >= 1000);
  const mean = useLocThousands
    ? formatLocCountAtDecimalPlaces(summary.mean, precision.decimalPlaces, true)
    : formatAxisValueWithDecimalPlaces(metricId, summary.mean, precision.decimalPlaces);
  const stdDev = useLocThousands
    ? formatLocCountAtDecimalPlaces(summary.stdDev, precision.decimalPlaces, true)
    : formatAxisValueWithDecimalPlaces(metricId, summary.stdDev, precision.decimalPlaces);
  return `${mean} +/- ${stdDev}`;
}

function formatListLabel(items, fallback) {
  if (!items.length) return fallback;
  if (items.length <= 3) return items.join(', ');
  return `${items.length} selected`;
}

function formatEvalLanguageLabel(evalLabel, languageLabel) {
  return `${evalLabel || 'Unknown'}-${languageLabel || 'n/a'}`;
}

function formatAgentModelShort(pairId) {
  const { agent, model } = splitPairId(pairId);
  return `${abbreviateAgent(agent)} / ${abbreviateModel(model)}`;
}

function formatAgentModelDisplay(pairId) {
  const fullName = rowPairId(pairId);
  return normalizeNameMode(STATE.nameMode) === 'full'
    ? fullName
    : formatAgentModelShort(fullName);
}

function formatAgentDisplay(agent) {
  const fullName = String(agent || 'Unknown Agent');
  return normalizeNameMode(STATE.nameMode) === 'full'
    ? fullName
    : abbreviateAgent(fullName);
}

function abbreviateAgent(agent) {
  const normalized = String(agent || '').toLowerCase();
  if (normalized === 'claude-code') return 'CC';
  if (normalized === 'codex-cli') return 'C';
  if (normalized === 'gemini-cli') return 'G';
  const parts = normalized.split(/[-_\s]+/).filter(Boolean);
  return parts.length
    ? parts.map((part) => part[0]).join('').toUpperCase()
    : 'n/a';
}

function abbreviateModel(model) {
  const { baseModel, effort } = splitModelEffortLabel(model);
  const normalized = String(baseModel || '').toLowerCase();
  const withEffort = (label) => (effort ? `${label} (${abbreviateEffort(effort)})` : label);
  const claudeMatch = normalized.match(/^claude-(opus|sonnet|haiku)-(\d+)-(\d+)/);
  if (claudeMatch) {
    return withEffort(`${claudeMatch[1][0].toUpperCase()}-${claudeMatch[2]}.${claudeMatch[3]}`);
  }
  const gptMatch = normalized.match(/^gpt-(\d+(?:\.\d+)?)(?:-(mini|codex))?/);
  if (gptMatch) {
    const suffix = gptMatch[2] === 'mini' ? '-m' : gptMatch[2] === 'codex' ? '-c' : '';
    return withEffort(`${gptMatch[1]}${suffix}`);
  }
  const geminiMatch = normalized.match(/^gemini-(\d+(?:\.\d+)?)(?:-(flash|pro))?/);
  if (geminiMatch) {
    const version = geminiMatch[1].includes('.') ? geminiMatch[1] : `${geminiMatch[1]}.0`;
    if (geminiMatch[2] === 'flash') return withEffort(`${version}-f`);
    if (geminiMatch[2] === 'pro') return withEffort(`${version}-p`);
    return withEffort(version);
  }
  return withEffort(baseModel || 'n/a');
}

function splitModelEffortLabel(model) {
  const value = String(model || '');
  const match = value.match(/^(.*) \(([^)]+)\)$/);
  if (!match) return { baseModel: value, effort: '' };
  return { baseModel: match[1], effort: match[2] };
}

function abbreviateEffort(effort) {
  const normalized = String(effort || '').toLowerCase();
  const labels = {
    none: 'none',
    minimal: 'min',
    low: 'low',
    medium: 'med',
    high: 'high',
    xhigh: 'xhigh',
  };
  return labels[normalized] || effort;
}

function formatScore(row) {
  if (Number.isFinite(row.score_count) && Number.isFinite(row.score_total) && row.score_total > 0) {
    return `${formatCount(row.score_count)}/${formatCount(row.score_total)} (${formatAxisValue('percent', row.score_pct)})`;
  }
  return formatAxisValue('percent', row.score_pct);
}

function formatRunTokens(row) {
  const total = row.input_tokens + row.output_tokens;
  return Number.isFinite(total) ? formatTokenCount(total) : 'n/a';
}

function buildResultLink(row) {
  if (!row.result_link) return 'n/a';
  const link = document.createElement('a');
  link.href = row.result_link;
  link.textContent = 'result';
  link.className = 'table-link';
  return link;
}

function buildPoints(colorMap, rowsByPairOverride) {
  const selectedLanguages = Array.from(STATE.selectedLanguages).sort();
  const selectedCategories = getSelectedAxisCategories(STATE.xAxis);
  const rowsByPair =
    rowsByPairOverride && rowsByPairOverride.size !== undefined
      ? rowsByPairOverride
      : getRowsByPairForCurrentSelection();

  const points = [];
  const rowsByPairList = Array.from(STATE.selectedPairs);
  rowsByPairList.forEach((pairId, index) => {
    const rows = rowsByPair.get(pairId) || [];
    if (!rows.length) return;
    const fallbackColor = PALETTE[index % PALETTE.length];

    if (isCategoricalXAxis(STATE.xAxis)) {
      selectedCategories.forEach((category) => {
        const categoryRows = rows.filter((row) => getRowCategoryValue(row, STATE.xAxis) === category);
        if (STATE.colorMode === 'language' && STATE.xAxis !== 'language') {
          selectedLanguages.forEach((language) => {
            const subset = categoryRows.filter((row) => row.language === language);
            const colorModeKey = getColorModeKey(pairId, language);
            const color = colorMap.get(colorModeKey) || fallbackColor;
            const point = summarizePoint(pairId, color, subset, language, {
              xAxis: STATE.xAxis,
              yAxis: STATE.yAxis,
              xAsCategory: true,
              xCategoryLabel: category,
              xCategoryValue: category,
            });
            if (point) {
              point.colorModeKey = colorModeKey;
              points.push(point);
            }
          });
        } else {
          const language = STATE.xAxis === 'language' ? category : null;
          const colorModeKey = getColorModeKey(pairId, language);
          const color = colorMap.get(colorModeKey) || fallbackColor;
          const point = summarizePoint(pairId, color, categoryRows, language, {
            xAxis: STATE.xAxis,
            yAxis: STATE.yAxis,
            xAsCategory: true,
            xCategoryLabel: category,
            xCategoryValue: category,
          });
          if (point) {
            point.colorModeKey = colorModeKey;
            points.push(point);
          }
        }
      });
    } else if (STATE.colorMode === 'language') {
      selectedLanguages.forEach((language) => {
        const subset = rows.filter((r) => r.language === language);
        const colorModeKey = getColorModeKey(pairId, language);
        const color = colorMap.get(colorModeKey) || fallbackColor;
        const point = summarizePoint(pairId, color, subset, language, {
          xAxis: STATE.xAxis,
          yAxis: STATE.yAxis,
          xAsCategory: false,
          xCategoryLabel: language,
        });
        if (point) {
          point.colorModeKey = colorModeKey;
          points.push(point);
        }
      });
    } else {
      const allLanguageLabel = `All ${selectedLanguages.length} languages`;
      const colorModeKey = getColorModeKey(pairId, allLanguageLabel);
      const color = colorMap.get(colorModeKey) || fallbackColor;
      const point = summarizePoint(pairId, color, rows, null, {
        xAxis: STATE.xAxis,
        yAxis: STATE.yAxis,
        xAsCategory: false,
        xCategoryLabel: allLanguageLabel,
      });
      if (point) {
        point.colorModeKey = colorModeKey;
        points.push(point);
      }
    }
  });

  return points;
}

function getRowsByPairForCurrentSelection() {
  const rowsByPair = new Map();

  STATE.rows.forEach((row) => {
    if (!STATE.selectedEvals.has(row.eval)) return;
    if (!isRowVersionSelected(row)) return;
    if (!STATE.selectedLanguages.has(row.language)) return;
    const pairId = rowPairId(row);
    if (!rowsByPair.has(pairId)) rowsByPair.set(pairId, []);
    rowsByPair.get(pairId).push(row);
  });

  return rowsByPair;
}

function getPairAvailability(rowsByPair) {
  const selectedLanguages = Array.from(STATE.selectedLanguages).sort();
  const availability = new Map();

  getPairs().forEach((pairId) => {
    const rows = rowsByPair.get(pairId) || [];
    availability.set(pairId, canRenderPair(rows, selectedLanguages));
  });

  return availability;
}

function getPairAvailabilityForRows(rowsByPair) {
  const availability = new Map();
  getPairs().forEach((pairId) => {
    const rows = rowsByPair.get(pairId) || [];
    availability.set(pairId, rows.length > 0);
  });
  return availability;
}

function canRenderPair(rows, selectedLanguages) {
  const xAxis = STATE.xAxis;
  const yAxis = STATE.yAxis;

  if (!rows.length) {
    return false;
  }

  if (isCategoricalXAxis(xAxis)) {
    return getSelectedAxisCategories(xAxis).some((category) => {
      const categoryRows = rows.filter((row) => getRowCategoryValue(row, xAxis) === category);
      if (!categoryRows.length) return false;
      if (STATE.colorMode === 'language' && xAxis !== 'language') {
        return selectedLanguages.some((language) => {
          const subset = categoryRows.filter((row) => row.language === language);
          if (!subset.length) return false;
          return summarizeMetric(subset, yAxis).hasData;
        });
      }
      return summarizeMetric(categoryRows, yAxis).hasData;
    });
  }

  if (STATE.colorMode === 'language') {
    return selectedLanguages.some((language) => {
      const subset = rows.filter((row) => row.language === language);
      const xSummary = summarizeMetric(subset, xAxis);
      const ySummary = summarizeMetric(subset, yAxis);
      return xSummary.hasData && ySummary.hasData;
    });
  }

  const xSummary = summarizeMetric(rows, xAxis);
  const ySummary = summarizeMetric(rows, yAxis);
  return xSummary.hasData && ySummary.hasData;
}

function getColorModeKey(pairId, language) {
  if (STATE.colorMode === 'language') {
    return language || `All ${STATE.selectedLanguages.size} languages`;
  }
  if (STATE.colorMode === 'agent') {
    const { agent } = splitPairId(pairId);
    return agent || 'Unknown Agent';
  }
  return pairId;
}

function summarizePoint(pairId, color, rows, language, options) {
  const xSummary = summarizeMetric(rows, options.xAxis);
  const ySummary = summarizeMetric(rows, options.yAxis);
  if (!xSummary.hasData || !ySummary.hasData) return null;

  return {
    pairId,
    pairLabel: rowPairId(pairId),
    color,
    language,
    rows,
    languages: Array.from(new Set(rows.map((row) => row.language))).sort(),
    evals: Array.from(new Set(rows.map((row) => row.eval))).sort(),
    xAsCategory: Boolean(options.xAsCategory),
    xAsLanguage: Boolean(options.xAsCategory && options.xAxis === 'language'),
    xSummary,
    ySummary,
    xValue: getReportValue(xSummary, STATE.reportType),
    yValue: getReportValue(ySummary, STATE.reportType),
    xCategoryLabel: options.xCategoryLabel,
    xCategoryValue: options.xCategoryValue || options.xCategoryLabel,
    xAxis: options.xAxis,
    yAxis: options.yAxis,
  };
}

function summarizeMetric(rows, metricId) {
  if (metricId === 'language' || metricId === 'eval') {
    return {
      hasData: true,
      worst: 0,
      mean: 0,
      min: 0,
      best: 0,
      max: 0,
      median: 0,
      count: rows.length,
    };
  }

  if (metricId === 'tokens_total') {
    const minClamp = METRICS.tokens_total?.minClamp;
    const input = rows
      .map((row) => row.input_tokens)
      .filter((value) => Number.isFinite(value));
    const output = rows
      .map((row) => row.output_tokens)
      .filter((value) => Number.isFinite(value));
    const totals = rows
      .map((row) => row.input_tokens + row.output_tokens)
      .filter((value) => Number.isFinite(value));
    if (!totals.length || !input.length || !output.length) return { hasData: false };
    const inStats = stats(input);
    const outStats = stats(output);
    const totalStats = stats(totals);
    if (!inStats || !outStats || !totalStats) return { hasData: false };

    const totalSummary = applySummaryClamp(totalStats, minClamp);
    const inputSummary = applySummaryClamp(inStats, minClamp);
    const outputSummary = applySummaryClamp(outStats, minClamp);
    return {
      hasData: true,
      stacked: true,
      count: totalSummary.count,
      worst: totalSummary.worst,
      mean: totalSummary.mean,
      best: totalSummary.best,
      min: totalSummary.min,
      max: totalSummary.max,
      median: totalSummary.median,
      meanInput: inputSummary.mean,
      minInput: inputSummary.min,
      maxInput: inputSummary.max,
      medianInput: inputSummary.median,
      bestInput: inputSummary.best,
      worstInput: inputSummary.worst,
      meanOutput: outputSummary.mean,
      minOutput: outputSummary.min,
      maxOutput: outputSummary.max,
      medianOutput: outputSummary.median,
      bestOutput: outputSummary.best,
      worstOutput: outputSummary.worst,
    };
  }

  const spec = METRICS[metricId];
  if (!spec) return { hasData: false };
  if (shouldCombineMetricAcrossEvals(rows, metricId)) {
    const combined = summarizeMetricAcrossEvals(rows, metricId, spec);
    if (!combined.hasData) return combined;
    const minClamp = spec.minClamp;
    if (!Number.isFinite(minClamp)) return combined;
    const clamped = applySummaryClamp(combined, minClamp);
    clamped.hasData = true;
    return clamped;
  }

  const values = rows
    .map((row) => spec.parse(row))
    .filter((value) => Number.isFinite(value));
  const s = stats(values);
  if (!s) return { hasData: false };
  const minClamp = spec.minClamp;
  if (!Number.isFinite(minClamp)) return { ...s, hasData: true };
  const clamped = applySummaryClamp(s, minClamp);
  clamped.hasData = true;
  return clamped;
}

function shouldCombineMetricAcrossEvals(rows, metricId) {
  if (!EVAL_COMBINED_METRIC_MODES[metricId]) return false;
  if (STATE.selectedEvals.size <= 1) return false;

  const evalsWithRows = new Set();
  rows.forEach((row) => {
    if (row.eval) evalsWithRows.add(row.eval);
  });
  return evalsWithRows.size > 1;
}

function summarizeMetricAcrossEvals(rows, metricId, spec) {
  const groupsByEval = new Map();
  rows.forEach((row) => {
    const value = spec.parse(row);
    if (!Number.isFinite(value)) return;

    const evalName = row.eval || 'Unknown Eval';
    if (!groupsByEval.has(evalName)) groupsByEval.set(evalName, []);
    groupsByEval.get(evalName).push(value);
  });

  const evalSummaries = Array.from(groupsByEval.values())
    .map((values) => stats(values))
    .filter(Boolean);
  if (!evalSummaries.length) return { hasData: false };

  const mode = EVAL_COMBINED_METRIC_MODES[metricId];
  if (mode === 'average') {
    const evalMeanStats = stats(evalSummaries.map((summary) => summary.mean));
    if (!evalMeanStats) return { hasData: false };
    return {
      ...evalMeanStats,
      hasData: true,
      count: evalSummaries.reduce((acc, summary) => acc + summary.count, 0),
      evalCount: evalSummaries.length,
    };
  }

  const divisor = mode === 'average' ? evalSummaries.length : 1;
  const combineField = (field) =>
    evalSummaries.reduce((acc, summary) => acc + summary[field], 0) / divisor;
  const varianceSum = evalSummaries.reduce(
    (acc, summary) => acc + Math.pow(summary.stdDev || 0, 2),
    0,
  );

  return {
    hasData: true,
    min: combineField('min'),
    worst: combineField('worst'),
    max: combineField('max'),
    best: combineField('best'),
    median: combineField('median'),
    mean: combineField('mean'),
    stdDev: Math.sqrt(varianceSum) / divisor,
    count: evalSummaries.reduce((acc, summary) => acc + summary.count, 0),
    evalCount: evalSummaries.length,
  };
}

function stats(values) {
  if (!values.length) return null;

  const sortedValues = [...values].sort((a, b) => a - b);
  const min = sortedValues[0];
  const max = sortedValues[sortedValues.length - 1];
  const mid = Math.floor(sortedValues.length / 2);
  const median = sortedValues.length % 2 === 0
    ? (sortedValues[mid - 1] + sortedValues[mid]) / 2
    : sortedValues[mid];

  const total = values.reduce((acc, value) => acc + value, 0);
  const mean = total / values.length;
  const variance =
    values.reduce((acc, value) => acc + Math.pow(value - mean, 2), 0) / values.length;
  return {
    min,
    worst: min,
    max,
    best: max,
    median,
    mean,
    stdDev: Math.sqrt(variance),
    count: values.length,
  };
}

function applySummaryClamp(summary, minClamp) {
  if (!summary || !Number.isFinite(minClamp)) return summary;
  return {
    ...summary,
    min: Math.max(summary.min, minClamp),
    mean: Math.max(summary.mean, minClamp),
    max: Math.max(summary.max, minClamp),
    median: Math.max(summary.median, minClamp),
    worst: Math.max(summary.worst, minClamp),
    best: Math.max(summary.best, minClamp),
  };
}

function getReportTypeLabel(reportType) {
  const normalizedReportType = normalizeReportType(reportType);
  const label = REPORT_TYPE_OPTIONS.find((item) => item.id === normalizedReportType)?.label;
  return label || (normalizedReportType === 'best'
    ? 'Best'
    : normalizedReportType === 'worst'
      ? 'Worst'
      : 'Mean');
}

function normalizeReportType(reportType) {
  const normalized = String(reportType || '').trim().toLowerCase();
  if (normalized === 'max' || normalized === 'maximum') return 'best';
  if (normalized === 'min' || normalized === 'minimum') return 'worst';
  if (normalized === 'avg' || normalized === 'average') return 'mean';
  return normalized;
}

function getReportValue(summary, reportType) {
  const normalizedReportType = normalizeReportType(reportType);
  if (!summary || !summary.hasData) return NaN;
  if (normalizedReportType === 'worst') return summary.worst;
  if (normalizedReportType === 'best') return summary.best;
  if (normalizedReportType === 'median') return summary.median;
  return summary.mean;
}

function getErrorBarRange(summary, mode, reportType, axisId) {
  if (!summary?.hasData) return null;
  if (mode === 'none') return null;
  if (mode === 'std') {
    const center = getReportValue(summary, reportType);
    if (
      !Number.isFinite(center) ||
      !Number.isFinite(summary.stdDev) ||
      summary.stdDev <= 0
    ) {
      return null;
    }
    let min = center - summary.stdDev;
    let max = center + summary.stdDev;
    if (METRICS[axisId]?.forceMin !== undefined) {
      min = Math.max(min, METRICS[axisId].forceMin);
    }
    if (METRICS[axisId]?.forceMax !== undefined) {
      max = Math.min(max, METRICS[axisId].forceMax);
    }
    if (METRICS[axisId]?.minClamp !== undefined) {
      min = Math.max(min, METRICS[axisId].minClamp);
      max = Math.max(max, METRICS[axisId].minClamp);
    }
    if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return null;
    return { min, max };
  }
  if (summary.min === summary.max) return null;
  return { min: summary.min, max: summary.max };
}

function renderLegend(points, colorMap) {
  const visibleColorKeys = new Set();
  const visibleOrder = [];
  points.forEach((point) => {
    const colorKey = point.colorModeKey || getColorModeKey(point.pairId, point.language);
    if (!visibleColorKeys.has(colorKey)) {
      visibleColorKeys.add(colorKey);
      visibleOrder.push(colorKey);
    }
  });

  const mapOrder = Array.from(colorMap.keys()).filter((key) => visibleColorKeys.has(key));
  const orderedKeys = mapOrder.length ? mapOrder : visibleOrder;

  orderedKeys.forEach((key, index) => {
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'legend-item';
    const hidden = STATE.hiddenColorKeys.has(key);
    if (hidden) row.classList.add('legend-item-hidden');
    row.setAttribute(
      'aria-pressed',
      hidden ? 'true' : 'false',
    );
    row.title = hidden
      ? 'Click to show this series'
      : 'Click to hide this series';
    const swatch = document.createElement('span');
    swatch.className = 'legend-color';
    swatch.style.background = colorMap.get(key) || PALETTE[index % PALETTE.length];
    row.appendChild(swatch);
    row.appendChild(document.createTextNode(getColorModeLabel(key)));
    row.addEventListener('click', () => {
      if (STATE.hiddenColorKeys.has(key)) {
        STATE.hiddenColorKeys.delete(key);
      } else {
        STATE.hiddenColorKeys.add(key);
      }
      render();
    });
    legendEl.appendChild(row);
  });
}

function getColorModeLabel(key) {
  if (STATE.colorMode === 'agent') return formatAgentDisplay(key);
  if (STATE.colorMode === 'language') return key;
  return formatAgentModelDisplay(key);
}

function drawFrontierConnector(points, frontierSet, xScale, yScale, layer) {
  if (frontierSet.size < 2) return;
  if (isCategoricalXAxis(STATE.xAxis)) return;
  const sorted = Array.from(frontierSet).slice().sort((a, b) => a.xValue - b.xValue);
  const coords = sorted
    .filter((p) => Number.isFinite(p.xValue) && Number.isFinite(p.yValue))
    .map((p) => `${xScale(p.xValue)},${yScale(p.yValue)}`);
  if (coords.length < 2) return;
  const line = createSvgElement('polyline');
  line.setAttribute('class', 'frontier-line');
  line.setAttribute('points', coords.join(' '));
  line.setAttribute('fill', 'none');
  layer.appendChild(line);
}

function computeParetoFrontier(points, xAxis, yAxis) {
  const frontier = new Set();
  if (isCategoricalXAxis(xAxis)) return frontier;
  const xDir = METRICS[xAxis]?.higherIsBetter ? 1 : -1;
  const yDir = METRICS[yAxis]?.higherIsBetter ? 1 : -1;
  const valid = points.filter(
    (p) => Number.isFinite(p.xValue) && Number.isFinite(p.yValue),
  );
  valid.forEach((p) => {
    const dominated = valid.some((q) => {
      if (q === p) return false;
      const xBE = q.xValue * xDir >= p.xValue * xDir;
      const yBE = q.yValue * yDir >= p.yValue * yDir;
      const xSB = q.xValue * xDir > p.xValue * xDir;
      const ySB = q.yValue * yDir > p.yValue * yDir;
      return xBE && yBE && (xSB || ySB);
    });
    if (!dominated) frontier.add(p);
  });
  return frontier;
}

function renderPlot(points) {
  chartEmpty.classList.add('hidden');

  const { width, height } = getChartSize();
  chartSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const margin = { top: 42, right: 34, bottom: 72, left: 88 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const plotLeft = margin.left + AXIS_PADDING.left;
  const plotRight = width - margin.right - AXIS_PADDING.right;
  const plotTop = margin.top + AXIS_PADDING.top;
  const plotBottom = height - margin.bottom - AXIS_PADDING.bottom;
  const plotWidth = Math.max(1, plotRight - plotLeft);
  const plotHeight = Math.max(1, plotBottom - plotTop);
  const innerHeightWithPad = Math.max(1, innerHeight - AXIS_PADDING.top - AXIS_PADDING.bottom);
  const innerWidthWithPad = Math.max(1, innerWidth - AXIS_PADDING.left - AXIS_PADDING.right);

  const xDomain = buildDomain(points, STATE.xAxis);
  const yDomain = buildDomain(points, STATE.yAxis);
  const xCategories = getSelectedAxisCategories(STATE.xAxis);
  const xScale = createXScale(xDomain, xCategories, plotLeft, plotRight);
  const yScale = createYScale(yDomain, plotTop, plotHeight);

  const panel = createSvgElement('rect');
  panel.setAttribute('class', 'chart-bg-panel');
  panel.setAttribute('x', String(plotLeft));
  panel.setAttribute('y', String(plotTop));
  panel.setAttribute('width', String(plotWidth));
  panel.setAttribute('height', String(plotHeight));
  panel.setAttribute('rx', '8');
  panel.setAttribute('ry', '8');
  chartSvg.appendChild(panel);

  drawAxes({
    innerWidth: innerWidthWithPad,
    innerHeight: innerHeightWithPad,
    plotLeft,
    plotRight,
    plotTop,
    plotBottom,
    xScale,
    yScale,
    xDomain,
    yDomain,
    xCategories,
  });

  const defs = createSvgElement('defs');
  const clipPath = createSvgElement('clipPath');
  clipPath.setAttribute('id', 'plot-clip');
  const clipRect = createSvgElement('rect');
  clipRect.setAttribute('x', String(plotLeft));
  clipRect.setAttribute('y', String(plotTop));
  clipRect.setAttribute('width', String(plotWidth));
  clipRect.setAttribute('height', String(plotHeight));
  clipPath.appendChild(clipRect);
  defs.appendChild(clipPath);
  chartSvg.appendChild(defs);

  const dataLayer = createSvgElement('g');
  dataLayer.setAttribute('clip-path', 'url(#plot-clip)');
  const labelsLayer = createSvgElement('g');
  labelsLayer.setAttribute('class', 'labels-layer');
  const markerLabels = [];
  const errorBarLines = [];
  const labelMode = normalizeLabelMode(STATE.labelMode);

  const frontierSet = computeParetoFrontier(points, STATE.xAxis, STATE.yAxis);
  drawFrontierConnector(points, frontierSet, xScale, yScale, dataLayer);

  points.forEach((point) => {
    const isOnFrontier = frontierSet.has(point);
    const baseRadius = 7.3;
    const hoverRadius = 8.8;

    const x = point.xAsCategory
      ? xScale(xCategories.indexOf(point.xCategoryValue))
      : xScale(point.xValue);
    const y = yScale(point.yValue);

    const g = createSvgElement('g');
    g.setAttribute('transform', `translate(${x}, ${y})`);

    const canShowErrorBars =
      !isCategoricalXAxis(STATE.xAxis) && STATE.errorBarMode !== 'none';
    const xBarRange = canShowErrorBars
      ? getErrorBarRange(point.xSummary, STATE.errorBarMode, STATE.reportType, STATE.xAxis)
      : null;
    const yBarRange = canShowErrorBars
      ? getErrorBarRange(point.ySummary, STATE.errorBarMode, STATE.reportType, STATE.yAxis)
      : null;

    if (!point.xAsCategory && xBarRange) {
      const left = xScale(xBarRange.min);
      const right = xScale(xBarRange.max);
      const rangeLine = createSvgElement('line');
      rangeLine.setAttribute('class', 'point-range-h');
      rangeLine.setAttribute('x1', String(left - x));
      rangeLine.setAttribute('x2', String(right - x));
      rangeLine.setAttribute('y1', '0');
      rangeLine.setAttribute('y2', '0');
      g.appendChild(rangeLine);
      errorBarLines.push({ x1: left, y1: y, x2: right, y2: y });
    }

    if (yBarRange) {
      const top = yScale(yBarRange.max);
      const bottom = yScale(yBarRange.min);
      const rangeLine = createSvgElement('line');
      rangeLine.setAttribute('class', 'point-range-v');
      rangeLine.setAttribute('x1', '0');
      rangeLine.setAttribute('x2', '0');
      rangeLine.setAttribute('y1', String(top - y));
      rangeLine.setAttribute('y2', String(bottom - y));
      g.appendChild(rangeLine);
      errorBarLines.push({ x1: x, y1: top, x2: x, y2: bottom });
    }

    if (point.xSummary.stacked || point.ySummary.stacked) {
      addTokenStackGlyph(g, point);
    }

    const pointCircle = createSvgElement('circle');
    pointCircle.setAttribute('r', String(baseRadius));
    pointCircle.setAttribute('fill', point.color);
    const pointClass = isOnFrontier
      ? 'point point-marker point-frontier'
      : 'point point-marker';
    pointCircle.setAttribute('class', pointClass);
    pointCircle.setAttribute('data-base-radius', String(baseRadius));
    pointCircle.setAttribute('tabindex', '0');
    pointCircle.setAttribute('role', 'img');
    pointCircle.setAttribute('aria-label', buildMarkerAriaLabel(point));
    g.appendChild(pointCircle);

    const label = createSvgElement('text');
    const shouldPlaceLabel =
      labelMode === 'all' || (labelMode === 'pareto' && isOnFrontier);
    const fullLabel = point.pairLabel || rowPairId(point.pairId);
    const labelText = formatAgentModelDisplay(fullLabel);
    const labelClass = shouldPlaceLabel
      ? `point-label point-label-persistent${isOnFrontier ? ' point-label-frontier' : ''}`
      : 'point-label point-label-hover';
    label.setAttribute('class', labelClass);
    label.setAttribute('pointer-events', 'none');
    setPointLabelText(label, labelText);
    if (!shouldPlaceLabel) {
      label.setAttribute('visibility', 'hidden');
    }
    const leader = createSvgElement('line');
    leader.setAttribute('class', 'point-leader');
    leader.setAttribute('visibility', 'hidden');
    labelsLayer.appendChild(label);
    labelsLayer.appendChild(leader);

    const showTooltipAt = (clientX, clientY) => {
      tooltip.style.display = 'block';
      tooltip.innerHTML = buildTooltip(point);
      const rect = chartSvg.getBoundingClientRect();
      const tooltipX = clientX - rect.left + 12;
      const tooltipY = clientY - rect.top + 12;
      const tooltipWidth = tooltip.offsetWidth || 280;
      const tooltipHeight = tooltip.offsetHeight || 160;
      tooltip.style.left = `${Math.max(8, Math.min(tooltipX, rect.width - tooltipWidth - 8))}px`;
      tooltip.style.top = `${Math.max(8, Math.min(tooltipY, rect.height - tooltipHeight - 8))}px`;
    };
    const onPointer = (event) => showTooltipAt(event.clientX, event.clientY);
    const markerCenter = () => {
      const mRect = pointCircle.getBoundingClientRect();
      return [mRect.left + mRect.width / 2, mRect.top + mRect.height / 2];
    };

    const showMarker = () => {
      pointCircle.classList.add('active');
      pointCircle.setAttribute('r', String(hoverRadius));
      if (!shouldPlaceLabel) {
        setLabelPosition(label, x + baseRadius + 6, y - baseRadius - 4, 'start', 'middle');
        label.setAttribute('visibility', 'visible');
      }
    };
    const hideMarker = () => {
      tooltip.style.display = 'none';
      pointCircle.classList.remove('active');
      pointCircle.setAttribute('r', pointCircle.getAttribute('data-base-radius') || String(baseRadius));
      if (!shouldPlaceLabel) {
        label.setAttribute('visibility', 'hidden');
      }
    };

    const onPointerEnter = (event) => {
      showMarker();
      onPointer(event);
    };
    const onFocus = () => {
      showMarker();
      const [cx, cy] = markerCenter();
      showTooltipAt(cx, cy);
    };
    pointCircle.addEventListener('pointerenter', onPointerEnter);
    pointCircle.addEventListener('pointermove', onPointer);
    pointCircle.addEventListener('pointerleave', hideMarker);
    pointCircle.addEventListener('focus', onFocus);
    pointCircle.addEventListener('focusin', onFocus);
    pointCircle.addEventListener('blur', hideMarker);
    pointCircle.addEventListener('focusout', hideMarker);

    dataLayer.appendChild(g);

    if (shouldPlaceLabel) {
      markerLabels.push({
        point,
        x,
        y,
        circle: pointCircle,
        label,
        labelText,
        leader,
        isOnFrontier,
      });
    }
  });

  chartSvg.appendChild(dataLayer);
  chartSvg.appendChild(labelsLayer);

  placePointLabels(markerLabels, {
    errorBarLines,
    width,
    height,
    margin,
  });

  const xLabel = createSvgElement('text');
  xLabel.setAttribute('x', String(width / 2));
  xLabel.setAttribute('y', String(height - 20));
  xLabel.setAttribute('text-anchor', 'middle');
  xLabel.setAttribute('class', 'axis-title');
  xLabel.textContent = getAxisMeta(STATE.xAxis).label;
  chartSvg.appendChild(xLabel);

  const yLabel = createSvgElement('text');
  yLabel.setAttribute('x', '20');
  yLabel.setAttribute('y', String(height / 2));
  yLabel.setAttribute('text-anchor', 'middle');
  yLabel.setAttribute('class', 'axis-title');
  yLabel.setAttribute('transform', `rotate(-90 20 ${height / 2})`);
  yLabel.textContent = getAxisMeta(STATE.yAxis).label;
  chartSvg.appendChild(yLabel);

  function addTokenStackGlyph(pointGroup, point) {
    const s = point.xSummary.stacked ? point.xSummary : point.ySummary;
    const total = s.meanInput + s.meanOutput;
    if (!Number.isFinite(total) || total <= 0) return;

    const width = 16;
    const height = 12;
    const inputHeight = Math.max(2, Math.round((s.meanInput / total) * height));
    const outputHeight = Math.max(2, height - inputHeight);
    const x = -width / 2 - 1;
    const y = -height / 2;

    const top = createSvgElement('rect');
    top.setAttribute('x', String(x));
    top.setAttribute('y', String(y));
    top.setAttribute('width', String(width));
    top.setAttribute('height', String(inputHeight));
    top.setAttribute('fill', '#8b5cf6');
    top.setAttribute('stroke', '#4a2db8');
    top.setAttribute('stroke-width', '0.6');
    pointGroup.appendChild(top);

    const bottom = createSvgElement('rect');
    bottom.setAttribute('x', String(x));
    bottom.setAttribute('y', String(y + inputHeight));
    bottom.setAttribute('width', String(width));
    bottom.setAttribute('height', String(outputHeight));
    bottom.setAttribute('fill', '#06b6d4');
    bottom.setAttribute('stroke', '#0b5c73');
    bottom.setAttribute('stroke-width', '0.6');
    pointGroup.appendChild(bottom);
  }
}

function placePointLabels(markers, { errorBarLines = [], width, height, margin }) {
  if (!markers.length) return;

  const panelBounds = {
    minX: margin.left + 6,
    maxX: width - margin.right - 6,
    minY: margin.top + 6,
    maxY: height - 42,
  };
  const padding = 4;
  const pointClearance = 4;
  const placedBoxes = [];
  const placedLeaderLines = [];
  const candidates = buildLabelCandidates();
  const preparedMarkers = markers.map((marker, index) => {
    const { point, x, y, label, leader } = marker;
    const baseRadius = Number.parseFloat(marker.circle.getAttribute('data-base-radius')) || 7;
    const text = marker.labelText || point.pairLabel || rowPairId(point.pairId);
    setPointLabelText(label, text);
    label.setAttribute('visibility', 'hidden');
    setLabelPosition(label, 0, 0, 'start', 'middle');
    leader.setAttribute('visibility', 'hidden');
    leader.setAttribute('x1', '0');
    leader.setAttribute('y1', '0');
    leader.setAttribute('x2', '0');
    leader.setAttribute('y2', '0');

    const layouts = candidates
      .map((candidate) => measureLabelCandidate(marker, candidate, {
        baseRadius,
        errorBarLines,
        padding,
        panelBounds,
        pointClearance,
      }))
      .filter(Boolean)
      .sort((a, b) => a.score - b.score);

    return {
      edgePressure: computeLabelEdgePressure(x, y, panelBounds),
      index,
      layouts,
      marker,
    };
  });

  const remaining = [...preparedMarkers];
  while (remaining.length) {
    let nextIndex = -1;
    let nextLayout = null;
    let nextAvailableLayouts = null;

    remaining.forEach((item, index) => {
      const availableLayouts = getAvailableLabelLayouts(item, placedBoxes, placedLeaderLines);
      if (!availableLayouts.length) return;

      if (
        nextLayout === null ||
        compareDynamicLabelChoice(
          item,
          availableLayouts,
          remaining[nextIndex],
          nextAvailableLayouts,
        ) < 0
      ) {
        nextIndex = index;
        nextAvailableLayouts = availableLayouts;
        nextLayout = availableLayouts[0];
      }
    });

    if (nextIndex === -1 || nextLayout === null) break;

    const [{ marker }] = remaining.splice(nextIndex, 1);
    const layout = nextLayout;
    if (!layout) return;

    const { label, leader, x, y } = marker;
    setLabelPosition(label, layout.x, layout.y, layout.anchor, layout.baseline);
    label.setAttribute('visibility', 'visible');

    const endpoint = closestPointOnRect({ x, y }, layout.textBox);
    leader.setAttribute('x1', String(x));
    leader.setAttribute('y1', String(y));
    leader.setAttribute('x2', String(endpoint.x));
    leader.setAttribute('y2', String(endpoint.y));
    leader.setAttribute('visibility', 'visible');

    placedBoxes.push(layout.bbox);
    placedLeaderLines.push(layout.leaderLine);
  }
}

function getAvailableLabelLayouts(item, placedBoxes, placedLeaderLines) {
  return item.layouts
    .filter((layout) => !intersectsAnyRect(layout.bbox, placedBoxes))
    .map((layout) => ({
      ...layout,
      score: layout.score + scoreLayoutAgainstPlaced(layout, placedBoxes, placedLeaderLines),
    }))
    .sort((a, b) => a.score - b.score);
}

function scoreLayoutAgainstPlaced(layout, placedBoxes, placedLeaderLines) {
  return (
    scoreRectLineIntersections(layout.bbox, placedLeaderLines, LABEL_LEADER_PENALTY) +
    scoreSegmentRectIntersections(layout.leaderLine, placedBoxes, LEADER_LABEL_PENALTY) +
    scoreSegmentLineIntersections(layout.leaderLine, placedLeaderLines, LEADER_CROSSING_PENALTY)
  );
}

function buildLabelCandidates() {
  const directions = [
    { x: 1, y: 0, anchor: 'start', baseline: 'middle' },
    { x: -1, y: 0, anchor: 'end', baseline: 'middle' },
    { x: 0, y: -1, anchor: 'middle', baseline: 'text-after-edge' },
    { x: 0, y: 1, anchor: 'middle', baseline: 'text-before-edge' },
    { x: 0.82, y: -0.82, anchor: 'start', baseline: 'text-after-edge' },
    { x: -0.82, y: -0.82, anchor: 'end', baseline: 'text-after-edge' },
    { x: 0.82, y: 0.82, anchor: 'start', baseline: 'text-before-edge' },
    { x: -0.82, y: 0.82, anchor: 'end', baseline: 'text-before-edge' },
  ];
  const distances = [22, 34, 48, 64, 84, 110, 142, 180];
  const candidates = [];
  distances.forEach((distance, distanceIndex) => {
    directions.forEach((direction, directionIndex) => {
      candidates.push({
        dx: direction.x * distance,
        dy: direction.y * distance,
        anchor: direction.anchor,
        baseline: direction.baseline,
        score: distanceIndex * 100 + directionIndex * 8 + distance * 0.25,
      });
    });
  });
  return candidates;
}

function compareDynamicLabelChoice(a, aAvailableLayouts, b, bAvailableLayouts) {
  if (!b || !bAvailableLayouts) return -1;

  const availability = aAvailableLayouts.length - bAvailableLayouts.length;
  if (availability !== 0) return availability;

  const edgePressure = b.edgePressure - a.edgePressure;
  if (edgePressure !== 0) return edgePressure;

  const frontierPriority =
    Number(Boolean(b.marker.isOnFrontier)) - Number(Boolean(a.marker.isOnFrontier));
  if (frontierPriority !== 0) return frontierPriority;

  const scoreDelta = aAvailableLayouts[0].score - bAvailableLayouts[0].score;
  if (scoreDelta !== 0) return scoreDelta;

  return a.index - b.index;
}

function computeLabelEdgePressure(x, y, bounds) {
  const left = Math.max(1, x - bounds.minX);
  const right = Math.max(1, bounds.maxX - x);
  const top = Math.max(1, y - bounds.minY);
  const bottom = Math.max(1, bounds.maxY - y);
  return 1 / Math.min(left, right) + 1 / Math.min(top, bottom);
}

function measureLabelCandidate(marker, candidate, {
  baseRadius,
  errorBarLines,
  padding,
  panelBounds,
  pointClearance,
}) {
  const { label, x, y } = marker;
  setLabelPosition(label, x + candidate.dx, y + candidate.dy, candidate.anchor, candidate.baseline);

  let bbox = label.getBBox();
  if (bbox.width === 0 || bbox.height === 0) return null;

  const maxLeft = panelBounds.maxX - bbox.width;
  const maxTop = panelBounds.maxY - bbox.height;
  if (maxLeft < panelBounds.minX || maxTop < panelBounds.minY) return null;

  const anchorOffsetX = getAnchorOffsetX(candidate.anchor, bbox.width);
  const anchorOffsetY = getAnchorOffsetY(candidate.baseline, bbox.height);
  const clampedLeft = Math.max(panelBounds.minX, Math.min(maxLeft, bbox.x));
  const clampedTop = Math.max(panelBounds.minY, Math.min(maxTop, bbox.y));
  const shift = Math.abs(clampedLeft - bbox.x) + Math.abs(clampedTop - bbox.y);
  const finalX = clampedLeft + anchorOffsetX;
  const finalY = clampedTop + anchorOffsetY;

  if (shift > 0) {
    setLabelPosition(label, finalX, finalY, candidate.anchor, candidate.baseline);
    bbox = label.getBBox();
    if (bbox.width === 0 || bbox.height === 0) return null;
  }

  if (!rectWithinBounds(bbox, panelBounds)) return null;

  const inflated = inflateRect(bbox, padding);
  const textBox = {
    x: bbox.x,
    y: bbox.y,
    width: bbox.width,
    height: bbox.height,
  };
  const endpoint = closestPointOnRect({ x, y }, textBox);
  const leaderLine = { x1: x, y1: y, x2: endpoint.x, y2: endpoint.y };
  if (scoreRectLineIntersections(inflateRect(textBox, LABEL_LINE_CLEARANCE), errorBarLines, 1) > 0) {
    return null;
  }
  const markerOverlapPenalty = rectIntersectsPoint(inflated, x, y, baseRadius + pointClearance)
    ? 600
    : 0;
  const errorBarPenalty =
    scoreSegmentLineIntersections(leaderLine, errorBarLines, LEADER_ERROR_BAR_PENALTY);

  return {
    x: finalX,
    y: finalY,
    anchor: candidate.anchor,
    baseline: candidate.baseline,
    leaderLine,
    textBox,
    bbox: inflated,
    score: candidate.score + shift * 4 + markerOverlapPenalty + errorBarPenalty,
  };
}

function rectWithinBounds(rect, bounds) {
  return (
    rect.x >= bounds.minX &&
    rect.y >= bounds.minY &&
    rect.x + rect.width <= bounds.maxX &&
    rect.y + rect.height <= bounds.maxY
  );
}

function setPointLabelText(label, text) {
  const lines = getPointLabelLines(text);
  label.replaceChildren();
  if (lines.length <= 1) {
    label.textContent = lines[0] || '';
    return;
  }

  const x = label.getAttribute('x') || '0';
  lines.forEach((line, index) => {
    const tspan = createSvgElement('tspan');
    tspan.textContent = line;
    tspan.setAttribute('x', x);
    if (index > 0) {
      tspan.setAttribute('dy', '1.08em');
    }
    label.appendChild(tspan);
  });
}

function getPointLabelLines(text) {
  const normalized = String(text || '');
  if (normalized.length <= POINT_LABEL_WRAP_LENGTH) return [normalized];

  const pairParts = normalized.split(' / ');
  if (pairParts.length >= 2) {
    const agent = pairParts.shift();
    const model = pairParts.join(' / ');
    return [agent, ...wrapLabelSegment(model)];
  }
  return wrapLabelSegment(normalized);
}

function wrapLabelSegment(segment) {
  if (segment.length <= POINT_LABEL_WRAP_LENGTH) return [segment];

  const lines = [];
  let current = '';
  segment.split('/').forEach((part) => {
    const next = current ? `${current}/${part}` : part;
    if (next.length <= POINT_LABEL_WRAP_LENGTH) {
      current = next;
      return;
    }
    if (current) lines.push(current);
    if (part.length <= POINT_LABEL_WRAP_LENGTH) {
      current = part;
    } else {
      lines.push(...splitLongLabelToken(part));
      current = '';
    }
  });
  if (current) lines.push(current);
  return lines.length ? lines : [segment];
}

function splitLongLabelToken(token) {
  const chunks = [];
  for (let i = 0; i < token.length; i += POINT_LABEL_WRAP_LENGTH) {
    chunks.push(token.slice(i, i + POINT_LABEL_WRAP_LENGTH));
  }
  return chunks;
}

function setLabelPosition(label, x, y, anchor, baseline) {
  label.setAttribute('x', String(x));
  label.setAttribute('y', String(y));
  label.setAttribute('text-anchor', anchor);
  label.setAttribute('dominant-baseline', baseline);
  label.querySelectorAll('tspan').forEach((tspan) => {
    tspan.setAttribute('x', String(x));
  });
}

function getAnchorOffsetX(anchor, width) {
  if (anchor === 'middle') return width / 2;
  if (anchor === 'end') return width;
  return 0;
}

function getAnchorOffsetY(baseline, height) {
  if (baseline === 'middle') return height / 2;
  if (baseline === 'text-after-edge') return height;
  return 0;
}

function inflateRect(rect, pad) {
  return {
    x: rect.x - pad,
    y: rect.y - pad,
    width: rect.width + pad * 2,
    height: rect.height + pad * 2,
  };
}

function intersectsAnyRect(candidate, existing) {
  return existing.some((existingRect) => rectsOverlap(candidate, existingRect));
}

function scoreRectLineIntersections(rect, lines, penalty) {
  return lines.reduce(
    (score, line) => score + (lineIntersectsRect(line, rect) ? penalty : 0),
    0,
  );
}

function scoreSegmentRectIntersections(line, rects, penalty) {
  return rects.reduce(
    (score, rect) => score + (lineIntersectsRect(line, rect) ? penalty : 0),
    0,
  );
}

function scoreSegmentLineIntersections(line, lines, penalty) {
  return lines.reduce(
    (score, other) => score + (segmentsIntersect(line, other) ? penalty : 0),
    0,
  );
}

function rectsOverlap(a, b) {
  return !(
    a.x + a.width < b.x ||
    a.x > b.x + b.width ||
    a.y + a.height < b.y ||
    a.y > b.y + b.height
  );
}

function lineIntersectsRect(line, rect) {
  if (
    pointInRect(line.x1, line.y1, rect) ||
    pointInRect(line.x2, line.y2, rect)
  ) {
    return true;
  }

  const left = rect.x;
  const right = rect.x + rect.width;
  const top = rect.y;
  const bottom = rect.y + rect.height;
  return (
    segmentsIntersect(line, { x1: left, y1: top, x2: right, y2: top }) ||
    segmentsIntersect(line, { x1: right, y1: top, x2: right, y2: bottom }) ||
    segmentsIntersect(line, { x1: right, y1: bottom, x2: left, y2: bottom }) ||
    segmentsIntersect(line, { x1: left, y1: bottom, x2: left, y2: top })
  );
}

function pointInRect(x, y, rect) {
  return (
    x >= rect.x &&
    x <= rect.x + rect.width &&
    y >= rect.y &&
    y <= rect.y + rect.height
  );
}

function segmentsIntersect(a, b) {
  const o1 = segmentOrientation(a.x1, a.y1, a.x2, a.y2, b.x1, b.y1);
  const o2 = segmentOrientation(a.x1, a.y1, a.x2, a.y2, b.x2, b.y2);
  const o3 = segmentOrientation(b.x1, b.y1, b.x2, b.y2, a.x1, a.y1);
  const o4 = segmentOrientation(b.x1, b.y1, b.x2, b.y2, a.x2, a.y2);

  if (o1 !== o2 && o3 !== o4) return true;
  if (o1 === 0 && pointOnSegment(b.x1, b.y1, a)) return true;
  if (o2 === 0 && pointOnSegment(b.x2, b.y2, a)) return true;
  if (o3 === 0 && pointOnSegment(a.x1, a.y1, b)) return true;
  if (o4 === 0 && pointOnSegment(a.x2, a.y2, b)) return true;
  return false;
}

function segmentOrientation(ax, ay, bx, by, cx, cy) {
  const value = (by - ay) * (cx - bx) - (bx - ax) * (cy - by);
  if (Math.abs(value) < 0.0001) return 0;
  return value > 0 ? 1 : 2;
}

function pointOnSegment(x, y, line) {
  return (
    x <= Math.max(line.x1, line.x2) + 0.0001 &&
    x >= Math.min(line.x1, line.x2) - 0.0001 &&
    y <= Math.max(line.y1, line.y2) + 0.0001 &&
    y >= Math.min(line.y1, line.y2) - 0.0001
  );
}

function rectIntersectsPoint(rect, pointX, pointY, radius) {
  const cx = Math.max(rect.x, Math.min(pointX, rect.x + rect.width));
  const cy = Math.max(rect.y, Math.min(pointY, rect.y + rect.height));
  const dx = pointX - cx;
  const dy = pointY - cy;
  return dx * dx + dy * dy < radius * radius;
}

function closestPointOnRect(point, rect) {
  return {
    x: Math.max(rect.x, Math.min(point.x, rect.x + rect.width)),
    y: Math.max(rect.y, Math.min(point.y, rect.y + rect.height)),
  };
}

function drawAxes({
  innerWidth,
  innerHeight,
  plotLeft,
  plotRight,
  plotTop,
  plotBottom,
  xScale,
  yScale,
  xDomain,
  yDomain,
  xCategories,
}) {
  const xAxisY = plotBottom;
  const xAxisLeft = typeof xScale.axisLeft === 'number' ? xScale.axisLeft : plotLeft;
  const xAxisRight = typeof xScale.axisRight === 'number' ? xScale.axisRight : plotRight;
  const yAxisX = xAxisLeft;
  const yTicks = buildNiceAxisTicks(
    yDomain.min,
    yDomain.max,
    AXIS_TICK_SEGMENTS,
    STATE.yAxis,
  );
  const xTicks =
    isCategoricalXAxis(STATE.xAxis)
      ? xCategories.map((_, index) => index)
      : buildNiceAxisTicks(xDomain.min, xDomain.max, AXIS_TICK_SEGMENTS, STATE.xAxis);
  const safeYTicks = yTicks.length ? yTicks : [yDomain.min, yDomain.max];
  const safeXTicks = xTicks.length ? xTicks : [xDomain.min, xDomain.max];

  for (let i = 0; i < safeYTicks.length; i++) {
    const value = safeYTicks[i];
    const y = yScale(value);
    const line = createSvgElement('line');
    line.setAttribute('x1', String(xAxisLeft));
    line.setAttribute('x2', String(xAxisRight));
    line.setAttribute('y1', String(y));
    line.setAttribute('y2', String(y));
    line.setAttribute('class', 'tick-line');
    chartSvg.appendChild(line);

    const label = createSvgElement('text');
    label.setAttribute('x', String(yAxisX - 10));
    label.setAttribute('y', String(y + 4));
    label.setAttribute('text-anchor', 'end');
    label.setAttribute('class', 'axis-text');
    label.textContent = formatAxisValue(STATE.yAxis, value);
    chartSvg.appendChild(label);
  }

  for (let i = 0; i < safeXTicks.length; i++) {
    const value = safeXTicks[i];
    const x = xScale(value);
    const line = createSvgElement('line');
    line.setAttribute('x1', String(x));
    line.setAttribute('x2', String(x));
    line.setAttribute('y1', String(plotTop));
    line.setAttribute('y2', String(plotBottom));
    line.setAttribute('class', 'tick-line');
    chartSvg.appendChild(line);
  }

  const yAxisLine = createSvgElement('line');
  yAxisLine.setAttribute('x1', String(yAxisX));
  yAxisLine.setAttribute('x2', String(yAxisX));
  yAxisLine.setAttribute('y1', String(plotTop));
  yAxisLine.setAttribute('y2', String(plotBottom));
  yAxisLine.setAttribute('class', 'axis-line');
  chartSvg.appendChild(yAxisLine);

  const xAxisLine = createSvgElement('line');
  xAxisLine.setAttribute('x1', String(xAxisLeft));
  xAxisLine.setAttribute('x2', String(xAxisRight));
  xAxisLine.setAttribute('y1', String(xAxisY));
  xAxisLine.setAttribute('y2', String(xAxisY));
  xAxisLine.setAttribute('class', 'axis-line');
  chartSvg.appendChild(xAxisLine);

  if (isCategoricalXAxis(STATE.xAxis)) {
    xCategories.forEach((category) => {
      const x = xScale(xCategories.indexOf(category));
      const tick = createSvgElement('line');
      tick.setAttribute('x1', String(x));
      tick.setAttribute('x2', String(x));
      tick.setAttribute('y1', String(xAxisY));
      tick.setAttribute('y2', String(xAxisY + 6));
      tick.setAttribute('stroke', '#8b96b5');
      chartSvg.appendChild(tick);
      const text = createSvgElement('text');
      text.setAttribute('x', String(x));
      text.setAttribute('y', String(xAxisY + 24));
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('class', 'axis-text');
      text.textContent = category;
      chartSvg.appendChild(text);
    });
  } else {
    for (let i = 0; i < safeXTicks.length; i++) {
      const value = safeXTicks[i];
      const x = xScale(value);
      const tick = createSvgElement('line');
      tick.setAttribute('x1', String(x));
      tick.setAttribute('x2', String(x));
      tick.setAttribute('y1', String(xAxisY));
      tick.setAttribute('y2', String(xAxisY + 6));
      tick.setAttribute('stroke', '#8b96b5');
      chartSvg.appendChild(tick);
      const text = createSvgElement('text');
      text.setAttribute('x', String(x));
      text.setAttribute('y', String(xAxisY + 24));
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('class', 'axis-text');
      text.textContent = formatAxisValue(STATE.xAxis, value);
      chartSvg.appendChild(text);
    }
  }
}

function buildDomain(points, axisId) {
  if (isCategoricalXAxis(axisId)) {
    const count = getSelectedAxisCategories(axisId).length;
    if (count <= 1) return { min: 0, max: 1 };
    return { min: 0, max: count - 1 };
  }

  const summaries = points
    .map((point) => (axisId === STATE.xAxis ? point.xSummary : point.ySummary))
    .filter((summary) => summary?.hasData);
  if (!summaries.length) return { min: 0, max: 1 };

  let min = Math.min(...summaries.map((summary) => summary.min));
  let max = Math.max(...summaries.map((summary) => summary.max));
  if (!Number.isFinite(min) || !Number.isFinite(max)) return { min: 0, max: 1 };

  ({ min, max } = applyDomainPadding(min, max, axisId));

  if (axisId === 'percent') {
    min = 0;
    max = 100;
  } else {
    if (METRICS[axisId]?.forceMin !== undefined) {
      min = METRICS[axisId].forceMin;
    }
    if (METRICS[axisId]?.forceMax !== undefined) {
      max = METRICS[axisId].forceMax;
    }
  }
  if (METRICS[axisId]?.minClamp !== undefined) {
    const minClamp = METRICS[axisId].minClamp;
    min = Math.max(min, minClamp);
    max = Math.max(max, minClamp);
  }

  const minClamp = METRICS[axisId]?.minClamp;
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    const spanPad = Math.max(
      AXIS_DOMAIN_MIN_PADDING,
      Math.abs(min || 0) * AXIS_DOMAIN_PADDING_FRACTION,
    );
    if (Number.isFinite(minClamp)) {
      const clampedMin = Math.max(min, minClamp);
      return {
        min: clampedMin,
        max: Math.max(clampedMin + spanPad, max + spanPad),
      };
    }

    const pad = Math.max(1, Math.abs(min || 0) * 0.2);
    return { min: min - pad, max: max + pad };
  }
  return { min, max };
}

function applyDomainPadding(min, max, axisId) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return { min: 0, max: 1 };
  }

  if (METRICS[axisId]?.forceMin !== undefined) {
    min = Math.max(min, METRICS[axisId].forceMin);
  }
  if (METRICS[axisId]?.forceMax !== undefined) {
    max = Math.min(max, METRICS[axisId].forceMax);
  }
  if (min > max) {
    return { min: 0, max: 1 };
  }

  if (min === max) {
    const pad = Math.max(AXIS_DOMAIN_MIN_PADDING, Math.abs(min || 0) * 0.2);
    return { min: min - pad, max: max + pad };
  }

  const span = max - min;
  if (!(span > 0)) {
    return { min: min - AXIS_DOMAIN_MIN_PADDING, max: max + AXIS_DOMAIN_MIN_PADDING };
  }

  const fractionPad = Math.max(
    AXIS_DOMAIN_MIN_PADDING,
    span * AXIS_DOMAIN_PADDING_FRACTION,
  );
  const paddedMin = min - fractionPad;
  const paddedMax = max + fractionPad;
  const hasForcedMin = METRICS[axisId]?.forceMin !== undefined;
  const hasForcedMax = METRICS[axisId]?.forceMax !== undefined;
  return {
    min: hasForcedMin ? METRICS[axisId].forceMin : paddedMin,
    max: hasForcedMax ? METRICS[axisId].forceMax : paddedMax,
  };
}

function buildNiceAxisTicks(min, max, segmentCount, axisId) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (max < min) {
    [min, max] = [max, min];
  }

  const segments = Math.max(1, Number.isFinite(segmentCount) ? segmentCount : AXIS_TICK_SEGMENTS);
  const span = max - min;
  if (!(span > 0)) {
    const defaultSpan = Math.max(AXIS_DOMAIN_MIN_PADDING, Math.abs(min || 0) * 0.2);
    const paddedMin = min - defaultSpan;
    const paddedMax = max + defaultSpan;
    return buildNiceAxisTicks(paddedMin, paddedMax, segments, axisId);
  }

  const rawStep = span / segments;
  const configuredMinTick = Number.isFinite(METRICS[axisId]?.minTickStep)
    ? METRICS[axisId].minTickStep
    : 0;
  const step = Math.max(niceStep(rawStep), configuredMinTick);
  const first = Math.floor(min / step) * step;
  const last = Math.ceil(max / step) * step;
  const ticks = [];
  for (let current = first; current <= last + 1e-12; current += step) {
    ticks.push(fixFloat(current));
  }

  return ticks;
}

function niceStep(value) {
  if (!Number.isFinite(value) || value <= 0) return 1;
  const base = Math.pow(10, Math.floor(Math.log10(value)));
  const fraction = value / base;
  const niceFractions = [1, 2, 5, 10];

  for (let i = 0; i < niceFractions.length; i += 1) {
    const step = niceFractions[i] * base;
    if (step >= value) {
      return step;
    }
  }

  return base * 10;
}

function fixFloat(value) {
  return Number.parseFloat(value.toFixed(12));
}

function getCategoryAxisSpan(plotLeft, plotRight, categories) {
  const totalSpan = plotRight - plotLeft;
  if (!categories.length || categories.length <= 1 || totalSpan <= 0) {
    return { left: plotLeft, right: plotRight };
  }

  const left = plotLeft + CATEGORY_AXIS_X_PADDING;
  const right = plotRight - CATEGORY_AXIS_X_PADDING;
  if (right <= left) return { left: plotLeft, right: plotRight };

  return { left, right };
}

function createXScale(domain, categories, plotLeft, plotRight) {
  const left = plotLeft;
  const right = plotRight;

  if (isCategoricalXAxis(STATE.xAxis)) {
    const { left: paddedLeft, right: paddedRight } = getCategoryAxisSpan(plotLeft, plotRight, categories);
    const scale = (value) => {
      if (!categories.length) return (left + right) / 2;
      if (categories.length === 1) return (left + right) / 2;
      if (paddedRight <= paddedLeft) return (left + right) / 2;

      const clamped = Math.min(
        Math.max(Number(value), 0),
        categories.length - 1,
      );
      return paddedLeft + (clamped / (categories.length - 1)) * (paddedRight - paddedLeft);
    };
    scale.axisLeft = paddedLeft;
    scale.axisRight = paddedRight;
    return scale;
  }

  return (value) => {
    if (!Number.isFinite(value)) return (left + right) / 2;
    if (domain.max === domain.min) return (left + right) / 2;
    const safe = Math.min(domain.max, Math.max(domain.min, value));
    return left + ((safe - domain.min) / (domain.max - domain.min)) * (right - left);
  };
}

function createYScale(domain, plotTop, plotHeight) {
  const top = plotTop;
  const height = plotHeight;
  return (value) => {
    if (!Number.isFinite(value)) return top + height / 2;
    if (domain.max === domain.min) return top + height / 2;
    const safe = Math.min(domain.max, Math.max(domain.min, value));
    return top + ((domain.max - safe) / (domain.max - domain.min)) * height;
  };
}

function getAxisMeta(axisId) {
  if (axisId === 'language') return { label: 'Language' };
  if (axisId === 'eval') return { label: 'Eval' };
  return METRICS[axisId] || { label: axisId };
}

function formatAxisValue(axisId, value) {
  if (!Number.isFinite(value)) return 'n/a';
  if (axisId === 'percent') return `${value.toFixed(1)}%`;
  if (axisId === 'tokens_input' || axisId === 'tokens_output' || axisId === 'tokens_total') {
    return formatTokenCount(value);
  }
  if (axisId === 'wall') return formatWallTime(value);
  if (axisId === 'loc') return formatLocCount(value);
  if (axisId === 'tools' || axisId === 'files') return formatCount(value);
  if (axisId === 'cost') return formatMoney(value);
  return String(value.toFixed(2));
}

function formatAxisValueWithDecimalPlaces(axisId, value, decimalPlaces) {
  if (!Number.isFinite(value)) return 'n/a';
  if (axisId === 'percent') return `${formatNumberAtDecimalPlaces(value, decimalPlaces)}%`;
  if (axisId === 'tokens_input' || axisId === 'tokens_output' || axisId === 'tokens_total') {
    return formatTokenCountAtDecimalPlaces(value, decimalPlaces);
  }
  if (axisId === 'wall') return formatWallTimeAtDecimalPlaces(value, decimalPlaces);
  if (axisId === 'loc') return formatLocCountAtDecimalPlaces(value, decimalPlaces);
  if (axisId === 'cost') return formatMoneyAtDecimalPlaces(value, decimalPlaces);
  return formatNumberAtDecimalPlaces(value, decimalPlaces);
}

function formatMoney(value) {
  if (!Number.isFinite(value)) return 'n/a';
  const asUsd = Math.round(value * 100) / 100;
  const sign = asUsd < 0 ? '-' : '';
  const fixed = Math.abs(asUsd).toFixed(2);
  const [integerRaw, decimalRaw] = fixed.split('.');
  const integer = Number(integerRaw).toLocaleString('en-US');
  if (decimalRaw === '00') return `${sign}$${integer}.00`;
  if (decimalRaw[1] === '0') return `${sign}$${integer}.${decimalRaw[0]}`;
  return `${sign}$${integer}.${decimalRaw}`;
}

function formatMoneyAtDecimalPlaces(value, decimalPlaces) {
  if (!Number.isFinite(value)) return 'n/a';
  const rounded = normalizeRoundedZero(roundToDecimalPlaces(value, decimalPlaces));
  const fractionDigits = getFractionDigitCount(decimalPlaces);
  const sign = rounded < 0 ? '-' : '';
  const amount = Math.abs(rounded).toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
  return `${sign}$${amount}`;
}

function formatCount(value) {
  if (!Number.isFinite(value)) return 'n/a';
  const rounded = Number.isInteger(value) ? value : Number(value.toFixed(2));
  return rounded.toLocaleString('en-US');
}

function formatLocCount(value) {
  if (!Number.isFinite(value)) return 'n/a';
  if (Math.abs(value) < 1000) return formatCount(value);
  return `${formatCompactSignificant(value / 1000)}K`;
}

function formatNumberAtDecimalPlaces(value, decimalPlaces) {
  if (!Number.isFinite(value)) return 'n/a';
  const rounded = normalizeRoundedZero(roundToDecimalPlaces(value, decimalPlaces));
  const fractionDigits = getFractionDigitCount(decimalPlaces);
  return rounded.toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

function formatLocCountAtDecimalPlaces(value, decimalPlaces, forceThousands = false) {
  if (!Number.isFinite(value)) return 'n/a';
  if (!forceThousands && Math.abs(value) < 1000) {
    return formatNumberAtDecimalPlaces(value, decimalPlaces);
  }
  return `${formatNumberAtDecimalPlaces(value / 1000, decimalPlaces + 3)}K`;
}

function formatTokenCount(value) {
  if (!Number.isFinite(value)) return 'n/a';
  const abs = Math.abs(value);
  if (abs < 1000) return Math.round(value).toLocaleString('en-US');

  if (abs >= 1_000_000) {
    return `${formatSignificant(value / 1_000_000)}M`;
  }
  return `${formatSignificant(value / 1000)}K`;
}

function formatTokenCountAtDecimalPlaces(value, decimalPlaces) {
  if (!Number.isFinite(value)) return 'n/a';
  const abs = Math.abs(value);
  if (abs < 1000) return formatNumberAtDecimalPlaces(value, decimalPlaces);
  if (abs >= 1_000_000) {
    return `${formatNumberAtDecimalPlaces(value / 1_000_000, decimalPlaces + 6)}M`;
  }
  return `${formatNumberAtDecimalPlaces(value / 1000, decimalPlaces + 3)}K`;
}

function formatWallTime(value) {
  if (!Number.isFinite(value)) return 'n/a';
  const totalMinutes = value;
  const totalMinutesRounded = Math.max(0, Number(totalMinutes.toFixed(4)));
  const totalSeconds = totalMinutesRounded * 60;
  if (totalSeconds < 60) return `${formatSignificant(totalSeconds)}s`;

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.round(totalSeconds % 60);
  if (!hours) return `${minutes}m ${seconds}s`;
  return `${hours}h ${minutes}m ${seconds}s`;
}

function formatWallTimeAtDecimalPlaces(value, decimalPlaces) {
  if (!Number.isFinite(value)) return 'n/a';
  const roundedMinutes = Math.max(0, roundToDecimalPlaces(value, decimalPlaces));
  if (decimalPlaces <= 0) {
    const totalMinutes = Math.round(roundedMinutes);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    if (hours && minutes) return `${hours}h ${minutes}m`;
    if (hours) return `${hours}h`;
    return `${minutes}m`;
  }

  const totalSeconds = Math.round(roundedMinutes * 60);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.round(totalSeconds % 60);
  if (!hours) return seconds ? `${minutes}m ${seconds}s` : `${minutes}m`;
  return seconds ? `${hours}h ${minutes}m ${seconds}s` : `${hours}h ${minutes}m`;
}

function formatSignificant(value, significantFigures = 3) {
  if (!Number.isFinite(value)) return 'n/a';
  if (value === 0) return '0';
  return new Intl.NumberFormat('en-US', {
    minimumSignificantDigits: significantFigures,
    maximumSignificantDigits: significantFigures,
  }).format(value);
}

function formatCompactSignificant(value, significantFigures = 3) {
  if (!Number.isFinite(value)) return 'n/a';
  if (value === 0) return '0';
  return new Intl.NumberFormat('en-US', {
    maximumSignificantDigits: significantFigures,
  }).format(value);
}

function getMeasuredValuePrecision(uncertainty) {
  if (!Number.isFinite(uncertainty) || uncertainty <= 0) {
    return { significantFigures: 1, decimalPlaces: 0 };
  }
  const leadingDigit = getLeadingSignificantDigit(uncertainty);
  const significantFigures = leadingDigit > 3 ? 1 : 2;
  const exponent = Math.floor(Math.log10(Math.abs(uncertainty)));
  return {
    significantFigures,
    decimalPlaces: significantFigures - exponent - 1,
  };
}

function getLeadingSignificantDigit(value) {
  if (!Number.isFinite(value) || value === 0) return 0;
  const exponent = Math.floor(Math.log10(Math.abs(value)));
  const scaled = Math.abs(value) / Math.pow(10, exponent);
  return Math.floor(scaled + 1e-12);
}

function roundToDecimalPlaces(value, decimalPlaces) {
  if (!Number.isFinite(value)) return NaN;
  if (!Number.isFinite(decimalPlaces)) return value;
  if (decimalPlaces >= 0) {
    const factor = Math.pow(10, decimalPlaces);
    return Math.round(value * factor) / factor;
  }
  const factor = Math.pow(10, -decimalPlaces);
  return Math.round(value / factor) * factor;
}

function normalizeRoundedZero(value) {
  return Object.is(value, -0) || Math.abs(value) < 1e-12 ? 0 : value;
}

function getFractionDigitCount(decimalPlaces) {
  if (!Number.isFinite(decimalPlaces) || decimalPlaces <= 0) return 0;
  return Math.min(12, Math.floor(decimalPlaces));
}

function buildMarkerAriaLabel(point) {
  const xMeta = getAxisMeta(point.xAxis);
  const yMeta = getAxisMeta(point.yAxis);
  const name = point.pairLabel || rowPairId(point.pairId);
  const xPart =
    isCategoricalXAxis(point.xAxis)
      ? `${xMeta.label} ${point.xCategoryLabel || ''}`
      : `${xMeta.label} ${formatAxisValue(point.xAxis, point.xValue)}`;
  const yPart = `${yMeta.label} ${formatAxisValue(point.yAxis, point.yValue)}`;
  return `${name}. ${xPart}. ${yPart}.`;
}

function buildTooltip(point) {
  const xMeta = getAxisMeta(point.xAxis);
  const yMeta = getAxisMeta(point.yAxis);
  const languages = point.languages?.length ? point.languages : [];
  const evals = point.evals?.length ? point.evals : [];
  const xRunCount = point.xSummary?.count || 0;
  const yRunCount = point.ySummary?.count || 0;
  const runCountLabel =
    xRunCount === yRunCount ? `Runs with metric data: ${xRunCount}` : `Runs with metric data: x=${xRunCount}, y=${yRunCount}`;
  const details = summarizePointDetails(point.rows || []);
  const reportTypeLabel = getReportTypeLabel(STATE.reportType);
  const formatAxisReportValue = (axisId, axisSummary) =>
    axisSummary?.hasData
      ? METRICS[axisId]?.formatSummary(axisSummary) ||
        formatAxisValue(axisId, getReportValue(axisSummary, STATE.reportType))
      : 'n/a';

  const lines = [
    `<strong>${point.pairLabel || rowPairId(point.pairId)}</strong>`,
    point.language &&
    (STATE.colorMode === 'language' || point.xAsLanguage)
      ? `Language: ${point.language}`
      : null,
    languages.length > 1 ? `Languages: ${languages.join(', ')}` : null,
    evals.length > 1 && point.xAxis !== 'eval' ? `Evals: ${evals.join(', ')}` : null,
    runCountLabel,
    isCategoricalXAxis(point.xAxis)
      ? `${xMeta.label}: ${point.xCategoryLabel}`
      : `${xMeta.label} (${reportTypeLabel}): ${formatAxisReportValue(point.xAxis, point.xSummary)}`,
    `${yMeta.label} (${reportTypeLabel}): ${formatAxisReportValue(point.yAxis, point.ySummary)}`,
  ].filter(Boolean);

  if (point.xSummary.stacked || point.ySummary.stacked) {
    const summary = point.xSummary.stacked ? point.xSummary : point.ySummary;
    if (summary && summary.stacked) {
      lines.push(
        `Tokens Total split: input ${formatTokenCount(summary.meanInput)} / output ${formatTokenCount(summary.meanOutput)}`,
      );
    }
  }

  const tokensTotalCovered =
    (point.xSummary.stacked && point.xAxis === 'tokens_total') ||
    (point.ySummary.stacked && point.yAxis === 'tokens_total');

  DETAIL_METRIC_IDS.forEach((metricId) => {
    if (!details[metricId]?.hasData) return;
    if (metricId === point.xAxis || metricId === point.yAxis) return;
    if (
      tokensTotalCovered &&
      (metricId === 'tokens_input' || metricId === 'tokens_output')
    ) {
      return;
    }
    const meta = METRICS[metricId];
    lines.push(`${meta.label}: ${meta.formatSummary(details[metricId])}`);
  });
  return lines.map((line) => `<div>${line}</div>`).join('');
}

function summarizePointDetails(rows) {
  const summaries = {};

  DETAIL_METRIC_IDS.forEach((metricId) => {
    const summary = summarizeMetric(rows, metricId);
    if (summary.hasData) {
      summaries[metricId] = summary;
    }
  });

  return summaries;
}

function getCheckedValues(container, groupName) {
  return Array.from(container.querySelectorAll(`input[data-group="${groupName}"]:checked`)).map(
    (input) => input.value,
  );
}

function rowPairId(rowOrPair) {
  if (typeof rowOrPair === 'string') return rowOrPair;
  const model = String(rowOrPair.model || 'default');
  const effort = String(rowOrPair.effort || '').trim();
  const modelLabel = effort ? `${model} (${effort})` : model;
  return `${rowOrPair.agent} / ${modelLabel}`;
}

function splitPairId(pairId) {
  const split = pairId.split(' / ');
  return {
    agent: split[0] || '',
    model: split.slice(1).join(' / ') || '',
  };
}

function getPairs() {
  const pairSet = new Set();
  STATE.rows.forEach((row) => {
    pairSet.add(rowPairId(row));
  });
  return Array.from(pairSet).sort((a, b) => a.localeCompare(b));
}

function getLanguages() {
  const languageSet = new Set();
  STATE.rows.forEach((row) => {
    if (row.language) languageSet.add(row.language);
  });
  return Array.from(languageSet).sort();
}

function getEvals() {
  const evalSet = new Set();
  STATE.rows.forEach((row) => {
    if (row.eval) evalSet.add(row.eval);
  });
  return Array.from(evalSet).sort((a, b) => {
    const aNum = parseInt(a.replace(/\D/g, ''), 10);
    const bNum = parseInt(b.replace(/\D/g, ''), 10);
    if (Number.isNaN(aNum) || Number.isNaN(bNum)) return a.localeCompare(b);
    return aNum - bNum;
  });
}

function getAllRows() {
  return STATE.rows;
}

function versionKey(version) {
  return String(version ?? '');
}

function formatVersionLabel(version) {
  return versionKey(version) || 'n/a';
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
    if (diff) return diff;
  }
  return versionKey(a).localeCompare(versionKey(b), undefined, {
    numeric: true,
    sensitivity: 'base',
  });
}

function versionMajorKey(version) {
  const parts = parseVersionParts(version);
  if (parts.length) return String(parts[0]);
  return versionKey(version) || '__unversioned__';
}

function getEvalVersions(evalName) {
  const versionSet = new Set();
  getAllRows().forEach((row) => {
    if (row.eval === evalName) versionSet.add(versionKey(row.eval_version));
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

function cloneVersionSelection(selection) {
  const clone = new Map();
  selection.forEach((versions, evalName) => {
    clone.set(evalName, new Set(versions));
  });
  return clone;
}

function mergeVersionSelectionWithDefaults(previousSelection) {
  const defaults = getDefaultEvalVersionSelections();
  const merged = new Map();
  getEvals().forEach((evalName) => {
    const availableVersions = new Set(getEvalVersions(evalName).map(versionKey));
    const previousVersions = previousSelection.get(evalName);
    const preserved = previousVersions
      ? Array.from(previousVersions).filter((version) => availableVersions.has(versionKey(version)))
      : [];
    merged.set(
      evalName,
      new Set(preserved.length ? preserved.map(versionKey) : Array.from(defaults.get(evalName) || [])),
    );
  });
  return merged;
}

function isEvalVersionSelected(evalName, version) {
  const selectedVersions = STATE.selectedEvalVersions.get(evalName);
  return Boolean(selectedVersions && selectedVersions.has(versionKey(version)));
}

function isRowVersionSelected(row) {
  return isEvalVersionSelected(row.eval, row.eval_version);
}

function getSelectedEvalVersionCount() {
  let count = 0;
  STATE.selectedEvals.forEach((evalName) => {
    const selectedVersions = STATE.selectedEvalVersions.get(evalName);
    if (!selectedVersions) return;
    count += selectedVersions.size;
  });
  return count;
}

function formatVersionSummary(evalName) {
  const versions = getEvalVersions(evalName);
  if (versions.length <= 1) {
    return `Version: ${formatVersionLabel(versions[0])}`;
  }
  const selectedVersions = versions.filter((version) => isEvalVersionSelected(evalName, version));
  if (!selectedVersions.length) return 'Versions: none';
  if (selectedVersions.length === versions.length) return 'Versions: all';
  const selectedMajors = new Set(selectedVersions.map(versionMajorKey));
  const allMajorVersionsSelected =
    selectedMajors.size === 1 &&
    versions
      .filter((version) => versionMajorKey(version) === Array.from(selectedMajors)[0])
      .every((version) => selectedVersions.includes(version));
  if (allMajorVersionsSelected) {
    return `Versions: ${Array.from(selectedMajors)[0]}.x`;
  }
  return `Versions: ${selectedVersions.map(formatVersionLabel).join(', ')}`;
}

function isCategoricalXAxis(axisId = STATE.xAxis) {
  return axisId === 'language' || axisId === 'eval';
}

function getSelectedAxisCategories(axisId) {
  if (axisId === 'language') {
    return getLanguages().filter((language) => STATE.selectedLanguages.has(language));
  }
  if (axisId === 'eval') {
    return getEvals().filter((evalName) => STATE.selectedEvals.has(evalName));
  }
  return [];
}

function getRowCategoryValue(row, axisId) {
  if (axisId === 'language') return row.language;
  if (axisId === 'eval') return row.eval;
  return '';
}

function setError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove('hidden');
}

function clearError() {
  errorBanner.textContent = '';
  errorBanner.classList.add('hidden');
}

function createSvgElement(tagName) {
  return document.createElementNS('http://www.w3.org/2000/svg', tagName);
}

async function loadRows() {
  const response = await fetch(`${DATA_PATH}?t=${Date.now()}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Unable to load ${DATA_PATH}`);
  const text = await response.text();
  return JSON.parse(text);
}

document.addEventListener('DOMContentLoaded', () => {
  updatePerTestExplorerAvailability();
});

async function updatePerTestExplorerAvailability() {
  const link = document.querySelector('[data-per-test-link]');
  if (!link) return;

  const available = await isPerTestDataAvailable();
  if (available) {
    link.classList.remove('disabled');
    link.removeAttribute('aria-disabled');
    link.href = 'test-results-dashboard.html';
    link.textContent = 'Per-test explorer';
    link.title = 'Open the locally generated per-test explorer.';
    return;
  }

  link.classList.add('disabled');
  link.setAttribute('aria-disabled', 'true');
  link.removeAttribute('href');
  link.textContent = 'Per-test explorer (local only)';
  link.title =
    'Generate published_results/web/test-results-published.json locally with clispecbench rebuild-dashboard to enable this explorer.';
}

async function isPerTestDataAvailable() {
  try {
    const response = await fetch(`${PER_TEST_DATA_PATH}?t=${Date.now()}`, {
      cache: 'no-store',
      method: 'HEAD',
    });
    return response.ok;
  } catch (_error) {
    return false;
  }
}

function normalizeDataset(data) {
  if (Array.isArray(data)) {
    return { rows: data };
  }
  return {
    rows: Array.isArray(data?.rows) ? data.rows : [],
  };
}

function coerceRow(raw) {
  const resultLink = firstPresent(raw.result_link, raw.resultLink, '');
  const transcriptLink = firstPresent(raw.transcript_link, raw.transcriptLink, '');
  const scoreCount = toNumber(firstPresent(raw.score_count, raw.passed));
  const scoreTotal = toNumber(firstPresent(raw.score_total, raw.total));
  const scorePctRaw = toNumber(raw.score_pct);
  const scorePct =
    Number.isFinite(scorePctRaw)
      ? scorePctRaw
      : Number.isFinite(scoreCount) && Number.isFinite(scoreTotal) && scoreTotal > 0
        ? (scoreCount / scoreTotal) * 100
        : NaN;
  const task = firstPresent(raw.task, '');
  const normalizedEval = normalizeEval(firstPresent(raw.eval, task), resultLink, transcriptLink, task);
  return {
    language: firstPresent(raw.language, languageFromTask(task), ''),
    agent: firstPresent(raw.agent, ''),
    model: firstPresent(raw.model, 'default'),
    effort: firstPresent(raw.effort, ''),
    run_id: String(firstPresent(raw.run_id, raw.run, '')),
    eval: normalizedEval,
    eval_instance: firstPresent(raw.eval_instance, ''),
    eval_version: firstPresent(raw.eval_version, ''),
    exit_reason: firstPresent(raw.exit_reason, 'completed'),
    status: firstPresent(raw.status, ''),
    agent_stop_reason: firstPresent(raw.agent_stop_reason, ''),
    agent_stop_label: firstPresent(raw.agent_stop_label, ''),
    agent_stop_message: firstPresent(raw.agent_stop_message, ''),
    agent_stop_source: firstPresent(raw.agent_stop_source, ''),
    failure_class: firstPresent(raw.failure_class, ''),
    notes: firstPresent(raw.notes, ''),
    eval_raw: firstPresent(raw.eval, ''),
    score_count: scoreCount,
    score_total: scoreTotal,
    score_pct: scorePct,
    wall_min: toNumber(raw.wall_min),
    input_tokens: toNumber(raw.input_tokens),
    output_tokens: toNumber(raw.output_tokens),
    cost_usd: toNumber(raw.cost_usd),
    tools: toNumber(firstPresent(raw.tools, raw.tool_calls)),
    files: toNumber(raw.files),
    loc: toNumber(raw.loc),
    result_link: resultLink,
    transcript_link: transcriptLink,
    last_message: firstPresent(raw.last_message, raw.last_message_summary, raw.agent_last_message, ''),
    last_message_verbatim: firstPresent(raw.last_message_verbatim, raw.agent_last_message, ''),
  };
}

function normalizeEval(rawEval, resultLink, transcriptLink, task) {
  const taskLabel = evalLabelFromTask(task);
  if (taskLabel !== 'Unknown') return taskLabel;

  const evalName = String(rawEval || '').trim();
  const searchText = `${resultLink || ''} ${transcriptLink || ''}`.toLowerCase();
  const linkedLabel = evalLabelFromTask(searchText);
  if (linkedLabel !== 'Unknown') return linkedLabel;

  if (!evalName) return 'Unknown';
  if (/^eval\d+$/i.test(evalName)) return 'Unknown';
  return evalLabelFromText(evalName);
}

function evalLabelFromTask(value) {
  const text = String(value || '').toLowerCase();
  const labels = [
    ['cncsim', 'CNCSim'],
    ['rs274', 'RS274'],
    ['wordcount', 'WordCount'],
    ['bibtex', 'BibTeX'],
    ['gedcom', 'GEDCOM'],
    ['ical', 'ICal'],
    ['iges', 'IGES'],
    ['marc21', 'MARC21'],
    ['las', 'LAS'],
  ];
  const match = labels.find(([needle]) => text.includes(needle));
  return match ? match[1] : 'Unknown';
}

function evalLabelFromText(value) {
  const cleaned = String(value || '').trim().replace(/[-_]+/g, ' ').toLowerCase();
  const tokens = cleaned.split(/\s+/).filter(Boolean);
  if (!tokens.length) return 'Unknown';
  return tokens
    .map((token, index) => {
      if (index === 0 && token === 'cncsim') return 'CNCSim';
      if (index === 0 && token === 'iges') return 'IGES';
      if (index === 0 && token === 'bibtex') return 'BibTeX';
      if (index === 0 && token === 'gedcom') return 'GEDCOM';
      if (index === 0 && token === 'ical') return 'ICal';
      if (index === 0 && token === 'marc21') return 'MARC21';
      if (index === 0 && token === 'las') return 'LAS';
      if (index === 0 && token === 'rs274') return 'RS274';
      return token[0].toUpperCase() + token.slice(1);
    })
    .join(' ');
}

function languageFromTask(task) {
  const match = String(task || '').match(/-(cpp|py|js|rs)$/i);
  return match ? match[1].toUpperCase() : '';
}

function firstPresent(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== '') ?? '';
}

function toNumber(value) {
  const parsed = Number.parseFloat(String(value).replace(/,/g, ''));
  return Number.isFinite(parsed) ? parsed : NaN;
}
