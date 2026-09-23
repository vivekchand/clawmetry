; Recursive cleanup must not add one list-view row per deleted file.
; A Windows runtime with abandoned pip upgrades can contain hundreds of
; thousands of files. NSIS synchronously inserts and scrolls a row for
; each deletion by default, making the UI dominate the uninstall time.
!include "LogicLib.nsh"

!macro ClawMetryRemoveTree DIRECTORY LABEL
  DetailPrint "Removing ${LABEL}..."
  SetDetailsPrint none
  ClearErrors
  RMDir /r "${DIRECTORY}"
  SetDetailsPrint lastused
  ${If} ${Errors}
    DetailPrint "Could not completely remove ${LABEL}: ${DIRECTORY}. Close programs using these files and retry."
    SetErrorLevel 1
  ${Else}
    DetailPrint "Removed ${LABEL}."
  ${EndIf}
!macroend
