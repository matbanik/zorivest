# Phase 6: GUI (Electron + React)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the desktop GUI last — it's the outermost layer. The Electron shell spawns the Python backend as a child process and the React UI communicates with it via REST on localhost. Use TanStack Table for data grids, Lightweight Charts for financial charts.

## GUI Image Display Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  TRADES TABLE (TanStack Table)                                    │
│  ┌──────┬────────────┬────────┬─────┬───────┬─────┬───────┬──────┐ │
│  │ Time │ Instrument │ Action │ Qty │ Price │ Acc │ Comm  │ 📷   │ │
│  ├──────┼────────────┼────────┼─────┼───────┼─────┼───────┼──────┤ │
│  │ ...  │ SPY STK    │  BOT   │ 100 │619.61 │ DU..│  1.02 │ 🖼×2 │ │  ← badge shows image count
│  │ ...  │ AAPL STK   │  SLD   │  50 │198.30 │ DU..│  0.52 │      │ │
│  └──────┴────────────┴────────┴─────┴───────┴─────┴───────┴──────┘ │
│                                                                     │
│  When a trade with images is selected:                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SCREENSHOT PANEL (below table or in side panel)                ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     ││
│  │  │ thumb 1  │  │ thumb 2  │  │  + Add   │     [Delete] [View] ││
│  │  │ 📷       │  │ 📷       │  │          │                     ││
│  │  │ "Entry"  │  │ "Exit"   │  │          │                     ││
│  │  └──────────┘  └──────────┘  └──────────┘                     ││
│  │  Caption: Entry screenshot SPY 2025-07-02                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Key React/Electron Components for Images

- **TanStack Table** with custom cell renderer for thumbnail badge column
- **CSS lightbox / react-medium-image-zoom** for full-size image viewing with zoom
- **HTML File Input + Drag/Drop** for screenshot import
- **Electron clipboard API** (`clipboard.readImage()`) for paste-from-clipboard (Ctrl+V)
- Image processing (thumbnail generation) remains in the Python backend via REST

## Screenshot Panel (React + Electron)

```typescript
// ui/src/components/ScreenshotPanel.tsx

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API = (window as any).__ZORIVEST_API_URL__ ?? 'http://localhost:8765/api/v1';

interface TradeImage {
  id: number;
  caption: string;
  mime_type: string;
  file_size: number;
  thumbnail_url: string;
}

export function ScreenshotPanel({ tradeId }: { tradeId: string }) {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Fetch thumbnails for the selected trade
  const { data: images = [] } = useQuery<TradeImage[]>({
    queryKey: ['trade-images', tradeId],
    queryFn: () => fetch(`${API}/trades/${tradeId}/images`).then(r => r.json()),
  });

  // Upload via file input or drag-and-drop
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return fetch(`${API}/trades/${tradeId}/images`, {
        method: 'POST', body: formData,
      }).then(r => r.json());
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trade-images', tradeId] }),
  });

  // Paste from clipboard (Ctrl+V) — uses Electron clipboard API
  const handlePaste = async () => {
    const { clipboard, nativeImage } = window.electronAPI;
    const img = clipboard.readImage();
    if (!img.isEmpty()) {
      const blob = new Blob([img.toPNG()], { type: 'image/png' });
      uploadMutation.mutate(new File([blob], 'clipboard.png'));
    }
  };

  return (
    <div className="screenshot-panel">
      {/* Thumbnail strip */}
      <div className="thumbnail-strip">
        {images.map(img => (
          <div key={img.id} className="thumb" onClick={() => setSelectedId(img.id)}>
            <img src={`${API}/images/${img.id}/thumbnail`} alt={img.caption} />
            <span>{img.caption}</span>
          </div>
        ))}
        <label className="thumb add-btn">
          + Add
          <input type="file" hidden accept="image/*"
            onChange={e => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])} />
        </label>
      </div>

      {/* Full-size viewer (lightbox) */}
      {selectedId && (
        <div className="lightbox" onClick={() => setSelectedId(null)}>
          <img src={`${API}/images/${selectedId}/full`} alt="Full size" />
        </div>
      )}

      <button onClick={handlePaste}>📋 Paste (Ctrl+V)</button>
    </div>
  );
}
```

## Exit Criteria

- Electron app launches, spawns Python backend
- Trades table displays with image badges
- Screenshot panel supports upload, paste, and lightbox viewing
- Display mode toggles ($ hide, % hide, % mode) work correctly

## Outputs

- Electron main process with Python backend lifecycle management
- React components: Trades table, Screenshot panel, Dashboard
- TanStack Table integration with image badge column
- Clipboard paste support via Electron API
