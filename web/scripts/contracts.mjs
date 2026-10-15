import { readFile, writeFile, mkdir } from 'node:fs/promises';
import Ajv2020 from 'ajv/dist/2020.js';
import standalone from 'ajv/dist/standalone/index.js';
const root = new URL('../', import.meta.url);
const schema = JSON.parse(await readFile(new URL('../contracts/recipe.schema.json', root), 'utf8'));
const source = await readFile(new URL('../contracts/events.md', root), 'utf8');
const messages = {};
for (const line of source.split('\n')) {
  const row = line.split('|').map(x => x.trim());
  if (!/^`[A-Z][A-Z_]+`$/.test(row[1] || '') || row.length !== 8) continue;
  messages[row[1].slice(1, -1)] = { en: row[4], ru: row[5], uz: row[6] };
}
if (!messages.FRAME_STALE || !source.includes('`unknown_reason`')) throw Error('Contract extraction failed');
await mkdir(new URL('src/generated/', root), { recursive: true });
await writeFile(new URL('src/generated/messages.js', root), `// Generated from contracts/events.md. Do not hand-edit.\nexport const messages = ${JSON.stringify(messages, null, 2)};\n`);
const ajv = new Ajv2020({ strict: false, allErrors: true, code: { source: true, esm: true, lines: true } });
const validatorSource = standalone(ajv, ajv.compile(schema)).replaceAll('require("ajv/dist/runtime/equal").default', 'ajvEqual.default');
await writeFile(new URL('src/generated/recipe.js', root), `// Generated from contracts/recipe.schema.json. Do not hand-edit.\nimport ajvEqual from 'ajv/dist/runtime/equal.js';\n${validatorSource}`);
console.log(`Generated recipe validator and ${Object.keys(messages).length} fixed messages.`);
