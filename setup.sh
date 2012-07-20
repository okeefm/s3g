#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install --use-mirrors coverage doxypy unittest-xml-reporting mock
cd ../pyserial
python setup.py install
