from distutils.core import setup
import py2exe
import os

try:
	os.system("del Menu_TSM")
except:
	pass

explicitIncludes = ["encodings.utf_8"]

setup(options = {"py2exe":{"includes":explicitIncludes,"optimize":2}},
	console=['menu_win.py'], 
	data_files = [("config",["seuils.txt"]) ,("config",["trace.log"]),("config",["bilan.log"]) , ("",["Doc_Technique_Menu.pdf"]) ] )


#
# OPTIMIZE: 2s
#

os.system("rename dist Menu_TSM")
os.system("rename Menu_TSM\\menu_win.exe Menu_TSM.exe")

