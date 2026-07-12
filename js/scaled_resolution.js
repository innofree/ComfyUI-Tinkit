import { app } from "../../scripts/app.js";

// Must stay in sync with resolution.py ASPECT_RATIO_PRESETS
const PRESETS = {
    "1:1  square 1024":    [1024, 1024],
    "3:4  portrait 768":   [768,  1024],
    "4:3  landscape 768":  [1024, 768],
    "2:3  portrait 832":   [832,  1216],
    "3:2  landscape 832":  [1216, 832],
    "9:16 portrait 576":   [576,  1024],
    "16:9 landscape 576":  [1024, 576],
    "9:16 portrait 768":   [768,  1344],
    "16:9 landscape 768":  [1344, 768],
    "5:8  portrait":       [640,  1024],
    "8:5  landscape":      [1024, 640],
    "21:9 cinematic":      [1024, 440],
    "3:4  portrait 896":   [896,  1152],
    "4:3  landscape 896":  [1152, 896],
    "1:1  square 1224":    [1224, 1224],
    "3:4  portrait 1224":  [1224, 1632],
    "4:3  landscape 1224": [1632, 1224],
};

function applyPreset(node) {
    const ar = node.widgets?.find(w => w.name === "aspect_ratio");
    const w  = node.widgets?.find(w => w.name === "width");
    const h  = node.widgets?.find(w => w.name === "height");
    const sw = node.widgets?.find(w => w.name === "swap_dimensions");
    const lbl = node.widgets?.find(w => w.name === "_res_label");

    if (!ar || !w || !h) return;

    const preset   = PRESETS[ar.value];
    const isCustom = !preset;

    w.disabled = !isCustom;
    h.disabled = !isCustom;

    if (preset) {
        w.value = preset[0];
        h.value = preset[1];
    }

    // Update display label
    if (lbl) {
        const pw = isCustom ? w.value  : preset[0];
        const ph = isCustom ? h.value  : preset[1];
        const swapped = sw?.value;
        lbl.value = swapped
            ? `base: ${ph} × ${pw}`
            : `base: ${pw} × ${ph}`;
    }

    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "Comfy.Tinkit.ScaledResolution",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ScaledResolution") return;

        // Patch onNodeCreated to wire callbacks and add display label
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.call(this);

            // Add a read-only label widget right after height
            const heightIdx = this.widgets?.findIndex(w => w.name === "height");
            const labelWidget = this.addWidget("text", "_res_label", "base: — × —", () => {});
            labelWidget.disabled = true;
            labelWidget.serialize = false;

            // Move label to just after height widget
            if (heightIdx >= 0) {
                const idx = this.widgets.indexOf(labelWidget);
                this.widgets.splice(idx, 1);
                this.widgets.splice(heightIdx + 1, 0, labelWidget);
            }

            // Intercept aspect_ratio changes
            const ar = this.widgets?.find(w => w.name === "aspect_ratio");
            if (ar) {
                const origCb = ar.callback;
                ar.callback = (value) => {
                    origCb?.call(ar, value);
                    applyPreset(this);
                };
            }

            // Intercept swap_dimensions changes
            const sw = this.widgets?.find(w => w.name === "swap_dimensions");
            if (sw) {
                const origCb = sw.callback;
                sw.callback = (value) => {
                    origCb?.call(sw, value);
                    applyPreset(this);
                };
            }

            // Intercept custom width/height changes (update label while in custom mode)
            for (const name of ["width", "height"]) {
                const wgt = this.widgets?.find(w => w.name === name);
                if (wgt) {
                    const origCb = wgt.callback;
                    wgt.callback = (value) => {
                        origCb?.call(wgt, value);
                        applyPreset(this);
                    };
                }
            }

            applyPreset(this);
        };

        // Re-apply on workflow load (widgets already populated at this point)
        const origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (config) {
            origConfigure?.call(this, config);
            setTimeout(() => applyPreset(this), 0);
        };
    },
});
