# -*- coding:utf-8 -*-
import os, sys, subprocess, re, struct, datetime
from getpass import getpass
from ctypes import windll, create_string_buffer
from donnees import *


		#=============#
		#  Fonctions  #
		#=============#


# Retourne sous forme de tableau le retour intéressant de la commande TSM
def retour_tsm(langue,trace,choix,num_cmd):
	mots_retour = []
	lignes_retour = []
	comma_retour = []
	dossier = os.getcwd()

	try:
		# Retour TSM -comma séparé virgule par virgule
		"""
		if langue != "":
			comm_split1 = list()
			if "fr" in langue.lower():
				f = open("retour_tsm.txt","r")
				for comm in f.read().split(","):
					comm_split1.append(comm)
				f.close()
				for i in range(len(comm_split1)):
					if comm_split1[i]:
						if comm_split1[i][0] == "\"":
							val = comm_split1[i].replace("\"","") + "," +comm_split1[i+1].replace("\"","")
							comma_retour.append(val)
							continue
						elif "\"" in comm_split1[i][-1]:
							continue
					
					comma_retour.append(comm_split1[i])

			else:
				f = open("retour_tsm.txt","r")
				for comm in f.read().split(",\""):
					comm_split1.append(comm)
				f.close()
				for c in comm_split1:
					if "\"," in c:
						avant , arriere = c.split("\",")
						comma_retour.append(avant)
						comma_retour.append(arriere)
					else:
						comma_retour.append(c)
		"""

		# Retour TSM séparé mot par mot
		f = open("retour_tsm.txt","r")
		for mot in f.read().split(" "):
			if not(mot in ["","\n"]) and not("-" in mot):
				mots_retour.append(mot)
		f.close()

		# Retour TSM séparé ligne par ligne
		f = open("retour_tsm.txt","r")
		for ligne in f.read().split("\n"):
			lignes_retour.append(ligne)
		f.close()

		# Création du fichier trace
		try:
			if trace:
				with open("{}\Menu_TSM\config\\trace.log".format(dossier),"a") as file:
					try:
						file.write("\n\n--- [ {} - {}] ---\n\n\t".format(choix,get_cmd()[choix][num_cmd]))
					except:
						file.write("\n\n--- [ {} ] ---\n\n\t".format(choix))
					file.write("\n\t".join(lignes_retour))
					file.close()
		except:
			print("\t# Impossible de creer une trace #")

		os.remove("retour_tsm.txt")

	except :
		print("\t# Impossible de recuperer le retour TSM #")

	return (mots_retour,lignes_retour,comma_retour)



# Récupérer la largeur de la console (et de la hauteur si demandé)
def largeur(hauteur = False):
	h = windll.kernel32.GetStdHandle(-12)
	csbi = create_string_buffer(22)
	res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
	if res:
		(bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
		sizex = right - left + 1
		sizey = bottom - top + 1
		if hauteur:
			return sizex,sizey
			# Largeur, Hauteur
		else:
			return sizex
			# Largeur
	else:
		return 100
		# Largeur par défaut (fixée au lancement du programme)



# Configuration de la langue de TSM
def langue(debut):
	langue = None
	while langue is None:
		try:
			# Chargement des infos du TSM
			check = subprocess.check_output(debut.split()+["q","opt",">>","retour_tsm.txt"],shell=False,stderr=subprocess.PIPE)
			r = retour_tsm("",True,"LANGUE",0)[0]
			# Récupération de la langue dans ces infos
			for i in range(len(r)):
				if "langu" in r[i].lower():
					langue = r[i+1]
			print("\nLangue : {}\n".format(langue))

		# Si echec du subprocess, redemander le login et le mot de passe
		except subprocess.CalledProcessError as e:
			print("\n"+"# Connexion a TSM impossible, ID ou Mot de passe invalide #".center(largeur()," ")+"\n")
			debut = connexion()
			continue
		# Si utre echec, TSM est inaccessible (mauvais dossier courant ou problème TSM)
		except:
			print("\n"+"# Impossible d'acceder a TSM #".center(largeur()," ")+"\n")
			print("#"*largeur())
			sys.exit()

	return langue , debut


# Demande d'action supplémentaire pour l'utilisateur 
def souhaitez_vous(action,bilan=False):
	# Si le mode bilan est activé on répond non directement(sinon trop d'affichage)
	if bilan:
		return False
	souhait = "vide"
	# Demande de la réponse
	while not(souhait.upper() in ["O","N",""]):
		print("\n")
		souhait = raw_input("# Souhaitez-vous {} ? (O/N): ".format(action))
	# Retour de la réponse au format booléen
	if souhait.upper() in ["O"]:
		return True
	else:
		return False


# Affiche l'arborescence contenant les commandes disponibles
def menu(config):
	largeur_menu = 0
	for bloc in get_arbo():
		for a in bloc:
			if len(a) > largeur_menu:
				largeur_menu = 14+len(a)

	# Délimitations du menu
	bords = (largeur()-50)/2
	ecart = " "*bords
	ligne = ("#"*largeur_menu).center(largeur()," ")
	menu = "\n"+ligne + "\n"

	# Ajouter les choix
	for b in get_arbo():
		# Catégorie 
		bloc = "\n{}{}\n".format(ecart,b[0])
		for i in range(1,len(b)):
			# Choix
			bloc += "{}\t{}\n".format(ecart,b[i])
		# Ajout du bloc
		menu += bloc
	print(menu+"\n\n{}* Menu: menu\n{}* Configuration: config\n{}* Quitter: quit\n\n{}\n".format(ecart,ecart,ecart,ligne))
	if not config:
		print("\n"+"# Impossible de charger la configuration (seuils definis par defaut). #".center(largeur()," ")+"\n")



# Verifie que le caractère entré correspond à une commande
def correct(c):
	# Choix vide ou null
	if c is None:
		return False
	if c == "":
		return False
	# Laisser passer les choix particuliers (non présents dans la liste l_choix)
	elif c.upper() in ["MENU","-M","QUIT","Q","CONFIG","-C","TRACE","-T"]:
		return True
	# Laisser passer le choix trace sur une seule action
	elif re.match("TRACE [A-{}]".format(l_choix[-1]),c.upper()):
		return True
	# Sinon afficher choix incorrect
	elif not(c.upper() in l_choix):
		print("  (Choix incorrect)")
		return False
	return True




# Permet de réediter le login et le mot de passe, si erreur lors de la première connexion
def connexion():
	pa = str()
	log = str()
	print("\n\n"+"[ Connexion TSM ]".center(largeur()," ")+"\n")

	# Récupération de l'identifiant (possibilité de quitter)
	milieu = " "*((largeur()-14)/2)
	while log == "":
		log = raw_input(milieu+"Identifiant : ")
		if log.upper() in ["QUIT","Q"]:
			quitter()

	# Récupération du mot de passe (possibilité de quitter)
	while pa == "":
		pa = getpass(milieu+"Mot de passe : ")
		if pa.upper() in ["QUIT","Q"]:
			quitter()

	# Début de commande intégrant -id et -pa (le -comma est ajouté plus tard)
	return "dsmadmc -id={} -pa={} ".format(log,pa)


# Quitter le programme correctement
def quitter():
	# S'assurer de la suppresion du fichier de retour (si echoué précédemment)
	try:
		os.remove("retour_tsm.txt")
	except:
		pass
	# Séparation programme et reste du terminal
	print("\n")
	print("#"*largeur())
	# Retablir la couleur de base
	os.system("color")
	sys.exit()



# Affiche une erreur
def aff_err(e,choix,num_cmd):
	lignes = retour_tsm("",True,"ERREUR {} ({})".format(choix,num_cmd),0)[1]

	# Lecture des erreurs dans l'exception du subprocess
	for l in e.output.split("\n"):
		# Cas où la commande TSM ne retourne rien
		# Retourner des valeurs adaptées à execution() avec b_bilan = True
		if "CODE" in l.upper() and "11" in l:
			if choix in ["E","F"]:
				print("Aucune sauvegarde programmee sur cette periode".center(largeur()," ")+"\n")
				return 0

			elif choix == "M":
				print("Aucune cartouche peu utilisee avec ce seuil".center(largeur()," ")+"\n")
				return

			elif choix == "G":
				print("Aucune tache administrative planifiee".center(largeur()," ")+"\n")
				return

			elif choix == "H": 
				if num_cmd == 1:
					print("Aucun chemin".center(largeur()," ")+"\n") 
				elif num_cmd == 2:
					print("Aucun drive".center(largeur()," ")+"\n")
				return False

			elif choix == "I":
				print("Aucune librairie".center(largeur()," ")+"\n")
				return

			elif choix == "L" and num_cmd == 1:
				print("Aucune librairie".center(largeur()," ")+"\n")
				return []
			elif choix == "L" and num_cmd == 2:
				return False

		# Cas où la commande TSM retourne une erreur
		if "AN" in l and l != "":
			print("\t- "+l[8:])
	
	# Lecture des erreurs dans le retour_tsm()
	print("\t# ERREUR #")
	for l in lignes:
		if "AN" in l and l != "":
			print("\t- "+l[8:])
	print("\n")


# Traitement du choix "config"
def configuration(l_seuils):
	aff_config(largeur(),l_seuils)

	# Si l'utilisateur veut modifier un seuil
	if souhaitez_vous("modifier un des seuils enregistres"):

		# Quel seuil
		num = ""
		while not (num in d_reconf.keys()):
			num = raw_input("# Numero du seuil a configurer: ")
		valeur = 0	

		if num == "8": #modifier la couleur
			maximum = 3
		elif num == "9": #modifier le format de date pour le choix D
			maximum = 2
		else:
			maximum = 99

		# La nouvelle valeur
		while not (0 < int(valeur) <= maximum ):
			valeur = raw_input("# Nouvelle valeur pour ce seuil: ")
			try:
				valeur = int(valeur)
			except ValueError:
				valeur = "-1"

		# Configuration de cette nouvelle valeur (retouner l'ancienn si rien n'a changé)
		new_config = set_config(num,valeur)
		if new_config is None:
			return l_seuils
		else:
			return new_config
	else:
		return l_seuils

