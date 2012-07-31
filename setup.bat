@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\Scripts\activate
pip install -q --use-mirrors argparse mock coverage doxypy lockfile unittest-xml-reporting
easy_install submodule/conveyor_bins/pyserial-2.7_mb-py2.7.egg
GOTO DONE

:DIRNOTEXISTS
python virtualenv.py --system-site-packages virtualenv
GOTO DIREXISTS

:DONE
