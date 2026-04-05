import '@testing-library/jest-dom/vitest'

// ── Canvas 2D Context Mock ──────────────────────────────────────────────────
// jsdom does not implement HTMLCanvasElement.prototype.getContext.
// This mock provides a no-op 2D context so the Sparkline component's
// useEffect drawing path actually executes during tests instead of
// bailing at `if (!ctx) return`.

function createMockCanvas2DContext(): CanvasRenderingContext2D {
    return {
        // Drawing methods used by Sparkline
        clearRect: () => {},
        beginPath: () => {},
        moveTo: () => {},
        lineTo: () => {},
        stroke: () => {},
        fill: () => {},
        arc: () => {},
        rect: () => {},
        closePath: () => {},
        save: () => {},
        restore: () => {},
        scale: () => {},
        translate: () => {},
        rotate: () => {},
        setTransform: () => {},
        resetTransform: () => {},
        // Property stubs
        strokeStyle: '',
        fillStyle: '',
        lineWidth: 1,
        lineJoin: 'miter' as CanvasLineJoin,
        lineCap: 'butt' as CanvasLineCap,
        font: '',
        textAlign: 'start' as CanvasTextAlign,
        textBaseline: 'alphabetic' as CanvasTextBaseline,
        globalAlpha: 1,
        globalCompositeOperation: 'source-over' as GlobalCompositeOperation,
        // Measurement stub
        measureText: () => ({ width: 0 }) as TextMetrics,
        // Image drawing stubs
        drawImage: () => {},
        createLinearGradient: () => ({
            addColorStop: () => {},
        }),
        createRadialGradient: () => ({
            addColorStop: () => {},
        }),
        getImageData: () => ({ data: new Uint8ClampedArray(0), width: 0, height: 0 }),
        putImageData: () => {},
        canvas: document.createElement('canvas'),
    } as unknown as CanvasRenderingContext2D
}

HTMLCanvasElement.prototype.getContext = function (contextId: string) {
    if (contextId === '2d') {
        return createMockCanvas2DContext()
    }
    return null
} as typeof HTMLCanvasElement.prototype.getContext
