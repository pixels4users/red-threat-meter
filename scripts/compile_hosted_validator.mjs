import { readFile, mkdir, writeFile } from 'node:fs/promises';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import standaloneCode from 'ajv/dist/standalone/index.js';

const schema = JSON.parse(await readFile(new URL('../schemas/dashboard/report.schema.json', import.meta.url)));
const ajv = new Ajv2020({ strict: false, code: { source: true }, allErrors: false });
addFormats(ajv);
const output = new URL('../hosting/.generated/', import.meta.url);
await mkdir(output, { recursive: true });
await writeFile(new URL('validate-report.cjs', output), standaloneCode(ajv, ajv.compile(schema)));
