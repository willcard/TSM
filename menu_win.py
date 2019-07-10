# -*- coding:utf-8 -*-
import os, sys, subprocess, string, re, struct, datetime
from datetime import *
from fonctions import *
from donnees import *
from shutil import copy



		#===================#
		#  Analyse retours  #
		#===================#



# Retourne la valeur au bon format
def valeur(valeur):
	v = valeur.replace("\"","")

	# Traitement de la difference "."" et "," en Francais ou Anglais
	if "fr" in langue_TSM.lower():
		if " " in valeur:
			v = v.replace(" ","")
		if "," in valeur:
			v = v.replace(",",".")
	else:
		if "," in valeur:
			v = v.replace(",","")
	return float(v)


# Répare une ligne coupée par les virgules (soucis de langue)
def relier(l):
	valeurs = l.split(",")
	ligne = list()
	dedans = False

	# On lie les différentes partie d'une partie valeur contenant une ","
	for i in range(len(valeurs)):
		if valeurs[i]:
			# On détecte l'entrée dans cette valeur
			if "\"" in valeurs[i][0]:
				avant = valeurs[i]
				dedans = True
			# On détecte la sortie
			elif "\"" in valeurs[i][-1]:
				arriere = valeurs[i]
				ligne.append("{},{}".format(avant,arriere))
				dedans = False
			# On détecte le centre de cette valeur si existant
			elif dedans:
				avant += ",{}".format(valeurs[i])
			else:
				ligne.append(valeurs[i])
		else:
			ligne.append("vide")
	return ligne



# Analyser les retours de certaines commandes
def analyser_retour(choix,num_commande,param=None):
	# Listes des mots, liste des lignes et liste des valeurs par comma du retour TSM (brut)
	m_retour,l_retour,c_retour = retour_tsm(langue_TSM,trace,choix,num_commande)	
	larg,haut = largeur(hauteur=True)

	# Analyse de la base de donnée
	if choix == "B":
		# Analyse mémoire DB
		if num_commande == 1:
			for l in l_retour:
				if l:
					ligne = relier(l)
					break

			total = valeur(ligne[1])
			used = valeur(ligne[2])

			pourcentage = round((used*100)/total,2)
			if pourcentage >= l_seuils["DB"]:
				print("\n"+"# ATTENTION : L'espace disque est utilise a {} % !".format(pourcentage).center(larg," ")+"\n")
				return False
			else:
				print("\n"+"- Utilisation de l'espace disque DB : {} %".format(pourcentage).center(larg," ")+"\n")	
				print("Le seuil {} % d'utilisation maximum DB est respecte".format(l_seuils["DB"]).center(larg," "))
				return True
			

		# Analyse mémoire Logs
		elif num_commande == 2:
			log1 = list()
			log2 = list()
			for l in l_retour:
				if l:
					ligne = relier(l)
					break

			premier = False
			for v in ligne:
				if v:
					if premier and ("\\" in v or "/" in v):
						log1 = log2
						log2 = list() 
						# On fait un décalage afin de réduire les lignes de codes
					log2.append(v)
					premier = True
				else:
					log2.append("vide")

			ok = True

			total_act = valeur(log1[1])
			used_act = valeur(log1[2])
			total_arch = valeur(log2[1])
			used_arch = valeur(log2[2])

			pourcentage_act = round((used_act*100)/total_act,2)
			pourcentage_arch = round((used_arch*100)/total_arch,2)

			print("\n")

			if pourcentage_act > 100:
				print("\t# Erreur de recuperation du taux pour ActLog #")
				ok = False
			elif pourcentage_act >= l_seuils["ACT"]:
				print("\n"+"# ATTENTION : L'espace disque ACTLOG est utilise a {} % !".format(pourcentage_act).center(larg," ")+"\n")
				ok = False
			else:
				print("- Utilisation de l'espace disque ACTLOG : {} %".format(pourcentage_act).center(larg," ")+"\n")

			if pourcentage_arch > 100:
				print("\t# Erreur de recuperation du taux pour ArchLog #")
				ok = False
			elif pourcentage_arch >= l_seuils["ARCH"]:
				print("\n"+"# ATTENTION : L'espace disque ARCHLOG est utilise a {} % !".format(pourcentage_arch).center(larg," ")+"\n")
				print("# Verifier que la sauvegarde de DB TSM s'est bien deroulee.".center(larg," ")+"\n")
				ok = False
			else:
				print("- Utilisation de l'espace disque ARCHLOG : {} %".format(pourcentage_arch).center(larg," ")+"\n")

			if ok:
				print("Le seuil {} % d'utilisation maximum ActLog est respecte".format(l_seuils["ACT"]).center(larg," "))
				print("Le seuil {} % d'utilisation maximum ArchLog est respecte".format(l_seuils["ARCH"]).center(larg," "))
				
				if param:
					print("\n\n"+"# OK #".center(larg," "))
					return True
		
	##############################################################################################################


	# Analyse de l'état des storage pools
	elif choix == "C":
		bons = list()
		pasbons = list()

		lignes = list()
		for l in l_retour:
			if l:
				lignes.append(relier(l))

		ok = True 
		for stg in lignes:
			if stg:
				if len(stg) == 8:
					indice = 3
				else:
					indice = 4
				if valeur(stg[indice]) >= l_seuils ["POOL"]:
					ok = False
					pasbons.append(stg)
				else:
					bons.append(stg)

		if not ok:
			total = len(pasbons)+len(bons)
			print("# ATTENTION: Il y a {}/{} Storage Pools depassants le seuil d'alerte configure:".format(len(pasbons),total).center(larg," "))
			if len(pasbons) > 5:
				afficher = souhaitez_vous("afficher la liste de ces Storage Pools",b_bilan)
			else:
				afficher = True

			if afficher:
				print("\n")
				for stg in pasbons:
					if stg:
						print("- {} est utilise a {} %".format(stg[0],valeur(stg[indice])).center(larg," "))
		else:
			print("Le seuil {} % de remplissage maximum est respecte".format(l_seuils["POOL"]).center(larg," "))
			print("\n\n"+"# OK #".center(larg," ")+"\n")
			return True

			afficher = souhaitez_vous("afficher la liste des Storage Pools et Device Class",b_bilan)
			if afficher:
				print("\n")
				align = len(max(lignes,key=len))
				for stg in lignes:
					if stg:
						ecart = align - len(l)
						print("- {} ==> {}".format(stg[0]+ecart*" ",stg[2]).center(larg," "))


	##############################################################################################################


	# Mise en forme des infos de sauvegarde de la DB 
	elif choix == "D":
		retour = l_retour
		retour.reverse()
		for l in retour:
			if l:
				save = relier(l)
				break

		v_date , v_time = save[0].split(" ")
		v_type = save[1]
		v_name = save[6]
		#v_backup = save[2]
		v_devclass = save[5]

		if "-" in v_date:
			v_date = v_date.replace("-","/")

		if "MM/JJ" in dateformat:
			M,J,A = v_date.split("/")
			v_date = "{}/{}/{}".format(J,M,A)

		sauvegarde = v_date.split("/")

		date = "- Date : {}".format(v_date)
		time = "- Heure : {}".format(v_time)
		ttype = "- Type du sauvegarde: {}".format(v_type)
		name = "- Nom du dernier volume: {}".format(v_name)
		#backup = "- Backup Series : {}".format(v_backup).center(larg," ")
		devclass = "- Device Class : {}".format(v_devclass)

		affichage = [date,time,devclass,name,ttype]
		align = len(max(affichage,key=len))
		for a in affichage:
			if a:
				ecart = align - len(a)
				print("{}".format(a+ecart*" ").center(larg," ")+"\n")

		try:
			date_aujd = datetime.date.today()
			date_sauvegarde = datetime.date(int(sauvegarde[2]),int(sauvegarde[1]),int(sauvegarde[0]))
				
			ecart = str(date_aujd - date_sauvegarde)

			if not "day" in ecart:
				jours = 0
			else:
				jours = ecart[:ecart.index("day")-1]

			if int(jours) > l_seuils["JOURS"]:
				print("\n"+"# ATTENTION : Pas de sauvegarde de DB TSM depuis {} jours !".format(jours).center(larg," "))
			else:
				print("\n"+"Le seuil de {} jours maximum est respecte".format(l_seuils["JOURS"]).center(larg," "))
				print("\n"+"# OK #".center(larg," "))
				return True
		except Exception as e:
			print("\t# Impossible d'analyser la date {} ".format(date))
			print("\tPenser a modifier le format de la date dans les configurations (config 9)")
			print("# ERREUR #\n\t{}".format(e))

	##############################################################################################################


	# Analyse de l'etat des sauvegardes	
	elif choix == "E":
		echecs = []
		futur = []
		sched = 0
		for l in l_retour:
			if l:
				sched+=1
				s = l.split(",")
				etat = s[-1].lower()
				if "futur" in etat:
					futur.append(s)
				elif not("termin" in etat or "complet" in etat):
					echecs.append(s)

		if len(echecs) > 0:
			if len(echecs) == 1:
				print("# ATTENTION: 1 sauvegarde a echoue !".center(larg," "))
			else:
				print("# ATTENTION: {} sauvegardes ont echoue !".format(len(echecs)).center(larg," "))
			if souhaitez_vous("afficher la liste de ces sauvegardes"):
				print("\n")
				for e in echecs:
					if e:
						print("- {}".format(e[2]).center(larg," "))

		else:
			print("\n"+"# OK #".center(larg," "))

		if souhaitez_vous("plus de details"):
			print("\n")
			if sched == 1:
				print("Il y 1 schedule dont {} a venir:".format(len(futur)).center(larg," "))
			else:
				print("Il y {} schedules dont {} a venir:".format(sched,len(futur)).center(larg," "))
			for f in futur:
				if f:
					print("- {}".format(f[2]).center(larg," "))


	##############################################################################################################


	# Analyse de l'etat des sauvegardes	(3 derniers jours)
	elif choix == "F":
		echecs = []
		futur = []
		sched = 0
		for l in l_retour:
			if l:
				sched+=1
				s = l.split(",")
				etat = s[-1].lower()
				if "futur" in etat:
					futur.append(s)
				elif not("termin" in etat or "complet" in etat):
					echecs.append(s)

		if len(echecs) > 0:
			if len(echecs) == 1:
				print("# ATTENTION: 1 sauvegarde a echoue !".center(larg," "))
			else:
				print("# ATTENTION: {} sauvegardes ont echoue !".format(len(echecs)).center(larg," "))
			if souhaitez_vous("afficher la liste de ces sauvegardes",b_bilan):
				print("\n")
				for e in echecs:
					if e:
						date = e[0].split(" ")[0]		
						if "MM/JJ" in dateformat:
							M,J,A = date.split("/")
							date = "{}/{}/{}".format(J,M,A)
						print("- {} le {}".format(e[2],date).center(larg," "))

		else:
			print("\n"+"# OK #".center(larg," "))
			return True

		if souhaitez_vous("plus de details",b_bilan):
			print("\n")
			if sched == 1:
				print("Il y 1 schedule dont {} a venir:".format(len(futur)).center(larg," "))
			else:
				print("Il y {} schedules dont {} a venir:".format(sched,len(futur)).center(larg," "))
			for f in futur:
				if f:
					print("- {}".format(f[2]).center(larg," "))


	##############################################################################################################


	# Analyse des tâches administratives	
	elif choix == "G":
		ok = True
		for l in l_retour:
			if l:
				s = l.split(",")
				date = s[0].replace("-","/")
				entity = s[1]
				if not ("completed" in s[-1].lower() or "termin" in s[-1].lower()):
					ok= False
					s = l.split(",")
					date = s[0].replace("-","/")
					entity = s[1]
					print("# ATTENTION: {} le {} a echoue !".format(entity,date).center(larg," "))
				else:
					print("- {} le {} : OK".format(entity,date).center(larg," "))


		if ok:
			print("\n\n"+"# OK #".center(larg," "))
			return True

	##############################################################################################################


	# Analyse des lecteurs et des paths
	elif choix == "H":
		if num_commande == 1:
			bons = list()
			pasbons = list()

			ok = True
			for l in l_retour:
				if l:
					online = l.split(",")[-1].lower()
					if "no" in online:
						ok = False
						pasbons.append(l)
					else:
						bons.append(l)

			if not ok:
				total=len(pasbons)+len(bons)
				if len(pasbons) == 1:
					print("# ATTENTION: Il y a {}/{} drive pas en ligne".format(len(pasbons),total).center(larg," "))
				else:
					print("# ATTENTION: Il y a {}/{} drives pas en ligne".format(len(pasbons),total).center(larg," "))
				if len(pasbons) > 5:
					afficher = souhaitez_vous("afficher la liste de ces drives",b_bilan)
				else:
					afficher = True


				if afficher:
					defilement = 0
					for l in pasbons:
						if l:
							defilement += 1
							name = l.split(",")[1]
							print("- {}".format(name).center(larg," "))
							if defilement == (haut - 5):
								defilement = 0
								if raw_input("(Entrer pour continuer ou A pour annuler)").upper() == "A":
									break

			else:
				print("\n"+"Tous les drives sont on-line".center(larg," "))
				#print("\n"+"# OK #".center(larg," "))
				return True


		elif num_commande == 2:			
			bons = list()
			pasbons = list()

			ok = True
			for l in l_retour:
				if l:
					online = l.split(",")[-1].lower()
					if "no" in online:
						ok = False
						pasbons.append(l)	
					else:
						bons.append(l)
			
			if not ok:
				total=len(pasbons)+len(bons)
				if len(pasbons) == 1:
					print("# ATTENTION: Il y a {}/{} chemin pas en ligne".format(len(pasbons),total).center(larg," "))
				else:
					print("# ATTENTION: Il y a {}/{} chemins pas en ligne".format(len(pasbons),total).center(larg," "))
				if len(pasbons) > 5:
					afficher = souhaitez_vous("afficher la liste de ces chemins",b_bilan)
				else:
					afficher = True
				if afficher:
					for l in pasbons:
						if l:
							name = l.split(",")[2]
							print("- {}".format(name).center(larg," "))
			else:
				print("Tous les chemins sont on-line".center(larg," "))
				if param:
					print("\n"+"# OK #".center(larg," ")+"\n")
					return True
				if souhaitez_vous("afficher la liste des chemins en ligne",b_bilan):
					print("\n")
					for l in l_retour:
						if l:
							s=l.split(",")
							print("- {} : {} : {} : {}".format(s[0],s[1],s[2],s[3]).center(larg," "))




	##############################################################################################################
	

	# Analyse des librairies	
	elif choix == "I":
		librairies = []
		for l in l_retour:
			if l:
				nom = l.split(",")[0]
				librairies.append(nom)
		if len(librairies) == 1:
			print("- Il y a 1 librairie:".center(larg," "))
		else:
			print("- Il y a {} librairies:".format(len(librairies)).center(larg," "))

		if len(librairies) > 5:
			afficher = souhaitez_vous("afficher la liste des librairies")
		else:
			afficher = True

		if afficher:
			defilement = 0
			for l in librairies:
				if l:
					defilement += 1
					print("- {}".format(l).center(larg," "))
					if defilement == (haut - 5):
						defilement = 0
						if raw_input("(Entrer pour continuer ou A pour annuler)").upper() == "A":
							break


	##############################################################################################################

	# Analyse des volumes en erreur
	elif choix == "J":
		bons = list()
		pasbons = list()
		readon = list()
		destroy = list()
		lto = list()
		vdisk = list()
		nomspe = list()

		ok = True
		for l in l_retour:
			if l:
				s = l.split(",")
				try:
					access = s[3].upper()
					if not("READWRITE" in access or "OFFSITE" in access):
						ok = False
						pasbons.append(s)
						if not (re.match(r"^[0-9A-Z]{6}(L)[0-9]{1}$",s[0]) or (("\\" in s[0]) or ("/" in s[0]) or (":" in s[0]))):
							nomspe.append(s)
					else:
						bons.append(s)
				except:
					print("\t# Probleme de tri (bon/pasbon) pour cette ligne:")
					print(s)

		for vol in pasbons:
			if vol:
				if "READONLY" in vol[3].upper():
					readon.append(vol)
				elif "DESTROYED" in vol[3].upper():
					destroy.append(vol)

		for b in bons:
			if b:
				if ("\\" in b[0]) or ("/" in b[0]) or (":" in b[0]):
					vdisk.append(b)
				elif re.match(r"^[0-9A-Z]{6}(L)[0-9]{1}$",b[0]):
					lto.append(b)
				else:
					ok = False
					nomspe.append(b)

		print("- Il y a {} LTO OK".format(len(lto)).center(larg," "))
		print("- Il y a {} volumes disques OK".format(len(vdisk)).center(larg," "))

		if len(nomspe) > 0:
			if len(nomspe) == 1:
				print("\n"+"# ATTENTION: Il y a 1 anomalie de nom:".center(larg," "))
			else:
				print("\n"+"# ATTENTION: Il y a {} anomalies de nom:".format(len(nomspe)).center(larg," "))
			
			if len(nomspe) > 5:
				afficher = souhaitez_vous("afficher la liste de ces anomalies",b_bilan)
			else:
				afficher = True

			if afficher:
				for n in nomspe:
					if n:
						print("- {} ".format(n[0]).center(larg," "))
		else:
			print("- Il n'y a pas d'anomalie de nom".center(larg," "))


		if len(destroy) > 0 or len(readon) > 0:
			if len(readon)+len(destroy) == 1:
				print("\n"+"# ATTENTION: Il y a 1 erreur:".center(larg," "))
			else:
				print("\n"+"# ATTENTION: Il y a {} erreurs:".format(len(readon)+len(destroy)).center(larg," "))
			if len(destroy)+len(readon) > 5:
				afficher = souhaitez_vous("afficher la liste de ces erreurs",b_bilan)
			else:
				afficher = True

			if afficher:
				if len(readon)+len(destroy) < 20:
					for r in readon:
						if r:
							print("- Volume: {}, Acces: {}".format(r[0],r[3]).center(larg," "))
					for d in destroy:
						if d:
							print("- Volume: {}, Acces: {}".format(d[0],d[3]).center(larg," "))

				else:
					defilement = 0
					for pb in [i for i in range(len(pasbons)) if i%2 == 0]:
						defilement += 1
						gauche = "- Volume: {}, Access: {}".format(pasbons[pb][0],pasbons[pb][3])
						
						if pb+1 < len(pasbons)-1:
							droite = "- Volume: {}, Access: {}".format(pasbons[pb+1][0],pasbons[pb+1][3])
							print(gauche.center(larg/2," ")+droite.center(larg/2," "))
						else:
							print(gauche.center(larg/2," "))

						if defilement == (haut - 5):
							defilement = 0
							if raw_input("(Entrer pour continuer ou A pour annuler)").upper() == "A":
								break



		else:
			print("- Il n'y a pas de volumes en erreur".center(larg," "))

		if ok:
			print("\n\n"+"# OK #".center(larg," "))
			return True


	##############################################################################################################
	

	# Analyse de l'integrité d'un stg	
	elif choix == "K":
		if num_commande == 1:
			for l in l_retour:
				if l:
					try:
						nb = int(l)
						if nb != 0:
							if nb == 1:
								print("# ATTENTION : Il y a 1 volume en acces anormal:".center(larg," "))
							else:
								print("# ATTENTION : Il y a {} volumes en acces anormal:".format(nb).center(larg," "))
						else:
							print("\n\n"+"# OK #".center(larg," "))
						break
					except:
						continue



		elif num_commande == 2:	
			readon = list()
			destroy = list()

			ok = True
			for l in l_retour:
				if l:
					ok = False
					s = l.split(",")
					try:
						access = s[2].upper()
						name = s[0].upper()
						if "READONLY" in access:
							readon.append(s)
						elif "DESTROYED" in access:
							destroy.append(s)
					except:
						print("\t# Probleme d'analyse pour la deuxième commande")
						print(s)


			if len(readon) != 0:
				if len(readon) == 1:
					print("\n"+"Il y a 1 volume en Readonly".center(larg," "))
				else:
					print("\n"+"Il y a {} volumes en Readonly".format(len(readon)).center(larg," "))
			else:
				afficher = False
			
			if len(readon) > 5:
				afficher = souhaitez_vous("afficher la liste de ces volumes en Readonly",b_bilan)
			elif 5 >= len(readon) > 0:
				afficher = True

			if afficher:
				volumes = []
				read = 0
				write = 0
				for vol in readon:
					if vol:
						error = ""
						if not (vol[3] == "0"):
							error += "Read Error: {}".format(vol[3])
							read += 1
						if not (vol[4] == "0"):
							write += 1
							if error == "":
								error = "Write Error: {}".format(vol[4])
							else:
								error += " - Write Error: {}".format(vol[4])
						if error != "":
							#volumes.append("- {} ({})".format(vol[0],error).center(larg," "))
							volumes.append("- {} ({})".format(vol[0],error))

				details = ""
				if read == 0:
					details += "Aucun Read Error"
				elif read == 1:
					details += "1 volume Read Error"
				else:
					details += "{} volumes en Read Error".format(read)

				details += " - "
				if write == 0:
					details += "Aucun Write Error"
				elif write == 1:
					details += "1 volume en Write Error"
				else:
					details += "{} volumes en Write Error".format(write)

				print(details.center(larg," ")+"\n")

				if len(volumes) > 0:
					align = len(max(volumes,key=len))
					defilement = 0
					for v in volumes:
						if v:
							defilement += 1
							ecart = align - len(l)
							print("{}".format(v+ecart*" ").center(larg," "))
							if defilement == (haut - 5):
								defilement = 0
								if raw_input("(Entrer pour continuer ou A pour annuler)").upper() == "A":
									break





						
			if len(destroy) != 0:
				if len(destroy) == 1:
					print("\n"+"Il y a 1 volume Destroyed".center(larg," "))
				else:
					print("\n"+"Il y a {} volumes Destroyed".format(len(destroy)).center(larg," "))
			else:
				afficher = False
			
			if len(destroy) > 5:
				afficher = souhaitez_vous("afficher la liste de ces volumes Destroyed",b_bilan)
			elif 5 >= len(destroy) > 0:
				afficher = True

			if afficher:
				volumes = []
				read = 0
				write = 0
				for vol in destroy:
					if vol:
						error = ""
						if not (vol[3] == "0"):
							error += "Read Error: {}".format(vol[3])
							read += 1
						if not (vol[4] == "0"):
							write += 1
							if error == "":
								error = "Write Error: {}".format(vol[4])
							else:
								error += " - Write Error: {}".format(vol[4])
						if error != "":
							#volumes.append("- {} ({})".format(vol[0],error).center(larg," "))
							volumes.append("- {} ({})".format(vol[0],error))

				details = ""
				if read == 0:
					details += "Aucun Read Error"
				elif read == 1:
					details += "1 volume Read Error"
				else:
					details += "{} volumes en Read Error".format(read)

				details += " - "
				if write == 0:
					details += "Aucun Write Error"
				elif write == 1:
					details += "1 volume en Write Error"
				else:
					details += "{} volumes en Write Error".format(write)

				print(details.center(larg," ")+"\n")

				if len(volumes) > 0:
					align = len(max(volumes,key=len))
					defilement = 0
					for v in volumes:
						if v:
							defilement += 1
							ecart = align - len(l)
							print("{}".format(v+ecart*" ").center(larg," "))
							if defilement == (haut - 5):
								defilement = 0
								if raw_input("(Entrer pour continuer ou A pour annuler)").upper() == "A":
									break


			if (len(readon) == 0) and (len(destroy) == 0):
				print("\n\n"+"# OK #".center(larg," "))
				return True


	##############################################################################################################


	# Analyse du nombre de bande Scratch
	elif choix == "L":
		if num_commande == 1:
			analyse = []
			nb = 0
			for l in l_retour:
				if l:
					nb += 1
					analyse.append(l.split(",")[0])
			if nb != 0:
				if nb == 1:
					print("- Il y a 1 librairie:".center(larg," "))
				else:
					print("- Il y a {} librairies:".format(nb).center(larg," "))
			else:
				print("- Aucune librairie".center(larg," "))
			return analyse

		elif num_commande == 2:
			for l in l_retour:
					if l:
						try:
							nb = int(l)
							if nb == 0:
								print("\n"+"# ATTENTION : Il n'y a plus de bandes scratch ! Il faut inserer de nouvelles bandes.".format(nb).center(larg," "))
							elif nb < l_seuils["SCRATCH"]:
								if nb == 1:
									print("\n"+"# ATTENTION : Il ne reste qu'1 bande scratch ! Il faut inserer de nouvelles bandes.".center(larg," "))
								else:
									print("\n"+"# ATTENTION : Il ne reste que {} bandes scratch ! Il faut inserer de nouvelles bandes.".format(nb).center(larg," "))
							else:	
								print("Le seuil {} de bande scratch minimum est respecte".format(l_seuils["SCRATCH"]).center(larg," "))
								print("Il y a {} bandes scratch dans cette librairie.".format(nb).center(larg," "))
								print("\n\n"+"# OK #".center(larg," "))
								return True
							#break
						except:
							continue

	##############################################################################################################
		

	# Analyse des cartouches peu utilisées
	elif choix == "M":

		cartouches = list()
		for l in l_retour:
			vol = list()
			if l:
				cartouches.append(relier(l))

		filling = []
		full = []
		suite_full = 0
		suite_filling = 0
		for c in cartouches:
			if c:
				if "FULL" in c[5]:
					if re.match(r"^[0-9A-Z]{6}(L)[0-9]{1}$",c[0]):
						full.insert(suite_full,c)
						suite_full+=1
					else:
						full.append(c)
				else:
					if re.match(r"^[0-9A-Z]{6}(L)[0-9]{1}$",c[0]):
						filling.insert(suite_filling,c)
						suite_filling+=1
					else:
						filling.append(c)

		if len(cartouches) != 0:
			if len(cartouches) == 1:
				print("- Il y a 1 cartouche peu utilisee:".center(larg," "))
			else:
				print("- Il y a {} cartouches peu utilisees:".format(len(cartouches)).center(larg," "))

			print("{} Full et {} Filling".format(len(full),len(filling)).center(larg," "))
		else:
			afficher = False
			print("\n\n"+"# OK #".center(larg," "))

		if len(cartouches) > 5:
			afficher = souhaitez_vous("afficher la liste de toutes ces cartouches")
			print("\n")
		elif 5>= len(cartouches) > 0:
			afficher = True



		if afficher:
			colonnes = []
			if len(full) > len(filling):
				indices = range(len(full))
			else:
				indices = range(len(filling))
			for k in indices:
				if k < len(full):
					gauche = "- {} utilise a {} %".format(full[k][0],valeur(full[k][4])).center(larg/2," ")
				else:
					gauche = "".center(larg/2," ")

				if k < len(filling):
					droite = "- {} utilise a {} %".format(filling[k][0],valeur(filling[k][4])).center(larg/2," ")
				else:
					droite = "".center(larg/2," ")
				colonnes.append(gauche+droite)


			align = len(max(colonnes,key=len))
			if align <= larg and len(full) > 0 and len(filling) > 0:
				print("Full :".center(larg/2," ")+"Filling :".center(larg/2," "))
				for c in colonnes:
					if c:
						print(c)

			else:
				if len(full) > 0:
					print("Full:".center(larg," ")+"\n")
					for f in full:
						if f:
							print("- {} utilise a {} %".format(f[0],valeur(f[4])).center(larg," "))

				if len(filling) > 0:
					print("\n"+"Filling:".center(larg," ")+"\n")
					colonne = []
					suite = 0
					for f in filling:
						if f:
							print("- {} utilise a {} %".format(f[0],valeur(f[4])).center(larg," "))

	##############################################################################################################
	

	# Analyse des nodes sans association	
	elif choix == "N":
		if num_commande == 1:
			for l in l_retour:
				if l:
					try:
						nb = int(l)
						if nb == 1:
							print( "Il y a 1 node sans association:".center(larg," "))
						else:
							print( "Il y a {} nodes sans association:".format(nb).center(larg," "))
						break
					except:
						continue

		elif num_commande == 2:
			if len(l_retour) > 5:
				afficher = souhaitez_vous("afficher la liste de tous ces nodes")
			else:
				afficher = True

			if afficher:
				print("\n")
				align = len(max(l_retour,key=len))

				if len(l_retour) < 10:
					for l in l_retour:
						if l:
							ecart = align - len(l)
							print("- {}".format(l+ecart*" ").center(larg," "))
				else:
					#### afficher en 2 colonnes pour gagner de la place 
					for k in [i for i in range(len(l_retour)) if i%2 == 0]:
						ecart = align - len(l_retour[k])
						gauche = "- {}".format(l_retour[k]+ecart*" ").center(align," ")
						
						if k+1 < len(l_retour)-1:
							ecart = align - len(l_retour[k+1])
							droite = "- {}".format(l_retour[k+1]+ecart*" ")
							print(gauche.center(larg/2," ")+droite.center(larg/2," "))
						else:
							print(gauche.center(larg/2," "))




	##############################################################################################################




def execution(cmd,choix):
	try:
		check = subprocess.check_output(cmd.split()+[">>","retour_tsm.txt"],shell=False,stderr=subprocess.PIPE)
		analyse = analyser_retour(choix.upper(),1)

	except subprocess.CalledProcessError as e:
		analyse = aff_err(e,choix,1)


	if len(get_cmd()[choix]) > 2:
		# Compatibilite entre les deux commandes (si la 1 echoue, ne pas faire la 2)
		if choix in ["L"]:
			if choix == "L" and len(analyse) > 0:
				for lib in analyse:
					if lib:
						cmd = debut+get_cmd()[choix.upper()][2].format(lib)
						print("[ {} ]".format(lib).center(largeur()/2," ")+"\n")
						try:
							check = subprocess.check_output(cmd.split()+[">>","retour_tsm.txt"],shell=False,stderr=subprocess.PIPE)
							ok = analyser_retour(choix.upper(),2)
						except subprocess.CalledProcessError as e:
							ok = aff_err(e,choix,2)
				return ok
			else:
				return False

		else:
			cmd = debut+get_cmd()[choix.upper()][2]
		try:
			check = subprocess.check_output(cmd.split()+[">>","retour_tsm.txt"],shell=False,stderr=subprocess.PIPE)
			# Passage de resultat entre les deux commandes (retour ok et valeurs)
			if choix in ["B","H"]:
				analyse = analyser_retour(choix.upper(),2,analyse)
			else:
				analyse = analyser_retour(choix.upper(),2)
		except subprocess.CalledProcessError as e:
			analyse = aff_err(e,choix,2)

	if b_bilan:
		if analyse is True:
			return True
		else:
			return False



# Mode bilan (plusieurs choix et synthèse des echecs/OK à la fin)
def bilan():
	actions_bilan = ["B","C","D","F","G","H","J","K","L"]
	print("\n"+" [ {} ] ".format(get_cmd()["A"][0][4:]).center(largeur()," ")+"\n\n")
	# Changement de sortie du print (on redirige vers un fichie rafin de pouvoir traiter les résultats plus tard)
	out_base = sys.stdout
	out_bilan = open("{}\Menu_TSM\config\\bilan.log".format(dossier),"a")
	sys.stdout = out_bilan

	d_bilan = dict()
	for a in actions_bilan:
		print("\n>{}<\n".format(a))
		print("[ {} ]".format(get_cmd()[a][0]).center(largeur()," "))
		commande = debut+get_cmd()[a][1]
		d_bilan[a] = execution(commande,a)
		print("\n><\n")

	# On rétablit la sortie de base pour pouvoir afficher dans le terminal
	sys.stdout = out_base
	out_bilan.close()
	reussis = list()
	rates = list()
	aff1 = ["- En erreur:"]
	aff2 = "- OK: "
	for b in actions_bilan:
		if not d_bilan[b]:
			aff1.append(get_cmd()[b][0])
			rates.append(b)
		else:
			reussis.append(b)

	align = len(max(aff1,key=len))
	for l in aff1:
		ecart = align - len(l)
		print("{}".format(l+ecart*" ").center(largeur()," "))

	for r in reussis:
		aff2 += "{} ".format(r)
	aff2 += " "*(align - len(aff2))
	print("\n"+aff2.center(largeur()," ")+"\n")

	print("# {} actions ont echoue et {} sont OK #".format(len(rates),len(reussis)).center(largeur()," "))

	# Si l'utilisateur demande, on affiche les résulats précedemments chargés dans bilan.log
	if souhaitez_vous("plus de details"):
		print("\n"+"Details:".center(largeur()," "))
		f = open("{}\Menu_TSM\config\\bilan.log".format(dossier),"r")
		balise = False
		for l in f.read().split("\n"):
			if l:
				# On affiche uniquement les résultats des actions echouées
				# On repère le début des résultats pour ce choix
				if re.match("^>[B-L]{1}<",l) and (l[1] in rates):	
					balise = True
					choix = l[1]
					continue
				# On repère la fin du résultat pour ce choix
				elif re.match("^><",l):
					balise = False
					continue
				if balise:
					if "[" in l and "]" in l:
						print("\n")
						# Affichage du titre de manière voyante par rapport aux autres lignes
						print(l[1:-1].replace("[ ","=> ").replace(" ]"," <="))
					else:
						print(l)
		f.close()
	# On efface le fichier bilan 
	open("{}\Menu_TSM\config\\bilan.log".format(dossier),"w").close()
	print("\n"+("["+"-"*len(get_cmd()["A"][0][4:])+"]").center(largeur()," ")+"\n")










										###################
										#                 #
										#    LANCEMENT    #
										#                 #
										###################

if __name__ == "__main__":	
	dossier = os.getcwd()
	try:
		open("{}\Menu_TSM\config\\trace.log".format(dossier),"w").close()
	except:
		pass

	# Préparation du terminal (Nettoyage, Couleur, ..)
	os.system("cls")
	os.system("mode con: lines=5000 cols=100")
	config, l_seuils = get_config()
	dateformat = get_date_format(l_seuils["DATEFORMAT"])
	couleur = l_seuils["COULEUR"]
	os.system("color {}".format(get_code_couleur(couleur)))

	print(rappel)

	# Première récupération des logins (début de commande)
	debut = connexion()

	# Nettoyage du fichier trace au démarrage
	try:
		open("{}\Menu_TSM\config\\trace.log".format(dossier),"w").close()
	except:
		pass

	# N ième récupération des logins (si première echouée) et chargement de la langue
	langue_TSM, debut = langue(debut)
	debut += " -comma "

	# Premier affichage du Menu avec alerte 
	menu(config)

	# Eviter d'appuyer sur ENtrer dès le lancement du programme (pour ne pas boucler sur le choix M)
	premier = True

	# Boucle principale
	while True:
		trace = False
		b_bilan = False
		choix = None

		# Recuperation du choix (entrer = Menu)
		if premier:
			while not(correct(choix)):
				choix = raw_input("\n>> Choisissez: ")
		else:
			while not(correct(choix) or choix == ""):
				choix = raw_input("\n>> Entrer pour continuer ou choisissez: ")
		if choix == "":
			choix = "-M"
		print("\n")
		premier = False

		# Interpretation des choix particuliers
		if choix.upper() in ["QUIT","Q"]:
			quitter()
		elif choix.upper() in ["MENU","-M"]:
			menu(config)
			choix = None
			continue

		# Exécution de tous les choix pouvant être OK ou EN ERREUR avec le mode Bilan (Synthèse des résultats)
		elif choix.upper() == "A":
			b_bilan = True
			bilan()
			print(rappel)
			continue

		# Affichage et modification des configurations (seuils et paramètres du programme)
		elif choix.upper() in ["CONFIG","-C"]:
			l_seuils = configuration(l_seuils)
			dateformat = get_date_format(l_seuils["DATEFORMAT"])
			couleur = l_seuils["COULEUR"]
			os.system("color {}".format(get_code_couleur(couleur)))
			choix = None
			print("\n"+rappel)
			continue

		# Exécution d'un seul choix avec le mode trace (enregistrement du retour TSM brut)
		elif re.match("TRACE [A-{}]".format(l_choix[-1]),choix.upper()):
			trace = True
			choix = choix.upper().split(" ")[1]
			commande = debut+get_cmd()[choix.upper()][1]	
			print("\n"+" [ {} ] ".format(get_cmd()[choix.upper()][0][4:]).center(largeur()," ")+"\n\n")
			execution(commande,choix.upper())
			print("\n"+("["+"-"*len(get_cmd()[choix.upper()][0][4:])+"]").center(largeur()," ")+"\n"+rappel)
			continue

		# Exécution de TOUS les choix avec le mode trace (enregistrement des retours TSM bruts)
		elif choix.upper() in ["TRACE","-T"]:
			if souhaitez_vous("lancer l'execution de toutes les actions"):
				trace = True
				for c in l_choix[2:]:
					commande = debut+get_cmd()[c.upper()][1]	
					print("\n"+" [ {} ] ".format(get_cmd()[c.upper()][0][4:]).center(largeur()," ")+"\n\n")
					execution(commande,c.upper())
					print("\n"+("["+"-"*len(get_cmd()[c.upper()][0][4:])+"]").center(largeur()," ")+"\n")
		
		# Exécution du choix normalement
		else:
			commande = debut+get_cmd()[choix.upper()][1]	
			print("\n"+" [ {} ] ".format(get_cmd()[choix.upper()][0][4:]).center(largeur()," ")+"\n\n")
			execution(commande,choix.upper())
			print("\n"+("["+"-"*len(get_cmd()[choix.upper()][0][4:])+"]").center(largeur()," ")+"\n"+rappel)
			continue
os.system("color")
