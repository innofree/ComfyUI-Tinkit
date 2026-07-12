import { app } from "../../scripts/app.js";

// Ensure exactly one trailing unconnected text_N slot exists.
function syncSlots(node) {
    const textInputs = node.inputs.filter(i => i.name.startsWith("text_"));

    // Add a slot if the last one is connected (or none exist yet)
    const last = textInputs[textInputs.length - 1];
    if (!last || last.link !== null) {
        node.addInput(`text_${textInputs.length}`, "STRING");
        node.setDirtyCanvas(true);
        return;
    }

    // Remove surplus trailing empty slots (keep exactly one)
    let trailingEmpty = 0;
    for (let i = textInputs.length - 1; i >= 0; i--) {
        if (textInputs[i].link === null) trailingEmpty++;
        else break;
    }
    while (trailingEmpty > 1) {
        // Remove the last text_ input
        for (let i = node.inputs.length - 1; i >= 0; i--) {
            if (node.inputs[i].name.startsWith("text_")) {
                node.removeInput(i);
                break;
            }
        }
        trailingEmpty--;
    }
    node.setDirtyCanvas(true);
}

app.registerExtension({
    name: "tinkit.RandomTextPicker",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "RandomTextPicker") return;

        // After node is created (new or loaded), ensure at least one empty slot
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            syncSlots(this);
        };

        // React to connections being added or removed
        const onConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (type, slotIndex, connected, linkInfo) {
            onConnectionsChange?.apply(this, arguments);
            if (type !== LiteGraph.INPUT) return;
            const slot = this.inputs[slotIndex];
            if (!slot?.name.startsWith("text_")) return;
            syncSlots(this);
        };
    },
});
