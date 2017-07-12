**I-BOT** : *Robot de validation W3C*
=========

> **Information :** Cette application est en réalité un robot autonome confectionner en pur python et grâce à l'aide de plusieurs librairies. Il va être utilisé en interne par les développeurs de l'entreprise pour regrouper ces informations et pouvoir les traiter plus facilement.  
 
 
 
 Dans un premier temps, le script récupère des URL depuis un web service privé, ce sont les adresses des sites web créés par I-com. Pour chacune d'entre elles, le robot va vérifier la date de la dernière validation, si cette validation est supérieure à 24 h, la vérification des normes W3C peut commencer. 

 L'application va se servir d'un site web en libre-service qui va pouvoir nous retourner les informations attendues, soit le type et l'explication de l'erreur. Grâce à quelques librairies, le robot récupère le code HTML du site qui a analysé notre URL et découpe que la partie qui nous intéresse, les erreurs. 

 Si les informations sont identique, le script s'arrête là pour cette URL. 
Sinon, il va stocker ces informations dans une base de données pour ensuite pouvoir les afficher, les trier et les manipuler sur un rendu graphique. Cette page web sera accessible par les développeurs grâce à des identifiants sécurisés.

*Librairies python*
--------------------
```
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

```

*Algorithme*
--------------------

![algoIbot](/img/IbotAlgo.png)

---
Projet de stage de [Quentin Papp](https://www.linkedin.com/in/quentin-papp-19528b105/)