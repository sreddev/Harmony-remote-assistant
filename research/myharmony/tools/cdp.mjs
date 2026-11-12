// Read-only DevTools probe (raw WebSocket, works with Chrome 29's DevTools server).
// Usage: node cdp.mjs "<js expression>"   or   node cdp.mjs --method Name '{"params":1}'
import net from 'node:net';
import crypto from 'node:crypto';

const list = await (await fetch('http://127.0.0.1:8088/json')).json();
const path = new URL(list[0].webSocketDebuggerUrl).pathname;
let method = 'Runtime.evaluate', params;
if (process.argv[2] === '--method') { method = process.argv[3]; params = JSON.parse(process.argv[4] || '{}'); }
else params = { expression: process.argv[2], returnByValue: true };

function frame(str) {
  const p = Buffer.from(str), mask = crypto.randomBytes(4);
  let h;
  if (p.length < 126) h = Buffer.from([0x81, 0x80 | p.length]);
  else if (p.length < 65536) { h = Buffer.alloc(4); h[0] = 0x81; h[1] = 0x80 | 126; h.writeUInt16BE(p.length, 2); }
  else { h = Buffer.alloc(10); h[0] = 0x81; h[1] = 0x80 | 127; h.writeBigUInt64BE(BigInt(p.length), 2); }
  const m = Buffer.alloc(p.length); for (let i = 0; i < p.length; i++) m[i] = p[i] ^ mask[i % 4];
  return Buffer.concat([h, mask, m]);
}

const s = net.connect(8088, '127.0.0.1');
let buf = Buffer.alloc(0), upgraded = false, msg = '';
s.on('connect', () => s.write(`GET ${path} HTTP/1.1\r\nHost: 127.0.0.1:8088\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${crypto.randomBytes(16).toString('base64')}\r\nSec-WebSocket-Version: 13\r\n\r\n`));
s.on('data', (d) => {
  buf = Buffer.concat([buf, d]); if(process.env.DBG) console.error('RX', d.length, JSON.stringify(d.toString().slice(0,200)));
  if (!upgraded) {
    const i = buf.indexOf('\r\n\r\n'); if (i < 0) return;
    upgraded = true; buf = buf.subarray(i + 4);
    s.write(frame(JSON.stringify({ id: 1, method, params })));
  }
  while (buf.length >= 2) {
    let len = buf[1] & 0x7f, off = 2;
    if (len === 126) { if (buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
    else if (len === 127) { if (buf.length < 10) return; len = Number(buf.readBigUInt64BE(2)); off = 10; }
    if (buf.length < off + len) return;
    const fin = buf[0] & 0x80; msg += buf.subarray(off, off + len).toString(); buf = buf.subarray(off + len);
    if (!fin) continue;
    const r = JSON.parse(msg); msg = '';
    if (r.id === 1) {
      const v = r.result?.result?.value ?? r.result ?? r.error;
      console.log(typeof v === 'string' ? v : JSON.stringify(v, null, 1));
      s.destroy();
    }
  }
});
setTimeout(() => { console.error('timeout'); process.exit(1); }, 15000);
