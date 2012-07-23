@ECHO OFF
SETLOCAL EnableDelayedExpansion

SET PYTHONDONTWRITEBYTECODE=1
SET PYTHONPATH=src\main\python\..\..\..\submodule\s3g\

IF NOT EXIST obj MD obj

CALL setup.bat
python unit_tests.py
_CODE = $?

ENDLOCAL EnableDelayedExpansion
exit _CODE
