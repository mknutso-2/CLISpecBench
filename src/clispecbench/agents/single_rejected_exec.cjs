// Parse a narrow wrapper shape, never execute generated JavaScript.
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const batches = JSON.parse(fs.readFileSync(0, 'utf8'));
function inspect(source) {
  const ast = acorn.parse(source, {ecmaVersion:'latest', sourceType:'module', allowAwaitOutsideFunction:true});
  let command = null, calls = 0, resultVariable = null;
  function awaitedExec(node) {
    if (!node || node.type !== 'AwaitExpression') return false;
    const call = node.argument, callee = call && call.callee;
    if (call.type !== 'CallExpression' || callee.type !== 'MemberExpression' || callee.computed || callee.object.type !== 'Identifier' || callee.object.name !== 'tools' || callee.property.name !== 'exec_command' || call.arguments.length !== 1) return false;
    const argument = call.arguments[0];
    if (argument.type !== 'ObjectExpression') return false;
    const values = new Map();
    for (const property of argument.properties) {
      if (property.type !== 'Property' || property.kind !== 'init' || property.method || property.computed || property.shorthand) return false;
      const key = property.key.type === 'Identifier' ? property.key.name : property.key.type === 'Literal' ? property.key.value : null;
      const value = property.value;
      if (typeof key !== 'string' || values.has(key) || value.type !== 'Literal' || value.regex || !['string','number','boolean','object'].includes(typeof value.value) || (typeof value.value === 'object' && value.value !== null)) return false;
      values.set(key,value.value);
    }
    if (typeof values.get('cmd') !== 'string') return false;
    command = values.get('cmd'); calls += 1; return true;
  }
  function printedResult(node) {
    if (!node || node.type !== 'CallExpression' || node.callee.type !== 'Identifier' || node.callee.name !== 'text' || node.arguments.length !== 1) return false;
    const arg=node.arguments[0];
    if (awaitedExec(arg)) return true;
    return resultVariable !== null && ((arg.type === 'Identifier' && arg.name === resultVariable) || (arg.type === 'MemberExpression' && !arg.computed && arg.object.type === 'Identifier' && arg.object.name === resultVariable && arg.property.name === 'output'));
  }
  for (const statement of ast.body) {
    if (statement.type === 'EmptyStatement') continue;
    if (statement.type === 'VariableDeclaration' && statement.declarations.length === 1 && resultVariable === null) {
      const declaration=statement.declarations[0];
      if (declaration.id.type !== 'Identifier' || !awaitedExec(declaration.init)) return {available:false,reason:'wrapper is not one direct awaited exec_command'};
      resultVariable=declaration.id.name;
    } else if (statement.type === 'ExpressionStatement' && (printedResult(statement.expression) || awaitedExec(statement.expression))) {
      // Exact print-result or awaited-call forms only; no loops/branches/catches.
    } else return {available:false,reason:'wrapper contains unsupported control flow or expressions'};
  }
  return calls === 1 ? {available:true,command} : {available:false,reason:'wrapper does not contain exactly one unambiguous awaited tool request'};
}
process.stdout.write(JSON.stringify(batches.map(item=>{
  try{return {id:item.id,...inspect(item.source)}}
  catch(error){return {id:item.id,available:false,parse_error:error instanceof SyntaxError,reason:'wrapper parse failed: '+error.message}}
})));
