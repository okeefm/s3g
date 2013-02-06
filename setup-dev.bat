@ECHO ON

SET PYTHON=%1

IF NOT "%PYTHON%"=="" GOTO CONTINUE
SET PYTHON=python
:CONTINUE

SET DIST_EGGS=submodule\conveyor_bins\python

IF NOT "%ENV_DIR%"==" " GOTO CONTINUE
SET ENV_DIR=virtualenv
:CONTINUE

IF EXIST %ENV_DIR% GOTO MODULES

%PYTHON% virtualenv.py --extra-search-dir=%DIST_EGGS% --never-download %ENV_DIR%

:MODULES
CALL virtualenv\Scripts\activate
easy_install -q %DIST_EGGS%\mock-1.0.1-py2.7.egg
easy_install -q %DIST_EGGS%\argparse-1.2.1-py2.7.egg
easy_install -q %DIST_EGGS%\unittest2-0.5.1-py2.7.egg
easy_install -q %DIST_EGGS%\lockfile-0.9.1-py2.7.egg

pip install -q --use-mirrors coverage doxypy unittest-xml-reporting

easy_install -q ..\pyserial\dist\pyserial-2.7_mb2.1-py2.7.egg

SET PYTHONPATH=%PYTHONPATH%;%CD%

:DONE




