Set WshShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
ScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Build the command to run streamlit
command = "cmd /c cd /d """ & ScriptDir & """ && streamlit run app.py"

' Run the command with hidden window (0 = hidden, 1 = normal, 2 = minimized)
WshShell.Run command, 2, False

' Show message
MsgBox "SPDM App is starting!" & vbCrLf & vbCrLf & "Your browser will open automatically." & vbCrLf & vbCrLf & "To stop: Open Task Manager and end 'python.exe' or 'streamlit' process.", vbInformation, "SPDM Streamlit App"

