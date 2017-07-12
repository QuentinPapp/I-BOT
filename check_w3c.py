#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import pymongo
import sys
import json
import requests
import configparser
import datetime
import logging
import hashlib
from bs4 import BeautifulSoup


def logInfo(info):
    logging.info(info)


def logError(error):
    logging.error(error)


def logDebug(debug):
    logging.debug(debug)


def logIn():
    try:
        r = session.post(urlLogin, timeout=3, data=json.dumps(data), headers=headers)
        if r.status_code == requests.codes.ok:
            logDebug("Connexion à l'intranet")
            login = r.json()
            return login
        else:
            logError("Connexion à l'intranet annulé")
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


def logOut():
    try:
        params = {'_format': 'json', 'token': tabLogIn['logout_token']}
        r = session.post(config.get('URL', 'logout'), params=params, timeout=3, headers=headers)
        if r.status_code == 204:
            logDebug("Deconnexion de l'intranet")
        else:
            logError("Deconnexion de l'intranet annulé")
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# Genère la nouvelle version pour la comparaison
def generateNewVer(html):
    logDebug('Mise en place de la nouvelle version de comparaison')
    try:
        newVer = hashlib.md5(str(html).encode('utf-8')).hexdigest()
        return str(newVer)
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


def generateTabUrl():
    logDebug('Récupération des urls')
    try:
        params = {'_format': 'json'}
        rConnect = session.get(config.get('URL', 'intranet'), params=params, timeout=3, headers=headers)
        if rConnect.status_code == requests.codes.ok:
            tabUrl = rConnect.json()
            return tabUrl
        else:
            logError('Erreur lors de la récupération des urls')
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# Initialisation des données si aucune donnée n'a était trouvée
def dataInit():
    try:
        tabDossier = os.listdir(config.get('URL', 'mainPath'))
        if not tabDossier:
            logInfo('Aucune donnée de validation trouvée, initialisation pour la première vérification')
            rInit = requests.get(config.get('URL', 'intranet'))
            tabInit = rInit.json()
            for i in tabInit:
                urlInit = "http://{}".format(i['name'])
                labelInit = '"' + (i['label']) + '"'
                r = requests.get(urlInit)
                html = BeautifulSoup(r.text, "lxml").encode("utf-8")
                statusCode = str(r.status_code)
                stockStatus(urlInit, statusCode)
                if statusCode == '200':
                    stockVersion(urlInit, createData(html))
                    validW3c(urlInit)
                    logInfo(labelInit + ' : VALIDÉE')
                else:
                    logError(statusCode + ' : ' + '"' + urlInit + '"')
            logInfo("Succès de la première vérification")
            logInfo('FIN')
            sys.exit(1)
        else:
            logDebug("Succès du chargement des données de vérification")
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


def runIbot():
    r = requests.get(config.get('URL', 'intranet'))
    tabUrl = r.json()
    for i in tabUrl:
        url = "http://{}".format(i['name'])
        label = '"' + (i['label']) + '"'
        r = requests.get(url)
        html = BeautifulSoup(r.text, "lxml").encode("utf-8")
        statusCode = str(r.status_code)
        stockStatus(url, statusCode)
        if statusCode == '200':
            if not compare(url, html, generateNewVer(html)):
                stockVersion(url, createData(html))
                validW3c(url)
                logInfo(label + ' : VALIDÉE')
            else:
                logInfo(label + ' : À JOUR')
        else:
            logError(statusCode + ' : ' + '"' + url + '"')


# On stocke la version si le statut = 200 et que la version est différente
def stockVersion(url, newVer):
    logDebug('Stockage de la nouvelle versions dans la base de donnée')
    try:
        dictVersion = {'date': datetime.datetime.utcnow(),
                       'version': newVer}
        db.urls.update(
            {
                'url': url
            },
            {
                '$setOnInsert': {
                    'url': url,
                    'created': datetime.datetime.utcnow()
                },
                '$push': {
                    'version': {
                        '$each': [dictVersion],
                        '$slice': 50,
                        '$position': 0,
                    },
                },
            },
            upsert=True
        )
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# On stock le statut au lancement du script
def stockStatus(url, statusCode):
    logDebug('Stockage du status dans la base de donnée')
    try:
        dictStatus = {'date': datetime.datetime.utcnow(),
                      'status': statusCode}
        db.urls.update(
            {
                'url': url
            },
            {
                '$setOnInsert': {
                    'url': url,
                    'created': datetime.datetime.utcnow()
                },
                '$push': {
                    'statusURL': {
                        '$each': [dictStatus],
                        '$slice': 300,
                        '$position': 0,
                    },
                },
            },
            upsert=True
        )
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# On stock le résultat d'une vérification w3c
def stockError(url, dictError):
    try:
        db.urls.update(
            {
                'url': url
            },
            {
                '$set': {
                    'updated': datetime.datetime.utcnow()
                },
                '$push': {
                    'w3c': {
                        '$each': [dictError],
                        '$slice': 4,
                        '$position': 0,
                    },
                }
            }
        )
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# Créer les fichiers html de chaque site pour la comparaison
def createData(html):
    logDebug("Stockage du nouveau fichier de comparaison")
    try:
        dateN = datetime.datetime.utcnow()
        version = hashlib.md5(str(html).encode('utf-8')).hexdigest()
        if not os.path.exists(config.get('URL', 'mainPath') + str(dateN.year)):
            os.mkdir(config.get('URL', 'mainPath') + str(dateN.year))
        if not os.path.exists(config.get('URL', 'mainPath') + str(dateN.year) + '/' + str(dateN.month)):
            os.mkdir(config.get('URL', 'mainPath') + str(dateN.year) + '/' + str(dateN.month))
        if not os.path.exists(config.get('URL', 'mainPath') + str(dateN.year) + '/' + str(dateN.month) + '/' + str(
                dateN.day)):
            os.mkdir(
                config.get('URL', 'mainPath') + str(dateN.year) + '/' + str(dateN.month) + '/' + str(dateN.day))
        oldPath = config.get('URL', 'mainPath') + str(dateN.year) + '/' + str(dateN.month) + '/' + str(
            dateN.day) + '/' + version + '.html '
        with open(oldPath, "w") as fichier:
            fichier.write(str(html))
        return version
    except Exception as e:
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# Compare les versions pour valider l'utilitée de lancer un validation W3C
def compare(url, html, newVer):
    logDebug('Comparaison des versions')
    try:
        tabVer = db.urls.find_one({'url': url}, {'version': {'$slice': 1}, 'w3c': False, 'status': False})
        oldVersion = tabVer['version'][0]['version']
        try:
            newVersion = config.get('URL', 'mainPath') + '/' + newVer + '.html'
            with open(newVersion, "w") as fichier:
                fichier.write(str(html))
            if oldVersion == newVer:
                os.remove(newVersion)
                logDebug('Les fichiers sont identiques')
                return True
            else:
                os.remove(newVersion)
                logDebug('Les fichiers sont différents')
                return False
        except Exception as e:
            logError('Erreur - {}'.format(e))
            sys.exit(0)
    except KeyError:
        logInfo('"' + url + '"' + ' inexistant dans la base de donnée')
        return False


# Retourne le titre et le label des erreurs W3C
def validW3c(url):
    try:
        r = requests.get(config.get('URL', 'w3cValidator') + url)
        try:
            logDebug("Récupération du code html")
            soup = BeautifulSoup(r.text, "lxml")
            success = soup.find_all("p", class_="success")
            if len(success) >= 1:
                logDebug("Aucune erreur W3C recensée")
                status = "Valide"
                dictError = {
                    'date': datetime.datetime.utcnow(),
                    'status': status,
                }
                stockError(url, dictError)
            failure = soup.find_all("p", class_="failure")
            if len(failure) >= 1:
                logDebug("Erreurs W3C trouvées")
                status = "Non Valide"
                logDebug("Récupération de l'html contenant les erreurs")
                errors = soup.find_all("li", class_="error")
                dictError = {
                    'date': datetime.datetime.utcnow(),
                    'status': status,
                    'errors': {
                        'total': 0,
                        'list': []
                    }
                }
                for error in errors:
                    title = str(error.find("strong").text)
                    label = str(error.find("span").text)
                    dictError['errors']['list'].append({'type': title, 'value': label})
                    if title in dictError['errors']:
                        dictError['errors'][title] += 1
                    else:
                        dictError['errors'][title] = 1
                    dictError['errors']['total'] += 1
                logDebug("Stockage des erreurs dans la base de donnée")
                stockError(url, dictError)
        except Exception as e:
            logError('Erreur - {}'.format(e))
            sys.exit(0)
    except Exception as e:
        logInfo('Application web de validation W3C indisponible')
        logError('Erreur - {}'.format(e))
        sys.exit(0)


# SCRIPT

# Chargement du fichier de config
try:
    config = configparser.ConfigParser()
    config.read('config.cfg')

    # Chargement des configuration du fichier log
    log = str(config.get('LOG', 'logLevel'))

    if log == 'INFO':
        logging.basicConfig(filename=config.get('URL', 'activity'), level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    if log == 'ERROR':
        logging.basicConfig(filename=config.get('URL', 'activity'), level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    if log == 'DEBUG':
        logging.basicConfig(filename=config.get('URL', 'activity'), level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
except:
    sys.exit('Erreur avec le chargement du fichier de config')

logInfo('START')

user = password = config.get('IDENT', 'identification')
urlLogin = config.get('URL', 'login')
data = {"name": user, "pass": password}
headers = {'Content-type': 'application/json'}
session = requests.session()

# Connexion à l'intranet
# tabLogIn = logIn()

# Connexion serveur bdd
logDebug('Connexion serveur base de donnée')
try:
    client = pymongo.MongoClient("mongodb://192.168.0.36")
except Exception as e:
    logError('Erreur - {}'.format(e))
    sys.exit(0)

# Selection de la base ibot
logDebug('Selection de la base ibot')
try:
    db = client.ibot
except Exception as e:
    logError('Erreur - {}'.format(e))
    sys.exit(0)

# Initialisation des datas si besoin
dataInit()

# Execution du bot
logDebug('Lancement du processus')
# runIbot(generateTabUrl())
runIbot()

# Deconnexion de l'intranet
# logOut()
logInfo('FIN')
sys.exit(1)
