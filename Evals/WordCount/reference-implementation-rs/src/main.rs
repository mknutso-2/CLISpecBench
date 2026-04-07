// WordCount reference implementation (Rust).
//
// Mirrors the contract exercised by Evals/WordCount/tests:
// - "characters" is the raw byte length of the input file.
// - "lines" counts '\n' bytes; a trailing line without '\n' still counts
//   as 1 line when the file is non-empty.
// - Words are whitespace-delimited tokens (ASCII whitespace).
// - Unique-word counts are case-insensitive; top_words emits lowercase forms.
// - top_words is ordered by descending count, then ascending word, capped at 10.

use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

struct Args {
    input: PathBuf,
    output: PathBuf,
}

fn parse_args(argv: &[String]) -> Option<Args> {
    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut i = 0;
    while i < argv.len() {
        match argv[i].as_str() {
            "--input" => {
                i += 1;
                if i >= argv.len() {
                    return None;
                }
                input = Some(PathBuf::from(&argv[i]));
            }
            "--output" => {
                i += 1;
                if i >= argv.len() {
                    return None;
                }
                output = Some(PathBuf::from(&argv[i]));
            }
            _ => return None,
        }
        i += 1;
    }
    Some(Args {
        input: input?,
        output: output?,
    })
}

fn is_ascii_whitespace(b: u8) -> bool {
    matches!(b, b' ' | b'\t' | b'\n' | b'\r' | 0x0c | 0x0b)
}

fn count_lines(buf: &[u8]) -> usize {
    if buf.is_empty() {
        return 0;
    }
    let newlines = buf.iter().filter(|&&b| b == b'\n').count();
    if *buf.last().unwrap() == b'\n' {
        newlines
    } else {
        newlines + 1
    }
}

fn split_words(buf: &[u8]) -> Vec<String> {
    let mut words: Vec<String> = Vec::new();
    let mut start: Option<usize> = None;
    for (i, &byte) in buf.iter().enumerate() {
        if is_ascii_whitespace(byte) {
            if let Some(s) = start {
                words.push(String::from_utf8_lossy(&buf[s..i]).into_owned());
                start = None;
            }
        } else if start.is_none() {
            start = Some(i);
        }
    }
    if let Some(s) = start {
        words.push(String::from_utf8_lossy(&buf[s..]).into_owned());
    }
    words
}

fn json_escape(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0c}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn analyze_and_serialize(buf: &[u8]) -> String {
    let words = split_words(buf);
    let mut counts: HashMap<String, usize> = HashMap::new();
    for w in &words {
        let lowered = w.to_lowercase();
        *counts.entry(lowered).or_insert(0) += 1;
    }

    let mut ranked: Vec<(String, usize)> = counts.iter().map(|(k, v)| (k.clone(), *v)).collect();
    ranked.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    ranked.truncate(10);

    let mut json = String::new();
    json.push('{');
    json.push_str(&format!("\"lines\":{},", count_lines(buf)));
    json.push_str(&format!("\"words\":{},", words.len()));
    json.push_str(&format!("\"characters\":{},", buf.len()));
    json.push_str(&format!("\"unique_words\":{},", counts.len()));
    json.push_str("\"top_words\":[");
    for (i, (word, count)) in ranked.iter().enumerate() {
        if i > 0 {
            json.push(',');
        }
        json.push_str(&format!("{{\"word\":{},\"count\":{}}}", json_escape(word), count));
    }
    json.push_str("]}");
    json
}

fn run() -> i32 {
    let argv: Vec<String> = env::args().skip(1).collect();
    let args = match parse_args(&argv) {
        Some(a) => a,
        None => return 1,
    };

    let data = match fs::read(&args.input) {
        Ok(d) => d,
        Err(_) => return 1,
    };

    let json = analyze_and_serialize(&data);

    if let Some(parent) = args.output.parent() {
        if !parent.as_os_str().is_empty() && fs::create_dir_all(parent).is_err() {
            return 2;
        }
    }
    if fs::write(&args.output, json).is_err() {
        return 2;
    }
    0
}

fn main() -> ExitCode {
    ExitCode::from(run() as u8)
}
