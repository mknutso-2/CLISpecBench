#!/usr/bin/env node
// WordCount reference implementation (JavaScript / Node.js).
//
// Mirrors the contract exercised by Evals/WordCount/tests:
// - "characters" is the raw byte length of the input file.
// - "lines" counts '\n' bytes; a trailing line without '\n' still counts
//   as 1 line when the file is non-empty.
// - Words are whitespace-delimited tokens (ASCII whitespace).
// - Unique-word counts are case-insensitive; top_words emits lowercase forms.
// - top_words is ordered by descending count, then ascending word, capped at 10.

"use strict";

const fs = require("fs");
const path = require("path");

function parseArgs(argv) {
  const args = { input: null, output: null };
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "--input") {
      args.input = argv[++i];
    } else if (token === "--output") {
      args.output = argv[++i];
    } else {
      return null;
    }
  }
  if (args.input === undefined || args.output === undefined) return null;
  if (args.input === null || args.output === null) return null;
  return args;
}

const WHITESPACE = new Set([0x20, 0x09, 0x0a, 0x0d, 0x0c, 0x0b]);

function countLines(buf) {
  if (buf.length === 0) return 0;
  let newlines = 0;
  for (const byte of buf) {
    if (byte === 0x0a) newlines++;
  }
  if (buf[buf.length - 1] === 0x0a) return newlines;
  return newlines + 1;
}

function splitWords(buf) {
  const words = [];
  let start = -1;
  for (let i = 0; i < buf.length; i++) {
    const byte = buf[i];
    if (WHITESPACE.has(byte)) {
      if (start !== -1) {
        words.push(buf.slice(start, i).toString("utf-8"));
        start = -1;
      }
    } else if (start === -1) {
      start = i;
    }
  }
  if (start !== -1) {
    words.push(buf.slice(start).toString("utf-8"));
  }
  return words;
}

function analyze(buf) {
  const words = splitWords(buf);
  const counts = new Map();
  for (const word of words) {
    const lowered = word.toLowerCase();
    counts.set(lowered, (counts.get(lowered) || 0) + 1);
  }

  const ranked = Array.from(counts.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1];
      if (a[0] < b[0]) return -1;
      if (a[0] > b[0]) return 1;
      return 0;
    })
    .slice(0, 10)
    .map(([word, count]) => ({ word, count }));

  return {
    lines: countLines(buf),
    words: words.length,
    characters: buf.length,
    unique_words: counts.size,
    top_words: ranked,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args === null) return 1;

  let data;
  try {
    data = fs.readFileSync(args.input);
  } catch (_err) {
    return 1;
  }

  let result;
  try {
    result = analyze(data);
  } catch (_err) {
    return 2;
  }

  try {
    fs.mkdirSync(path.dirname(path.resolve(args.output)), { recursive: true });
    fs.writeFileSync(args.output, JSON.stringify(result));
  } catch (_err) {
    return 2;
  }

  return 0;
}

process.exit(main());
