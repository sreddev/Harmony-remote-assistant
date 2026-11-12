# MyHarmony research tools

What was used to analyse the MyHarmony 1.0.1.308 desktop app on 11 November 2026. The extracted
material itself (app packages, assemblies, strings, protocol templates, page scripts) is Logitech's
software and is not published here; these tools extract it again from an installed copy.

| Tool | Does |
|---|---|
| `tools/xap.py` | lists a XAP's manifest and assemblies |
| `tools/ext.py` | extracts a XAP whose entries use backslash paths |
| `tools/str.py` | prints ASCII and UTF-16 strings of a binary |
| `tools/cdp.mjs` | a raw WebSocket DevTools client for the app's Chrome 29 debugging port (8088), read-only `Runtime.evaluate` |
| `tools/snap.mjs` | renders an HTML page (file or URL) in headless Edge and saves it as MHTML |

The packages are cached by the app under
`C:\Program Files (x86)\Logitech\MyHarmony\AppFiles\temp\data` (`f_*` files that are ZIP archives).

`pages/` holds the HTML sources of the three published pages, and `pages/render/` the copies used to
render them with their diagrams.
