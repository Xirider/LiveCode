'use strict';
import * as vscode from "vscode";
import PreviewManager from "./PreviewManager"
import vscodeUtils from "./vscodeUtilities";

let previewManager: PreviewManager = null;

export function activate(context: vscode.ExtensionContext) {

    previewManager = new PreviewManager(context);

    // Register the commands that are provided to the user
    const livecode = vscode.commands.registerCommand("extension.currentlivecodeSession", () => {
        previewManager.startlivecode();
    });

    const newlivecodeSession = vscode.commands.registerCommand("extension.newlivecodeSession", ()=>{
        vscodeUtils.newUnsavedPythonDoc(vscodeUtils.getHighlightedText())
            .then(()=>{previewManager.startlivecode()});
    });

    const closelivecode = vscode.commands.registerCommand("extension.closelivecode", ()=>{
        previewManager.dispose()
    });

    // exact same as above, just defining command so users are aware of the feature
    const livecodeOnHighlightedCode = vscode.commands.registerCommand("extension.newlivecodeSessionOnHighlightedCode", ()=>{
        vscodeUtils.newUnsavedPythonDoc(vscodeUtils.getHighlightedText())
            .then(()=>{previewManager.startlivecode()});
    });

    const executelivecode = vscode.commands.registerCommand("extension.executelivecode", () => {
        previewManager.runlivecode()
    });

    const executelivecodeBlock = vscode.commands.registerCommand("extension.executelivecodeBlock", () => {
        previewManager.runlivecodeBlock()
    });

    const printDir = vscode.commands.registerCommand("extension.printDir", () => {
        previewManager.printDir()
    });

    // push to subscriptions list so that they are disposed automatically
    context.subscriptions.push(...[
        livecode,
        newlivecodeSession,
        closelivecode,
        livecodeOnHighlightedCode,
        executelivecode,
        executelivecodeBlock,
        printDir
    ]);
}