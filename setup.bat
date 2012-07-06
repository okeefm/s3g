@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\Scripts\activate
pip install --use-mirrors argparse mock coverage doxypy lockfile pyserial unittest-xml-reporting
GOTO DONE

:DIRNOTEXISTS
python virtualenv.py virtualenv
GOTO DIREXISTS

:DONE
