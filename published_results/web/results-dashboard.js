const DATA_PATH = 'results-2_1_1_runs.csv';

const AXIS_OPTIONS = [
  { id: 'percent', label: 'Pass rate' },
  { id: 'tokens_input', label: 'Tokens Input' },
  { id: 'tokens_output', label: 'Tokens Output' },
  { id: 'tokens_total', label: 'Tokens Total' },
  { id: 'cost', label: 'Cost (USD)' },
  { id: 'wall', label: 'Wall Clock Time' },
  { id: 'tools', label: 'Tools Used' },
  { id: 'loc', label: 'LOC' },
  { id: 'language', label: 'Language', axisOnly: true },
];

const COLOR_MODE_OPTIONS = [
  { id: 'pair', label: 'Agent / Model Pair' },
  { id: 'language', label: 'Language' },
  { id: 'agent', label: 'Agent' },
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
    formatMean: (value) => formatCount(value),
    formatSummary: (s) => `${formatCount(s.mean)} (min ${formatCount(s.min)}, max ${formatCount(s.max)})`,
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
const LANGUAGE_AXIS_X_PADDING = 24;
const AXIS_TICK_SEGMENTS = 5;
const AXIS_DOMAIN_PADDING_FRACTION = 0.06;
const AXIS_DOMAIN_MIN_PADDING = 0.5;

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

const STATE = {
  rows: [],
  selectedPairs: new Set(),
  selectedLanguages: new Set(),
  selectedEval: '',
  xAxis: 'cost',
  yAxis: 'percent',
  colorMode: 'pair',
  reportType: 'mean',
  errorBarMode: 'std',
  hiddenColorKeys: new Set(),
};

const pairListEl = document.getElementById('pair-list');
const pairUnavailableHintEl = document.getElementById('pair-unavailable-hint');
const pairSelectAllButton = document.getElementById('pair-select-all');
const pairUnselectAllButton = document.getElementById('pair-unselect-all');
const languageListEl = document.getElementById('language-list');
const evalSelect = document.getElementById('eval-select');
const xAxisSelect = document.getElementById('x-axis');
const yAxisSelect = document.getElementById('y-axis');
const reportTypeSelect = document.getElementById('report-type');
const errorBarsSelect = document.getElementById('error-bars');
const colorModeSelect = document.getElementById('color-mode');
const fileInputEl = document.getElementById('csv-file-input');
const validationEl = document.getElementById('validation-message');
const statusEl = document.getElementById('status');
const errorBanner = document.getElementById('error-banner');
const chartSvg = document.getElementById('scatter-svg');
const chartEmpty = document.getElementById('chart-empty');
const legendEl = document.getElementById('legend');
const tooltip = document.getElementById('tooltip');

document.addEventListener('DOMContentLoaded', () => {
  if (
    !pairListEl ||
    !pairSelectAllButton ||
    !pairUnselectAllButton ||
    !languageListEl ||
    !evalSelect ||
    !xAxisSelect ||
    !yAxisSelect ||
    !reportTypeSelect ||
    !errorBarsSelect ||
    !colorModeSelect
  ) {
    console.error('Dashboard initialization failed: expected UI elements are missing.');
    return;
  }

  attachEvents();

  if (fileInputEl) {
    fileInputEl.addEventListener('change', async (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const rows = parseCsv(text);
        initializeDashboard(rows, file.name, { preserveView: true });
      } catch (error) {
        setError(`Could not parse ${file.name}: ${error.message}`);
      }
    });
  }

  (async () => {
    try {
      const rows = await loadRows();
      initializeDashboard(rows, DATA_PATH);
    } catch (error) {
      const message =
        window.location.protocol === 'file:'
          ? `Unable to load ${DATA_PATH} from file://. Use the data source picker below, or serve this page from a local server (for example: python -m http.server 8000 from published_results/web).`
          : `Unable to load ${DATA_PATH}: ${error.message}. Open this page through a local web server and refresh (for example: python -m http.server 8000 from published_results/web).`;
      setError(message);
      return;
    }
  })();
});

function initializeDashboard(rows, sourceName, { preserveView = false } = {}) {
  if (!rows.length) {
    throw new Error('No result rows were found in the CSV.');
  }
  STATE.rows = rows;
  initSelectionDefaults({ preserveView });
  buildControls();
  render();
  statusEl.textContent = `Loaded ${STATE.rows.length} runs from ${sourceName || DATA_PATH}.`;
  clearError();
}

function initSelectionDefaults({ preserveView = false } = {}) {
  const previousView = preserveView
    ? {
        xAxis: STATE.xAxis,
        yAxis: STATE.yAxis,
        colorMode: STATE.colorMode,
        reportType: STATE.reportType,
        errorBarMode: STATE.errorBarMode,
      }
    : null;

  STATE.selectedPairs = new Set();
  STATE.selectedLanguages = new Set();
  STATE.hiddenColorKeys = new Set();
  const pairs = getPairs();
  const languages = getLanguages();
  const evals = getEvals();

  if (!pairs.length || !languages.length || !evals.length) {
    throw new Error(
      'The CSV loaded but did not contain expected pair/language/eval rows for the controls.',
    );
  }

  pairs.forEach((id) => STATE.selectedPairs.add(id));
  languages.forEach((lang) => STATE.selectedLanguages.add(lang));
  STATE.selectedEval = evals[0] || '';

  if (previousView) {
    STATE.xAxis = previousView.xAxis;
    STATE.yAxis = previousView.yAxis;
    STATE.colorMode = previousView.colorMode;
    STATE.reportType = previousView.reportType;
    STATE.errorBarMode = previousView.errorBarMode;
  } else {
    STATE.xAxis = 'cost';
    STATE.yAxis = 'percent';
    STATE.colorMode = 'agent';
    STATE.reportType = 'mean';
    STATE.errorBarMode = getDefaultErrorBarMode();
  }
}

function buildControls() {
  renderPairList();
  renderLanguageList();
  renderEvalList();
  renderColorModeSelector();
  renderReportTypeSelector();
  renderErrorBarSelector();
  updateAxisSelectors();
}

function attachEvents() {
  if (pairSelectAllButton) {
    pairSelectAllButton.addEventListener('click', () => {
      const allPairInputs = Array.from(pairListEl.querySelectorAll('input[data-group="pair"]'));
      const selectablePairIds = allPairInputs.filter((input) => !input.disabled).map((input) => input.value);
      STATE.selectedPairs = new Set(selectablePairIds);
      allPairInputs.forEach((input) => {
        input.checked = !input.disabled;
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
    if (STATE.selectedPairs.size === 0) {
      const fallbackInput = Array.from(
        pairListEl.querySelectorAll('input[data-group="pair"]:not([disabled])'),
      )[0];
      const fallback = fallbackInput?.value;
      if (fallback) STATE.selectedPairs.add(fallback);
      if (fallbackInput) fallbackInput.checked = true;
    }
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
    syncErrorBarModeWithDefaults();
    updateAxisSelectors();
    render();
  });

  evalSelect.addEventListener('change', () => {
    STATE.selectedEval = evalSelect.value;
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

    if (!isSelectable) {
      if (STATE.selectedPairs.has(pairId)) STATE.selectedPairs.delete(pairId);
      unavailableLabels.push(`${agent} / ${model}`);
      return;
    }

    const row = document.createElement('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.dataset.group = 'pair';
    cb.value = pairId;
    cb.checked = STATE.selectedPairs.has(pairId);
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
  evalSelect.replaceChildren();
  getEvals().forEach((evalName) => {
    const option = document.createElement('option');
    option.value = evalName;
    option.textContent = evalName;
    option.selected = evalName === STATE.selectedEval;
    evalSelect.appendChild(option);
  });
}

function updateAxisSelectors() {
  const canUseLanguageAxis = STATE.selectedLanguages.size > 1;

  xAxisSelect.replaceChildren();
  AXIS_OPTIONS.forEach((axis) => {
    const option = document.createElement('option');
    option.value = axis.id;
    option.textContent = axis.label;
    if (axis.axisOnly && !canUseLanguageAxis) {
      option.disabled = true;
      option.textContent = `${axis.label} (select 2+ languages)`;
    }
    xAxisSelect.appendChild(option);
  });
  if (STATE.xAxis === 'language' && !canUseLanguageAxis) {
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

function getDefaultErrorBarMode() {
  if (STATE.selectedLanguages.size > 1 && STATE.xAxis !== 'language') {
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
  clearError();
  const validation = validateSelection();
  if (!validation.ok) {
    showNoData(validation.message);
    return;
  }

  const colorMap = getColorMap();
  const rowsByPair = getRowsByPairForCurrentSelection();
  const canRenderPairById = getPairAvailability(rowsByPair);
  const selectedPairs = new Set();
  STATE.selectedPairs.forEach((pairId) => {
    if (canRenderPairById.get(pairId)) {
      selectedPairs.add(pairId);
    }
  });
  STATE.selectedPairs = selectedPairs;
  renderPairList(canRenderPairById);
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
  if (!STATE.selectedEval) {
    return { ok: false, message: 'Choose an eval.' };
  }
  if (!STATE.selectedPairs.size) {
    return { ok: false, message: 'Choose at least one agent/model pair.' };
  }
  if (!STATE.selectedLanguages.size) {
    return { ok: false, message: 'Choose at least one language.' };
  }
  if (STATE.xAxis === 'language' && STATE.selectedLanguages.size < 2) {
    return { ok: false, message: 'Language is available when at least two languages are selected.' };
  }
  return { ok: true };
}

function showNoData(message) {
  clearChart();
  chartEmpty.textContent = message;
  chartEmpty.classList.remove('hidden');
  legendEl.innerHTML = '';
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

function buildPoints(colorMap, rowsByPairOverride) {
  const selectedLanguages = Array.from(STATE.selectedLanguages).sort();
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

    if (STATE.xAxis === 'language') {
      selectedLanguages.forEach((language) => {
        const subset = rows.filter((r) => r.language === language);
        const colorModeKey = getColorModeKey(pairId, language);
        const color = colorMap.get(colorModeKey) || fallbackColor;
        const point = summarizePoint(pairId, color, subset, language, {
          xAxis: STATE.xAxis,
          yAxis: STATE.yAxis,
          xAsLanguage: true,
          xCategoryLabel: language,
        });
        if (point) {
          point.colorModeKey = colorModeKey;
          points.push(point);
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
          xAsLanguage: false,
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
        xAsLanguage: false,
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
    if (row.eval !== STATE.selectedEval) return;
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

function canRenderPair(rows, selectedLanguages) {
  const xAxis = STATE.xAxis;
  const yAxis = STATE.yAxis;

  if (!rows.length) {
    return false;
  }

  if (xAxis === 'language') {
    return selectedLanguages.some((language) => {
      const subset = rows.filter((row) => row.language === language);
      if (!subset.length) return false;
      const summary = summarizeMetric(subset, yAxis);
      return summary.hasData;
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
    xAsLanguage: options.xAsLanguage,
    xSummary,
    ySummary,
    xValue: getReportValue(xSummary, STATE.reportType),
    yValue: getReportValue(ySummary, STATE.reportType),
    xCategoryLabel: options.xCategoryLabel,
    xAxis: options.xAxis,
    yAxis: options.yAxis,
  };
}

function summarizeMetric(rows, metricId) {
  if (metricId === 'language') {
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

function getErrorBarRange(summary, mode, reportType) {
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
    const min = Number.isFinite(summary.min)
      ? Math.max(center - summary.stdDev, summary.min)
      : center - summary.stdDev;
    const max = Number.isFinite(summary.max)
      ? Math.min(center + summary.stdDev, summary.max)
      : center + summary.stdDev;
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
  if (STATE.colorMode === 'agent') return key;
  if (STATE.colorMode === 'language') return key;
  const { agent, model } = splitPairId(key);
  if (!agent && !model) return key;
  return `${agent} / ${model}`;
}

function drawFrontierConnector(points, frontierSet, xScale, yScale, layer) {
  if (frontierSet.size < 2) return;
  if (STATE.xAxis === 'language') return;
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
  if (xAxis === 'language') return frontier;
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
  const selectedLanguages = Array.from(STATE.selectedLanguages).sort();
  const xScale = createXScale(xDomain, selectedLanguages, plotLeft, plotRight);
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
    selectedLanguages,
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

  const frontierSet = computeParetoFrontier(points, STATE.xAxis, STATE.yAxis);
  drawFrontierConnector(points, frontierSet, xScale, yScale, dataLayer);

  points.forEach((point) => {
    const isOnFrontier = frontierSet.has(point);
    const baseRadius = 7.3;
    const hoverRadius = 8.8;

    const x = point.xAsLanguage
      ? xScale(selectedLanguages.indexOf(point.language))
      : xScale(point.xValue);
    const y = yScale(point.yValue);

    const g = createSvgElement('g');
    g.setAttribute('transform', `translate(${x}, ${y})`);
    const pointClearance = 4;
    const obstacleRects = [];
    const markerRadius = baseRadius + pointClearance;
    obstacleRects.push({
      x: x - markerRadius,
      y: y - markerRadius,
      width: markerRadius * 2,
      height: markerRadius * 2,
    });

    const canShowErrorBars =
      STATE.xAxis !== 'language' && STATE.errorBarMode !== 'none';
    const xBarRange = canShowErrorBars
      ? getErrorBarRange(point.xSummary, STATE.errorBarMode, STATE.reportType)
      : null;
    const yBarRange = canShowErrorBars
      ? getErrorBarRange(point.ySummary, STATE.errorBarMode, STATE.reportType)
      : null;

    if (!point.xAsLanguage && xBarRange) {
      const left = xScale(xBarRange.min);
      const right = xScale(xBarRange.max);
      const rangeLine = createSvgElement('line');
      rangeLine.setAttribute('class', 'point-range-h');
      rangeLine.setAttribute('x1', String(left - x));
      rangeLine.setAttribute('x2', String(right - x));
      rangeLine.setAttribute('y1', '0');
      rangeLine.setAttribute('y2', '0');
      g.appendChild(rangeLine);
      obstacleRects.push({
        x: Math.min(left, right),
        y: y - 8,
        width: Math.abs(right - left),
        height: 16,
      });
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
      obstacleRects.push({
        x: x - 2,
        y: Math.min(top, bottom),
        width: 4,
        height: Math.abs(bottom - top),
      });
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
    const labelClass = isOnFrontier
      ? 'point-label point-label-frontier'
      : 'point-label point-label-hover';
    label.setAttribute('class', labelClass);
    label.setAttribute('pointer-events', 'none');
    label.textContent = point.pairLabel || rowPairId(point.pairId);
    if (!isOnFrontier) {
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
      if (!isOnFrontier) {
        label.setAttribute('x', String(x + baseRadius + 6));
        label.setAttribute('y', String(y - baseRadius - 4));
        label.setAttribute('text-anchor', 'start');
        label.setAttribute('visibility', 'visible');
      }
    };
    const hideMarker = () => {
      tooltip.style.display = 'none';
      pointCircle.classList.remove('active');
      pointCircle.setAttribute('r', pointCircle.getAttribute('data-base-radius') || String(baseRadius));
      if (!isOnFrontier) {
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

    if (isOnFrontier) {
      markerLabels.push({
        point,
        x,
        y,
        circle: pointCircle,
        label,
        leader,
        obstacleRects,
      });
    }
  });

  chartSvg.appendChild(dataLayer);
  chartSvg.appendChild(labelsLayer);

  placePointLabels(markerLabels, {
    width,
    height,
    margin,
    chartSvg,
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

function placePointLabels(markers, { width, height, margin }) {
  if (!markers.length) return;

  const panelBounds = {
    minX: margin.left + 6,
    maxX: width - margin.right - 6,
    minY: margin.top + 6,
    maxY: height - margin.bottom - 8,
  };
  const padding = 4;
  const pointClearance = 4;
  const placedBoxes = [];
  const candidates = [
    { dx: 20, dy: -12, anchor: 'start', baseline: 'text-before-edge' },
    { dx: 20, dy: 12, anchor: 'start', baseline: 'text-after-edge' },
    { dx: -20, dy: -12, anchor: 'end', baseline: 'text-before-edge' },
    { dx: -20, dy: 12, anchor: 'end', baseline: 'text-after-edge' },
    { dx: 26, dy: 0, anchor: 'start', baseline: 'middle' },
    { dx: -26, dy: 0, anchor: 'end', baseline: 'middle' },
    { dx: 30, dy: -14, anchor: 'start', baseline: 'text-before-edge' },
    { dx: -30, dy: -14, anchor: 'end', baseline: 'text-before-edge' },
    { dx: 30, dy: 14, anchor: 'start', baseline: 'text-after-edge' },
    { dx: -30, dy: 14, anchor: 'end', baseline: 'text-after-edge' },
  ];
  const labelFallbacks = [
    { dx: 20, dy: -18, anchor: 'start', baseline: 'text-before-edge' },
    { dx: -20, dy: -18, anchor: 'end', baseline: 'text-before-edge' },
    { dx: 20, dy: 18, anchor: 'start', baseline: 'text-before-edge' },
    { dx: -20, dy: 18, anchor: 'end', baseline: 'text-before-edge' },
  ];

  markers.forEach((marker) => {
    const { point, x, y, label, leader } = marker;
    const obstacleRects = marker.obstacleRects || [];
    const baseRadius = Number.parseFloat(marker.circle.getAttribute('data-base-radius')) || 7;
    const text = point.pairLabel || rowPairId(point.pairId);
    label.textContent = text;
    label.setAttribute('visibility', 'hidden');
    label.setAttribute('x', '0');
    label.setAttribute('y', '0');
    label.setAttribute('text-anchor', 'start');
    label.setAttribute('dominant-baseline', 'middle');
    leader.setAttribute('visibility', 'hidden');
    leader.setAttribute('x1', '0');
    leader.setAttribute('y1', '0');
    leader.setAttribute('x2', '0');
    leader.setAttribute('y2', '0');

    let placed = null;
    for (const candidate of candidates) {
      label.setAttribute('x', String(x + candidate.dx));
      label.setAttribute('y', String(y + candidate.dy));
      label.setAttribute('text-anchor', candidate.anchor);
      label.setAttribute('dominant-baseline', candidate.baseline);

      const bbox = label.getBBox();
      if (bbox.width === 0 || bbox.height === 0) continue;
      if (bbox.x < panelBounds.minX || bbox.y < panelBounds.minY || bbox.x + bbox.width > panelBounds.maxX || bbox.y + bbox.height > panelBounds.maxY) {
        continue;
      }

      const inflated = inflateRect(bbox, padding);
      const overlaps = intersectsAnyRect(inflated, placedBoxes);
      if (overlaps) continue;
      if (intersectsAnyRect(inflated, obstacleRects)) continue;
      if (rectIntersectsPoint(inflated, x, y, Math.max(baseRadius + pointClearance, pointClearance))) {
        continue;
      }

      placed = {
        x,
        y,
        radius: baseRadius,
        bbox: inflated,
        anchor: candidate.anchor,
        baseline: candidate.baseline,
      };
      break;
    }

    if (!placed) {
      for (const candidate of labelFallbacks) {
        label.setAttribute('x', String(x + candidate.dx));
        label.setAttribute('y', String(y + candidate.dy));
        label.setAttribute('text-anchor', candidate.anchor);
        label.setAttribute('dominant-baseline', candidate.baseline);

        const bbox = label.getBBox();
        if (bbox.width === 0 || bbox.height === 0) continue;

        const anchorOffsetX = getAnchorOffsetX(candidate.anchor, bbox.width);
        const anchorOffsetY = getAnchorOffsetY(candidate.baseline, bbox.height);

        const left = bbox.x;
        const top = bbox.y;
        const clampedLeft = Math.max(panelBounds.minX, Math.min(panelBounds.maxX - bbox.width, left));
        const clampedTop = Math.max(panelBounds.minY, Math.min(panelBounds.maxY - bbox.height, top));
        const finalX = clampedLeft + anchorOffsetX;
        const finalY = clampedTop + anchorOffsetY;

        label.setAttribute('x', String(finalX));
        label.setAttribute('y', String(finalY));

        const clampedBbox = label.getBBox();
        if (clampedBbox.width === 0 || clampedBbox.height === 0) continue;

        const inflated = inflateRect(clampedBbox, padding);
        if (intersectsAnyRect(inflated, placedBoxes)) continue;
        if (intersectsAnyRect(inflated, obstacleRects)) continue;
        if (rectIntersectsPoint(inflated, x, y, baseRadius + pointClearance)) continue;

        placed = {
          x,
          y,
          radius: baseRadius,
          bbox: inflateRect(clampedBbox, padding),
          anchor: candidate.anchor,
          baseline: candidate.baseline,
        };
        break;
      }
    }

    if (!placed) {
      return;
    }

    const chosen = placed.bbox;
    label.setAttribute('visibility', 'visible');
    const endpoint = closestPointOnRect({ x, y }, chosen);
    leader.setAttribute('x1', String(x));
    leader.setAttribute('y1', String(y));
    leader.setAttribute('x2', String(endpoint.x));
    leader.setAttribute('y2', String(endpoint.y));
    leader.setAttribute('visibility', 'visible');
    placedBoxes.push(placed.bbox);
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

function rectsOverlap(a, b) {
  return !(
    a.x + a.width < b.x ||
    a.x > b.x + b.width ||
    a.y + a.height < b.y ||
    a.y > b.y + b.height
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
  selectedLanguages,
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
    STATE.xAxis === 'language'
      ? selectedLanguages.map((_, index) => index)
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

  if (STATE.xAxis === 'language') {
    selectedLanguages.forEach((language) => {
      const x = xScale(selectedLanguages.indexOf(language));
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
      text.textContent = language;
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
  if (axisId === 'language') {
    const count = STATE.selectedLanguages.size;
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

function getLanguageAxisSpan(plotLeft, plotRight, selectedLanguages) {
  const totalSpan = plotRight - plotLeft;
  if (!selectedLanguages.length || selectedLanguages.length <= 1 || totalSpan <= 0) {
    return { left: plotLeft, right: plotRight };
  }

  const left = plotLeft + LANGUAGE_AXIS_X_PADDING;
  const right = plotRight - LANGUAGE_AXIS_X_PADDING;
  if (right <= left) return { left: plotLeft, right: plotRight };

  return { left, right };
}

function createXScale(domain, selectedLanguages, plotLeft, plotRight) {
  const left = plotLeft;
  const right = plotRight;

  if (STATE.xAxis === 'language') {
    const { left: paddedLeft, right: paddedRight } = getLanguageAxisSpan(plotLeft, plotRight, selectedLanguages);
    const scale = (value) => {
      if (!selectedLanguages.length) return (left + right) / 2;
      if (selectedLanguages.length === 1) return (left + right) / 2;
      if (paddedRight <= paddedLeft) return (left + right) / 2;

      const clamped = Math.min(
        Math.max(Number(value), 0),
        selectedLanguages.length - 1,
      );
      return paddedLeft + (clamped / (selectedLanguages.length - 1)) * (paddedRight - paddedLeft);
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
  return METRICS[axisId] || { label: axisId };
}

function formatAxisValue(axisId, value) {
  if (!Number.isFinite(value)) return 'n/a';
  if (axisId === 'percent') return `${value.toFixed(1)}%`;
  if (axisId === 'tokens_input' || axisId === 'tokens_output' || axisId === 'tokens_total') {
    return formatTokenCount(value);
  }
  if (axisId === 'wall') return formatWallTime(value);
  if (axisId === 'tools' || axisId === 'loc') return formatCount(value);
  if (axisId === 'cost') return formatMoney(value);
  return String(value.toFixed(2));
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

function formatCount(value) {
  if (!Number.isFinite(value)) return 'n/a';
  const rounded = Number.isInteger(value) ? value : Number(value.toFixed(2));
  return rounded.toLocaleString('en-US');
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

function formatSignificant(value, significantFigures = 3) {
  if (!Number.isFinite(value)) return 'n/a';
  if (value === 0) return '0';
  return new Intl.NumberFormat('en-US', {
    minimumSignificantDigits: significantFigures,
    maximumSignificantDigits: significantFigures,
  }).format(value);
}

function buildMarkerAriaLabel(point) {
  const xMeta = getAxisMeta(point.xAxis);
  const yMeta = getAxisMeta(point.yAxis);
  const name = point.pairLabel || rowPairId(point.pairId);
  const xPart =
    point.xAxis === 'language'
      ? `${xMeta.label} ${point.xCategoryLabel || ''}`
      : `${xMeta.label} ${formatAxisValue(point.xAxis, point.xValue)}`;
  const yPart = `${yMeta.label} ${formatAxisValue(point.yAxis, point.yValue)}`;
  return `${name}. ${xPart}. ${yPart}.`;
}

function buildTooltip(point) {
  const xMeta = getAxisMeta(point.xAxis);
  const yMeta = getAxisMeta(point.yAxis);
  const languages = point.languages?.length ? point.languages : [];
  const xRunCount = point.xSummary?.count || 0;
  const yRunCount = point.ySummary?.count || 0;
  const runCountLabel =
    xRunCount === yRunCount ? `Runs with metric data: ${xRunCount}` : `Runs with metric data: x=${xRunCount}, y=${yRunCount}`;
  const details = summarizePointDetails(point.rows || []);
  const reportTypeLabel = getReportTypeLabel(STATE.reportType);
  const formatAxisReportValue = (axisId, axisSummary) =>
    formatAxisValue(axisId, getReportValue(axisSummary, STATE.reportType));

  const lines = [
    `<strong>${point.pairLabel || rowPairId(point.pairId)}</strong>`,
    point.language &&
    (STATE.colorMode === 'language' || point.xAsLanguage)
      ? `Language: ${point.language}`
      : null,
    languages.length > 1 ? `Languages: ${languages.join(', ')}` : null,
    runCountLabel,
    point.xAxis === 'language'
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
  return `${rowOrPair.agent} / ${rowOrPair.model}`;
}

function splitPairId(pairId) {
  const split = pairId.split(' / ');
  return {
    agent: split[0] || '',
    model: split[1] || '',
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
  return parseCsv(text);
}

function parseCsv(text) {
  const lines = text.replace(/\r\n/g, '\n').trim().split('\n');
  if (!lines.length) return [];
  const header = parseCsvLine(lines[0]).map((value) =>
    String(value || '').replace(/^\uFEFF/, '').trim(),
  );
  const rows = [];

  for (let i = 1; i < lines.length; i += 1) {
    const cells = parseCsvLine(lines[i]);
    if (!cells.length || !cells[0].trim()) continue;
    const row = {};
    header.forEach((headerName, index) => {
      row[headerName] = (cells[index] ?? '').trim();
    });
    rows.push(coerceRow(row));
  }

  return rows;
}

function parseCsvLine(line) {
  const values = [];
  let inQuotes = false;
  let current = '';

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    const next = line[i + 1];

    if (ch === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (ch === ',' && !inQuotes) {
      values.push(current);
      current = '';
      continue;
    }

    current += ch;
  }
  values.push(current);
  return values;
}

function coerceRow(raw) {
  const normalizedEval = normalizeEval(raw.eval, raw.result_link, raw.transcript_link);
  return {
    language: raw.language || '',
    agent: raw.agent || '',
    model: raw.model || '',
    effort: raw.effort || '',
    run_id: raw.run_id || '',
    eval: normalizedEval,
    eval_raw: raw.eval || '',
    score_count: toNumber(raw.score_count),
    score_total: toNumber(raw.score_total),
    score_pct: toNumber(raw.score_pct),
    wall_min: toNumber(raw.wall_min),
    input_tokens: toNumber(raw.input_tokens),
    output_tokens: toNumber(raw.output_tokens),
    cost_usd: toNumber(raw.cost_usd),
    tools: toNumber(raw.tools),
    files: toNumber(raw.files),
    loc: toNumber(raw.loc),
    result_link: raw.result_link || '',
    transcript_link: raw.transcript_link || '',
    last_message: raw.last_message || '',
  };
}

function normalizeEval(rawEval, resultLink, transcriptLink) {
  const evalName = String(rawEval || '').trim();
  const searchText = `${resultLink || ''} ${transcriptLink || ''}`.toLowerCase();

  if (/cncsim(?:-full)?(?:-(?:cpp|py|js|rs))?/.test(searchText)) return 'CNCSim';
  if (searchText.includes('iges')) return 'IGES';
  if (!evalName) return 'CNCSim';
  if (/^eval\d+$/i.test(evalName)) return 'CNCSim';
  return evalLabelFromText(evalName);
}

function evalLabelFromText(value) {
  const cleaned = String(value || '').trim().replace(/[-_]+/g, ' ').toLowerCase();
  const tokens = cleaned.split(/\s+/).filter(Boolean);
  if (!tokens.length) return 'Unknown';
  return tokens
    .map((token, index) => {
      if (index === 0 && token === 'cncsim') return 'CNCSim';
      if (index === 0 && token === 'iges') return 'IGES';
      return token[0].toUpperCase() + token.slice(1);
    })
    .join(' ');
}

function toNumber(value) {
  const parsed = Number.parseFloat(String(value).replace(/,/g, ''));
  return Number.isFinite(parsed) ? parsed : NaN;
}
