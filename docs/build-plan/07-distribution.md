# Phase 7: Distribution & Release

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: All previous phases

---

## Goal

Package the application for end-user distribution and publish library packages for developers.

## Desktop Application (Electron Builder)

The desktop app bundles both the Electron/React frontend and a PyInstaller-built Python backend into a single installer:

```bash
# 1. Build the Python backend as a standalone executable
pyinstaller --name zorivest-api --onefile --distpath dist-python packages/api/src/zorivest_api/__main__.py

# 2. Build the Electron app with the Python binary included as extra resource
npx electron-builder --config electron-builder.config.js
```

```javascript
// electron-builder.config.js
module.exports = {
  appId: 'com.zorivest.app',
  productName: 'Zorivest',
  directories: { output: 'dist' },
  extraResources: [
    { from: 'dist-python/zorivest-api${ext}', to: 'backend/' }
  ],
  win: { target: ['nsis'], icon: 'assets/icon.ico' },
  mac: { target: ['dmg'], icon: 'assets/icon.icns' },
  linux: { target: ['AppImage'] },
};
```

The Electron main process detects whether it's running in development (spawn `python -m zorivest_api`) or packaged mode (spawn the PyInstaller binary from `resources/backend/`).

## Python Library (PyPI)

```bash
# Publish zorivest-core to PyPI for Python developers
cd packages/core
uv build
uv publish  # or: twine upload dist/*
```

This enables other Python projects to `pip install zorivest-core` and use the domain entities, services, and calculator without the UI or MCP.

## TypeScript MCP Server (npm)

```bash
# Publish standalone MCP server for AI agent users
cd mcp-server
npm run build
npm publish --access public  # @zorivest/mcp-server
```

Users install with `npx @zorivest/mcp-server --api-url http://localhost:8765` or add to their IDE's MCP configuration.

## GitHub Releases

Automate with GitHub Actions: on tag push, build all three artifacts (desktop installer, PyPI package, npm package) and attach to the GitHub Release with auto-generated changelog from conventional commits.

## Exit Criteria

- Desktop installer builds for Windows, macOS, Linux
- PyPI package publishes and installs correctly
- npm package publishes and serves MCP tools
- GitHub Actions CI/CD pipeline passes

## Outputs

- Windows NSIS installer, macOS DMG, Linux AppImage
- `zorivest-core` on PyPI
- `@zorivest/mcp-server` on npm
- GitHub Actions release workflow
