// Parse a narrow wrapper shape, never execute generated JavaScript.
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const batches = JSON.parse(fs.readFileSync(0, 'utf8'));
function inspect(source) {
  const ast = acorn.parse(source, {ecmaVersion:'latest', sourceType:'module', allowAwaitOutsideFunction:true});
  let command = null, patch = null, tool = null, calls = 0, resultVariable = null;
  let literalVariable = null, literalValue = null, literalUsed = false;
  function awaitedTool(node) {
    if (!node || node.type !== 'AwaitExpression') return false;
    const call = node.argument, callee = call && call.callee;
    if (call.type !== 'CallExpression' || callee.type !== 'MemberExpression' || callee.computed || callee.object.type !== 'Identifier' || callee.object.name !== 'tools' || call.arguments.length !== 1) return false;
    const argument = call.arguments[0];
    if (callee.property.name === 'apply_patch') {
      if (argument.type === 'Literal' && typeof argument.value === 'string') patch = argument.value;
      else if (argument.type === 'Identifier' && literalVariable !== null && argument.name === literalVariable) {
        patch = literalValue; literalUsed = true;
      } else return false;
      tool = 'apply_patch'; calls += 1; return true;
    }
    if (callee.property.name !== 'exec_command') return false;
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
    command = values.get('cmd'); tool = 'exec_command'; calls += 1; return true;
  }
  function printedResult(node) {
    if (!node || node.type !== 'CallExpression' || node.callee.type !== 'Identifier' || node.callee.name !== 'text' || node.arguments.length !== 1) return false;
    const arg=node.arguments[0];
    if (awaitedTool(arg)) return true;
    // This exact display-only ternary follows a direct awaited tool request.
    // Do not admit branches that choose whether (or which) tool gets called.
    if (arg.type === 'ConditionalExpression' && resultVariable !== null && resultVariable !== 'JSON' && literalVariable !== 'JSON') {
      const test = arg.test, stringify = arg.alternate, callee = stringify.callee;
      const isResult = node => node && node.type === 'Identifier' && node.name === resultVariable;
      if (test.type === 'BinaryExpression' && test.operator === '===' &&
          test.left.type === 'UnaryExpression' && test.left.operator === 'typeof' && isResult(test.left.argument) &&
          test.right.type === 'Literal' && test.right.value === 'string' && isResult(arg.consequent) &&
          stringify.type === 'CallExpression' && !stringify.optional &&
          callee.type === 'MemberExpression' && !callee.computed && !callee.optional &&
          callee.object.type === 'Identifier' && callee.object.name === 'JSON' && callee.property.name === 'stringify' &&
          stringify.arguments.length === 1 && isResult(stringify.arguments[0])) return true;
    }
    return resultVariable !== null && ((arg.type === 'Identifier' && arg.name === resultVariable) || (arg.type === 'MemberExpression' && !arg.computed && arg.object.type === 'Identifier' && arg.object.name === resultVariable && arg.property.name === 'output'));
  }
  for (const statement of ast.body) {
    if (statement.type === 'EmptyStatement') continue;
    if (statement.type === 'VariableDeclaration' && statement.declarations.length === 1 && resultVariable === null) {
      const declaration=statement.declarations[0];
      if (statement.kind === 'const' && literalVariable === null && calls === 0 && declaration.id.type === 'Identifier' && !['tools','text'].includes(declaration.id.name) && declaration.init && declaration.init.type === 'Literal' && typeof declaration.init.value === 'string') {
        literalVariable = declaration.id.name; literalValue = declaration.init.value; continue;
      }
      if (declaration.id.type === 'Identifier' && (['tools','text',literalVariable].includes(declaration.id.name))) return {available:false,reason:'wrapper shadows a binding'};
      if (declaration.id.type !== 'Identifier' || !awaitedTool(declaration.init)) return {available:false,reason:'wrapper is not one direct awaited tool call'};
      resultVariable=declaration.id.name;
    } else if (statement.type === 'ExpressionStatement' && (printedResult(statement.expression) || awaitedTool(statement.expression))) {
      // Exact display or awaited-call forms only; no loops/tool-selection branches/catches.
    } else return {available:false,reason:'wrapper contains unsupported control flow or expressions'};
  }
  return calls === 1 && (literalVariable === null || literalUsed)
    ? {available:true,tool,command,patch}
    : {available:false,reason:'wrapper does not contain exactly one unambiguous awaited tool request'};
}
process.stdout.write(JSON.stringify(batches.map(item=>{
  try{return {id:item.id,...inspect(item.source)}}
  catch(error){return {id:item.id,available:false,parse_error:error instanceof SyntaxError,reason:'wrapper parse failed: '+error.message}}
})));
