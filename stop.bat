@ECHO OFF

IF NOT EXIST virtualenv GOTO NOVIRTUALENV
CALL virtualenv\Scripts\deactivate
GOTO DONE

:NOVIRTUALENV
ECHO Could not find directory virtualenv

:DONE
REM Done!
