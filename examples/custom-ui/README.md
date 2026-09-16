# Starter custom UI

One HTML file, no build step, no dependencies. It reads the ClawMetry
`q/1` API and draws 30 days of agent spend by day, runtime and model.

It exists to be edited. Open it, change it, or hand it to a coding agent
along with the API guide and ask for the view you actually want.

## Run it

```bash
# 1. serve this directory on a port
cd examples/custom-ui && python3 -m http.server 3000

# 2. create a key that names that origin
clawmetry key create --name starter \
    --scope read:metrics --origin http://localhost:3000

# 3. open http://localhost:3000 and paste the key
```

The key is kept in this browser's local storage and sent to your own
ClawMetry, nowhere else.

## Why `read:metrics`

This page has no backend, so any key it holds lives in the browser.
`read:metrics` is the scope that covers counts, tokens, cost and health
and cannot return a prompt, a reply or a file path. If you extend the
page into something that needs session content, put a backend in front of
it and keep the wider key there.

## Making it yours

The API describes itself. Fetch the guide with your key and give it to a
coding agent with a description of what you want:

```bash
curl -H "Authorization: Bearer cmk_..." \
     http://localhost:8900/api/q/1/llms.txt
```

Full walkthrough: [`docs/BUILD_YOUR_OWN_UI.md`](../../docs/BUILD_YOUR_OWN_UI.md).
