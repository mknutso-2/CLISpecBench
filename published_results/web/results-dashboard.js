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
  { id: 'model', label: 'Model (efforts connected)' },
  { id: 'pair', label: 'Agent / Model / Effort' },
  { id: 'language', label: 'Language' },
  { id: 'agent', label: 'Agent' },
];

// Above this many visible points, 'auto' labels only the Pareto frontier.
const AUTO_LABEL_POINT_LIMIT = 12;

const LABEL_MODE_OPTIONS = [
  { id: 'auto', label: 'Auto' },
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

const AXIS_SCALE_OPTIONS = [
  { id: 'linear', label: 'Linear' },
  { id: 'log', label: 'Log' },
];

// Reasoning-effort levels from least to most compute. Used to connect a
// model's effort levels in order and to pick a model's highest effort.
const EFFORT_ORDER = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'];

// Fewer runs than this in any selected eval/language cell draws a hollow marker.
const LOW_RUN_COUNT_THRESHOLD = 3;

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
  '#a16207',
  '#65a30d',
  '#9f1239',
  '#1e3a8a',
  '#14b8a6',
  '#a855f7',
  '#78716c',
  '#eab308',
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
  xScaleMode: 'linear',
  yScaleMode: 'linear',
  colorMode: 'model',
  labelMode: 'auto',
  nameMode: 'short',
  reportType: 'mean',
  errorBarMode: 'std',
  tableMode: 'summary',
  tableGroupBy: 'pair',
  tableSortBy: '',
  tableSortDirection: 'asc',
  controlsCollapsed: false,
  hiddenColorKeys: new Set(),
  pairSearch: '',
  showCohorts: false,
  collapsedAgents: new Set(),
  heatmapMetric: 'percent',
  heatmapSort: 'name',
  facetByEval: true,
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
const xScaleSelect = document.getElementById('x-scale');
const yScaleSelect = document.getElementById('y-scale');
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
const mainChartSvg = document.getElementById('scatter-svg');
// Points at the SVG being drawn; swapped per facet when charts are split by eval.
let chartSvg = mainChartSvg;
const chartWrapEl = document.getElementById('chart-wrap');
const facetGridEl = document.getElementById('facet-grid');
const facetToggleInput = document.getElementById('facet-toggle');
const evalChipsEl = document.getElementById('eval-chips');
const pairSearchInput = document.getElementById('pair-search');
const showCohortsInput = document.getElementById('show-cohorts');
const pairPresetNewestButton = document.getElementById('pair-preset-newest');
const pairPresetTopEffortButton = document.getElementById('pair-preset-top-effort');
const heatmapPanel = document.getElementById('heatmap-panel');
const heatmapTableEl = document.getElementById('heatmap-table');
const heatmapEmptyEl = document.getElementById('heatmap-empty');
const heatmapTitleEl = document.getElementById('heatmap-title');
const heatmapScaleEl = document.getElementById('heatmap-scale');
const heatmapMetricSelect = document.getElementById('heatmap-metric');
const heatmapSortSelect = document.getElementById('heatmap-sort');
const heatmapControls = Array.from(document.querySelectorAll('.heatmap-control'));
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
  if (!preserveView) applyUrlState();
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
        xScaleMode: STATE.xScaleMode,
        yScaleMode: STATE.yScaleMode,
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
    STATE.xScaleMode = previousView.xScaleMode;
    STATE.yScaleMode = previousView.yScaleMode;
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
    STATE.xScaleMode = 'linear';
    STATE.yScaleMode = 'linear';
    STATE.colorMode = 'model';
    STATE.labelMode = 'auto';
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

// Default selection: the newest model in each model line (for example the
// latest Claude Opus, or GPT-5.6 Sol) at its highest effort, among base-cohort
// pairs with at least one run in every selected eval and language (or, if no
// pair covers every cell, any runs). When a line's pick has no runs for a
// selected eval, the line's newest cohort variant with runs there is added, so
// data recorded under a separate cohort (for example a network-access
// condition) still appears. Points with missing or few runs render as hollow
// markers rather than being hidden.
function getDefaultSelectedPairs(pairs, selectedEvals, selectedLanguages) {
  const evalsByPair = getEvalsWithRunsByPair(selectedEvals, selectedLanguages);
  const withRuns = pairs.filter((pairId) => evalsByPair.has(pairId));
  const fullCoverage = new Set(getPairsWithRunCount(pairs, selectedEvals, selectedLanguages, 1));
  const base = withRuns.filter((pairId) => !parsePairModel(pairId).cohort);
  const basePool = base.some((pairId) => fullCoverage.has(pairId))
    ? base.filter((pairId) => fullCoverage.has(pairId))
    : base;
  const selected = new Set(pickNewestPerLine(basePool).values());

  selectedEvals.forEach((evalName) => {
    const linesWithEval = () =>
      new Set(
        Array.from(selected)
          .filter((pairId) => evalsByPair.get(pairId)?.has(evalName))
          .map(getModelLineKey),
      );
    // Prefer a line's base-cohort pair with partial coverage, then a cohort variant.
    [false, true].forEach((wantCohort) => {
      const covered = linesWithEval();
      const fillers = withRuns.filter(
        (pairId) =>
          Boolean(parsePairModel(pairId).cohort) === wantCohort &&
          evalsByPair.get(pairId).has(evalName) &&
          !covered.has(getModelLineKey(pairId)),
      );
      pickNewestPerLine(fillers).forEach((pairId) => selected.add(pairId));
    });
  });
  return Array.from(selected);
}

function getModelLineKey(pairId) {
  const { agent, baseModel } = parsePairModel(pairId);
  return `${agent} / ${getModelLine(baseModel).line}`;
}

// Map of model line → newest pair (highest version, then highest effort).
function pickNewestPerLine(pairIds) {
  const newestByLine = new Map();
  pairIds.forEach((pairId) => {
    const { baseModel, effort } = parsePairModel(pairId);
    const candidate = {
      pairId,
      version: getModelLine(baseModel).version,
      effortRank: getEffortRank(effort),
    };
    const lineKey = getModelLineKey(pairId);
    const current = newestByLine.get(lineKey);
    if (!current || compareModelCandidates(candidate, current) > 0) {
      newestByLine.set(lineKey, candidate);
    }
  });
  return new Map(Array.from(newestByLine.entries()).map(([key, candidate]) => [key, candidate.pairId]));
}

// Map of pair id → set of selected evals with at least one selected-version run.
function getEvalsWithRunsByPair(selectedEvals, selectedLanguages) {
  const evalSet = new Set(selectedEvals);
  const languageSet = new Set(selectedLanguages);
  const evalsByPair = new Map();
  STATE.rows.forEach((row) => {
    if (!evalSet.has(row.eval) || !languageSet.has(row.language)) return;
    if (!isRowVersionSelected(row)) return;
    const pairId = rowPairId(row);
    if (!evalsByPair.has(pairId)) evalsByPair.set(pairId, new Set());
    evalsByPair.get(pairId).add(row.eval);
  });
  return evalsByPair;
}

function compareModelCandidates(a, b) {
  const length = Math.max(a.version.length, b.version.length);
  for (let index = 0; index < length; index += 1) {
    const diff = (a.version[index] || 0) - (b.version[index] || 0);
    if (diff) return diff;
  }
  return a.effortRank - b.effortRank;
}

// Groups a model id into a release line plus a comparable version, so that
// claude-opus-4-8 supersedes claude-opus-4-1-20250805 and gpt-5.6-sol is its
// own line. Unrecognized ids form single-model lines.
function getModelLine(baseModel) {
  const normalized = String(baseModel || '').toLowerCase().split('/').pop();
  const claudeMatch = normalized.match(/^claude-([a-z]+)-(\d+)(?:-(\d+))?/);
  if (claudeMatch) {
    const minor = claudeMatch[3] && claudeMatch[3].length < 8 ? Number(claudeMatch[3]) : 0;
    return { line: `claude-${claudeMatch[1]}`, version: [Number(claudeMatch[2]), minor] };
  }
  const gptMatch = normalized.match(/^gpt-(\d+)(?:\.(\d+))?(?:-([a-z][a-z0-9]*))?/);
  if (gptMatch) {
    return {
      line: `gpt-${gptMatch[3] || ''}`,
      version: [Number(gptMatch[1]), Number(gptMatch[2] || 0)],
    };
  }
  const geminiMatch = normalized.match(/^gemini-(\d+)(?:\.(\d+))?(?:-([a-z]+))?/);
  if (geminiMatch) {
    return {
      line: `gemini-${geminiMatch[3] || ''}`,
      version: [Number(geminiMatch[1]), Number(geminiMatch[2] || 0)],
    };
  }
  return { line: normalized, version: [0] };
}

function getEffortRank(effort) {
  return EFFORT_ORDER.indexOf(String(effort || '').trim().toLowerCase());
}

// Splits a pair id into agent, base model, effort and comparison-cohort suffix.
function parsePairModel(pairId) {
  const { agent, model } = splitPairId(rowPairId(pairId));
  const cohortMatch = model.match(/^(.*?)( \[[^\]]+\])$/);
  const modelWithoutCohort = cohortMatch ? cohortMatch[1] : model;
  const { baseModel, effort } = splitModelEffortLabel(modelWithoutCohort);
  return { agent, baseModel, effort, cohort: cohortMatch ? cohortMatch[2] : '' };
}

function getModelFamilyKey(pairId) {
  const { agent, baseModel, cohort } = parsePairModel(pairId);
  return `${agent} / ${baseModel}${cohort}`;
}

function getPairsWithRunCount(pairs, selectedEvals, selectedLanguages, requiredCount) {
  if (!selectedEvals.length || !selectedLanguages.length) return [];

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
    getDefaultSelectedPairs(getPairs(), selectedEvals, selectedLanguages),
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
  renderHeatmapControls();
  updateAxisSelectors();
  if (pairSearchInput) pairSearchInput.value = STATE.pairSearch;
  if (showCohortsInput) showCohortsInput.checked = STATE.showCohorts;
  if (facetToggleInput) facetToggleInput.checked = STATE.facetByEval;
  syncViewModeControls();
  syncControlsColumn();
}

function renderAxisScaleSelectors() {
  [
    [xScaleSelect, 'xScaleMode', STATE.xAxis],
    [yScaleSelect, 'yScaleMode', STATE.yAxis],
  ].forEach(([select, stateKey, axisId]) => {
    if (!select) return;
    select.replaceChildren();
    AXIS_SCALE_OPTIONS.forEach((mode) => {
      const option = document.createElement('option');
      option.value = mode.id;
      option.textContent = mode.label;
      select.appendChild(option);
    });
    const allowed = canUseLogScale(axisId);
    if (!allowed || STATE[stateKey] !== 'log') STATE[stateKey] = 'linear';
    select.value = STATE[stateKey];
    select.disabled = !allowed;
    select.title = allowed ? '' : 'Log scale applies to positive numeric metrics only.';
  });
}

function attachEvents() {
  controlsToggleButton.addEventListener('click', () => {
    STATE.controlsCollapsed = !STATE.controlsCollapsed;
    syncControlsColumn();
    writeUrlState();
    if (STATE.rows.length) {
      window.requestAnimationFrame(() => render());
    }
  });

  viewModeEl.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-view-mode]');
    if (!button) return;
    STATE.viewMode = normalizeViewMode(button.dataset.viewMode);
    syncViewModeControls();
    render();
  });

  if (pairSelectAllButton) {
    pairSelectAllButton.addEventListener('click', () => {
      // Adds every visible (search- and cohort-filtered), available configuration.
      const visibleInputs = Array.from(
        pairListEl.querySelectorAll('input[data-group="pair"]:not(:disabled)'),
      ).filter((input) => !input.closest('.hidden'));
      visibleInputs.forEach((input) => STATE.selectedPairs.add(input.value));
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

  pairListEl.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action="toggle-family"]');
    if (!button) return;
    const inputs = Array.from(
      button.closest('.model-family').querySelectorAll('input[data-group="pair"]:not(:disabled)'),
    );
    const allSelected = inputs.length && inputs.every((input) => STATE.selectedPairs.has(input.value));
    inputs.forEach((input) => {
      if (allSelected) STATE.selectedPairs.delete(input.value);
      else STATE.selectedPairs.add(input.value);
    });
    render();
  });

  if (pairSearchInput) {
    pairSearchInput.addEventListener('input', () => {
      STATE.pairSearch = pairSearchInput.value;
      renderPairList();
    });
  }

  if (showCohortsInput) {
    showCohortsInput.addEventListener('change', () => {
      STATE.showCohorts = showCohortsInput.checked;
      render();
    });
  }

  if (pairPresetNewestButton) {
    pairPresetNewestButton.addEventListener('click', () => {
      STATE.selectedPairs = new Set(
        getDefaultSelectedPairs(getPairs(), getSelectedEvalNames(), getSelectedLanguageNames()),
      );
      render();
    });
  }

  if (pairPresetTopEffortButton) {
    pairPresetTopEffortButton.addEventListener('click', () => {
      STATE.selectedPairs = new Set(getTopEffortPairs());
      render();
    });
  }

  if (evalChipsEl) {
    evalChipsEl.addEventListener('change', () => {
      STATE.selectedEvals = new Set(getCheckedValues(evalChipsEl, 'eval-chip'));
      renderEvalList();
      updateAxisSelectors();
      syncErrorBarModeWithDefaults();
      render();
    });
  }

  if (heatmapMetricSelect) {
    heatmapMetricSelect.addEventListener('change', () => {
      STATE.heatmapMetric = normalizeHeatmapMetric(heatmapMetricSelect.value);
      render();
    });
  }

  if (heatmapSortSelect) {
    heatmapSortSelect.addEventListener('change', () => {
      STATE.heatmapSort = heatmapSortSelect.value === 'value' ? 'value' : 'name';
      render();
    });
  }

  if (facetToggleInput) {
    facetToggleInput.addEventListener('change', () => {
      STATE.facetByEval = facetToggleInput.checked;
      render();
    });
  }

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
    renderAxisScaleSelectors();
    render();
  });
  yAxisSelect.addEventListener('change', () => {
    STATE.yAxis = yAxisSelect.value;
    renderAxisScaleSelectors();
    render();
  });
  [
    [xScaleSelect, 'xScaleMode'],
    [yScaleSelect, 'yScaleMode'],
  ].forEach(([select, stateKey]) => {
    if (!select) return;
    select.addEventListener('change', () => {
      STATE[stateKey] = select.value === 'log' ? 'log' : 'linear';
      render();
    });
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

// Model picker: agents → model families → effort chips. Every pair keeps a
// checkbox input (data-group="pair") so selection still reads from the DOM;
// filtering and collapsed groups only hide rows.
function renderPairList(canRenderPairById) {
  pairListEl.replaceChildren();
  const rowsByPair = getRowsByPairForCurrentSelection();
  const availabilityMap = canRenderPairById || getPairAvailability(rowsByPair);
  const unavailableLabels = [];
  const search = STATE.pairSearch.trim().toLowerCase();
  const evals = getSelectedEvalNames();
  const languages = getSelectedLanguageNames();

  const agents = new Map();
  getPairs().forEach((pairId) => {
    const { agent, effort, cohort } = parsePairModel(pairId);
    const familyKey = getModelFamilyKey(pairId);
    if (!agents.has(agent)) agents.set(agent, new Map());
    const families = agents.get(agent);
    if (!families.has(familyKey)) families.set(familyKey, { cohort, pairs: [] });
    families.get(familyKey).pairs.push({ pairId, effort });
    if (!(availabilityMap.get(pairId) ?? true) && STATE.selectedPairs.has(pairId)) {
      unavailableLabels.push(pairId);
    }
  });

  agents.forEach((families, agent) => {
    const group = document.createElement('details');
    group.className = 'model-group';
    group.open = !STATE.collapsedAgents.has(agent) || Boolean(search);
    group.addEventListener('toggle', () => {
      if (search) return;
      if (group.open) STATE.collapsedAgents.delete(agent);
      else STATE.collapsedAgents.add(agent);
    });
    const summary = document.createElement('summary');
    const selectedInAgent = Array.from(families.values())
      .flatMap((family) => family.pairs)
      .filter(({ pairId }) => STATE.selectedPairs.has(pairId)).length;
    summary.appendChild(document.createTextNode(agent));
    const count = document.createElement('span');
    count.className = 'model-group-count';
    count.textContent = selectedInAgent ? `${selectedInAgent} selected` : '';
    summary.appendChild(count);
    group.appendChild(summary);

    let visibleFamilies = 0;
    Array.from(families.entries())
      .sort(([a], [b]) => compareFamiliesNewestFirst(a, b))
      .forEach(([familyKey, family]) => {
        const row = buildModelFamilyRow(familyKey, family, availabilityMap, rowsByPair, evals, languages);
        const anySelected = family.pairs.some(({ pairId }) => STATE.selectedPairs.has(pairId));
        const haystack = `${familyKey} ${formatModelFamilyDisplay(familyKey)} ${family.pairs
          .map(({ effort }) => effort)
          .join(' ')}`.toLowerCase();
        const matchesSearch = !search || search.split(/\s+/).every((term) => haystack.includes(term));
        const cohortHidden = family.cohort && !STATE.showCohorts && !anySelected;
        if (!matchesSearch || cohortHidden) row.classList.add('hidden');
        else visibleFamilies += 1;
        group.appendChild(row);
      });
    if (!visibleFamilies) group.classList.add('hidden');
    pairListEl.appendChild(group);
  });

  if (pairUnavailableHintEl) {
    if (unavailableLabels.length) {
      const noun = unavailableLabels.length === 1 ? 'selection has' : 'selections have';
      pairUnavailableHintEl.textContent =
        `${unavailableLabels.length} ${noun} no data for this view: ${unavailableLabels.join(', ')}.`;
    } else {
      pairUnavailableHintEl.textContent = '';
    }
  }

  return availabilityMap;
}

// Newest model versions first within an agent; cohort variants follow their base model.
function compareFamiliesNewestFirst(aKey, bKey) {
  const aModel = splitPairId(aKey).model;
  const bModel = splitPairId(bKey).model;
  const aCohort = / \[[^\]]+\]$/.test(aModel);
  const bCohort = / \[[^\]]+\]$/.test(bModel);
  const aLine = getModelLine(aModel.replace(/ \[[^\]]+\]$/, ''));
  const bLine = getModelLine(bModel.replace(/ \[[^\]]+\]$/, ''));
  const versionDiff = compareModelCandidates(
    { version: bLine.version, effortRank: 0 },
    { version: aLine.version, effortRank: 0 },
  );
  if (versionDiff) return versionDiff;
  if (aLine.line !== bLine.line) return aLine.line.localeCompare(bLine.line);
  if (aCohort !== bCohort) return aCohort ? 1 : -1;
  return aKey.localeCompare(bKey);
}

function buildModelFamilyRow(familyKey, family, availabilityMap, rowsByPair, evals, languages) {
  const row = document.createElement('div');
  row.className = 'model-family';
  if (family.cohort) row.classList.add('model-family-cohort');

  const name = document.createElement('button');
  name.type = 'button';
  name.className = 'model-family-name';
  name.dataset.action = 'toggle-family';
  name.dataset.family = familyKey;
  name.textContent = formatModelFamilyDisplay(familyKey);
  name.title = `${familyKey}\nClick to select or clear every available effort.`;
  const selectable = family.pairs.filter(({ pairId }) => availabilityMap.get(pairId) ?? true);
  const selectedCount = family.pairs.filter(({ pairId }) => STATE.selectedPairs.has(pairId)).length;
  name.setAttribute(
    'aria-pressed',
    selectedCount && selectedCount === selectable.length ? 'true' : selectedCount ? 'mixed' : 'false',
  );
  name.disabled = !selectable.length;
  row.appendChild(name);

  const chips = document.createElement('div');
  chips.className = 'effort-chips';
  family.pairs
    .slice()
    .sort((a, b) => getEffortRank(a.effort) - getEffortRank(b.effort))
    .forEach(({ pairId, effort }) => {
      const isSelectable = availabilityMap.get(pairId) ?? true;
      const chip = document.createElement('label');
      chip.className = 'effort-chip';
      const minRuns = getMinRunsPerCell(rowsByPair.get(pairId) || [], evals, languages);
      if (isSelectable && minRuns < LOW_RUN_COUNT_THRESHOLD) chip.classList.add('effort-chip-low-n');
      chip.classList.toggle('unavailable-option', !isSelectable);
      chip.title = isSelectable
        ? `${pairTitleWithVersion(pairId)}\nFewest runs in a selected eval/language cell: ${minRuns}`
        : `${pairId}\nNo data for this view`;
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.dataset.group = 'pair';
      input.value = pairId;
      input.checked = STATE.selectedPairs.has(pairId);
      input.disabled = !isSelectable;
      chip.appendChild(input);
      chip.appendChild(document.createTextNode(effort ? abbreviateEffort(effort) : 'default'));
      chips.appendChild(chip);
    });
  row.appendChild(chips);
  return row;
}

// Highest effort of every model family with data for the current view.
function getTopEffortPairs() {
  const availability = getPairAvailability(getRowsByPairForCurrentSelection());
  const best = new Map();
  getPairs().forEach((pairId) => {
    if (!availability.get(pairId)) return;
    const { effort, cohort } = parsePairModel(pairId);
    if (cohort && !STATE.showCohorts) return;
    const key = getModelFamilyKey(pairId);
    const rank = getEffortRank(effort);
    const current = best.get(key);
    if (!current || rank > current.rank) best.set(key, { pairId, rank });
  });
  return Array.from(best.values()).map((entry) => entry.pairId);
}

function renderLanguageList() {
  languageListEl.replaceChildren();
  getLanguages().forEach((language) => {
    languageListEl.appendChild(
      buildFilterChip('language', language, language, STATE.selectedLanguages.has(language)),
    );
  });
}

function renderEvalChips() {
  if (!evalChipsEl) return;
  evalChipsEl.replaceChildren();
  getEvals().forEach((evalName) => {
    evalChipsEl.appendChild(
      buildFilterChip('eval-chip', evalName, evalName, STATE.selectedEvals.has(evalName)),
    );
  });
}

function buildFilterChip(group, value, text, checked) {
  const chip = document.createElement('label');
  chip.className = 'filter-chip';
  const input = document.createElement('input');
  input.type = 'checkbox';
  input.dataset.group = group;
  input.value = value;
  input.checked = checked;
  chip.appendChild(input);
  chip.appendChild(document.createTextNode(text));
  return chip;
}

function renderEvalList() {
  renderEvalChips();
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
  renderAxisScaleSelectors();
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
    : 'auto';
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

const VIEW_MODES = ['graph', 'heatmap', 'table'];

function normalizeViewMode(mode) {
  return VIEW_MODES.includes(mode) ? mode : 'graph';
}

function syncViewModeControls() {
  document.body.classList.toggle('table-view-active', STATE.viewMode === 'table');
  heatmapControls.forEach((el) => {
    el.classList.toggle('hidden', STATE.viewMode !== 'heatmap');
  });
  if (heatmapPanel) heatmapPanel.classList.toggle('hidden', STATE.viewMode !== 'heatmap');
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

// Shareable view state: every render mirrors the current selection into the
// query string, and a page load with a query string restores it.
function writeUrlState() {
  if (!window.history?.replaceState) return;
  const params = new URLSearchParams();
  params.set('view', STATE.viewMode);
  params.set('x', STATE.xAxis);
  params.set('y', STATE.yAxis);
  if (STATE.xScaleMode === 'log') params.set('xs', 'log');
  if (STATE.yScaleMode === 'log') params.set('ys', 'log');
  params.set('report', STATE.reportType);
  params.set('err', STATE.errorBarMode);
  params.set('color', STATE.colorMode);
  params.set('labels', STATE.labelMode);
  params.set('names', STATE.nameMode);
  params.set('evals', getSelectedEvalNames().join(','));
  getSelectedEvalNames().forEach((evalName) => {
    const versions = Array.from(STATE.selectedEvalVersions.get(evalName) || []);
    params.append('ver', `${evalName}:${versions.join('|')}`);
  });
  params.set('langs', getSelectedLanguageNames().join(','));
  const pairs = getPairs().filter((pairId) => STATE.selectedPairs.has(pairId));
  if (pairs.length) {
    pairs.forEach((pairId) => params.append('pair', pairId));
  } else {
    params.set('pair', '');
  }
  STATE.hiddenColorKeys.forEach((key) => params.append('hide', key));
  if (STATE.viewMode === 'table') {
    params.set('tmode', STATE.tableMode);
    params.set('tgroup', STATE.tableGroupBy);
    if (STATE.tableSortBy) params.set('tsort', STATE.tableSortBy);
    params.set('tdir', STATE.tableSortDirection);
  }
  if (STATE.viewMode === 'heatmap') {
    params.set('hm', STATE.heatmapMetric);
    if (STATE.heatmapSort !== 'name') params.set('hs', STATE.heatmapSort);
  }
  if (!STATE.facetByEval) params.set('facet', 'off');
  if (STATE.showCohorts) params.set('cohorts', 'show');
  if (STATE.controlsCollapsed) params.set('controls', 'hidden');
  const nextUrl = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
  try {
    window.history.replaceState(null, '', nextUrl);
  } catch (error) {
    // Some embedded or file:// contexts reject replaceState; the view still works.
  }
}

function applyUrlState() {
  const params = new URLSearchParams(window.location.search);
  if (![...params.keys()].length) return;
  const pick = (key, options) => {
    const value = params.get(key);
    return options.includes(value) ? value : null;
  };
  const listParam = (key, available) =>
    String(params.get(key) || '')
      .split(',')
      .filter((value) => available.includes(value));

  const view = pick('view', VIEW_MODES);
  if (view) STATE.viewMode = view;
  const axisIds = AXIS_OPTIONS.map((axis) => axis.id);
  STATE.xAxis = pick('x', axisIds) || STATE.xAxis;
  STATE.yAxis = pick('y', axisIds.filter((id) => METRICS[id])) || STATE.yAxis;
  STATE.xScaleMode = params.get('xs') === 'log' ? 'log' : 'linear';
  STATE.yScaleMode = params.get('ys') === 'log' ? 'log' : 'linear';
  STATE.reportType = pick('report', REPORT_TYPE_OPTIONS.map((o) => o.id)) || STATE.reportType;
  STATE.errorBarMode = pick('err', ERROR_BAR_OPTIONS.map((o) => o.id)) || STATE.errorBarMode;
  STATE.colorMode = pick('color', COLOR_MODE_OPTIONS.map((o) => o.id)) || STATE.colorMode;
  STATE.labelMode = pick('labels', LABEL_MODE_OPTIONS.map((o) => o.id)) || STATE.labelMode;
  STATE.nameMode = pick('names', NAME_MODE_OPTIONS.map((o) => o.id)) || STATE.nameMode;

  const evals = listParam('evals', getEvals());
  if (evals.length) STATE.selectedEvals = new Set(evals);
  params.getAll('ver').forEach((entry) => {
    const separator = entry.indexOf(':');
    if (separator < 0) return;
    const evalName = entry.slice(0, separator);
    const available = new Set(getEvalVersions(evalName).map(versionKey));
    const versions = entry
      .slice(separator + 1)
      .split('|')
      .filter((version) => available.has(versionKey(version)));
    if (versions.length) STATE.selectedEvalVersions.set(evalName, new Set(versions));
  });
  const languages = listParam('langs', getLanguages());
  if (languages.length) STATE.selectedLanguages = new Set(languages);

  const selectedEvals = getSelectedEvalNames();
  const selectedLanguages = getSelectedLanguageNames();
  if (params.has('pair')) {
    const available = new Set(getPairs());
    STATE.selectedPairs = new Set(params.getAll('pair').filter((pairId) => available.has(pairId)));
  } else {
    STATE.selectedPairs = new Set(getDefaultSelectedPairs(getPairs(), selectedEvals, selectedLanguages));
  }
  STATE.pairEligibilitySyncKey = getEvalLanguageSelectionKey(selectedEvals, selectedLanguages);
  STATE.hiddenColorKeys = new Set(params.getAll('hide'));

  const tableMode = pick('tmode', ['summary', 'runs']);
  if (tableMode) STATE.tableMode = tableMode;
  STATE.tableGroupBy =
    pick('tgroup', ['pair', 'pair_language', 'pair_eval', 'pair_eval_language']) || STATE.tableGroupBy;
  if (params.has('tsort')) STATE.tableSortBy = params.get('tsort');
  STATE.tableSortDirection = pick('tdir', ['asc', 'desc']) || STATE.tableSortDirection;
  STATE.controlsCollapsed = params.get('controls') === 'hidden';
  STATE.heatmapMetric = normalizeHeatmapMetric(params.get('hm'));
  STATE.heatmapSort = params.get('hs') === 'value' ? 'value' : 'name';
  STATE.facetByEval = params.get('facet') !== 'off';
  STATE.showCohorts = params.get('cohorts') === 'show';
}

function render() {
  if (syncSelectedPairsForCurrentEvalLanguages()) {
    renderPairList();
  }
  writeUrlState();

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
    STATE.viewMode === 'graph'
      ? getPairAvailability(rowsByPair)
      : getPairAvailabilityForRows(rowsByPair);
  renderPairList(canRenderPairById);

  if (STATE.viewMode === 'table') {
    renderTableView();
    return;
  }
  if (STATE.viewMode === 'heatmap') {
    renderHeatmapView(rowsByPair);
    return;
  }

  if (shouldFacetByEval()) {
    renderFacetedGraph(colorMap, rowsByPair);
    return;
  }
  showSingleChart();

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
  resetSeriesHandles();
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
  } else if (STATE.colorMode === 'model') {
    colorKeys = Array.from(
      new Set(Array.from(STATE.selectedPairs).map((pairId) => getModelFamilyKey(pairId))),
    ).sort();
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
  showSingleChart();
  clearChart();
  heatmapTableEl?.replaceChildren();
  if (heatmapScaleEl) heatmapScaleEl.replaceChildren();
  if (heatmapEmptyEl) {
    heatmapEmptyEl.textContent = message;
    heatmapEmptyEl.classList.remove('hidden');
  }
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

const HEATMAP_METRIC_OPTIONS = [
  { id: 'percent', label: 'Pass rate' },
  { id: 'cost', label: 'Cost (USD)' },
  { id: 'tokens_total', label: 'Tokens Total' },
  { id: 'wall', label: 'Wall Clock Time' },
];

function normalizeHeatmapMetric(metric) {
  return HEATMAP_METRIC_OPTIONS.some((option) => option.id === metric) ? metric : 'percent';
}

function renderHeatmapControls() {
  if (!heatmapMetricSelect || !heatmapSortSelect) return;
  heatmapMetricSelect.replaceChildren();
  HEATMAP_METRIC_OPTIONS.forEach((metric) => {
    const option = document.createElement('option');
    option.value = metric.id;
    option.textContent = metric.label;
    heatmapMetricSelect.appendChild(option);
  });
  STATE.heatmapMetric = normalizeHeatmapMetric(STATE.heatmapMetric);
  heatmapMetricSelect.value = STATE.heatmapMetric;
  heatmapSortSelect.value = STATE.heatmapSort;
}

// Models × (eval, language) matrix of one metric. Pass rate is colored on a
// fixed 0–100% scale; the other metrics use a log scale over the visible
// cells, where lower is better.
function renderHeatmapView(rowsByPair) {
  clearChart();
  heatmapTableEl.replaceChildren();
  heatmapScaleEl.replaceChildren();
  const metricId = normalizeHeatmapMetric(STATE.heatmapMetric);
  const metric = METRICS[metricId];
  const evals = getSelectedEvalNames();
  const languages = getSelectedLanguageNames();
  const columns = evals.flatMap((evalName) => languages.map((language) => ({ evalName, language })));
  heatmapTitleEl.textContent = `${metric.label} by eval and language (${getReportTypeLabel(
    STATE.reportType,
  ).toLowerCase()})`;

  const rows = getPairs()
    .filter((pairId) => STATE.selectedPairs.has(pairId) && (rowsByPair.get(pairId) || []).length)
    .map((pairId) => {
      const pairRows = rowsByPair.get(pairId) || [];
      const cells = columns.map(({ evalName, language }) => {
        const subset = pairRows.filter((row) => row.eval === evalName && row.language === language);
        const summary = summarizeMetric(subset, metricId);
        return {
          evalName,
          language,
          runs: subset.length,
          summary,
          value: summary.hasData ? getReportValue(summary, STATE.reportType) : NaN,
        };
      });
      const values = cells.map((cell) => cell.value).filter(Number.isFinite);
      const overall = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : NaN;
      return { pairId, cells, overall, covered: values.length };
    });

  if (!rows.length) {
    heatmapEmptyEl.textContent = 'No selected configuration has runs for these evals and languages.';
    heatmapEmptyEl.classList.remove('hidden');
    return;
  }
  heatmapEmptyEl.classList.add('hidden');

  if (STATE.heatmapSort === 'value') {
    const direction = metric.higherIsBetter ? -1 : 1;
    rows.sort((a, b) => {
      if (!Number.isFinite(a.overall)) return 1;
      if (!Number.isFinite(b.overall)) return -1;
      return direction * (a.overall - b.overall);
    });
  } else {
    rows.sort((a, b) =>
      formatAgentModelDisplay(a.pairId).localeCompare(formatAgentModelDisplay(b.pairId), undefined, {
        numeric: true,
      }),
    );
  }

  const allValues = rows.flatMap((row) => row.cells.map((cell) => cell.value)).filter(Number.isFinite);
  const colorFor = buildHeatmapColorScale(metricId, allValues);

  const thead = document.createElement('thead');
  const evalHeader = document.createElement('tr');
  const corner = document.createElement('th');
  corner.textContent = 'Configuration';
  corner.rowSpan = languages.length > 1 ? 2 : 1;
  corner.className = 'heatmap-row-header';
  evalHeader.appendChild(corner);
  evals.forEach((evalName) => {
    const th = document.createElement('th');
    th.colSpan = languages.length;
    th.className = 'heatmap-eval-header';
    th.textContent = languages.length > 1 ? evalName : `${evalName} · ${languages[0]}`;
    evalHeader.appendChild(th);
  });
  const overallHeader = document.createElement('th');
  overallHeader.rowSpan = languages.length > 1 ? 2 : 1;
  overallHeader.className = 'numeric heatmap-overall-header';
  overallHeader.textContent = 'Mean of cells';
  overallHeader.title = 'Average of the cells that have runs; Coverage shows how many cells that is.';
  evalHeader.appendChild(overallHeader);
  thead.appendChild(evalHeader);
  if (languages.length > 1) {
    const languageHeader = document.createElement('tr');
    columns.forEach(({ language }) => {
      const th = document.createElement('th');
      th.className = 'heatmap-language-header';
      th.textContent = language;
      languageHeader.appendChild(th);
    });
    thead.appendChild(languageHeader);
  }
  heatmapTableEl.appendChild(thead);

  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    const label = document.createElement('th');
    label.scope = 'row';
    label.className = 'heatmap-row-header';
    label.textContent = formatAgentModelDisplay(row.pairId);
    label.title = pairTitleWithVersion(row.pairId);
    tr.appendChild(label);
    row.cells.forEach((cell) => {
      const td = document.createElement('td');
      td.className = 'heatmap-cell';
      if (!Number.isFinite(cell.value)) {
        td.classList.add('heatmap-cell-empty');
        td.textContent = '—';
        td.title = `${cell.evalName} · ${cell.language}: no runs`;
      } else {
        td.style.background = colorFor(cell.value);
        const value = document.createElement('span');
        value.className = 'heatmap-value';
        value.textContent = metric.formatMean(cell.value);
        const runs = document.createElement('span');
        runs.className = 'heatmap-runs';
        runs.textContent = `n=${cell.runs}`;
        td.append(value, runs);
        if (cell.runs < LOW_RUN_COUNT_THRESHOLD) td.classList.add('heatmap-cell-low-n');
        td.title = `${row.pairId}\n${cell.evalName} · ${cell.language}\n${metric.formatSummary(
          cell.summary,
        )}\nRuns: ${cell.runs}`;
      }
      tr.appendChild(td);
    });
    const overall = document.createElement('td');
    overall.className = 'numeric heatmap-overall';
    overall.textContent = Number.isFinite(row.overall)
      ? `${metric.formatMean(row.overall)} (${row.covered}/${columns.length})`
      : '—';
    tr.appendChild(overall);
    tbody.appendChild(tr);
  });
  heatmapTableEl.appendChild(tbody);
  renderHeatmapScale(metricId, allValues, colorFor);
}

function buildHeatmapColorScale(metricId, values) {
  const metric = METRICS[metricId];
  // Map "goodness" in [0, 1] to a red → amber → green ramp.
  const ramp = (goodness) => {
    const g = Math.min(1, Math.max(0, goodness));
    return `hsl(${Math.round(4 + g * 128)}, 62%, ${Math.round(80 + g * 4)}%)`;
  };
  if (metric.isPercent) return (value) => ramp(value / 100);
  const positive = values.filter((value) => value > 0);
  if (!positive.length) return () => ramp(0.5);
  const low = Math.log10(Math.min(...positive));
  const high = Math.log10(Math.max(...positive));
  return (value) => {
    if (!(value > 0) || high === low) return ramp(0.5);
    const fraction = (Math.log10(value) - low) / (high - low);
    return ramp(metric.higherIsBetter ? fraction : 1 - fraction);
  };
}

function renderHeatmapScale(metricId, values, colorFor) {
  const metric = METRICS[metricId];
  const finite = values.filter(Number.isFinite);
  if (!finite.length) return;
  const low = metric.isPercent ? 0 : Math.min(...finite);
  const high = metric.isPercent ? 100 : Math.max(...finite);
  const lowLabel = document.createElement('span');
  lowLabel.textContent = metric.formatMean(low);
  const bar = document.createElement('span');
  bar.className = 'heatmap-scale-bar';
  const stops = [0, 0.25, 0.5, 0.75, 1].map((t) => {
    const value = metric.isPercent ? t * 100 : Math.pow(10, Math.log10(low || 1e-9) + t * (Math.log10(high || 1) - Math.log10(low || 1e-9)));
    return colorFor(value);
  });
  bar.style.background = `linear-gradient(90deg, ${stops.join(', ')})`;
  const highLabel = document.createElement('span');
  highLabel.textContent = metric.formatMean(high);
  const note = document.createElement('span');
  note.className = 'heatmap-scale-note';
  note.textContent = metric.isPercent ? '' : 'log scale, lower is greener';
  heatmapScaleEl.append(lowLabel, bar, highLabel, note);
}

// ---- Faceted graph: one scatter per selected eval -------------------------

// The eval whose facet is being drawn; scopes run-coverage checks to it.
let CURRENT_FACET_EVAL = null;
let plotClipCounter = 0;

function shouldFacetByEval() {
  return (
    STATE.viewMode === 'graph' &&
    STATE.facetByEval &&
    getSelectedEvalNames().length > 1 &&
    !isCategoricalXAxis(STATE.xAxis)
  );
}

function showSingleChart() {
  if (facetGridEl) {
    facetGridEl.replaceChildren();
    facetGridEl.classList.add('hidden');
  }
  mainChartSvg.classList.remove('hidden');
  chartWrapEl?.classList.remove('chart-wrap-faceted');
  chartSvg = mainChartSvg;
}

function renderFacetedGraph(colorMap, rowsByPair) {
  clearChart();
  mainChartSvg.classList.add('hidden');
  chartWrapEl?.classList.add('chart-wrap-faceted');
  facetGridEl.replaceChildren();
  facetGridEl.classList.remove('hidden');
  legendEl.innerHTML = '';
  chartEmpty.classList.add('hidden');
  resetSeriesHandles();

  const allPoints = [];
  getSelectedEvalNames().forEach((evalName) => {
    const facet = document.createElement('figure');
    facet.className = 'facet';
    const title = document.createElement('figcaption');
    title.textContent = `${evalName} · ${formatVersionSummary(evalName).replace(/^Versions?:\s*/, 'v')}`;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    facet.append(title, svg);
    facetGridEl.appendChild(facet);

    const facetRows = new Map();
    rowsByPair.forEach((rows, pairId) => {
      const subset = rows.filter((row) => row.eval === evalName);
      if (subset.length) facetRows.set(pairId, subset);
    });
    CURRENT_FACET_EVAL = evalName;
    try {
      const points = buildPoints(colorMap, facetRows);
      allPoints.push(...points);
      const visible = points.filter((point) => !STATE.hiddenColorKeys.has(point.colorModeKey));
      if (!visible.length) {
        const empty = document.createElement('p');
        empty.className = 'chart-empty';
        empty.textContent = points.length ? 'All series hidden.' : 'No runs for the selected models.';
        facet.replaceChild(empty, svg);
        return;
      }
      chartSvg = svg;
      renderPlot(visible);
    } finally {
      chartSvg = mainChartSvg;
      CURRENT_FACET_EVAL = null;
    }
  });

  if (!allPoints.length) {
    showNoData('No matching results for the current filters.');
    return;
  }
  renderLegend(allPoints, colorMap);
  validationEl.textContent = '';
}

// ---- Legend hover highlighting --------------------------------------------

let SERIES_HANDLES = [];

function resetSeriesHandles() {
  SERIES_HANDLES = [];
}

function highlightSeries(key) {
  if (!chartWrapEl) return;
  chartWrapEl.classList.add('highlighting');
  chartWrapEl.querySelectorAll('[data-color-key]').forEach((el) => {
    el.classList.toggle('series-active', el.dataset.colorKey === key);
  });
  SERIES_HANDLES.filter((handle) => handle.key === key).forEach((handle) => handle.show());
}

function clearSeriesHighlight() {
  if (!chartWrapEl) return;
  chartWrapEl.classList.remove('highlighting');
  chartWrapEl.querySelectorAll('.series-active').forEach((el) => el.classList.remove('series-active'));
  SERIES_HANDLES.forEach((handle) => handle.hide());
}

function resolveLabelMode(pointCount) {
  const mode = normalizeLabelMode(STATE.labelMode);
  if (mode !== 'auto') return mode;
  return pointCount <= AUTO_LABEL_POINT_LIMIT ? 'all' : 'pareto';
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
      title: (row) => pairTitleWithVersion(row.pairId),
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
      title: (row) => pairTitleWithVersion(rowPairId(row)),
    },
    { key: 'run', label: 'Run', numeric: true, render: (row) => row.run_id || 'n/a' },
    { key: 'version', label: 'Graded', render: (row) => row.eval_version || 'n/a' },
    { key: 'generation_version', label: 'Generated', render: (row) => row.generation_eval_version || row.eval_version || 'n/a' },
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

// Cache mapping a pairId -> the agent CLI version seen for it. Lets the label
// surface which CLI generation produced a row (e.g. claude-code 2.0.2 vs
// 2.1.120) without baking version into the grouping key. Rebuilt when
// STATE.rows changes identity.
let _pairVersionCache = null;
let _pairVersionCacheRows = null;
function pairAgentVersion(pairId) {
  if (_pairVersionCacheRows !== STATE.rows) {
    _pairVersionCache = {};
    (STATE.rows || []).forEach((r) => {
      const id = rowPairId(r);
      if (r.agent_version && !_pairVersionCache[id]) _pairVersionCache[id] = r.agent_version;
    });
    _pairVersionCacheRows = STATE.rows;
  }
  return _pairVersionCache[pairId] || '';
}

function formatAgentModelShort(pairId) {
  // Abbreviated mode stays clean (no inline CLI version) — the version is
  // surfaced on hover via the column `title` (see pairTitleWithVersion).
  const { agent, model } = splitPairId(pairId);
  const short = `${abbreviateAgent(agent)} / ${abbreviateModel(model)}`;
  // Never let two different pairs share a label; fall back to the full model id.
  return getAmbiguousShortLabels().has(short) ? `${abbreviateAgent(agent)} / ${model}` : short;
}

let _ambiguousShortLabels = new Set();
let _ambiguousShortLabelsRows = null;

function getAmbiguousShortLabels() {
  if (_ambiguousShortLabelsRows !== STATE.rows) {
    const counts = new Map();
    getPairs().forEach((pairId) => {
      const { agent, model } = splitPairId(pairId);
      const short = `${abbreviateAgent(agent)} / ${abbreviateModel(model)}`;
      counts.set(short, (counts.get(short) || 0) + 1);
    });
    _ambiguousShortLabels = new Set(
      Array.from(counts.entries())
        .filter(([, count]) => count > 1)
        .map(([short]) => short),
    );
    _ambiguousShortLabelsRows = STATE.rows;
  }
  return _ambiguousShortLabels;
}

function formatModelFamilyDisplay(familyKey) {
  const { agent, model } = splitPairId(familyKey);
  if (normalizeNameMode(STATE.nameMode) === 'full') return `${agent} / ${model}`;
  const cohortMatch = model.match(/^(.*?)( \[[^\]]+\])$/);
  const baseModel = cohortMatch ? cohortMatch[1] : model;
  const cohort = cohortMatch ? ` [${abbreviateCohort(cohortMatch[2].slice(2, -1))}]` : '';
  return `${abbreviateAgent(agent)} / ${abbreviateModel(baseModel)}${cohort}`;
}

function formatAgentModelFull(pairId) {
  // Full-names mode inlines the CLI version after the agent where available,
  // e.g. "claude-code 2.0.2 / claude-opus-4-20250514 (max)".
  const { agent, model } = splitPairId(pairId);
  const ver = pairAgentVersion(pairId);
  const agentLabel = ver ? `${agent} ${ver}` : agent;
  return `${agentLabel} / ${model}`;
}

// Hover-tooltip text for the agent/model column: the full pair id plus the CLI
// version where available. Used in both name modes so the version is always
// reachable on hover even when the label itself omits it.
function pairTitleWithVersion(pairId) {
  const id = rowPairId(pairId);
  const ver = pairAgentVersion(id);
  return ver ? `${id} · CLI ${ver}` : id;
}

function formatAgentModelDisplay(pairId) {
  const fullName = rowPairId(pairId);
  return normalizeNameMode(STATE.nameMode) === 'full'
    ? formatAgentModelFull(fullName)
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
  // claude-code is a single agent across CLI generations; the CLI version
  // (e.g. 2.0.2 vs 2.1.120) is appended in formatAgentModelShort, not encoded
  // as a separate agent id.
  if (normalized === 'claude-code') return 'CC';
  if (normalized === 'codex-cli') return 'C';
  if (normalized === 'gemini-cli') return 'G';
  const parts = normalized.split(/[-_\s]+/).filter(Boolean);
  return parts.length
    ? parts.map((part) => part[0]).join('').toUpperCase()
    : 'n/a';
}

function abbreviateModel(model) {
  const cohortLabel = String(model || '').match(/^(.*) \[([^\]]+)\]$/);
  if (cohortLabel) return `${abbreviateModel(cohortLabel[1])} [${abbreviateCohort(cohortLabel[2])}]`;
  const { baseModel, effort } = splitModelEffortLabel(model);
  // Drop routing prefixes such as "openrouter/moonshotai/".
  const normalized = String(baseModel || '').toLowerCase().split('/').pop();
  const withEffort = (label) => (effort ? `${label} (${abbreviateEffort(effort)})` : label);
  const claudeMatch = normalized.match(/^claude-(opus|sonnet|haiku|fable)-(\d+)(?:-(\d+))?/);
  if (claudeMatch) {
    // An 8-digit third group is a date (e.g. 20250514), so the model is
    // major.0 — claude-opus-4-20250514 → O-4.0. Without a minor: S-5.
    const minorGroup = claudeMatch[3];
    const minor = !minorGroup ? '' : minorGroup.length === 8 ? '.0' : `.${minorGroup}`;
    return withEffort(`${claudeMatch[1][0].toUpperCase()}-${claudeMatch[2]}${minor}`);
  }
  const gptMatch = normalized.match(/^gpt-(\d+(?:\.\d+)?)(?:-([a-z][a-z0-9]*))?/);
  if (gptMatch) {
    // Keep named variants (gpt-5.6-sol → 5.6 Sol) so sibling models stay distinct.
    const variant = gptMatch[2] || '';
    const suffix =
      variant === 'mini'
        ? '-m'
        : variant === 'codex'
          ? '-c'
          : variant
            ? ` ${variant[0].toUpperCase()}${variant.slice(1)}`
            : '';
    return withEffort(`${gptMatch[1]}${suffix}`);
  }
  const geminiMatch = normalized.match(/^gemini-(\d+(?:\.\d+)?)(?:-(flash|pro))?/);
  if (geminiMatch) {
    const version = geminiMatch[1].includes('.') ? geminiMatch[1] : `${geminiMatch[1]}.0`;
    if (geminiMatch[2] === 'flash') return withEffort(`${version}-f`);
    if (geminiMatch[2] === 'pro') return withEffort(`${version}-p`);
    return withEffort(version);
  }
  return withEffort(normalized || 'n/a');
}

// Short cohort tag for abbreviated labels: drops commit hashes and anything
// after ';', then keeps whole words up to about 12 characters.
function abbreviateCohort(cohort) {
  const cleaned = String(cohort || '')
    .split(';')[0]
    .replace(/[0-9a-f]{8,}/gi, '')
    .trim();
  if (cleaned.length <= 12) return cleaned;
  let result = '';
  for (const match of cleaned.matchAll(/[^\s-]+[\s-]?/g)) {
    if ((result + match[0]).trimEnd().length > 12) break;
    result += match[0];
  }
  return `${result.replace(/[\s-]+$/, '') || cleaned.slice(0, 11)}…`;
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
  if (STATE.colorMode === 'model') return getModelFamilyKey(pairId);
  return pairId;
}

function summarizePoint(pairId, color, rows, language, options) {
  const xSummary = summarizeMetric(rows, options.xAxis);
  const ySummary = summarizeMetric(rows, options.yAxis);
  if (!xSummary.hasData || !ySummary.hasData) return null;

  const cellEvals =
    options.xAxis === 'eval'
      ? [options.xCategoryValue]
      : CURRENT_FACET_EVAL
        ? [CURRENT_FACET_EVAL]
        : getSelectedEvalNames();
  const cellLanguages = language ? [language] : getSelectedLanguageNames();
  const minRunsPerCell = getMinRunsPerCell(rows, cellEvals, cellLanguages);

  return {
    pairId,
    minRunsPerCell,
    lowRunCount: minRunsPerCell < LOW_RUN_COUNT_THRESHOLD,
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

// Smallest run count across the eval × language cells a point aggregates;
// 0 means at least one cell has no runs at all.
function getMinRunsPerCell(rows, evals, languages) {
  const counts = new Map();
  rows.forEach((row) => {
    const key = `${row.eval}\u0000${row.language}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  });
  let min = Infinity;
  evals.forEach((evalName) => {
    languages.forEach((language) => {
      min = Math.min(min, counts.get(`${evalName}\u0000${language}`) || 0);
    });
  });
  return Number.isFinite(min) ? min : 0;
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
    if (!hidden) {
      row.addEventListener('mouseenter', () => highlightSeries(key));
      row.addEventListener('focus', () => highlightSeries(key));
      row.addEventListener('mouseleave', clearSeriesHighlight);
      row.addEventListener('blur', clearSeriesHighlight);
    }
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
  if (STATE.colorMode === 'model') return formatModelFamilyDisplay(key);
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

// In model color mode, link each model's effort levels (low → max) so a
// model's cost/quality trade-off reads as one curve.
function drawEffortConnectors(points, xScale, yScale, layer) {
  if (STATE.colorMode !== 'model') return;
  if (isCategoricalXAxis(STATE.xAxis)) return;
  const byFamily = new Map();
  points.forEach((point) => {
    if (!Number.isFinite(point.xValue) || !Number.isFinite(point.yValue)) return;
    const key = point.colorModeKey;
    if (!byFamily.has(key)) byFamily.set(key, []);
    byFamily.get(key).push(point);
  });
  byFamily.forEach((familyPoints) => {
    if (familyPoints.length < 2) return;
    const ordered = familyPoints
      .slice()
      .sort(
        (a, b) =>
          getEffortRank(parsePairModel(a.pairId).effort) -
          getEffortRank(parsePairModel(b.pairId).effort),
      );
    const line = createSvgElement('polyline');
    line.setAttribute('class', 'effort-line');
    line.dataset.colorKey = ordered[0].colorModeKey || '';
    line.setAttribute('points', ordered.map((p) => `${xScale(p.xValue)},${yScale(p.yValue)}`).join(' '));
    line.setAttribute('fill', 'none');
    line.style.stroke = ordered[0].color;
    layer.appendChild(line);
  });
}

// Marker size encodes effort in model color mode (larger = more effort).
function getPointRadius(point) {
  if (STATE.colorMode !== 'model') return 7.3;
  const rank = getEffortRank(parsePairModel(point.pairId).effort);
  if (rank < 0) return 7.3;
  return 5.4 + (rank / (EFFORT_ORDER.length - 1)) * 3.6;
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
  const svgForTooltip = chartSvg;

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

  const xIsLog = isLogAxis('x');
  const yIsLog = isLogAxis('y');
  const xDomain = buildPlotDomain(points, STATE.xAxis, 'x', xIsLog);
  const yDomain = buildPlotDomain(points, STATE.yAxis, 'y', yIsLog);
  const xCategories = getSelectedAxisCategories(STATE.xAxis);
  const xScale = createXScale(xDomain, xCategories, plotLeft, plotRight, xIsLog);
  const yScale = createYScale(yDomain, plotTop, plotHeight, yIsLog);

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
    xIsLog,
    yIsLog,
  });

  const defs = createSvgElement('defs');
  const clipPath = createSvgElement('clipPath');
  plotClipCounter += 1;
  const clipId = `plot-clip-${plotClipCounter}`;
  clipPath.setAttribute('id', clipId);
  // Pad the clip so markers at the domain edge (e.g. 100% pass rate) draw whole.
  const clipPad = 11;
  const clipRect = createSvgElement('rect');
  clipRect.setAttribute('x', String(plotLeft - clipPad));
  clipRect.setAttribute('y', String(plotTop - clipPad));
  clipRect.setAttribute('width', String(plotWidth + 2 * clipPad));
  clipRect.setAttribute('height', String(plotHeight + 2 * clipPad));
  clipPath.appendChild(clipRect);
  defs.appendChild(clipPath);
  chartSvg.appendChild(defs);

  const dataLayer = createSvgElement('g');
  dataLayer.setAttribute('clip-path', `url(#${clipId})`);
  const labelsLayer = createSvgElement('g');
  labelsLayer.setAttribute('class', 'labels-layer');
  const markerLabels = [];
  const errorBarLines = [];
  const labelMode = resolveLabelMode(points.length);

  const frontierSet = computeParetoFrontier(points, STATE.xAxis, STATE.yAxis);
  drawFrontierConnector(points, frontierSet, xScale, yScale, dataLayer);
  drawEffortConnectors(points, xScale, yScale, dataLayer);

  points.forEach((point) => {
    const isOnFrontier = frontierSet.has(point);
    const baseRadius = getPointRadius(point);
    const hoverRadius = baseRadius + 1.5;

    const x = point.xAsCategory
      ? xScale(xCategories.indexOf(point.xCategoryValue))
      : xScale(point.xValue);
    const y = yScale(point.yValue);

    const g = createSvgElement('g');
    g.setAttribute('transform', `translate(${x}, ${y})`);
    g.dataset.colorKey = point.colorModeKey || '';

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
    // Hollow markers flag points backed by fewer runs than the threshold.
    pointCircle.setAttribute('fill', point.lowRunCount ? '#ffffff' : point.color);
    if (point.lowRunCount) pointCircle.style.stroke = point.color;
    const pointClass = `point point-marker${isOnFrontier ? ' point-frontier' : ''}${
      point.lowRunCount ? ' point-low-n' : ''
    }`;
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
    label.dataset.colorKey = point.colorModeKey || '';
    leader.dataset.colorKey = point.colorModeKey || '';
    labelsLayer.appendChild(label);
    labelsLayer.appendChild(leader);

    const showTooltipAt = (clientX, clientY) => {
      tooltip.style.display = 'block';
      tooltip.innerHTML = buildTooltip(point);
      // Tooltip is positioned inside the chart wrapper, which also holds facets.
      const rect = (chartWrapEl || svgForTooltip).getBoundingClientRect();
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
    SERIES_HANDLES.push({ key: point.colorModeKey, show: showMarker, hide: hideMarker });

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
  xIsLog = false,
  yIsLog = false,
}) {
  const xAxisY = plotBottom;
  const xAxisLeft = typeof xScale.axisLeft === 'number' ? xScale.axisLeft : plotLeft;
  const xAxisRight = typeof xScale.axisRight === 'number' ? xScale.axisRight : plotRight;
  const yAxisX = xAxisLeft;
  const yTicks = getAxisTicks(yDomain, STATE.yAxis, yIsLog);
  const xTicks =
    isCategoricalXAxis(STATE.xAxis)
      ? xCategories.map((_, index) => index)
      : getAxisTicks(xDomain, STATE.xAxis, xIsLog);
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
    label.textContent = formatAxisTick(STATE.yAxis, value);
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
      text.textContent = formatAxisTick(STATE.xAxis, value);
      chartSvg.appendChild(text);
    }
  }
}

function isLogAxis(which) {
  const axisId = which === 'x' ? STATE.xAxis : STATE.yAxis;
  const mode = which === 'x' ? STATE.xScaleMode : STATE.yScaleMode;
  return mode === 'log' && canUseLogScale(axisId);
}

function canUseLogScale(axisId) {
  return !isCategoricalXAxis(axisId) && axisId !== 'percent' && Boolean(METRICS[axisId]);
}

// Linear axes snap their domain outward to tick boundaries so no tick falls
// outside the plot (out-of-domain ticks used to be clamped onto the edge and
// collide with their neighbours). Log axes span the positive data range.
function buildPlotDomain(points, axisId, which, isLog) {
  if (isLog) return buildLogDomain(points, axisId, which);
  const domain = buildDomain(points, axisId, which);
  if (isCategoricalXAxis(axisId)) return domain;
  const ticks = buildNiceAxisTicks(domain.min, domain.max, AXIS_TICK_SEGMENTS, axisId);
  if (ticks.length < 2) return domain;
  return { min: ticks[0], max: ticks[ticks.length - 1] };
}

function buildLogDomain(points, axisId, which) {
  const values = [];
  points.forEach((point) => {
    const summary = which === 'x' ? point.xSummary : point.ySummary;
    if (!summary?.hasData) return;
    [summary.min, summary.max].forEach((value) => {
      if (Number.isFinite(value) && value > 0) values.push(value);
    });
  });
  if (!values.length) return { min: 1, max: 10 };
  const min = Math.min(...values);
  const max = Math.max(...values);
  // Pad by a fixed ratio on each side; a single value still gets a span.
  const pad = max / min < 1.5 ? 1.5 : 1.15;
  return { min: min / pad, max: max * pad };
}

function getAxisTicks(domain, axisId, isLog) {
  const ticks = isLog
    ? buildLogAxisTicks(domain.min, domain.max)
    : buildNiceAxisTicks(domain.min, domain.max, AXIS_TICK_SEGMENTS, axisId);
  const tolerance = Math.abs(domain.max - domain.min) * 1e-9;
  const inDomain = ticks.filter(
    (value) => value >= domain.min - tolerance && value <= domain.max + tolerance,
  );
  return inDomain.length ? inDomain : [domain.min, domain.max];
}

// 1-2-5 ticks per decade, thinned to at most about eight labels.
function buildLogAxisTicks(min, max) {
  if (!(min > 0) || !(max > min)) return [];
  const ticks = [];
  for (let exponent = Math.floor(Math.log10(min)); exponent <= Math.ceil(Math.log10(max)); exponent += 1) {
    [1, 2, 5].forEach((multiplier) => {
      const value = fixFloat(multiplier * Math.pow(10, exponent));
      if (value >= min && value <= max) ticks.push(value);
    });
  }
  if (ticks.length <= 8) return ticks;
  const decades = ticks.filter(
    (value) => Math.abs(Math.log10(value) - Math.round(Math.log10(value))) < 1e-9,
  );
  return decades.length >= 2 ? decades : ticks.filter((_, index) => index % 2 === 0);
}

function buildDomain(points, axisId, which) {
  if (isCategoricalXAxis(axisId)) {
    const count = getSelectedAxisCategories(axisId).length;
    if (count <= 1) return { min: 0, max: 1 };
    return { min: 0, max: count - 1 };
  }

  const useX = which ? which === 'x' : axisId === STATE.xAxis;
  const summaries = points
    .map((point) => (useX ? point.xSummary : point.ySummary))
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

// Maps a value to [0, 1] within the domain on a linear or log10 scale.
function domainFraction(domain, value, isLog) {
  const safe = Math.min(domain.max, Math.max(domain.min, value));
  if (isLog) {
    const low = Math.log10(domain.min);
    const high = Math.log10(domain.max);
    return high === low ? 0.5 : (Math.log10(safe) - low) / (high - low);
  }
  return (safe - domain.min) / (domain.max - domain.min);
}

function createXScale(domain, categories, plotLeft, plotRight, isLog = false) {
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
    return left + domainFraction(domain, value, isLog) * (right - left);
  };
}

function createYScale(domain, plotTop, plotHeight, isLog = false) {
  const top = plotTop;
  const height = plotHeight;
  return (value) => {
    if (!Number.isFinite(value)) return top + height / 2;
    if (domain.max === domain.min) return top + height / 2;
    return top + (1 - domainFraction(domain, value, isLog)) * height;
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

// Tick labels keep a uniform money format ($0.10, $1.00) so neighbouring ticks
// read consistently; sub-cent ticks on log axes keep one significant digit.
function formatAxisTick(axisId, value) {
  if (axisId === 'cost' && Number.isFinite(value)) {
    if (value > 0 && value < 0.01) return `$${Number(value.toPrecision(1))}`;
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return formatAxisValue(axisId, value);
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
    point.lowRunCount
      ? point.minRunsPerCell === 0
        ? '<em>Hollow marker: no runs for at least one selected eval/language</em>'
        : `<em>Hollow marker: only ${point.minRunsPerCell} run${point.minRunsPerCell === 1 ? '' : 's'} for at least one selected eval/language</em>`
      : null,
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
  const cohort = rowOrPair.comparison_cohort;
  return `${rowOrPair.agent} / ${modelLabel}${cohort ? ` [${cohort}]` : ''}`;
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
    // Even a patch can change scored assertions or repair invalid fixtures.
    // Default to one rubric; historical comparisons require an explicit choice.
    selections.set(evalName, new Set([versions[0]]));
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
  const selectedVersions = versions.filter((version) => isEvalVersionSelected(evalName, version));
  if (!selectedVersions.length) return 'Versions: none';
  if (selectedVersions.length === 1) {
    return `Version: ${formatVersionLabel(selectedVersions[0])}`;
  }
  return `Mixed grading versions (${selectedVersions.length})`;
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
    agent_version: firstPresent(raw.agent_version, ''),
    served_model: firstPresent(raw.served_model, ''),
    model: firstPresent(raw.model, 'default'),
    effort: firstPresent(raw.effort, ''),
    run_id: String(firstPresent(raw.run_id, raw.run, '')),
    eval: normalizedEval,
    eval_instance: firstPresent(raw.eval_instance, ''),
    eval_version: firstPresent(raw.eval_version, ''),
    generation_eval_version: firstPresent(raw.generation_eval_version, raw.eval_version, ''),
    comparison_cohort: firstPresent(raw.comparison_cohort, ''),
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
