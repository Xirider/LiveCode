import {workspace} from "vscode"

/**
 * simple alias for workspace.getConfiguration("livecode")
 */
export function settings(){
    return workspace.getConfiguration("livecode")
}