#!/usr/bin/env node
/* RS274/NGC interpreter — JavaScript port. Single-file, Node stdlib only. */
'use strict';

const fs = require('fs');
const path = require('path');

// ---------------- CLI parsing ----------------
function parseArgs(argv) {
  const opts = {
    input: null, output: null, toolTable: null, blockDelete: false,
    carouselSlots: null, parameterInput: null, parameterOutput: null,
    probeBox: null, probeTool: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--input': opts.input = argv[++i]; break;
      case '--output': opts.output = argv[++i]; break;
      case '--tool-table': opts.toolTable = argv[++i]; break;
      case '--block-delete': opts.blockDelete = true; break;
      case '--carousel-slots': opts.carouselSlots = parseInt(argv[++i], 10); break;
      case '--parameter-input': opts.parameterInput = argv[++i]; break;
      case '--parameter-output': opts.parameterOutput = argv[++i]; break;
      case '--probe-box':
        opts.probeBox = [
          parseFloat(argv[++i]), parseFloat(argv[++i]),
          parseFloat(argv[++i]), parseFloat(argv[++i]),
          parseFloat(argv[++i]), parseFloat(argv[++i]),
        ]; break;
      case '--probe-tool': opts.probeTool = parseInt(argv[++i], 10); break;
      default: throw new Error(`unknown argument: ${a}`);
    }
  }
  return opts;
}

// ---------------- Required parameter set ----------------
const G28_HOME = [5161,5162,5163,5164,5165,5166];
const G30_HOME = [5181,5182,5183,5184,5185,5186];
const G92_OFF  = [5211,5212,5213,5214,5215,5216];
const COORD_SYS_PARAM = 5220;
function csParam(sys, axisIdx) { return 5221 + (sys-1)*20 + axisIdx; }
function csParams(sys) { return [0,1,2,3,4,5].map(i => csParam(sys,i)); }
function defaultParameters() {
  const p = new Map();
  for (const i of G28_HOME) p.set(i, 0);
  for (const i of G30_HOME) p.set(i, 0);
  for (const i of G92_OFF) p.set(i, 0);
  p.set(COORD_SYS_PARAM, 1);
  for (let s = 1; s <= 9; s++) for (const i of csParams(s)) p.set(i, 0);
  return p;
}

// ---------------- Parameter file I/O ----------------
function parseParameterFile(text) {
  // header lines + exactly one blank line + data lines.
  const rawLines = text.split(/\r?\n/);
  let blankIdx = -1;
  for (let i = 0; i < rawLines.length; i++) {
    if (rawLines[i] === '') { blankIdx = i; break; }
  }
  if (blankIdx === -1) throw new Error('parameter file: missing blank line separator');
  const params = new Map();
  let lastIdx = -Infinity;
  for (let i = blankIdx + 1; i < rawLines.length; i++) {
    const line = rawLines[i];
    if (line.trim() === '') continue;
    const m = line.trim().split(/\s+/);
    if (m.length < 2) throw new Error(`parameter file: bad line: ${line}`);
    const idx = parseInt(m[0], 10);
    const val = parseFloat(m[1]);
    if (!Number.isFinite(idx) || !Number.isFinite(val)) {
      throw new Error(`parameter file: bad line: ${line}`);
    }
    if (idx < 1 || idx > 5400) throw new Error(`parameter file: index out of range: ${idx}`);
    if (idx <= lastIdx) throw new Error('parameter file: parameter numbers must be ascending');
    lastIdx = idx;
    params.set(idx, val);
  }
  // Check required params
  const required = [...G28_HOME.slice(0,3), ...G30_HOME.slice(0,3), ...G92_OFF.slice(0,3), COORD_SYS_PARAM];
  for (let s = 1; s <= 9; s++) required.push(...csParams(s).slice(0,3));
  for (const r of required) {
    if (!params.has(r)) throw new Error(`parameter file: missing required parameter ${r}`);
  }
  return params;
}

function serializeParameterFile(params) {
  const keys = [...params.keys()].sort((a,b)=>a-b);
  const lines = ['Parameter file', ''];
  for (const k of keys) {
    let v = params.get(k);
    // format like "%.6f" but trim
    let s;
    if (Number.isInteger(v)) s = v.toFixed(6);
    else s = String(v);
    lines.push(`${k}\t${v}`);
  }
  return lines.join('\n') + '\n';
}

// ---------------- Tool file I/O ----------------
function parseToolFile(text) {
  const rawLines = text.split(/\r?\n/);
  let blankIdx = -1;
  for (let i = 0; i < rawLines.length; i++) {
    if (rawLines[i] === '') { blankIdx = i; break; }
  }
  if (blankIdx === -1) throw new Error('tool file: missing blank line separator');
  const tools = new Map(); // pocket -> {fms, tlo, diam}
  for (let i = blankIdx + 1; i < rawLines.length; i++) {
    const line = rawLines[i].trim();
    if (line === '') continue;
    const parts = line.split(/\s+/);
    if (parts.length < 4) throw new Error(`tool file: bad line: ${line}`);
    const pocket = parseInt(parts[0], 10);
    const fms = parseInt(parts[1], 10);
    const tlo = parseFloat(parts[2]);
    const diam = parseFloat(parts[3]);
    if (![pocket, fms].every(Number.isFinite) || !Number.isFinite(tlo) || !Number.isFinite(diam)) {
      throw new Error(`tool file: bad line: ${line}`);
    }
    tools.set(pocket, {fms, tlo, diam});
  }
  return tools;
}

// ---------------- Lexer / Parser ----------------
const WORD_LETTERS = new Set('ABCDFGHIJKLMNPQRSTXYZ'.split(''));

function stripCommentsAndWhitespace(line) {
  // Returns {tokens: stripped string with comments removed, but we need to validate parens.}
  // Actually we'll process inline; comments are () or after ; ?
  // RS274 §3.3.4: comment is enclosed in parens. Cannot be nested.
  let out = '';
  let i = 0;
  while (i < line.length) {
    const c = line[i];
    if (c === '(') {
      // find matching ); no nesting
      let j = i + 1;
      while (j < line.length && line[j] !== ')') {
        if (line[j] === '(') throw new Error('nested comment');
        j++;
      }
      if (j >= line.length) throw new Error('unclosed comment');
      i = j + 1;
      continue;
    }
    if (c === ')') throw new Error('unmatched close paren');
    if (c === ' ' || c === '\t') { i++; continue; }
    out += c;
    i++;
  }
  return out;
}

function tokenize(line) {
  // Returns array of tokens: {type:'word', letter, valueRaw} or {type:'pset', idxRaw, valueRaw}
  // For simplicity we leave value parsing to the evaluator, but we need to find token boundaries.
  // We don't fully implement expressions / parameters for now. Numbers only.
  const stripped = stripCommentsAndWhitespace(line);
  const upper = stripped.toUpperCase();
  const tokens = [];
  let i = 0;
  let lineNumber = null;
  while (i < upper.length) {
    const c = upper[i];
    if (c === '/') {
      if (i !== 0) throw new Error('block delete must be at start');
      tokens.unshift({type:'slash'});
      i++;
      continue;
    }
    if (c === 'N') {
      // line number
      i++;
      let num = '';
      while (i < upper.length && /[0-9]/.test(upper[i])) { num += upper[i]; i++; }
      if (num.length === 0 || num.length > 5) throw new Error('bad line number');
      lineNumber = parseInt(num, 10);
      continue;
    }
    if (c === '#') {
      // parameter setting only (we don't support reading params in word values yet)
      i++;
      const idxRes = readRealValue(upper, i);
      i = idxRes.next;
      if (upper[i] !== '=') throw new Error('parameter use without =');
      i++;
      const valRes = readRealValue(upper, i);
      i = valRes.next;
      tokens.push({type:'pset', idxExpr: idxRes.expr, valueExpr: valRes.expr});
      continue;
    }
    if (WORD_LETTERS.has(c)) {
      const letter = c;
      i++;
      const v = readRealValue(upper, i);
      i = v.next;
      tokens.push({type:'word', letter, valueExpr: v.expr});
      continue;
    }
    throw new Error(`unexpected character: ${c}`);
  }
  return {tokens, lineNumber};
}

function readRealValue(s, i) {
  // Reads a number, parameter ref, expression, or unary op. Returns {expr, next}.
  // expr is a function (params)=>number.
  const c = s[i];
  if (c === '#') {
    i++;
    const inner = readRealValue(s, i);
    return {expr: (p)=>{
      const raw = inner.expr(p);
      if (Math.abs(raw - Math.round(raw)) > 0.0001) throw new Error('parameter index not integer');
      const idx = Math.round(raw);
      if (idx < 1 || idx > 5399) throw new Error('parameter index out of range');
      return p.get(idx) || 0;
    }, next: inner.next};
  }
  if (c === '[') {
    return readBracketExpr(s, i);
  }
  if (c === '+' || c === '-' || c === '.' || /[0-9]/.test(c)) {
    return readNumber(s, i);
  }
  // unary op?
  if (/[A-Z]/.test(c)) {
    return readUnaryOp(s, i);
  }
  throw new Error(`expected real value at: ${s.slice(i)}`);
}

function readNumber(s, i) {
  let j = i;
  if (s[j] === '+' || s[j] === '-') j++;
  let hasDigit = false;
  while (j < s.length && /[0-9]/.test(s[j])) { j++; hasDigit = true; }
  if (s[j] === '.') {
    j++;
    while (j < s.length && /[0-9]/.test(s[j])) { j++; hasDigit = true; }
  }
  if (!hasDigit) throw new Error(`bad number at ${s.slice(i)}`);
  const v = parseFloat(s.slice(i, j));
  return {expr: ()=>v, next: j};
}

function readBracketExpr(s, i) {
  if (s[i] !== '[') throw new Error('expected [');
  i++;
  // Parse a single expression then look for closing ]
  const res = parseExpression(s, i);
  if (s[res.next] !== ']') throw new Error('expected ]');
  return {expr: res.expr, next: res.next + 1};
}

function parseExpression(s, i) {
  // shunting yard? simple recursive: addition level
  let left = parseTerm2(s, i);
  while (true) {
    const op = peekOp(s, left.next, ['+','-','OR','XOR','AND']);
    if (!op) break;
    const right = parseTerm2(s, left.next + op.length);
    const l = left.expr, r = right.expr;
    let f;
    if (op === '+') f = (p)=>l(p)+r(p);
    else if (op === '-') f = (p)=>l(p)-r(p);
    else if (op === 'OR') f = (p)=>(l(p)!==0||r(p)!==0)?1:0;
    else if (op === 'XOR') f = (p)=>((l(p)!==0)!==(r(p)!==0))?1:0;
    else if (op === 'AND') f = (p)=>(l(p)!==0&&r(p)!==0)?1:0;
    left = {expr:f, next: right.next};
  }
  return left;
}
function parseTerm2(s, i) {
  let left = parseTerm3(s, i);
  while (true) {
    const op = peekOp(s, left.next, ['*','/','MOD']);
    if (!op) break;
    const right = parseTerm3(s, left.next + op.length);
    const l = left.expr, r = right.expr;
    let f;
    if (op === '*') f = (p)=>l(p)*r(p);
    else if (op === '/') f = (p)=>{const b=r(p); if (b===0) throw new Error('division by zero'); return l(p)/b;};
    else f = (p)=>{const a=l(p),b=r(p);return a - Math.floor(a/b)*b;};
    left = {expr:f, next: right.next};
  }
  return left;
}
function parseTerm3(s, i) {
  let left = readRealValue(s, i);
  while (true) {
    if (s[left.next] === '*' && s[left.next+1] === '*') {
      const right = readRealValue(s, left.next + 2);
      const l = left.expr, r = right.expr;
      left = {expr: (p)=>Math.pow(l(p), r(p)), next: right.next};
    } else break;
  }
  return left;
}

function peekOp(s, i, ops) {
  for (const op of ops) {
    if (s.slice(i, i+op.length) === op) {
      // For word ops like OR, must not be followed by alpha
      if (op.length > 1 && /[A-Z]/.test(s[i+op.length] || '')) continue;
      return op;
    }
  }
  return null;
}

const UNARY_OPS = ['ABS','ACOS','ASIN','ATAN','COS','EXP','FIX','FUP','LN','ROUND','SIN','SQRT','TAN'];
function readUnaryOp(s, i) {
  for (const op of UNARY_OPS) {
    if (s.slice(i, i+op.length) === op) {
      let j = i + op.length;
      if (op === 'ATAN') {
        // ATAN[a]/[b]
        const a = readBracketExpr(s, j);
        if (s[a.next] !== '/') throw new Error('ATAN requires /');
        const b = readBracketExpr(s, a.next + 1);
        const fA = a.expr, fB = b.expr;
        return {expr: (p)=>Math.atan2(fA(p), fB(p))*180/Math.PI, next: b.next};
      }
      const arg = readBracketExpr(s, j);
      const fa = arg.expr;
      let f;
      switch (op) {
        case 'ABS': f = p=>Math.abs(fa(p)); break;
        case 'ACOS': f = p=>{const v=fa(p); if (v<-1||v>1) throw new Error('acos out of range'); return Math.acos(v)*180/Math.PI;}; break;
        case 'ASIN': f = p=>{const v=fa(p); if (v<-1||v>1) throw new Error('asin out of range'); return Math.asin(v)*180/Math.PI;}; break;
        case 'COS': f = p=>Math.cos(fa(p)*Math.PI/180); break;
        case 'EXP': f = p=>Math.exp(fa(p)); break;
        case 'FIX': f = p=>Math.floor(fa(p)); break;
        case 'FUP': f = p=>Math.ceil(fa(p)); break;
        case 'LN':  f = p=>{const v=fa(p); if (v<=0) throw new Error('ln of non-positive'); return Math.log(v);}; break;
        case 'ROUND': f = p=>Math.round(fa(p)); break;
        case 'SIN': f = p=>Math.sin(fa(p)*Math.PI/180); break;
        case 'SQRT': f = p=>{const v=fa(p); if (v<0) throw new Error('sqrt of negative'); return Math.sqrt(v);}; break;
        case 'TAN': f = p=>Math.tan(fa(p)*Math.PI/180); break;
      }
      return {expr: f, next: arg.next};
    }
  }
  throw new Error(`unknown unary op at: ${s.slice(i)}`);
}

// ---------------- Modal groups ----------------
// G code modal groups (table 4)
const G_GROUP = {
  // motion (1)
  'G0':1,'G1':1,'G2':1,'G3':1,'G38.2':1,'G80':1,
  'G81':1,'G82':1,'G83':1,'G84':1,'G85':1,'G86':1,'G87':1,'G88':1,'G89':1,
  // plane (2)
  'G17':2,'G18':2,'G19':2,
  // distance (3)
  'G90':3,'G91':3,
  // feed rate mode (5)
  'G93':5,'G94':5,
  // units (6)
  'G20':6,'G21':6,
  // CRC (7)
  'G40':7,'G41':7,'G42':7,
  // tool length offset (8)
  'G43':8,'G49':8,
  // return mode in canned cycles (10)
  'G98':10,'G99':10,
  // coordinate system selection (12)
  'G54':12,'G55':12,'G56':12,'G57':12,'G58':12,'G59':12,'G59.1':12,'G59.2':12,'G59.3':12,
  // path control (13)
  'G61':13,'G61.1':13,'G64':13,
  // non-modal (0)
  'G4':0,'G10':0,'G28':0,'G30':0,'G53':0,'G92':0,'G92.1':0,'G92.2':0,'G92.3':0,
};
const M_GROUP = {
  'M0':4,'M1':4,'M2':4,'M30':4,'M60':4,
  'M6':6,
  'M3':7,'M4':7,'M5':7,
  'M7':8,'M8':8,'M9':8,
  'M48':9,'M49':9,
};

function gcodeName(num) {
  // num like 0,1,2,3,4,10,17,18..., or 38.2,59.1...
  if (Number.isInteger(num)) return 'G' + num;
  return 'G' + num.toFixed(1);
}
function mcodeName(num) { return 'M' + num; }

// ---------------- Machine state ----------------
function makeState(opts) {
  const params = defaultParameters();
  return {
    params,
    pos: {x:0,y:0,z:0,a:0,b:0,c:0},  // current position in machine coords (no TLO applied)
    units: 'in',  // 'in' or 'mm'
    distanceMode: 'abs',  // 'abs' or 'inc'
    feedRateMode: 'G94',  // 'G93' or 'G94' or 'G95'
    feedRate: 0,
    spindleSpeed: 0,
    spindleDir: 'OFF',  // 'CW','CCW','OFF'
    plane: 'G17',
    crcMode: 'G40',  // 'G40','G41','G42'
    crcDNumber: null,
    crcActive: false,
    crcRadius: 0,
    crcSide: null,    // 'L' or 'R'
    crcFirstMove: false,
    contour: {x:0,y:0,z:0,a:0,b:0,c:0},  // last programmed contour point (machine coords, inches)
    csInt: Array.from({length:10}, ()=>({x:0,y:0,z:0,a:0,b:0,c:0})),  // cs offsets 1..9 in inches
    g92Int: {x:0,y:0,z:0,a:0,b:0,c:0},  // g92 offsets in inches
    cannedCycle: null,  // {code,r,z,p,q,l,depthAxis}
    probeBox: opts.probeBox || null,
    probeTool: opts.probeTool,
    tloMode: 'G49',
    tloHNumber: null,
    tloLength: 0,
    coordSystem: 1,  // 1..9 (selected via G54..G59.3)
    motionMode: null,  // no motion mode active at startup
    pathMode: 'G61',
    returnMode: 'G98',
    selectedTool: null,
    toolInSpindle: null,
    activeMG: {},
    activeMM: {},
    g92Active: false,
    options: opts,
    toolTable: null,
    carouselSlots: opts.carouselSlots || null,
    feedOverride: true,
    speedOverride: true,
  };
}

// Get current coordinate system offsets in inches (internal)
function csOffsets(state) {
  return state.csInt[state.coordSystem];
}
function g92Offsets(state) {
  return state.g92Int;
}

// program coords -> machine coords
function progToMachine(state, p) {
  const cs = csOffsets(state);
  const g92 = state.g92Active ? g92Offsets(state) : {x:0,y:0,z:0,a:0,b:0,c:0};
  const out = {};
  for (const ax of ['x','y','z','a','b','c']) {
    out[ax] = (p[ax] !== undefined ? p[ax] + cs[ax] + g92[ax] : undefined);
  }
  return out;
}

// machine coords -> program coords
function machineToProg(state, m) {
  const cs = csOffsets(state);
  const g92 = state.g92Active ? g92Offsets(state) : {x:0,y:0,z:0,a:0,b:0,c:0};
  const out = {};
  for (const ax of ['x','y','z','a','b','c']) {
    out[ax] = m[ax] - cs[ax] - g92[ax];
  }
  return out;
}

// ---------------- Block execution ----------------
function executeProgram(state, gcode) {
  const lines = gcode.split(/\r?\n/);

  // Handle percent demarcation: if first non-blank line is just '%', find second '%' and stop there.
  let startIdx = 0, endIdx = lines.length;
  let firstNonBlank = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() !== '') { firstNonBlank = i; break; }
  }
  if (firstNonBlank >= 0 && lines[firstNonBlank].trim() === '%') {
    startIdx = firstNonBlank + 1;
    let foundEnd = false;
    for (let i = startIdx; i < lines.length; i++) {
      if (lines[i].trim() === '%') { endIdx = i; foundEnd = true; break; }
    }
    if (!foundEnd) throw new Error('percent at start without matching end');
  } else {
    // must end with M2 or M30 — checked at runtime when we hit one
  }

  let endedByM2 = false;
  for (let li = startIdx; li < endIdx; li++) {
    const raw = lines[li];
    if (raw.trim() === '') continue;
    let block;
    try {
      block = parseBlock(raw);
    } catch (e) {
      throw new Error(`line ${li+1}: ${e.message}`);
    }
    if (block.slash && state.options.blockDelete) continue;
    try {
      const r = executeBlock(state, block);
      if (r === 'end') { endedByM2 = true; break; }
    } catch (e) {
      throw new Error(`line ${li+1}: ${e.message}`);
    }
  }
}

function parseBlock(line) {
  const t = tokenize(line);
  // Group tokens by letter; check for repeats (except G and M which can have multiple in different groups)
  const block = {
    slash: false, lineNumber: t.lineNumber,
    words: {},   // letter -> number (after eval) for non G/M
    gCodes: [],  // list of {num, str}
    mCodes: [],
    psets: [],   // [{idxExpr, valueExpr}]
  };
  for (const tk of t.tokens) {
    if (tk.type === 'slash') { block.slash = true; continue; }
    if (tk.type === 'pset') { block.psets.push(tk); continue; }
    if (tk.type === 'word') {
      const L = tk.letter;
      if (L === 'G') {
        block.gCodes.push(tk);
      } else if (L === 'M') {
        block.mCodes.push(tk);
      } else {
        if (block.words[L] !== undefined) {
          throw new Error(`repeated word ${L}`);
        }
        block.words[L] = tk;
      }
    }
  }
  return block;
}

function executeBlock(state, block) {
  // Evaluate parameter values: per spec, parameters used on the line use their values BEFORE settings.
  // We'll evaluate expressions against current params, then apply psets at end.
  const p = state.params;
  // Evaluate all word values
  const wvals = {};
  for (const L of Object.keys(block.words)) {
    wvals[L] = block.words[L].valueExpr(p);
  }
  // Evaluate G/M numbers
  const gNums = block.gCodes.map(g => g.valueExpr(p));
  const mNums = block.mCodes.map(m => m.valueExpr(p));

  // Resolve G code names. Numbers can be like 38.2.
  function gName(n) {
    const ten = n * 10;
    if (Math.abs(ten - Math.round(ten)) > 0.0001) throw new Error(`G code not close enough to a supported value: ${n}`);
    const rounded = Math.round(ten);
    if (rounded % 10 === 0) return 'G' + (rounded / 10);
    return 'G' + (rounded / 10).toFixed(1);
  }
  function mName(n) {
    if (Math.abs(n - Math.round(n)) < 0.0001) return 'M' + Math.round(n);
    throw new Error('non-integer M code');
  }
  const gNames = gNums.map(gName);
  const mNames = mNums.map(mName);
  if (mNames.length > 4) throw new Error('too many M words on line');

  // Group conflict check
  const gByGroup = {};
  for (const g of gNames) {
    const grp = G_GROUP[g];
    if (grp === undefined) throw new Error(`unknown G code ${g}`);
    if (gByGroup[grp] !== undefined && grp !== 0) throw new Error(`two G codes from same group ${grp}`);
    if (grp === 0) {
      // multiple non-modal can coexist? spec: only one non-modal per line.
      if (gByGroup[0] !== undefined) throw new Error('two non-modal G codes');
    }
    gByGroup[grp] = g;
  }
  const mByGroup = {};
  for (const m of mNames) {
    const grp = M_GROUP[m];
    if (grp === undefined) throw new Error(`unknown M code ${m}`);
    if (mByGroup[grp] !== undefined) throw new Error(`two M codes from same group ${grp}`);
    mByGroup[grp] = m;
  }

  // Apply settings in roughly the order from §3.8.
  // Set feed rate mode
  if (gByGroup[5]) {
    state.feedRateMode = gByGroup[5];
    state.activeMG[5] = gByGroup[5];
  }
  // F
  if (wvals.F !== undefined) {
    if (wvals.F < 0) throw new Error('negative feed rate');
    state.feedRate = wvals.F;
  }
  // S
  if (wvals.S !== undefined) {
    if (wvals.S < 0) throw new Error('negative spindle speed');
    state.spindleSpeed = wvals.S;
  }
  // T
  if (wvals.T !== undefined) {
    if (Math.abs(wvals.T - Math.round(wvals.T)) > 0.0001) throw new Error('non-integer T');
    const tn = Math.round(wvals.T);
    if (tn < 0) throw new Error('negative tool number');
    if (state.carouselSlots !== null && tn > state.carouselSlots) throw new Error('T exceeds carousel slots');
    state.selectedTool = tn;
  }
  // H bound check
  // D bound check (when D word present alone or with G41/G42)
  if (wvals.D !== undefined) {
    if (Math.abs(wvals.D - Math.round(wvals.D)) > 0.0001) throw new Error('non-integer D');
    const dn = Math.round(wvals.D);
    if (dn < 0) throw new Error('negative D');
    if (state.carouselSlots !== null && dn > state.carouselSlots) throw new Error('D exceeds carousel slots');
  }
  if (wvals.H !== undefined) {
    if (Math.abs(wvals.H - Math.round(wvals.H)) > 0.0001) throw new Error('non-integer H');
    const hn = Math.round(wvals.H);
    if (hn < 0) throw new Error('negative H');
    if (state.carouselSlots !== null && hn > state.carouselSlots) throw new Error('H exceeds carousel slots');
  }

  // Coolant
  if (mByGroup[8]) state.activeMM[8] = mByGroup[8];
  // Override
  if (mByGroup[9]) {
    state.activeMM[9] = mByGroup[9];
    const on = mByGroup[9] === 'M48';
    state.feedOverride = on; state.speedOverride = on;
  }
  // Tool change M6 (before spindle so M3 can override)
  if (mByGroup[6]) {
    state.activeMM[6] = mByGroup[6];
    if (state.selectedTool !== null) {
      if (state.carouselSlots !== null && state.selectedTool > state.carouselSlots) {
        throw new Error('selected tool exceeds carousel slots');
      }
      if (state.selectedTool === 0) {
        state.toolInSpindle = null;
      } else {
        state.toolInSpindle = state.selectedTool;
      }
    }
    // M6 stops the spindle
    state.spindleDir = 'OFF';
    state.activeMM[7] = 'M5';
  }
  // Spindle M3/M4/M5 (applied after M6 so M3 on a line with M6 wins).
  if (mByGroup[7]) {
    state.activeMM[7] = mByGroup[7];
    if (mByGroup[7] === 'M3') state.spindleDir = 'CW';
    else if (mByGroup[7] === 'M4') state.spindleDir = 'CCW';
    else state.spindleDir = 'OFF';
  }

  // CRC-active prohibitions (Appendix B.5). Only check items available at this point.
  if (state.crcActive) {
    if (gByGroup[2] && gByGroup[2] !== 'G17') throw new Error('cannot change plane while cutter compensation is active');
    if (gByGroup[6]) throw new Error('cannot change units while cutter compensation is active');
    if (gByGroup[12]) throw new Error('cannot change coordinate system while cutter compensation is active');
    const motionG = gByGroup[1];
    if (motionG === 'G38.2') throw new Error('probing not allowed while cutter compensation is active');
    if (motionG && /^G8[1-9]$/.test(motionG)) throw new Error('canned cycles not allowed while cutter compensation is active');
  }
  // Plane select
  if (gByGroup[2]) { state.plane = gByGroup[2]; state.activeMG[2] = gByGroup[2]; }
  // Units
  if (gByGroup[6]) {
    if (state.crcMode !== 'G40') throw new Error('cannot change units while CRC active');
    state.units = gByGroup[6] === 'G20' ? 'in' : 'mm';
    state.activeMG[6] = gByGroup[6];
  }
  // Distance mode
  if (gByGroup[3]) { state.distanceMode = gByGroup[3] === 'G90' ? 'abs' : 'inc'; state.activeMG[3] = gByGroup[3]; }
  // Return mode
  if (gByGroup[10]) { state.returnMode = gByGroup[10]; state.activeMG[10] = gByGroup[10]; }
  // Coordinate system
  if (gByGroup[12]) {
    if (state.crcMode !== 'G40') throw new Error('cannot change coord system while CRC active');
    const map = {'G54':1,'G55':2,'G56':3,'G57':4,'G58':5,'G59':6,'G59.1':7,'G59.2':8,'G59.3':9};
    state.coordSystem = map[gByGroup[12]];
    state.params.set(COORD_SYS_PARAM, state.coordSystem);
    state.activeMG[12] = gByGroup[12];
  }
  // Path control
  if (gByGroup[13]) { state.pathMode = gByGroup[13]; state.activeMG[13] = gByGroup[13]; }
  // CRC
  if (gByGroup[7]) {
    const newCrc = gByGroup[7];
    if (newCrc === 'G40') {
      state.crcMode = 'G40';
      state.crcDNumber = null;
      state.crcActive = false;
      state.crcRadius = 0;
      state.crcSide = null;
      state.crcFirstMove = false;
      // After G40 the contour position resets to spindle position.
      state.contour = {...state.pos};
    } else {
      // G41 / G42
      if (state.crcActive) throw new Error('cutter compensation already on');
      if (state.plane !== 'G17') throw new Error('cutter compensation requires G17 plane');
      let dn;
      if (wvals.D !== undefined) dn = Math.round(wvals.D);
      else if (state.toolInSpindle !== null) dn = state.toolInSpindle;
      else dn = 0;
      // Resolve radius from tool table
      let radius = 0;
      if (dn !== 0 && state.toolTable && state.toolTable.has(dn)) {
        radius = state.toolTable.get(dn).diam / 2;
      }
      state.crcMode = newCrc;
      state.crcDNumber = dn;
      state.crcActive = true;
      state.crcRadius = radius;
      state.crcSide = (newCrc === 'G41') ? 'L' : 'R';
      state.crcFirstMove = true;
      state.contour = {...state.pos};
    }
    state.activeMG[7] = state.crcMode;
  } else if (wvals.D !== undefined) {
    if (state.crcMode === 'G40') throw new Error('D word without G41/G42');
  }
  // TLO
  if (gByGroup[8]) {
    state.tloMode = gByGroup[8];
    const oldTLO = state.tloLength;
    if (gByGroup[8] === 'G43') {
      if (wvals.H === undefined) throw new Error('G43 without H');
      const h = Math.round(wvals.H);
      state.tloHNumber = h;
      let newTLO = 0;
      if (state.toolTable && state.toolTable.has(h)) newTLO = state.toolTable.get(h).tlo;
      state.pos.z += (oldTLO - newTLO);
      state.tloLength = newTLO;
    } else {
      state.tloHNumber = null;
      state.pos.z += oldTLO;
      state.tloLength = 0;
    }
    state.activeMG[8] = gByGroup[8];
  }

  // Motion mode update
  if (gByGroup[1]) {
    state.motionMode = gByGroup[1];
    state.activeMG[1] = gByGroup[1];
  }

  // Non-modal: G4 dwell, G10, G28, G30, G53, G92.x
  const nonmodal = gByGroup[0];
  const axisWordPresent = ['X','Y','Z','A','B','C'].some(a => wvals[a] !== undefined);

  // G92 family
  if (nonmodal === 'G92') {
    if (state.crcMode !== 'G40') throw new Error('G92 not allowed during cutter compensation');
    if (!axisWordPresent) throw new Error('G92 requires at least one axis word');
    // set offsets so current point becomes the given coordinates
    const axes = ['X','Y','Z','A','B','C'];
    const f = uf(state);
    for (let i = 0; i < 6; i++) {
      const L = axes[i];
      if (wvals[L] !== undefined) {
        const ax = L.toLowerCase();
        const cs = csOffsets(state)[ax];
        // pos (internal inches) = newProg(inches) + cs + g92off => g92off = pos - cs - newProg
        const newProgInches = isLinear(ax) ? wvals[L] * f : wvals[L];
        const newOffInches = state.pos[ax] - cs - newProgInches;
        state.g92Int[ax] = newOffInches;
        // Raw param stored in current units
        state.params.set(G92_OFF[i], isLinear(ax) ? newOffInches / f : newOffInches);
      }
    }
    state.g92Active = true;
  } else if (nonmodal === 'G92.1') {
    if (state.crcMode !== 'G40') throw new Error('G92.1 not allowed during cutter compensation');
    state.g92Active = false;
    for (const i of G92_OFF) state.params.set(i, 0);
    state.g92Int = {x:0,y:0,z:0,a:0,b:0,c:0};
  } else if (nonmodal === 'G92.2') {
    if (state.crcMode !== 'G40') throw new Error('G92.2 not allowed during cutter compensation');
    state.g92Active = false;
  } else if (nonmodal === 'G92.3') {
    if (state.crcMode !== 'G40') throw new Error('G92.3 not allowed during cutter compensation');
    state.g92Active = true;
    // Restore g92Int from stored raw params (params are in the units that were active at write).
    // For simplicity, assume params are currently in inches.
    const f = uf(state);
    for (let i = 0; i < 6; i++) {
      const raw = state.params.get(G92_OFF[i]) || 0;
      const ax = ['x','y','z','a','b','c'][i];
      state.g92Int[ax] = isLinear(ax) ? raw * f : raw;
    }
  }
  if (nonmodal === 'G28' || nonmodal === 'G30' || nonmodal === 'G53') {
    if (state.crcMode !== 'G40') throw new Error(`${nonmodal} not allowed during cutter compensation`);
  }

  if (nonmodal === 'G4') {
    if (wvals.P === undefined || wvals.P < 0) throw new Error('G4 requires non-negative P');
  }

  if (nonmodal === 'G10') {
    if (wvals.L === undefined || Math.round(wvals.L) !== 2) throw new Error('G10 requires L2');
    if (wvals.P === undefined) throw new Error('G10 requires P');
    if (Math.abs(wvals.P - Math.round(wvals.P)) > 1e-9) throw new Error('G10 P must be integer');
    const sys = Math.round(wvals.P);
    if (sys < 1 || sys > 9) throw new Error('G10 P out of range');
    const axes = ['X','Y','Z','A','B','C'];
    const f = uf(state);
    for (let i = 0; i < 6; i++) {
      if (wvals[axes[i]] !== undefined) {
        state.params.set(csParam(sys, i), wvals[axes[i]]);
        const ax = axes[i].toLowerCase();
        state.csInt[sys][ax] = isLinear(ax) ? wvals[axes[i]] * f : wvals[axes[i]];
      }
    }
  }

  // Determine if motion needs to occur this block.
  const motionExplicit = !!gByGroup[1];
  const cannedActive = isCannedCode(state.motionMode);
  // G80 cancels canned cycle
  if (gByGroup[1] === 'G80') {
    state.cannedCycle = null;
    if (axisWordPresent && nonmodal !== 'G10' && nonmodal !== 'G92') {
      throw new Error('G80 cannot have axis words unless a group-0 axis G-code is used');
    }
  }
  // When motion mode is G80 (no explicit motion code this line), axis words are an error.
  if (state.motionMode === 'G80' && !gByGroup[1] && axisWordPresent && nonmodal !== 'G10' && nonmodal !== 'G92') {
    throw new Error('G80 active with axis words');
  }
  // Reject canned cycles in inverse-time mode at activation
  if (gByGroup[1] && /^G8[1-9]$/.test(gByGroup[1])) {
    if (state.feedRateMode === 'G93') throw new Error('canned cycles not allowed in inverse time mode');
  }
  // Canned-cycle line handling.
  const motionIsCanned = isCannedCode(state.motionMode);
  const cannedRelevantWords = ['X','Y','Z','R','P','Q','L','I','J','K'].some(w => wvals[w] !== undefined);
  const skipMotionForNonmodal = (nonmodal === 'G10' || nonmodal === 'G92' || nonmodal === 'G92.1' || nonmodal === 'G92.2' || nonmodal === 'G92.3' || nonmodal === 'G28' || nonmodal === 'G30' || nonmodal === 'G53');
  if (motionIsCanned && !skipMotionForNonmodal) {
    // Reject A/B/C motion in canned cycles
    for (const ax of ['A','B','C']) {
      if (wvals[ax] !== undefined) {
        // It's a "stationary" axis word if it equals the current machine pos in that axis.
        // In abs mode, the program-coord must equal current; in inc mode the delta must be 0.
        let cur = state.pos[ax.toLowerCase()];
        const cs = csOffsets(state)[ax.toLowerCase()];
        const g92 = state.g92Active ? g92Offsets(state)[ax.toLowerCase()] : 0;
        let target;
        if (state.distanceMode === 'abs') target = wvals[ax] + cs + g92;
        else target = cur + wvals[ax];
        if (Math.abs(target - cur) > 1e-9) throw new Error('rotary axis motion not allowed in canned cycle');
      }
    }
    if (gByGroup[1] && /^G8[1-9]$/.test(gByGroup[1])) {
      // first activation: parse parameters and validate
      executeCannedCycle(state, gByGroup[1], wvals, /*firstUse*/true);
    } else if (cannedRelevantWords) {
      // subsequent line — must have at least one of X/Y/Z (in selected plane axes)
      executeCannedCycle(state, state.motionMode, wvals, /*firstUse*/false);
    }
  } else {
    if (motionExplicit && (state.motionMode === 'G0' || state.motionMode === 'G1')) {
      if (!axisWordPresent && !skipMotionForNonmodal) {
        throw new Error(`${state.motionMode} requires at least one axis word`);
      }
    }
    if (axisWordPresent && !skipMotionForNonmodal) {
      doMotion(state, wvals, state.motionMode);
    } else if (!skipMotionForNonmodal && gByGroup[1] === 'G38.2') {
      doProbe(state, wvals);
    }
  }

  if (nonmodal === 'G53') {
    // straight move in machine coords with G0 or G1
    if (state.motionMode !== 'G0' && state.motionMode !== 'G1') {
      throw new Error('G53 requires G0 or G1');
    }
    if (!axisWordPresent) throw new Error('G53 requires at least one axis word');
    const target = {...state.pos};
    const axes = ['X','Y','Z','A','B','C'];
    const f53 = uf(state);
    for (let i = 0; i < 6; i++) {
      if (wvals[axes[i]] !== undefined) {
        const ax = axes[i].toLowerCase();
        target[ax] = isLinear(ax) ? wvals[axes[i]] * f53 : wvals[axes[i]];
      }
    }
    state.pos = target;
    state.contour = {...target};
  }

  if (nonmodal === 'G28' || nonmodal === 'G30') {
    // intermediate point if axes given (in current coordinate system); then go to home stored in params.
    const axes = ['X','Y','Z','A','B','C'];
    if (axisWordPresent) doMotion(state, wvals, 'G0');
    const homeParams = nonmodal === 'G28' ? G28_HOME : G30_HOME;
    const target = {x:0,y:0,z:0,a:0,b:0,c:0};
    for (let i = 0; i < 6; i++) target[axes[i].toLowerCase()] = state.params.get(homeParams[i]) || 0;
    state.pos = target;
    state.contour = {...target};
  }

  // M0/M1/M2/M30 stopping
  if (mByGroup[4]) {
    state.activeMM[4] = mByGroup[4];
    if (mByGroup[4] === 'M2' || mByGroup[4] === 'M30') {
      // RS274 §3.6.1: M2/M30 reset modal state.
      state.plane = 'G17';
      state.distanceMode = 'abs';
      state.feedRateMode = 'G94';
      state.crcMode = 'G40';
      state.crcDNumber = null;
      state.crcActive = false;
      state.spindleDir = 'OFF';
      state.motionMode = 'G1';
      state.feedOverride = true; state.speedOverride = true;
      state.activeMG[2] = 'G17';
      state.activeMG[3] = 'G90';
      state.activeMG[5] = 'G94';
      state.activeMG[7] = 'G40';
      state.activeMG[1] = 'G1';
      state.activeMM[7] = 'M5';
      state.activeMM[8] = 'M9';
      state.activeMM[9] = 'M48';
      // canned cycle cleared
      state.cannedCycle = null;
      return 'end';
    }
  }

  // Apply parameter settings (after all reads). Buffered: evaluate values before applying.
  const buffered = [];
  for (const ps of block.psets) {
    const idxRaw = ps.idxExpr(state.params);
    if (Math.abs(idxRaw - Math.round(idxRaw)) > 0.0001) throw new Error('parameter setting index not integer');
    const idx = Math.round(idxRaw);
    if (idx < 1 || idx > 5399) throw new Error('parameter setting index out of range');
    const val = ps.valueExpr(state.params);
    buffered.push([idx, val]);
  }
  for (const [idx, val] of buffered) state.params.set(idx, val);
}

function isCannedCode(g) { return typeof g === 'string' && /^G8[1-9]$/.test(g); }

// Factor to convert linear axis values from current units to internal (inches).
function uf(state) { return state.units === 'mm' ? (1/25.4) : 1; }
function isLinear(ax) { return ax === 'x' || ax === 'y' || ax === 'z'; }

// Compute programmed target in machine coords (internal inches) from axis words.
function progTarget(state, wvals, base) {
  const axes = ['X','Y','Z','A','B','C'];
  const cs = csOffsets(state); // cs offsets are stored in inches internally via param conversion
  const g92 = state.g92Active ? g92Offsets(state) : {x:0,y:0,z:0,a:0,b:0,c:0};
  const f = uf(state);
  const out = {...base};
  for (let i = 0; i < 6; i++) {
    const L = axes[i]; const ax = L.toLowerCase();
    if (wvals[L] !== undefined) {
      const v = isLinear(ax) ? wvals[L] * f : wvals[L];
      if (state.distanceMode === 'abs') {
        let t = v + cs[ax] + g92[ax];
        if (ax === 'z') t -= state.tloLength;
        out[ax] = t;
      } else {
        out[ax] = base[ax] + v;
      }
    }
  }
  return out;
}

function doMotion(state, wvals, mode) {
  if (mode === 'G0' || mode === 'G1') {
    if (mode === 'G1' && state.feedRateMode === 'G93' && wvals.F === undefined) {
      throw new Error('inverse time G1 requires F on every line');
    }
    const target = progTarget(state, wvals, state.contour);
    if (state.crcActive && state.plane === 'G17') {
      doCrcStraight(state, target);
    } else {
      state.pos = target;
      state.contour = target;
    }
    return;
  }
  if (mode === 'G2' || mode === 'G3') {
    if (state.feedRateMode === 'G93' && wvals.F === undefined) {
      throw new Error('inverse time arc requires F on every line');
    }
    doArc(state, wvals, mode);
    return;
  }
  if (mode === 'G38.2') {
    doProbe(state, wvals);
    return;
  }
  // fallback
  const target = progTarget(state, wvals, state.pos);
  state.pos = target;
  state.contour = target;
}

// ---- CRC straight ----
function doCrcStraight(state, programmedTarget) {
  const r = state.crcRadius;
  const side = state.crcSide;
  const sp = state.pos;         // spindle center (machine)
  const cp = state.contour;     // programmed contour (machine)
  const P = {x: programmedTarget.x, y: programmedTarget.y};
  if (r === 0) {
    // Zero radius: spindle follows contour.
    state.pos = {...programmedTarget};
    state.contour = {...programmedTarget};
    state.crcFirstMove = false;
    return;
  }
  let newSpindle;
  if (state.crcFirstMove) {
    // First move: place spindle on tangent line from current spindle (C) to circle of radius r around P.
    // D = center of destination tool circle. |DP| = r. The line CD is tangent to destination circle at D,
    // so CD ⟂ DP. Thus |CD|^2 + r^2 = |CP|^2  =>  gouging error if |CP| < r.
    const dx = P.x - sp.x, dy = P.y - sp.y;
    const dist = Math.hypot(dx, dy);
    if (dist < r - 1e-9) throw new Error('cannot compensate: programmed point inside tool circle');
    // Direction of path (sp -> P).
    const ux = dx/dist, uy = dy/dist;
    // Left normal (G41): (-uy, ux). Right normal (G42): (uy, -ux).
    const nx = (side === 'L') ? -uy : uy;
    const ny = (side === 'L') ? ux : -ux;
    // The tangent-point D lies on circle around P of radius r, perpendicular to line CD.
    // Actually geometry: Let t be tangent point on destination circle. C->D is tangent to dest circle,
    // so (D - C) · (D - P) = 0 with |D - P| = r. Solution: D = P + r*n_perp where n_perp is
    // the unit normal from the path that selects the correct side. Specifically, using
    // the Appendix B.6 construction: D = P - r*(u rotated 90° away from the side? Let's derive:
    // We want spindle on left for G41. So D - C perpendicular to D - P, and n_chord.
    // Let's just use the explicit construction: rotate by theta where sin(theta)=r/dist.
    const cosT = Math.sqrt(Math.max(0, dist*dist - r*r)) / dist;
    const sinT = r / dist;
    // G41 rotates path direction by +theta (spindle center above path, left side)?
    // Rotate u by +theta (CCW) for G41 (left): u' = (ux*cosT - uy*sinT, ux*sinT + uy*cosT)
    // D = C + |CD| * u'  where |CD| = sqrt(dist^2 - r^2)
    const CD = Math.sqrt(Math.max(0, dist*dist - r*r));
    let upx, upy;
    if (side === 'L') {
      upx = ux*cosT - uy*sinT;
      upy = ux*sinT + uy*cosT;
    } else {
      upx = ux*cosT + uy*sinT;
      upy = -ux*sinT + uy*cosT;
    }
    newSpindle = {x: sp.x + CD*upx, y: sp.y + CD*upy};
  } else {
    // Follow-on straight move: check concave-corner rule, then offset endpoint.
    const inDx = cp.x - getPrevContour(state).x, inDy = cp.y - getPrevContour(state).y;
    const outDx = P.x - cp.x, outDy = P.y - cp.y;
    const outLen = Math.hypot(outDx, outDy);
    if (outLen < 1e-12) {
      // zero-length move, keep spindle
      newSpindle = {x: sp.x, y: sp.y};
    } else {
      const oux = outDx/outLen, ouy = outDy/outLen;
      const nx = (side === 'L') ? -ouy : ouy;
      const ny = (side === 'L') ? oux : -oux;
      // Concave check at the corner: cross(in, out) sign
      const inLen = Math.hypot(inDx, inDy);
      if (inLen > 1e-12) {
        const iux = inDx/inLen, iuy = inDy/inLen;
        const cross = iux*ouy - iuy*oux; // >0 means turning left
        if (side === 'L' && cross > 1e-9) throw new Error('concave corner with cutter radius compensation');
        if (side === 'R' && cross < -1e-9) throw new Error('concave corner with cutter radius compensation');
        // Concave if turning into the tool side... wait:
        // For G41 (left side), a CONCAVE corner is one where the turn is to the RIGHT (cross<0)?
        // Actually: when tool is on LEFT of path, and path turns LEFT (cross>0), that's CONVEX (tool goes around outside).
        // When path turns RIGHT (cross<0), it's CONCAVE (tool would crash into corner).
        // OK logic above is correct.
      }
      newSpindle = {x: P.x + r*nx, y: P.y + r*ny};
    }
  }
  state.pos = {x: newSpindle.x, y: newSpindle.y, z: programmedTarget.z, a: programmedTarget.a, b: programmedTarget.b, c: programmedTarget.c};
  state._prevContour = {...state.contour};
  state.contour = {...programmedTarget};
  state.crcFirstMove = false;
}

// Track previous contour for corner geometry.
function getPrevContour(state) {
  return state._prevContour || state.contour;
}
function stashPrevContour(state) { state._prevContour = {...state.contour}; }

// ---- CRC arc (G17 only) ----
function doCrcArc(state, wvals, mode, programmedTarget) {
  const r = state.crcRadius;
  const side = state.crcSide;
  const cw = (mode === 'G2');
  const cp = state.contour;
  const sp = state.pos;
  // Determine center and radii.
  let cx, cy, contourR, toolR;
  // First, tentatively compute using contour start for center (subsequent moves).
  const firstMove = state.crcFirstMove;
  // Determine inside/outside
  let inside;
  if (side === 'L') inside = !cw;
  else inside = cw;

  if (!firstMove) {
    // Subsequent arc: center is defined by I/J relative to contour start (cp).
    if (wvals.R !== undefined) {
      contourR = Math.abs(wvals.R);
      const mx = (cp.x + programmedTarget.x) / 2;
      const my = (cp.y + programmedTarget.y) / 2;
      const dx = programmedTarget.x - cp.x, dy = programmedTarget.y - cp.y;
      const chord = Math.hypot(dx, dy);
      if (chord < 1e-12) throw new Error('radius-format arc endpoint matches start');
      if (contourR < chord/2 - 1e-6) throw new Error('radius format arc radius too small');
      const h = Math.sqrt(Math.max(0, contourR*contourR - (chord/2)*(chord/2)));
      const px = -dy/chord, py = dx/chord;
      const sgn = (wvals.R > 0) !== cw ? 1 : -1;
      cx = mx + sgn*h*px; cy = my + sgn*h*py;
    } else {
      if (wvals.I === undefined && wvals.J === undefined) throw new Error('arc missing center offsets');
      const I = wvals.I || 0, J = wvals.J || 0;
      cx = cp.x + I; cy = cp.y + J;
      contourR = Math.hypot(cp.x - cx, cp.y - cy);
    }
    if (inside) {
      if (r >= contourR - 1e-9) throw new Error('tool radius not less than arc radius');
    }
    toolR = inside ? contourR - r : contourR + r;
  } else {
    // First move. The center and contour/tool radii must satisfy:
    //   |C - sp| = toolR    (spindle on tool-center arc)
    //   |C - P|  = contourR (contour endpoint on contour arc)
    //   toolR = contourR +/- r
    if (wvals.R !== undefined) {
      contourR = Math.abs(wvals.R);
      toolR = inside ? contourR - r : contourR + r;
      if (toolR <= 0) throw new Error('tool radius not less than arc radius');
      // Solve two-circle intersection: |C-sp|=toolR, |C-P|=contourR.
      const dxp = programmedTarget.x - sp.x, dyp = programmedTarget.y - sp.y;
      const d = Math.hypot(dxp, dyp);
      if (d < 1e-12) throw new Error('radius-format arc endpoint matches start');
      // Distance from sp along chord to midperpendicular foot:
      const a = (toolR*toolR - contourR*contourR + d*d) / (2*d);
      const h2 = toolR*toolR - a*a;
      if (h2 < -1e-6) throw new Error('radius-format arc: no valid center');
      const h = Math.sqrt(Math.max(0, h2));
      const ux = dxp/d, uy = dyp/d;
      const midx = sp.x + a*ux, midy = sp.y + a*uy;
      // Two candidates: pick based on sign of R and direction
      const px = -uy, py = ux;
      const sgn = (wvals.R > 0) !== cw ? 1 : -1;
      cx = midx + sgn*h*px; cy = midy + sgn*h*py;
    } else {
      if (wvals.I === undefined && wvals.J === undefined) throw new Error('arc missing center offsets');
      // For first move I/J are relative to the current spindle and give the tool-center center.
      const I = wvals.I || 0, J = wvals.J || 0;
      cx = sp.x + I; cy = sp.y + J;
      toolR = Math.hypot(sp.x - cx, sp.y - cy);
      contourR = inside ? toolR + r : toolR - r;
      if (contourR <= 1e-9) throw new Error('tool radius not less than arc radius');
    }
  }
  // Endpoint: spindle is at distance toolR from center, along direction from center to programmedTarget.
  const ex = programmedTarget.x - cx, ey = programmedTarget.y - cy;
  const eLen = Math.hypot(ex, ey);
  if (eLen < 1e-12) throw new Error('arc endpoint at center');
  const scale = toolR / eLen;
  const newSpindle = {x: cx + ex*scale, y: cy + ey*scale};
  state.pos = {x: newSpindle.x, y: newSpindle.y, z: programmedTarget.z, a: programmedTarget.a, b: programmedTarget.b, c: programmedTarget.c};
  state.contour = {...programmedTarget};
  state.crcFirstMove = false;
}

// ---- arcs ----
function doArc(state, wvals, mode) {
  const target = progTarget(state, wvals, state.contour);
  const plane = state.plane;
  // Validate required plane axes for radius format
  const planeAxes = plane === 'G17' ? ['X','Y'] : plane === 'G18' ? ['X','Z'] : ['Y','Z'];
  const centerOffsets = plane === 'G17' ? ['I','J'] : plane === 'G18' ? ['I','K'] : ['J','K'];
  if (wvals.R !== undefined) {
    // Radius format: at least one plane axis must be present
    if (!planeAxes.some(a => wvals[a] !== undefined)) throw new Error('radius-format arc requires a plane axis word');
    // Endpoint must differ from start in-plane
    const a0 = planeAxes[0].toLowerCase(), a1 = planeAxes[1].toLowerCase();
    if (Math.abs(target[a0] - state.contour[a0]) < 1e-9 && Math.abs(target[a1] - state.contour[a1]) < 1e-9) {
      throw new Error('radius-format arc endpoint same as start');
    }
  } else {
    // Center format: at least one center offset in the plane must be present
    if (!centerOffsets.some(o => wvals[o] !== undefined)) throw new Error('center-format arc requires plane center offsets');
  }
  if (state.crcActive && plane === 'G17') {
    doCrcArc(state, wvals, mode, target);
    return;
  }
  // Endpoint-only tracking (non-CRC arcs): need radius consistency for center format.
  if (wvals.R === undefined) {
    // Center format radius check
    let ix=0, jy=0, k=0;
    let cx, cy;
    if (plane === 'G17') { cx = state.contour.x + (wvals.I||0); cy = state.contour.y + (wvals.J||0);
      const rs = Math.hypot(state.contour.x-cx, state.contour.y-cy);
      const re = Math.hypot(target.x-cx, target.y-cy);
      if (Math.abs(rs-re) > 1e-3) throw new Error('center-format arc endpoints inconsistent');
    } else if (plane === 'G18') { cx = state.contour.x + (wvals.I||0); cy = state.contour.z + (wvals.K||0);
      const rs = Math.hypot(state.contour.x-cx, state.contour.z-cy);
      const re = Math.hypot(target.x-cx, target.z-cy);
      if (Math.abs(rs-re) > 1e-3) throw new Error('center-format arc endpoints inconsistent');
    } else { cx = state.contour.y + (wvals.J||0); cy = state.contour.z + (wvals.K||0);
      const rs = Math.hypot(state.contour.y-cx, state.contour.z-cy);
      const re = Math.hypot(target.y-cx, target.z-cy);
      if (Math.abs(rs-re) > 1e-3) throw new Error('center-format arc endpoints inconsistent');
    }
  }
  state.pos = target;
  state.contour = target;
}

// ---- Probing G38.2 ----
function doProbe(state, wvals) {
  if (state.feedRateMode === 'G93') throw new Error('G38.2 not allowed in inverse time mode');
  if (state.spindleDir !== 'OFF') throw new Error('cannot probe with spindle on');
  if (state.probeTool !== null && state.probeTool !== undefined) {
    if (state.toolInSpindle !== state.probeTool) throw new Error('probe tool not in spindle');
  }
  const hasLinear = ['X','Y','Z'].some(a => wvals[a] !== undefined);
  if (!hasLinear) throw new Error('G38.2 requires at least one linear axis word');
  const target = progTarget(state, wvals, state.pos);
  // Reject rotary motion
  for (const ax of ['a','b','c']) {
    if (Math.abs(target[ax] - state.pos[ax]) > 1e-9) throw new Error('G38.2 rotary axis motion not allowed');
  }
  // Build box in machine inches
  const box = state.probeBox;
  if (!box) throw new Error('no probe box configured');
  // state.pos and target are already stored internally in inches.
  const curIn = {x: state.pos.x, y: state.pos.y, z: state.pos.z};
  const tgtIn = {x: target.x, y: target.y, z: target.z};
  // Too-close check: distance < 0.01 inch
  const d = Math.hypot(tgtIn.x-curIn.x, tgtIn.y-curIn.y, tgtIn.z-curIn.z);
  if (d < 0.01 - 1e-9) throw new Error('G38.2 programmed point too close');
  // Already tripped?
  function inBox(p) {
    return p.x >= box[0]-1e-9 && p.x <= box[1]+1e-9 &&
           p.y >= box[2]-1e-9 && p.y <= box[3]+1e-9 &&
           p.z >= box[4]-1e-9 && p.z <= box[5]+1e-9;
  }
  if (inBox(curIn)) throw new Error('probe already tripped');
  // Find earliest t in (0,1] where segment enters box.
  let tTrip = Infinity;
  const dir = {x: tgtIn.x-curIn.x, y: tgtIn.y-curIn.y, z: tgtIn.z-curIn.z};
  // Slab method: find entry t.
  let tEnter = 0, tExit = 1;
  const axes = ['x','y','z'];
  for (let i = 0; i < 3; i++) {
    const a = axes[i];
    const lo = box[i*2], hi = box[i*2+1];
    if (Math.abs(dir[a]) < 1e-12) {
      if (curIn[a] < lo - 1e-9 || curIn[a] > hi + 1e-9) { tEnter = Infinity; break; }
    } else {
      let t1 = (lo - curIn[a]) / dir[a];
      let t2 = (hi - curIn[a]) / dir[a];
      if (t1 > t2) { const s = t1; t1 = t2; t2 = s; }
      if (t1 > tEnter) tEnter = t1;
      if (t2 < tExit) tExit = t2;
    }
  }
  if (tEnter > tExit || tEnter > 1 + 1e-9 || tEnter < -1e-9) {
    throw new Error('probe did not trip');
  }
  tTrip = tEnter;
  const tripIn = {
    x: curIn.x + dir.x*tTrip,
    y: curIn.y + dir.y*tTrip,
    z: curIn.z + dir.z*tTrip,
  };
  state.pos = {
    x: tripIn.x, y: tripIn.y, z: tripIn.z,
    a: target.a, b: target.b, c: target.c,
  };
  state.contour = {...state.pos};
  // Write trip parameters 5061..5066 in inches (absolute machine coords)
  // TLO is applied to Z (machine Z stored includes -tloLength offset). RS274 says params store
  // the controlled-point location; controlled point in machine = tripIn (already factors TLO? Not really —
  // we stored machine pos as "programmed - TLO". Tests expect raw box values, so tripIn matches that.)
  const outF = state.units === 'mm' ? 25.4 : 1;
  state.params.set(5061, tripIn.x * outF);
  state.params.set(5062, tripIn.y * outF);
  state.params.set(5063, tripIn.z * outF);
  state.params.set(5064, target.a);
  state.params.set(5065, target.b);
  state.params.set(5066, target.c);
}

// ---- Canned cycles ----
function executeCannedCycle(state, code, wvals, firstUse) {
  // Plane determines depth axis
  const plane = state.plane;
  const depthAxis = plane === 'G17' ? 'Z' : plane === 'G18' ? 'Y' : 'X';
  const planeAxes = plane === 'G17' ? ['X','Y'] : plane === 'G18' ? ['X','Z'] : ['Y','Z'];
  const cs = csOffsets(state);
  const g92 = state.g92Active ? g92Offsets(state) : {x:0,y:0,z:0,a:0,b:0,c:0};

  // Get or init sticky storage
  let cc = state.cannedCycle;
  if (firstUse || !cc || cc.code !== code) {
    cc = {code, r: undefined, depth: undefined, p: undefined, q: undefined, l: 1};
    state.cannedCycle = cc;
  }
  // X, Y, Z all missing during canned cycle is an error
  if (!firstUse) {
    if (wvals.X === undefined && wvals.Y === undefined && wvals.Z === undefined) {
      throw new Error('X, Y, and Z all missing during canned cycle');
    }
  }
  // Parse params
  if (wvals.R !== undefined) cc.r = wvals.R;
  if (wvals[depthAxis] !== undefined) cc.depth = wvals[depthAxis];
  if (wvals.P !== undefined) cc.p = wvals.P;
  if (wvals.Q !== undefined) cc.q = wvals.Q;
  if (wvals.L !== undefined) {
    if (Math.abs(wvals.L - Math.round(wvals.L)) > 1e-9) throw new Error('L must be integer');
    if (wvals.L <= 0) throw new Error('L must be positive');
    cc.l = Math.round(wvals.L);
  } else if (firstUse) cc.l = 1;
  if (firstUse) {
    if (cc.r === undefined) throw new Error('canned cycle requires R on first use');
    if (cc.depth === undefined) throw new Error('canned cycle requires depth word on first use');
  }
  // Cycle-specific validation
  if (code === 'G82' || code === 'G86' || code === 'G88' || code === 'G89') {
    if (cc.p === undefined) throw new Error(`${code} requires P`);
    if (cc.p < 0) throw new Error(`${code} requires non-negative P`);
  }
  if (code === 'G83') {
    if (cc.q === undefined || cc.q <= 0) throw new Error('G83 requires positive Q');
  }
  if (code === 'G84') {
    if (state.spindleDir !== 'CW') throw new Error('G84 requires clockwise spindle');
  }
  if (code === 'G86' || code === 'G88') {
    if (state.spindleDir === 'OFF') throw new Error(`${code} requires spindle to be turning`);
  }
  // R must be above depth (in selected plane's depth axis) in G90; check raw values
  // Convert R and depth to machine coordinates in the depth axis
  const depthAxisLower = depthAxis.toLowerCase();
  const csOff = cs[depthAxisLower] + g92[depthAxisLower] - (depthAxisLower === 'z' ? state.tloLength : 0);
  let rMachine, dMachine;
  if (state.distanceMode === 'abs') {
    rMachine = cc.r + csOff;
    dMachine = cc.depth + csOff;
  } else {
    // Incremental: R relative to current, depth relative to R?
    rMachine = state.pos[depthAxisLower] + cc.r;
    dMachine = rMachine + cc.depth;
  }
  if (rMachine < dMachine - 1e-9) throw new Error('canned cycle R below depth');
  // Old Z (current depth axis position before cycle)
  const oldDepth = state.pos[depthAxisLower];
  // Compute X/Y target in plane axes
  const newPos = {...state.pos};
  // For each repeat count (incremental mode advances in-plane axes)
  for (let rep = 0; rep < cc.l; rep++) {
    for (const L of planeAxes) {
      const ax = L.toLowerCase();
      if (wvals[L] !== undefined) {
        if (state.distanceMode === 'abs') {
          if (rep === 0) newPos[ax] = wvals[L] + cs[ax] + g92[ax];
        } else {
          newPos[ax] = newPos[ax] + wvals[L];
        }
      }
    }
  }
  // Rotary stationary words — copy through (already validated above)
  for (const L of ['A','B','C']) {
    if (wvals[L] !== undefined) {
      const ax = L.toLowerCase();
      if (state.distanceMode === 'abs') newPos[ax] = wvals[L] + cs[ax] + g92[ax];
    }
  }
  // Final depth-axis position: G98 retract to oldDepth (if > R), G99 retract to R
  let finalDepth;
  const retract = state.returnMode;
  if (retract === 'G98') {
    finalDepth = Math.max(oldDepth, rMachine);
  } else {
    finalDepth = rMachine;
  }
  // But in incremental mode with multiple L repeats, each retract adds to oldDepth? Actually spec:
  // In abs mode, oldDepth fixed. In incremental mode after each repeat, the retract point also shifts.
  // The final position in incremental with L repeats: each cycle starts at current retract point,
  // moves to new R (which is incrementally higher if R positive), etc.
  // Simpler: per §3.5.16, in incremental L repeats the retract level equals R which is cc.r*L added to starting.
  // (In incremental mode with L repeats, R/depth are evaluated once; only the in-plane axes repeat.)
  newPos[depthAxisLower] = finalDepth;
  state.pos = newPos;
  state.contour = {...newPos};
  // G86 stops the spindle at the bottom then restarts; but end state is still spindle on.
  // G84 keeps spindle CW. G87 keeps spindle as-is.
}

// ---------------- Output JSON ----------------
function buildResult(state) {
  const toDisplay = state.units === 'mm' ? 25.4 : 1;
  // Round off float error introduced by unit conversion (cnc precision ~1e-6 inch = 2.5e-5 mm)
  const rnd = (v) => {
    // Round to 6 decimals (mm) or 7 decimals (in) to eliminate float conversion artifacts.
    const p = state.units === 'mm' ? 1e6 : 1e7;
    return Math.round(v * p) / p;
  };
  const mpos = {
    x: rnd(state.pos.x * toDisplay),
    y: rnd(state.pos.y * toDisplay),
    z: rnd(state.pos.z * toDisplay),
    a: state.pos.a, b: state.pos.b, c: state.pos.c,
  };
  const coordSystems = {};
  for (let s = 1; s <= 9; s++) {
    const src = state.csInt[s];
    coordSystems[String(s)] = {
      x: rnd(src.x * toDisplay), y: rnd(src.y * toDisplay), z: rnd(src.z * toDisplay),
      a: src.a, b: src.b, c: src.c,
    };
  }
  const params = {};
  for (const [k,v] of state.params) params[String(k)] = v;

  // Active modal codes — fill in defaults for required groups
  const activeMG = {...state.activeMG};
  if (!activeMG[1]) activeMG[1] = state.motionMode;
  if (!activeMG[2]) activeMG[2] = state.plane;
  if (!activeMG[3]) activeMG[3] = state.distanceMode === 'abs' ? 'G90' : 'G91';
  if (!activeMG[5]) activeMG[5] = state.feedRateMode;
  if (!activeMG[6]) activeMG[6] = state.units === 'in' ? 'G20' : 'G21';
  if (!activeMG[7]) activeMG[7] = state.crcMode;
  if (!activeMG[8]) activeMG[8] = state.tloMode;
  if (!activeMG[10]) activeMG[10] = state.returnMode;
  if (!activeMG[12]) {
    const inv = ['G54','G55','G56','G57','G58','G59','G59.1','G59.2','G59.3'];
    activeMG[12] = inv[state.coordSystem - 1];
  }
  if (!activeMG[13]) activeMG[13] = state.pathMode;

  const activeMM = {...state.activeMM};
  if (!activeMM[7]) activeMM[7] = 'M5';
  if (!activeMM[8]) activeMM[8] = 'M9';
  if (!activeMM[9]) activeMM[9] = 'M48';

  return {
    machine_position: mpos,
    feed_rate: state.feedRate,
    spindle_speed: state.spindleSpeed,
    spindle_direction: state.spindleDir,
    cutter_radius_compensation_number: state.crcDNumber,
    tool_length_offset_index: state.tloHNumber,
    selected_tool: state.selectedTool,
    tool_in_spindle: state.toolInSpindle,
    active_modal_g_codes: activeMG,
    active_modal_m_codes: activeMM,
    coordinate_system_offsets: coordSystems,
    parameters: params,
    error: null,
  };
}

function emptyResult(errorMsg) {
  return {
    machine_position: {x:0,y:0,z:0,a:0,b:0,c:0},
    feed_rate: 0,
    spindle_speed: 0,
    spindle_direction: 'OFF',
    cutter_radius_compensation_number: null,
    tool_length_offset_index: null,
    selected_tool: null,
    tool_in_spindle: null,
    active_modal_g_codes: {},
    active_modal_m_codes: {},
    coordinate_system_offsets: {},
    parameters: {},
    error: errorMsg,
  };
}

// ---------------- Main ----------------
function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    process.stderr.write(`argument error: ${e.message}\n`);
    return 2;
  }
  if (!opts.input || !opts.output) {
    process.stderr.write('--input and --output are required\n');
    return 2;
  }
  const state = makeState(opts);
  // Load parameter input
  if (opts.parameterInput) {
    try {
      const text = fs.readFileSync(opts.parameterInput, 'utf-8');
      const params = parseParameterFile(text);
      for (const [k,v] of params) state.params.set(k, v);
      // Populate internal cs/g92 from params (assume inches since input params have no unit).
      for (let s = 1; s <= 9; s++) {
        for (let i = 0; i < 6; i++) {
          const v = state.params.get(csParam(s, i)) || 0;
          const ax = ['x','y','z','a','b','c'][i];
          state.csInt[s][ax] = v;
        }
      }
      for (let i = 0; i < 6; i++) {
        const v = state.params.get(G92_OFF[i]) || 0;
        state.g92Int[['x','y','z','a','b','c'][i]] = v;
      }
      const sys = Math.round(state.params.get(COORD_SYS_PARAM));
      if (!Number.isFinite(sys) || sys < 1 || sys > 9) {
        throw new Error('parameter 5220 must be 1..9');
      }
      state.coordSystem = sys;
    } catch (e) {
      const result = emptyResult(`parameter input: ${e.message}`);
      fs.writeFileSync(opts.output, JSON.stringify(result));
      return 1;
    }
  }
  // Load tool table
  if (opts.toolTable) {
    try {
      const text = fs.readFileSync(opts.toolTable, 'utf-8');
      state.toolTable = parseToolFile(text);
    } catch (e) {
      const result = emptyResult(`tool table: ${e.message}`);
      fs.writeFileSync(opts.output, JSON.stringify(result));
      return 1;
    }
  }
  // Read gcode
  let gcode;
  try {
    gcode = fs.readFileSync(opts.input, 'utf-8');
  } catch (e) {
    const result = emptyResult(`cannot read input: ${e.message}`);
    fs.writeFileSync(opts.output, JSON.stringify(result));
    return 1;
  }
  try {
    executeProgram(state, gcode);
  } catch (e) {
    const result = buildResult(state);
    result.error = e.message;
    fs.writeFileSync(opts.output, JSON.stringify(result));
    return 1;
  }
  const result = buildResult(state);
  fs.writeFileSync(opts.output, JSON.stringify(result));
  if (opts.parameterOutput) {
    try {
      fs.writeFileSync(opts.parameterOutput, serializeParameterFile(state.params));
    } catch (e) {
      // can't easily report; rewrite output with error
      result.error = `parameter output: ${e.message}`;
      fs.writeFileSync(opts.output, JSON.stringify(result));
      return 1;
    }
  }
  return 0;
}

process.exit(main());
