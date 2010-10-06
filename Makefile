PY_UI_SRC=kodos/ui/ui_main.py


all: $(PY_UI_SRC)


kodos/ui/ui_main.py: ui/main.ui
	pyuic4 $< -o $@
