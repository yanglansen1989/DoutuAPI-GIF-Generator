document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        text: document.getElementById('text-input'),
        effect: document.getElementById('effect-select'),
        theme: document.getElementById('theme-select'),
        color: document.getElementById('color-input'),
        width: document.getElementById('width-input'),
        frames: document.getElementById('frames-input'),
        delay: document.getElementById('delay-input'),
        wrap: document.getElementById('wrap-input'),
        adaptiveCanvas: document.getElementById('adaptive-canvas-input'),

        widthVal: document.getElementById('width-val'),
        framesVal: document.getElementById('frames-val'),
        delayVal: document.getElementById('delay-val'),

        preview: document.getElementById('gif-preview'),
        loading: document.getElementById('loading'),
        urlInput: document.getElementById('url-input'),
        downloadBtn: document.getElementById('download-btn'),
        copyBtn: document.getElementById('copy-btn')
    };

    let debounceTimer;
    let previewRequestId = 0;
    let previewController = null;
    let previewObjectUrl = null;
    let fullUrl = '';

    elements.adaptiveCanvas.checked = true;
    elements.width.addEventListener('input', (e) => elements.widthVal.textContent = e.target.value);
    elements.frames.addEventListener('input', (e) => elements.framesVal.textContent = e.target.value);
    elements.delay.addEventListener('input', (e) => elements.delayVal.textContent = e.target.value);

    function appendEffectParams(params) {
        let colorParam = elements.color.value.trim();
        const effect = elements.effect.value;

        if (effect) {
            if (effect === 'breathing' && colorParam.includes(':')) {
                if (!colorParam.startsWith('breathing:')) {
                    colorParam = `breathing:${colorParam}`;
                }
                params.append('color', colorParam);
            } else if (effect === 'breathing') {
                params.append('color', 'breathing:#ff0000:#0000ff');
            } else {
                params.append('color', effect);
            }
        } else if (colorParam) {
            params.append('color', colorParam);
        }
    }

    function buildGenerateUrl({ preview = false, bustCache = false } = {}) {
        const params = new URLSearchParams();
        const selectedWidth = Number(elements.width.value);
        const selectedFrames = Number(elements.frames.value);

        params.append('width_pixels', preview ? Math.min(selectedWidth, 320) : selectedWidth);
        params.append('frame_count', preview ? Math.min(selectedFrames, 10) : selectedFrames);
        params.append('delay', elements.delay.value);
        params.append('theme', elements.theme.value);

        if (preview) {
            params.append('preview', 'true');
        }

        if (elements.wrap.checked) {
            params.append('wrap', 'true');
        }

        if (elements.adaptiveCanvas.checked) {
            params.append('adaptive_canvas', 'true');
        }

        appendEffectParams(params);
        params.append('text', elements.text.value || 'Hello');
        if (bustCache) {
            params.append('_ts', String(Date.now()));
        }

        return `/generate?${params.toString()}`;
    }

    async function updatePreview() {
        const requestId = ++previewRequestId;
        const previewUrl = buildGenerateUrl({ preview: true, bustCache: true });
        fullUrl = buildGenerateUrl({ preview: false });
        elements.urlInput.value = window.location.origin + fullUrl;

        if (previewController) {
            previewController.abort();
        }
        previewController = new AbortController();
        elements.loading.classList.add('active');

        try {
            const response = await fetch(previewUrl, {
                signal: previewController.signal,
                cache: 'no-store'
            });
            if (!response.ok) {
                throw new Error(`Preview failed: ${response.status}`);
            }
            const blob = await response.blob();
            if (requestId !== previewRequestId) {
                return;
            }

            if (previewObjectUrl) {
                URL.revokeObjectURL(previewObjectUrl);
            }
            previewObjectUrl = URL.createObjectURL(blob);
            elements.preview.src = previewObjectUrl;
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error(error);
            }
        } finally {
            if (requestId === previewRequestId) {
                elements.loading.classList.remove('active');
            }
        }
    }

    function triggerUpdate() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(updatePreview, 250);
    }

    const inputs = [
        elements.text, elements.effect, elements.theme,
        elements.color, elements.width, elements.frames,
        elements.delay, elements.wrap, elements.adaptiveCanvas
    ];

    inputs.forEach(input => {
        input.addEventListener('input', triggerUpdate);
        input.addEventListener('change', triggerUpdate);
    });

    elements.downloadBtn.addEventListener('click', () => {
        const link = document.createElement('a');
        link.href = fullUrl || buildGenerateUrl({ preview: false });
        link.download = 'neon_text.gif';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    elements.copyBtn.addEventListener('click', async () => {
        elements.urlInput.select();
        const url = elements.urlInput.value;

        try {
            await navigator.clipboard.writeText(url);
        } catch {
            document.execCommand('copy');
        }

        const originalText = elements.copyBtn.textContent;
        elements.copyBtn.textContent = '已复制!';
        setTimeout(() => elements.copyBtn.textContent = originalText, 2000);
    });

    updatePreview();
});
