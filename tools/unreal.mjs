// Builds and checks Velisect (this folder is the Unreal project):
//
//   compile   UnrealBuildTool compiles the C++ module for the editor (Source/Velisect)
//   test      the "Velisect.*" automation tests, headless in the editor (VS_TEST=Velisect.Content runs one group)
//   package   compile, cook and pack the game: Packaged/Windows/Velisect.exe
//   play      start the packaged game, as Play Velisect.bat does
//   open      open the editor with its MCP server on port 8010 (8000 belongs to the Mournhollow editor)
//   py <file> run a Python file inside the open Velisect editor (remote execution; editor automation),
//             or in a headless editor when none is open (no viewport or PIE; prints come back the same)
//   blender <file>  run a Blender pipeline script in a fresh headless Blender (factory settings)
//   shot [name]     in the open editor: start PIE, wait, save the editor's image to Saved/ToolLogs/shots/<name>.png, stop PIE
//
// Usage: node tools/unreal.mjs <step> [arg]... [--verbose]   (no steps = compile test)
// Quiet by default: each step's whole output goes to Saved/ToolLogs/<step>.log; the console gets the step's time,
// its errors when it fails, failed tests and the summary. --verbose (or VS_VERBOSE=1) prints everything.
// compile and package need every Velisect editor and the packaged game closed (ask the user; never kill them).
import { spawn, execSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, rmSync, mkdirSync, openSync, closeSync, appendFileSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const project = join(dirname(fileURLToPath(import.meta.url)), '..');
const uproject = join(project, 'Velisect.uproject');
const pipeline = join(project, 'tools', 'pipeline');
const gameDir = join(project, 'Packaged', 'Windows');
const gameExe = join(gameDir, 'Velisect.exe');
const toolLogs = join(project, 'Saved', 'ToolLogs');

function findEngine() {
  if (process.env.UE_ROOT) return process.env.UE_ROOT;
  const root = join(process.env.ProgramFiles || 'C:\\Program Files', 'Epic Games');
  const newest = existsSync(root) && readdirSync(root).filter((d) => /^UE_5\.\d+$/.test(d)).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }))[0];
  if (!newest) throw new Error('No Unreal Engine 5 found; set UE_ROOT.');
  return join(root, newest);
}
const engine = findEngine();
const editorExe = join(engine, 'Engine', 'Binaries', 'Win64', 'UnrealEditor.exe');
// Unreal's .NET tools on the .NET it ships with, run directly (no shell, so paths with spaces stay whole)
const dotnet = join(engine, 'Engine', 'Binaries', 'ThirdParty', 'DotNet', '10.0', 'win-x64', 'dotnet.exe');

const verbose = process.argv.includes('--verbose') || process.env.VS_VERBOSE === '1';
let stepLog = null;
const note = (text) => { if (stepLog) appendFileSync(stepLog, text + '\n'); };
const rel = (f) => f.slice(project.length + 1).replace(/\\/g, '/');

function run(cmd, args, opts = {}) {
  const quiet = !verbose && stepLog && !opts.detached && !opts.loud;
  if (quiet) note(`> ${cmd} ${args.join(' ')}`); else console.log(`> ${cmd} ${args.join(' ')}`);
  const fd = quiet ? openSync(stepLog, 'a') : null;
  return new Promise((done) => {
    const finish = (code) => { if (fd !== null) closeSync(fd); done(code); };
    const child = spawn(cmd, args, { cwd: project, stdio: 'inherit', ...opts, ...(quiet ? { stdio: ['ignore', fd, fd] } : {}) });
    child.on('error', (e) => { console.error(e.message); finish(1); }).on('exit', (code) => finish(code ?? 1));
    if (opts.detached) { child.unref(); finish(0); }
  });
}

// a failed step's log cut to what explains it: its error lines (once each) and its last few lines
function errorLines(file) {
  if (!existsSync(file)) return '';
  const lines = readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean);
  const hits = [...new Set(lines.filter((l) => /\berror\b|fatal|exception|failed/i.test(l) && !/\b0 error/i.test(l)).map((l) => l.trim()))];
  return [...hits.slice(0, 30), ...(hits.length > 30 ? [`… ${hits.length - 30} more`] : []), '--- last lines ---', ...lines.slice(-8)].join('\n');
}

const running = (pattern) => { try { return pattern.test(execSync('tasklist /V /FO CSV /NH', { encoding: 'utf8' })); } catch { return false; } };
const velisectEditorOpen = () => running(/UnrealEditor\.exe.*Velisect - Unreal Editor/i);

function testReport(dir) {
  const index = join(dir, 'index.json');
  if (!existsSync(index)) { console.error('No test report: did the editor start? See Saved/Logs/Velisect.log'); return 1; }
  const r = JSON.parse(readFileSync(index, 'utf8').trimStart());
  const out = (ok, text) => { if (verbose || !ok) console.log(text); else note(text); };
  for (const t of r.tests) {
    const ok = t.state === 'Success';
    out(ok, `${ok ? 'ok  ' : 'FAIL'} ${t.fullTestPath}`);
    for (const e of t.entries || []) if (e.event && (ok ? e.event.type === 'Info' : e.event.type !== 'Info')) out(ok, `       ${e.event.type}: ${e.event.message}`);
  }
  console.log(`${r.succeeded + (r.succeededWithWarnings || 0)} passed, ${r.failed} failed${r.notRun ? `, ${r.notRun} not run` : ''}${verbose ? '' : ` (each result in ${rel(stepLog)})`}`);
  return r.tests.length && !r.failed && !r.notRun ? 0 : 1;
}

const python = (script, args = []) => run('python', ['-I', join(pipeline, script), ...args], { loud: true });
const argAfter = (step) => { const i = process.argv.indexOf(step); return i >= 0 ? process.argv[i + 1] : undefined; };

const steps = {
  compile: () => {
    if (velisectEditorOpen()) { console.error('The Velisect editor is open: ask the user to close it (or save and close it), then compile.'); return 1; }
    // -NoHotReloadFromIDE: the Mournhollow editor's Live Coding would otherwise block every build on this engine
    return run(dotnet, [join(engine, 'Engine', 'Binaries', 'DotNET', 'UnrealBuildTool', 'UnrealBuildTool.dll'), 'VelisectEditor', 'Win64', 'Development', `-Project=${uproject}`, '-WaitMutex', '-NoHotReloadFromIDE']);
  },
  test: async () => {
    const dir = join(project, 'Saved', 'Automation', 'Velisect');
    rmSync(dir, { recursive: true, force: true });
    await run(editorExe.replace(/UnrealEditor\.exe$/, 'UnrealEditor-Cmd.exe'), [uproject, `-ExecCmds=Automation RunTests ${process.env.VS_TEST || 'Velisect'}`, '-TestExit=Automation Test Queue Empty',
      `-ReportExportPath=${dir}`, '-unattended', '-nullrhi', '-nosplash', '-nopause', '-NoSound', '-stdout']);
    return testReport(dir);
  },
  package: async () => {
    if (running(/Velisect\.exe|Velisect-Win64/i)) { console.error('Velisect is running: close the game, then package again.'); return 1; }
    if (velisectEditorOpen()) { console.error('The Velisect editor is open: ask the user to close it, then package.'); return 1; }
    const code = await run(dotnet, [join(engine, 'Engine', 'Binaries', 'DotNET', 'AutomationTool', 'AutomationTool.dll'), 'BuildCookRun',
      `-project=${uproject}`, '-noP4', '-platform=Win64', '-clientconfig=Development', '-build', '-cook', '-stage', '-pak', '-iostore', '-prereqs',
      '-archive', `-archivedirectory=${join(project, 'Packaged')}`, '-unattended', '-utf8output', '-nocompileeditor', '-NoHotReloadFromIDE']);
    if (code) return code;
    // the cook succeeds even when a material fails and the game falls back to the default one: fail it here
    const lines = readFileSync(stepLog, 'utf8').split(/\r?\n/);
    const bad = [...new Set(lines.flatMap((l, i) => /Failed to compile Material/.test(l) ? [l.trim(), (lines[i + 1] || '').trim()] : []))];
    if (bad.length) { console.error(`Materials that won't render in the game:\n${bad.slice(0, 12).join('\n')}`); return 1; }
    return 0;
  },
  play: () => {
    if (!existsSync(gameExe)) { console.error('No packaged game yet: node tools/unreal.mjs package'); return 1; }
    return run(gameExe, [], { cwd: gameDir, detached: true, stdio: 'ignore' });
  },
  open: () => run(editorExe, [uproject, '-ModelContextProtocolStartServer', '-ModelContextProtocolPort=8010'], { detached: true, stdio: 'ignore' }),
  py: async () => {
    const file = argAfter('py');
    if (!file) { console.error('Usage: node tools/unreal.mjs py <file.py>'); return 2; }
    if (velisectEditorOpen()) return python('uepy.py', [resolve(project, file)]);
    // No editor open: the python commandlet, with print() routed into the log so the script's output comes back
    const wrapper = join(toolLogs, 'py_headless.py');
    writeFileSync(wrapper, ['import sys, unreal', 'class Out:', '    buf = ""',
      '    def write(self, s):', '        self.buf += s', '        *lines, self.buf = self.buf.split(chr(10))',
      '        for line in lines: unreal.log_warning("VSPY " + line)', '    def flush(self): pass',
      'sys.stdout = Out()', `target = ${JSON.stringify(resolve(project, file))}`,
      'exec(compile(open(target).read(), target, "exec"), {"__name__": "__main__", "__file__": target})'].join('\n'));
    await run(editorExe.replace(/UnrealEditor\.exe$/, 'UnrealEditor-Cmd.exe'), [uproject, '-run=pythonscript', `-script=${wrapper}`,
      '-unattended', '-nullrhi', '-nosplash', '-nopause', '-NoSound', '-stdout']);
    const lines = readFileSync(stepLog, 'utf8').split(/\r?\n/);
    for (const l of lines) { const m = l.match(/\]LogPython: Warning: VSPY (.*)$/); if (m) console.log(m[1]); }  // not the summary's repeats
    const errors = lines.filter((l) => /LogPython: Error|Traceback/.test(l));
    if (errors.length) { console.error(errors.slice(0, 20).join('\n')); return 1; }
    return 0;
  },
  blender: () => {
    const file = argAfter('blender');
    if (!file) { console.error('Usage: node tools/unreal.mjs blender <file.py>'); return 2; }
    return python('blx.py', [resolve(project, file)]);
  },
  shot: () => {
    mkdirSync(join(toolLogs, 'shots'), { recursive: true });
    return python('pie_shot.py', [join(toolLogs, 'shots', `${argAfter('shot') || 'pie'}.png`)]);
  },
};

const known = Object.keys(steps);
const given = process.argv.slice(2).filter((a, i, all) => a !== '--verbose' && !['py', 'blender', 'shot'].includes(all[i - 1]));
const wanted = given.length ? given : ['compile', 'test'];
mkdirSync(toolLogs, { recursive: true });
for (const s of wanted) {
  if (!steps[s]) { console.error(`Unknown step "${s}". Steps: ${known.join(', ')}`); process.exit(2); }
  console.log(`\n=== ${s} ===`);
  stepLog = join(toolLogs, `${s}.log`);
  writeFileSync(stepLog, '');
  const t0 = Date.now();
  const code = await steps[s]();
  const secs = Math.round((Date.now() - t0) / 1000);
  if (code) {
    if (!verbose) console.error(errorLines(stepLog));
    console.error(`\nStep "${s}" failed (exit ${code}, ${secs} s)${verbose ? '' : `: whole output in ${rel(stepLog)}`}.`);
    process.exit(code);
  }
  console.log(`${s} ok (${secs} s)`);
}
if (wanted.includes('package')) console.log(`\nVelisect is built: ${gameExe}\nPlay it with Play Velisect.bat (or npm run play).`);
