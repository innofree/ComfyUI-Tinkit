import { app } from "../../scripts/app.js";

// Parse "W×H" from a preset name like "3:2  landscape 1216×832  SDXL"
function parseDims(name) {
    const m = name.match(/(\d+)[×x](\d+)/);
    return m ? [parseInt(m[1]), parseInt(m[2])] : null;
}

function applyPreset(node, presets) {
    const ar  = node.widgets?.find(w => w.name === "aspect_ratio");
    const w   = node.widgets?.find(w => w.name === "width");
    const h   = node.widgets?.find(w => w.name === "height");
    const sw  = node.widgets?.find(w => w.name === "swap_dimensions");
    const lbl = node.widgets?.find(w => w.name === "_res_label");

    if (!ar || !w || !h) return;

    const dims     = presets[ar.value];
    const isCustom = !dims;

    w.disabled = !isCustom;
    h.disabled = !isCustom;

    if (dims) {
        w.value = dims[0];
        h.value = dims[1];
    }

    if (lbl) {
        const pw = isCustom ? w.value : dims[0];
        const ph = isCustom ? h.value : dims[1];
        lbl.value = sw?.value ? `base: ${ph} × ${pw}` : `base: ${pw} × ${ph}`;
    }

    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "Comfy.Tinkit.ScaledResolution",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ScaledResolution") return;

        // Build preset map from nodeData — automatically in sync with Python
        const presetNames = nodeData.input?.required?.aspect_ratio?.[0] ?? [];
        const presets = {};
        for (const name of presetNames) {
            if (name === "custom") continue;
            const dims = parseDims(name);
            if (dims) presets[name] = dims;
        }

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.call(this);

            // Read-only label widget inserted after height
            const heightIdx = this.widgets?.findIndex(w => w.name === "height") ?? -1;
            const labelWidget = this.addWidget("text", "_res_label", "base: — × —", () => {});
            labelWidget.disabled  = true;
            labelWidget.serialize = false;

            if (heightIdx >= 0) {
                const idx = this.widgets.indexOf(labelWidget);
                this.widgets.splice(idx, 1);
                this.widgets.splice(heightIdx + 1, 0, labelWidget);
            }

            for (const [wname, hook] of [
                ["aspect_ratio",  null],
                ["swap_dimensions", null],
                ["width",         null],
                ["height",        null],
            ]) {
                const wgt = this.widgets?.find(w => w.name === wname);
                if (!wgt) continue;
                const origCb = wgt.callback;
                wgt.callback = (value) => {
                    origCb?.call(wgt, value);
                    applyPreset(this, presets);
                };
            }

            applyPreset(this, presets);
        };

        const origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (config) {
            origConfigure?.call(this, config);
            setTimeout(() => applyPreset(this, presets), 0);
        };
    },
});
