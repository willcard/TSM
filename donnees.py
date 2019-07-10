# -*- coding:utf-8 -*-
import os,string
from fonctions import *


		#=========================#
		#  Données Configuration  #
		#=========================#

# Récupération des valeurs dans le fichier seuils.txt
def get_config():
	l_seuils = {"DB":85,"ACT":85,"ARCH":80,"SCRATCH":5,"POOL":90,"JOURS":3,"CARTOUCHES":30,"COULEUR":2,"DATEFORMAT":1}
	nb = 0
	try:
		dossier = os.getcwd()
		for l in open("{}\Menu_TSM\config\seuils.txt".format(dossier),"r"):
			if "###" in l:
				break
			elif "DB" in l.upper():
				i = l.index("=")
				l_seuils["DB"] = int(l[i+1:])
				nb+=1
			elif "ACT" in l.upper():
				i = l.index("=")
				l_seuils["ACT"] = int(l[i+1:])
				nb+=1
			elif "ARCH" in l.upper():
				i = l.index("=")
				l_seuils["ARCH"] = int(l[i+1:])
				nb+=1
			elif "SCRATCH" in l.upper():
				i = l.index("=")
				l_seuils["SCRATCH"] = int(l[i+1:])
				nb+=1
			elif "POOL" in l.upper():
				i = l.index("=")
				l_seuils["POOL"] = int(l[i+1:])
				nb+=1
			elif "JOURS" in l.upper():
				i = l.index("=")
				l_seuils["JOURS"] = int(l[i+1:])
				nb+=1
			elif "CARTOUCHES" in l.upper():
				i = l.index("=")
				l_seuils["CARTOUCHES"] = int(l[i+1:])
				nb+=1
			elif "COULEUR" in l.upper():
				i = l.index("=")
				l_seuils["COULEUR"] = int(l[i+1:])
				nb+=1
			elif "DATEFORMAT" in l.upper():
				i = l.index("=")
				l_seuils["DATEFORMAT"] = int(l[i+1:])
				nb+=1

		if nb == len(l_seuils):
			config = True
		else:
			config = False
	except Exception as e:
		config = False
		pass
	return (config, l_seuils)

# Afficher les seuils configurés et l'index de modification correspondant
def aff_config(largeur,l_seuils):
	print("\n"+" [ Configuration des seuils d'alerte ] ".center(largeur," ")+"\n\n")
	print("(1) - Espace disque DB utilise maximum : {} %".format(l_seuils["DB"]).center(largeur," ")+"\n")
	print("(2) - Espace disque ActLog utilise maximum : {} %".format(l_seuils["ACT"]).center(largeur," ")+"\n")
	print("(3) - Espace disque ArchLog utilise maximum : {} %".format(l_seuils["ARCH"]).center(largeur," ")+"\n")
	print("(4) - Nombre de bandes Scratch minimum : {}".format(l_seuils["SCRATCH"]).center(largeur," ")+"\n")
	print("(5) - Espace disque Storage Pool utilise maximum : {} %".format(l_seuils["POOL"]).center(largeur," ")+"\n")
	print("(6) - Nombre de jours minimum depuis la derniere sauvegarde : {}".format(l_seuils["JOURS"]).center(largeur," ")+"\n")
	print("(7) - Espace disque minimum utilise par cartouche : {} %".format(l_seuils["CARTOUCHES"]).center(largeur," ")+"\n")
	print("(8) - Couleur de fond du menu (1=Blanc, 2=Bleu, 3=Noir) : {}".format(l_seuils["COULEUR"]).center(largeur," ")+"\n")
	print("(9) - Format de date retourne par TSM (1='JJ/MM/AAAA', 2='MM/JJ/AAAA') : {}".format(l_seuils["DATEFORMAT"]).center(largeur," ")+"\n")


# Configurer les seuils d'alerte depuis le programme
def set_config(num,valeur):
	key = d_reconf[num]
	try:
		dossier = os.getcwd()

		with open("{}\Menu_TSM\config\seuils.txt".format(dossier),"r+") as file:
			# On récupère l'ancienne configuration
			ancienne = file.read().splitlines()
			nouvelle = list()
			# On la modifie avec la nouvelle valeur
			for i in range(len(ancienne)):
				ligne = ancienne[i]
				if key in ligne.upper():
					new_ligne = ligne[:ligne.index("= ")+2]+str(valeur)
					nouvelle.append(new_ligne)
				else:
					nouvelle.append(ligne)
			# On efface l'ancienne et réecrit la nouvelle configuration dans le fichier	
			ecrire = "\n".join(nouvelle)
			file.truncate()
			file.seek(0,0)
			file.write(ecrire)
			file.close()

		return get_config()[1]
	except:
		print("# Impossible configurer ce seuil #")
		return None




		#=================#
		#  Données Texte  #
		#=================#


# Retourne l'arborescence des choix disponibles
def get_arbo():
	l_arbo = [ 
	  ["(I) Etat de sante TSM",
		"A - Bilan",
		"B - Etat de la base de donnees",
		"C - Etat des Storage Pools",
		"D - Informations de sauvegardes de la DB",],
	  ["(II) Planifications",
		"E - Etat des sauvegardes",
		"F - Etat des sauvegardes (3 derniers jours)",
		"G - Taches administratives"],
	  ["(III) Devices",
		"H - Etat des chemins de donnees",
		"I - Liste des librairies"],
	  ["(IV) Volumes",
		"J - Detection de volumes ou cartouches en erreur",
		"K - Test d'acces des Volumes",
		"L - Nombre de bandes scratch",
		"M - Cartouches peu utilisees ({} %)".format(get_config()[1]["CARTOUCHES"])],
	  ["(V) Nodes",
		"N - Nodes sans association"]]
	return l_arbo


# Retourne un dictionnaire avec l'association "choix":(Titre,commande 1,commande 2)
def get_cmd():
	l_arbo = get_arbo()
	d_cmd = {
		"A":(l_arbo[0][1],""),
		"B":(l_arbo[0][2],"q db f=d","q log f=d"),
		"C":(l_arbo[0][3],"q stg"),
		"D":(l_arbo[0][4],"q volh t=dbb"),
		"E":(l_arbo[1][1],'q ev * * begind=-1 endd=today'),
		"F":(l_arbo[1][2],'q ev * * begind=-3 endd=today'),
		"G":(l_arbo[1][3],"select cast(ACTUAL_START as DATE),SCHEDULE_NAME,STATUS FROM events WHERE node_name IS NULL AND DAYS(current_timestamp)-DAYS(ACTUAL_START)<=1"),
		"H":(l_arbo[2][1],"q dr","q path"),
		"I":(l_arbo[2][2],"q libr"),
		"J":(l_arbo[3][1],"select volume_name, read_errors, write_errors,ACCESS from volumes "),
		"K":(l_arbo[3][2],"select COUNT(*) from volumes where ACCESS<>'READWRITE' and ACCESS<>'OFFSITE'","select volume_name,stgpool_name,access,read_errors,write_errors from volumes where ACCESS<>'READWRITE' and ACCESS<>'OFFSITE'"),
		"L":(l_arbo[3][3],"q libr","select COUNT(*) from libvolumes where status='Scratch' and library_name='{}'"),
		"M":(l_arbo[3][4],"select volume_name,devclass_name,stgpool_name,pct_reclaim,pct_utilized,status from volumes where (status='FULL' or status='FILLING') and pct_utilized<{} order by pct_utilized desc".format(get_config()[1]["CARTOUCHES"])),
		"N":(l_arbo[4][1],"select COUNT(*) from nodes where node_name not in (select node_name from associations)","select node_name FROM nodes WHERE node_name not IN (SELECT node_name FROM associations) order by node_name desc")}
	return d_cmd


# Correspondance code hexa couleur windows et valeur de configuration
def get_code_couleur(val):
		return {1:"F0",2:"1F",3:"0F"}[val]


# Correspondance format de date et valeur de configuration
def get_date_format(val):
		return {1:'JJ/MM/AAAA',2:'MM/JJ/AAAA'}[val]


# Valeurs des choix disponibles
l_choix = list(string.ascii_uppercase)[:len(get_cmd())]

# Correspondance {numéro : seuil} pour la re-configuration
d_reconf = {"1":"DB","2":"ACT","3":"ARCH","4":"SCRATCH","5":"POOL","6":"JOURS","7":"CARTOUCHES","8":"COULEUR","9":"DATEFORMAT"}


# Rappel de commande à chaque éxecution d'un choix
rappel = "\n###############\n{}\n{}\n###############\n".format("Menu: menu".center(15," "),"Quitter: quit".center(15," "))



