# DLNAPlayOn v1.8.1 (https://github.com/PCigales/DLNAPlayOn)
# Copyright © 2022 PCigales
# This program is licensed under the GNU GPLv3 copyleft license (see https://www.gnu.org/licenses)

from functools import partial
import threading
import selectors
import argparse
import os
import shutil
import msvcrt
import subprocess
import time
from http import server, client, HTTPStatus
import socket
import socketserver
import ssl
import urllib.request, urllib.parse, urllib.error
from io import BytesIO
from xml.dom import minidom
import json
import html
import struct
import array
import hashlib
import base64
import re
import webbrowser
import mimetypes
import random
import locale
import ctypes, ctypes.wintypes

FR_STRINGS = {
  'mediaprovider': {
    'opening': 'Ouverture de "%s" reconnu comme "%s" en mode "%s" - titre: %s',
    'extension': 'Extension de "%s" retenue comme "%s"',
    'failure': 'Échec de l\'ouverture de "%s" en tant que "%s"',
    'subopening': 'Ouverture des sous-titres "%s" reconnus comme "%s"',
    'subextension': 'Extension des sous_titres retenue comme "%s"',
    'subfailure': 'Échec de l\'ouverture des sous-titres "%s" en tant que "%s"',
    'contentpath': 'chemin d\'accès de contenu',
    'contenturl': 'url de contenu',
    'webpageurl': 'url de page web',
    'loadstart': 'Début du chargement dans le tampon du contenu',
    'segmentbuffering': 'Segment %d -> placement dans la zone %d du tampon',
    'segmentfailure': 'Segment %d -> échec de lecture du contenu',
    'loadstop': 'Fin du chargement dans le tampon du contenu',
    'loadinterrupt': 'Interruption du chargement dans le tampon du contenu',
    'connection': 'Connexion pour diffusion de "%s": persistente = %s - requêtes partielles = %s',
    'yes': 'oui',
    'no': 'non',
    'indexation': 'Indexation du tampon sur la connexion %d',
    'deindexation': 'Désindexation du tampon',
    'translation': 'Translation du tampon vers la position %d',
    'present': 'Segment %d -> déjà présent dans la zone %d du tampon'
  },
  'mediaserver': {
    'connection': 'Connexion au serveur de diffusion de %s:%s',
    'deliverystart': 'Connexion %d -> début de la distribution du contenu à %s:%s',
    'delivery1': 'Connexion %d -> segment %d -> distribution à partir de la zone %d du tampon',
    'delivery2': 'Connexion %d -> segment %d -> distribution',
    'delivery3': 'Connexion %d -> segment %d -> distribution à partir du tampon',
    'exceeded': 'Connexion %d -> segment %d -> la zone %d a été dépassée par la queue du tampon',
    'expulsion': 'Connexion %d -> segment %d -> expulsion du tampon',
    'failure': 'Connexion %d -> segment %d -> échec de distribution du contenu',
    'deliveryfailure': 'Connexion %d -> échec de distribution du contenu',
    'deliverystop': 'Connexion %d -> fin de la distribution du contenu',
    'subdelivery': 'Distribution des sous-titres à %s:%s',
    'subfailure': 'Échec de distribution des sous-titres à %s:%s',
    'start': 'Démarrage, sur l\'interface %s, du serveur de diffusion en mode %s%s',
    'sequential': 'séquentiel',
    'random': 'aléatoire',
    'unsupported': ' non supporté par la source',
    'shutdown': 'Fermeture du serveur de diffusion'
  },
  'dlnanotification': {
    'start': 'Démarrage du serveur d\'écoute des notifications d\'événement de %s DLNA à l\'adresse %s:%s',
    'stop': 'Arrêt du serveur d\'écoute des notifications d\'événement de %s DLNA à l\'adresse %s:%s',
    'alreadyactivated': 'Serveur d\'écoute des notifications d\'événement de %s DLNA à l\'adresse %s:%s déjà activée',
    'receipt': 'DLNA Renderer %s -> service %s -> réception de la notification d\'événement %s',
    'notification': 'DLNA Renderer %s -> Service %s -> notification d\'événement %s -> %s est passé à %s',
    'alert': 'DLNA Renderer %s -> Service %s -> notification d\'événement %s -> alerte: %s est passé à %s'
  },
  'dlnaadvertisement': {
    'receipt': 'Réception, sur l\'interface %s, d\'une publicité du périphérique %s (%s:%s): %s',
    'ignored': 'Publicité du périphérique %s (%s:%s) ignorée en raison de la discordance d\'adresse de l\'URL de description',
    'set': 'Mise en place de l\'écoute des publicités de périphérique DLNA sur l\'interface %s',
    'fail': 'Échec de la mise en place de l\'écoute des publicités de périphérique DLNA sur l\'interface %s',
    'alreadyactivated': 'Écoute des publicités de périphérique DLNA déjà activée',
    'start': 'Démarrage du serveur d\'écoute des publicités de périphérique DLNA',
    'stop': 'Arrêt du serveur d\'écoute des publicités de périphérique DLNA'
  },
  'dlnahandler': {
    'ip_failure': 'Échec de la récupération de l\'adresse ip de l\'hôte',
    'registering': 'Enregistrement du %s %s sur l\'interface %s',
    'msearch1': 'Envoi d\'un message de recherche de uuid:%s',
    'msearch2': 'Envoi d\'un message de recherche de périphérique DLNA',
    'msearch3': 'Envoi d\'un message de recherche de %s DLNA',
    'sent': 'Envoi du message de recherche sur l\'interface %s',
    'fail': 'Échec de l\'envoi du message de recherche sur l\'interface %s',
    'receipt': 'Réception, sur l\'interface %s, d\'une réponse au message de recherche de %s:%s',
    'ignored': 'Réponse de %s:%s ignorée en raison de la discordance d\'adresse de l\'URL de description',
    'alreadyactivated': 'Recherche de %s DLNA déjà activée',
    'start': 'Démarrage de la recherche de %s DLNA',
    'stop': 'Fin de la recherche de %s DLNA',
    'commandabandonment': '%s %s -> service %s -> abandon de l\'envoi de la commande %s',
    'commandsending': '%s %s -> service %s -> envoi de la commande %s',
    'commandfailure': '%s %s -> service %s -> échec de l\'envoi de la commande %s',
    'commandsuccess': '%s %s -> service %s -> succès de l\'envoi de la commande %s',
    'responsefailure': '%s %s -> service %s -> échec du traitement de la réponse à la commande %s',
    'responsesuccess': '%s %s -> service %s -> succès de la réception de la réponse à la commande %s',
    'advertalreadyactivated': 'Écoute des publicités de %s déjà activée',
    'advertstart': 'Démarrage de l\'écoute des publicités de %s',
    'advertstop': 'Fin de l\'écoute des publicités de %s',
    'subscralreadyactivated': 'Renderer %s -> service %s -> souscription au serveur d\'événements déjà en place',
    'subscrfailure': 'Renderer %s -> service %s -> échec de la demande de souscription au serveur d\'événements',
    'subscrsuccess': 'Renderer %s -> service %s -> souscription au serveur d\'événements sous le SID %s pour une durée de %s',
    'subscrrenewfailure': 'Renderer %s -> service %s -> échec de la demande de renouvellement de souscription de SID %s au serveur d\'événements',
    'subscrrenewsuccess': 'Renderer %s -> service %s -> renouvellement de la souscription de SID %s au serveur d\'événements pour une durée de %s',
    'subscrunsubscrfailure': 'Renderer %s -> service %s -> échec de la demande de fin de souscription de SID %s au serveur d\'événements',
    'subscrunsubscrsuccess': 'Renderer %s -> service %s -> fin de la souscription de SID %s au serveur d\'événements'
  },
  'websocket': {
    'endacksuccess': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> succès de l\'envoi de l\'accusé de réception de l\'avis de fin de connexion',
    'endackfailure': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> échec de l\'envoi de l\'accusé de réception de l\'avis de fin de connexion',
    'errorendnotification': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> envoi d\'avis de fin de connexion pour cause d\'erreur %s',
    'errorendnotificationsuccess': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> succès de l\'envoi de l\'avis de fin de connexion',
    'errorendnotificationfailure': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> échec de l\'envoi de l\'avis de fin de connexion',
    'terminationdatasuccess': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> succès de l\'envoi de la donnée de terminaison %s',
    'terminationdatafailure': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> échec de l\'envoi de la donnée de terminaison %s',
    'endnotificationsuccess': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> succès de l\'envoi de l\'avis de fin de connexion',
    'endnotificationfailure': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> échec de l\'envoi de l\'avis de fin de connexion',
    'datasuccess': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> envoi de la donnée %s',
    'datafailure': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> échec de l\'envoi de la donnée %s',
    'datareceipt': 'WebSocket serveur %s:%s/%s -> WebSocket %s:%s -> réception de la donnée %s',
    'connectionrequest': 'WebSocket serveur %s:%s -> demande de connexion du WebSocket %s:%s',
    'connectionrequestinvalid': 'WebSocket serveur %s:%s -> demande de connexion du WebSocket %s:%s invalide',
    'connectionrequestnotfound': 'WebSocket serveur %s:%s -> chemin de demande de connexion du WebSocket %s:%s introuvable: /%s',
    'connectionresponsefailure': 'WebSocket serveur %s:%s/%s -> échec de l\'envoi de la réponse à la demande de connexion du WebSocket %s:%s',
    'connection': 'WebSocket serveur %s:%s/%s -> connexion au WebSocket %s:%s',
    'endack': 'WebSocket serveur %s:%s/%s -> accusé de réception de fin de connexion du WebSocket %s:%s',
    'endnotification': 'WebSocket serveur %s:%s/%s -> avis de fin de connexion du WebSocket %s:%s',
    'connectionend': 'WebSocket serveur %s:%s/%s -> fin de connexion au WebSocket %s:%s',
    'start': 'Démarrage du serveur pour Websocket à l\'adresse %s:%s',
    'fail': 'Échec du démarrage du serveur pour Websocket à l\'adresse %s:%s',
    'open': 'Websocket serveur %s:%s: ouverture du canal /%s',
    'close': 'Websocket serveur %s:%s: fermeture du canal /%s',
    'shutdown': 'Fermeture du serveur pour Websocket à l\'adresse %s:%s'
  },
  'webinterface': {
    'ip_failure': 'Échec de la récupération de l\'adresse ip de l\'hôte',
    'connection': 'Connexion de l\'interface web %s:%s',
    'response': 'Réponse à l\'interface Web %s:%s - requête: %s',
    'formdatareceipt': 'Réception de la donnée de formulaire %s de %s:%s',
    'formdatareject': 'Rejet de la donnée de formulaire %s de %s:%s',
    'playbackaccept': 'Prise en compte de la demande de lecture de %s%s à partir de %s sur %s de %s:%s',
    'playbacksub': ' et %s',
    'playbackreject': 'Rejet de la demande de lecture de %s%s à partir de %s sur %s de %s:%s',
    'rendererstart': 'Démarrage du gestionnaire d\'affichage de renderer pour serveur d\'interface Web',
    'launchrendererstart': 'Démarrage du gestionnaire d\'affichage de renderer dans le formulaire de lancement pour serveur d\'interface Web',
    'rendererstop': 'Arrêt du gestionnaire d\'affichage de renderer pour serveur d\'interface Web',
    'controlstart': 'Démarrage du gestionnaire de contrôleur de lecture pour serveur d\'interface Web',
    'controlinterrupt': 'Interruption du gestionnaire de contrôleur de lecture pour serveur d\'interface Web',
    'controlrenderer': 'Sélection du renderer %s sur l\'interface %s',
    'playlist': 'Liste de lecture générée depuis l\'adresse %s: %s contenus média',
    'nocontent': 'Absence de contenu média sous l\'adresse %s',
    'nonegapless': 'Absence de support de la lecture sans blanc par le renderer %s',
    'gapless': 'Lecture sans blanc des contenus média depuis l\'adresse %s activée',
    'nogapless': 'Adresse %s incompatible avec la lecture sans blanc',
    'norendereranswer': 'Absence de réponse du renderer %s',
    'ready': 'Prêt pour lecture de "%s"%s, par %s, sur le renderer "%s"',
    'subtitled': ', sous-titrée',
    'direct': 'transmission directe de l\'adresse',
    'random': 'diffusion via serveur en mode accès aléatoire',
    'sequential': 'diffusion via serveur en mode accès séquentiel%s',
    'remuxed': ', remuxé en %s',
    'controlstop': 'Arrêt du gestionnaire de contrôleur de lecture pour serveur d\'interface Web%s%s%s%s',
    'status': ' - statut ',
    'start': 'Démarrage du serveur d\'interface Web sur l\'interface %s',
    'alreadyrunning': 'Serveur d\'interface Web déjà en place',
    'fail': 'Échec du démarrage du serveur d\'interface Web sur l\'interface %s',
    'shutdown': 'Fermeture du serveur d\'interface Web',
    'jstart': 'Interface de démarrage',
    'jcontrol': 'Interface de contrôle',
    'jrenderers': 'Renderers',
    'jmwebsocketfailure': 'Échec de l\'établissement de la connexion WebSocket',
    'jmrenderersclosed': 'Renderers - interface close',
    'jmentervalidurl': 'Saisissez une URL de contenu média valide',
    'jmentervalidsuburl': 'Saisissez une URL de sous-titres valide',
    'jmselectrenderer': 'Sélectionnez d\'abord un renderer',
    'jplaybackposition': 'Position de lecture',
    'jgoplay': 'Lire',
    'jreset': 'Réinitialiser',
    'jplay': 'Lecture',
    'jpause': 'Pause',
    'jstop': 'Arrêt',
    'jinterfaceclosed': 'interface close',
    'jback': 'retour',
    'jinitialization': 'initialisation',
    'jready': 'prêt',
    'jreadyfromstart': 'prêt (lecture à partir du début)',
    'jinprogress': 'en cours',
    'jinplayback': 'lecture',
    'jinpause': 'pause',
    'jinstop': 'arrêt',
    'jplaylist': 'Liste de lecture',
    'jurl': 'URL du média',
    'jstatus': 'Statut',
    'jtargetposition': 'Position cible',
    'jmstop': 'Arrêter la lecture ?'
  },
  'parser': {
    'license': 'Ce programme est sous licence copyleft GNU GPLv3 (voir https://www.gnu.org/licenses)',
    'help': 'affichage du message d\'aide et interruption du script',
    'ip': 'adresse IP de l\'interface web [auto-sélectionnée par défaut - "0.0.0.0", soit toutes les interfaces, si option présente sans mention d\'adresse]',
    'port': 'port TCP de l\'interface web [8000 par défaut]',
    'hip': 'adresse IP du contrôleur/client DLNA [auto-sélectionnée par défaut - "0.0.0.0", soit toutes les interfaces, si option présente sans mention d\'adresse]',
    'rendereruuid': 'uuid du renderer [premier renderer sans sélection sur l\'uuid par défaut]',
    'renderername': 'nom du renderer [premier renderer sans sélection sur le nom par défaut]',
    'servertype': 'type de serveur (a:auto, s:séquentiel, r:aléatoire, g:sans-blanc/aléatoire, n:aucun) [a par défaut]',
    'buffersize': 'taille du tampon en blocs de 1 Mo [75 par défaut]',
    'bufferahead': 'taille du sous-tampon de chargement par anticipation en blocs de 1 Mo [25 par défaut]',
    'muxcontainer': 'type de conteneur de remuxage précédé de ! pour qu\'il soit systématique [MP4 par défaut]',
    'onreadyplay': 'lecture directe dès que le contenu média et le renderer sont prêts [désactivé par défaut]',
    'displayrenderers': 'Affiche les renderers présents sur le réseau',
    'start': 'Démarre l\'interface à partir de la page de lancement',
    'control': 'Démarre l\'interface à partir de la page de contrôle',
    'mediasrc1': 'adresse du contenu multimédia [aucune par défaut]',
    'mediasrc2': 'adresse du contenu multimédia',
    'mediasubsrc': 'adresse du contenu de sous-titres [aucun par défaut]',
    'mediasublang': 'langue de sous-titres, . pour pas de sélection [fr,fre,fra,fr.* par défaut]',
    'mediasublangcode': 'fr,fre,fra,fr.*',
    'mediastartfrom': 'position temporelle de démarrage ou durée d\'affichage au format H:MM:SS [début/indéfinie par défaut]',
    'slideshowduration': 'durée d\'affichage des images, si mediastrartfrom non défini, au format H:MM:SS [aucune par défaut]',
    'endless': 'lecture en boucle [désactivé par défaut, toujours actif en mode lecture aléatoire de liste]',
    'verbosity': 'niveau de verbosité de 0 à 2 [0 par défaut]',
    'stopkey': 'Appuyez sur "S" pour stopper',
    'auto': 'auto',
    'sequential': 'séquentiel',
    'random': 'aléatoire',
    'remuxkey': 'Appuyez sur "!" et "M" pour alterner entre les modes de remuxage (MP4, MPEGTS, !MP4, !MPEGTS) pour la prochaine session de lecture - mode actuel: %s',
    'servertypekey': 'Appuyez sur "T" pour alterner entre les types de serveur (auto, séquentiel, aléatoire) pour la prochaine session de lecture - mode actuel: %s',
    'endlesskey': 'Appuyez sur "E" pour activer/désactiver la lecture en boucle - mode actuel: %s',
    'enabled': 'activé',
    'disabled': 'désactivé',
    'remuxnext': 'Mode de remuxage pour la prochaine session de lecture: %s',
    'servertypenext': 'Type de serveur pour la prochaine session de lecture: %s',
    'endlessstatus': 'Lecture en boucle: %s'
  }
}
EN_STRINGS = {
  'mediaprovider': {
    'opening': 'Opening of "%s" recognized as "%s" in "%s" mode - title: %s',
    'extension': 'Extension of "%s" retained as "%s"',
    'failure': 'Failure of the opening of "%s" as "%s"',
    'subopening': 'Opening of the subtitles "%s" recognized as "%s"',
    'subextension': 'Extension of the subtitles retained as "%s"',
    'subfailure': 'Failure of the opening of the subtitles "%s" as "%s"',
    'contentpath': 'content path',
    'contenturl': 'content url',
    'webpageurl': 'web page url',
    'loadstart': 'Start of the loading in the content buffer',
    'segmentbuffering': 'Segment %d -> placement in the zone %d of the buffer',
    'segmentfailure': 'Segment %d -> failure of reading of the content',
    'loadstop': 'End of the loading in the content buffer',
    'loadinterrupt': 'Interruption of the loading in the content buffer',
    'connection': 'Connection for delivery of "%s": persistent = %s - partial requests = %s',
    'yes': 'yes',
    'no': 'no',
    'indexation': 'Indexation of the buffer on the connection %d',
    'deindexation': 'Deindexation of the buffer',
    'translation': 'Translation of the buffer to the position %d',
    'present': 'Segment %d -> already present in the zone %d of the buffer'
  },
  'mediaserver': {
    'connection': 'Connection to the delivery server of %s:%s',
    'deliverystart': 'Connection %d -> start of the delivery of the content to %s:%s',
    'delivery1': 'Connection %d -> segment %d -> delivery from the zone %d of the buffer',
    'delivery2': 'Connection %d -> segment %d -> delivery',
    'delivery3': 'Connection %d -> segment %d -> delivery from the buffer',
    'exceeded': 'Connection %d -> segment %d -> the zone %d has been exceeded by the tail of the buffer',
    'expulsion': 'Connection %d -> segment %d -> expulsion of the buffer',
    'failure': 'Connection %d -> segment %d -> failure of the delivery of the content',
    'deliveryfailure': 'Connection %d -> failure of the delivery of the content',
    'deliverystop': 'Connection %d -> end of the delivery of the content',
    'subdelivery': 'Delivery of the subtitles to %s:%s',
    'subfailure': 'Failure of the delivery of the subtitles to %s:%s',
    'start': 'Start, on the interrface %s, of the delivery server in %s mode%s',
    'sequential': 'sequential',
    'random': 'random',
    'unsupported': ' unsupported by the source',
    'shutdown': 'Shutdown of the delivery server'
  },
  'dlnanotification': {
    'start': 'Start of the server of listening of event notifications from DLNA %s at the address %s:%s',
    'stop': 'Shutdown of the server of listening of event notifications from DLNA %s at the address %s:%s',
    'alreadyactivated': 'Server of listening of event notifications from DLNA %s at the address %s:%s already activated',
    'receipt': 'DLNA Renderer %s -> service %s -> receipt of the notification of event %s',
    'notification': 'DLNA Renderer %s -> Service %s -> notification of event %s -> %s is changed to %s',
    'alert': 'DLNA Renderer %s -> Service %s -> notification of event %s -> alerte: %s is changed to %s'
  },
  'dlnaadvertisement': {
    'receipt': 'Receipt, on the interface %s, of an advertisement from the device %s (%s:%s): %s',
    'ignored': 'Advertisement of the device %s (%s:%s) ignored due to the mismatch of the address of the description URL',
    'set': 'Installation of the listening of advertisements of DLNA devices on the interface %s',
    'fail': 'Failure of the installation of the listening of advertisements of DLNA devices on the interface %s',
    'alreadyactivated': 'Listening of advertisements of DLNA devices already activated',
    'start': 'Start of the server of listening of advertisements of DLNA devices',
    'stop': 'Shutdown of the server of listening of advertisements of DLNA devices'
  },
  'dlnahandler': {
    'ip_failure': 'Failure of the retrieval of the host ip address',
    'registering': 'Registration of the %s %s on the interface %s',
    'msearch1': 'Sending of a search message of uuid:%s',
    'msearch2': 'Sending of a search message of DLNA device',
    'msearch3': 'Sending of a search message of DNLA %s',
    'sent': 'Sending of the search message on the interface %s',
    'fail': 'Failure of the sending of the search message on the interface %s',
    'receipt': 'Receipt, on the interface %s, of a response to the search message from %s:%s',
    'ignored': 'Response from %s:%s ignored due to the mismatch of the address of the description URL',
    'alreadyactivated': 'Search of DNLA %s already activated',
    'start': 'Start of the search of DLNA %s',
    'stop': 'End of the search of DLNA %s',
    'commandabandonment': '%s %s -> service %s -> abandonment of the sending of the command %s',
    'commandsending': '%s %s -> service %s -> sending of the command %s',
    'commandfailure': '%s %s -> service %s -> failure of the sending of the command %s',
    'commandsuccess': '%s %s -> service %s -> success of the sending of the command %s',
    'responsefailure': '%s %s -> service %s -> failure of the processing of the response to the command %s',
    'responsesuccess': '%s %s -> service %s -> success of the receipt of the response to the command %s',
    'advertalreadyactivated': 'Listening of the advertisements of %s already activated',
    'advertstart': 'Start of the listening of advertisements of %s',
    'advertstop': 'End of the listening of advertisements of %s',
    'subscralreadyactivated': 'Renderer %s -> service %s -> subscription to the events server already in place',
    'subscrfailure': 'Renderer %s -> service %s -> failure of the request of subscription to the events server',
    'subscrsuccess': 'Renderer %s -> service %s -> subscription to the events server under the SID %s for a period of %s',
    'subscrrenewfailure': 'Renderer %s -> service %s -> failure of the request of renewal of subscription under SID %s to the events server',
    'subscrrenewsuccess': 'Renderer %s -> service %s -> renewal of the subscription under SID %s to the events server for a period of %s',
    'subscrunsubscrfailure': 'Renderer %s -> service %s -> failure of the request of end of subscription under SID %s to the events server',
    'subscrunsubscrsuccess': 'Renderer %s -> service %s -> end of subscription under SID %s to the events server'
  },
  'websocket': {
    'endacksuccess': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> success of the sending of the acknowledgment of receipt of the notice of end of connection',
    'endackfailure': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> failure of the sending of the acknowledgment of receipt of the notice of end of connection',
    'errorendnotification': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> sending of a notice of end of connection because of error %s',
    'errorendnotificationsuccess': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> success of the sending of the notice of end of connection',
    'errorendnotificationfailure': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> failure of the sending of the notice of end of connection',
    'terminationdatasuccess': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> success of the sending of the termination data %s',
    'terminationdatafailure': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> failure of the sending of the termination data %s',
    'endnotificationsuccess': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> success of the sending of the notice of end of connection',
    'endnotificationfailure': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> failure of the sending of the notice of end of connection',
    'datasuccess': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> sending of the data %s',
    'datafailure': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> failure of the sending of the data %s',
    'datareceipt': 'WebSocket server %s:%s/%s -> WebSocket %s:%s -> receipt of the data %s',
    'connectionrequest': 'WebSocket server %s:%s -> connection request from the WebSocket %s:%s',
    'connectionrequestinvalid': 'WebSocket server %s:%s -> connection request from the WebSocket %s:%s invalid',
    'connectionrequestnotfound': 'WebSocket server %s:%s -> path of the connection request from the WebSocket %s:%s not found: /%s',
    'connectionresponsefailure': 'WebSocket server %s:%s/%s -> failure of the sending of the response to the connection request from the WebSocket %s:%s',
    'connection': 'WebSocket server %s:%s/%s -> connection to the WebSocket %s:%s',
    'endack': 'WebSocket server %s:%s/%s -> acknowledgment of end of connection from the WebSocket %s:%s',
    'endnotification': 'WebSocket server %s:%s/%s -> notice of end of connection from the WebSocket %s:%s',
    'connectionend': 'WebSocket server %s:%s/%s -> end of connection to the WebSocket %s:%s',
    'start': 'Start of the server for Websocket at the address %s:%s',
    'fail': 'Failure of the start of the server for Websocket at the address %s:%s',
    'open': 'Websocket server %s:%s: opening of the channel /%s',
    'close': 'Websocket server %s:%s: closure of the channel /%s',
    'shutdown': 'Shutdonw of the server for Websocket at the address %s:%s'
  },
  'webinterface': {
    'ip_failure': 'Failure of the retrieval of the host ip address',
    'connection': 'Connection of the Web interface %s:%s',
    'response': 'Response to the Web interface %s:%s - request: %s',
    'formdatareceipt': 'Receipt of the form data %s from %s:%s',
    'formdatareject': 'Rejection of the form data %s from %s:%s',
    'playbackaccept': 'Acceptance of the playback request of %s%s starting at %s on %s from %s:%s',
    'playbacksub': ' and %s',
    'playbackreject': 'Rejection of the playback request of %s%s starting at %s on %s from %s:%s',
    'rendererstart': 'Start of the display manager of renderer for Web interface server',
    'launchrendererstart': 'Start of the display manager of renderer in the launch form for Web interface server',
    'rendererstop': 'Shutdown of the display manager of renderer for Web interface server',
    'controlstart': 'Start of the playback controller manager for Web interface server',
    'controlinterrupt': 'Interruption of the playback controller manager for Web interface server',
    'controlrenderer': 'Selection of the renderer %s on the interface %s',
    'playlist': 'Playlist generated from the address %s: %s media contents',
    'nocontent': 'Absence of media content under the address %s',
    'nonegapless': 'Absence of support of gapless playback by the renderer %s',
    'gapless': 'Gapless playback of the media contents from the address %s enabled',
    'nogapless': 'Address %s incompatible with gapless playback',
    'norendereranswer': 'Absence of response from the renderer %s',
    'ready': 'Ready for playback of "%s"%s, by %s, on the renderer "%s"',
    'subtitled': ', subtitled',
    'direct': 'direct transmission of the address',
    'random': 'delivery through server in random access mode',
    'sequential': 'delivery through server in sequential access mode%s',
    'remuxed': ', remuxed in %s',
    'controlstop': 'Shutdown of the playback controller manager for Web interface server%s%s%s%s',
    'status': ' - status ',
    'start': 'Start of the Web interface server on the interface %s',
    'alreadyrunning': 'Web interface server already in place',
    'fail': 'Failure of the start of the Web interface server on the interface %s',
    'shutdown': 'Shutdown of the Web interface server',
    'jstart': 'Launch interface',
    'jcontrol': 'Control interface',
    'jrenderers': 'Renderers',
    'jmwebsocketfailure': 'Failure of the establishment of the WebSocket connection',
    'jmrenderersclosed': 'Renderers - interface closed',
    'jmentervalidurl': 'Enter a valid media content URL',
    'jmentervalidsuburl': 'Enter a valid subtitles URL',
    'jmselectrenderer': 'First select a renderer',
    'jplaybackposition': 'Playback position',
    'jgoplay': 'Play',    
    'jreset': 'Reset',
    'jplay': 'Play',
    'jpause': 'Pause',
    'jstop': 'Stop',
    'jinterfaceclosed': 'interface closed',
    'jback': 'back',
    'jinitialization': 'initialization',
    'jready': 'ready',
    'jreadyfromstart': 'ready (playback from the beginning)',
    'jinprogress': 'in progress',
    'jinplayback': 'playback',
    'jinpause': 'pause',
    'jinstop': 'stop',
    'jplaylist': 'Playlist',
    'jurl': 'Media URL',
    'jstatus': 'Status',
    'jtargetposition': 'Target position',
    'jmstop': 'Stop the playback ?'
  },
  'parser': {
    'license': 'This program is licensed under the GNU GPLv3 copyleft license (see https://www.gnu.org/licenses)',
    'help': 'display of the help message and interruption of the script',
    'ip': 'IP address of the web interface [auto-selected by default - "0.0.0.0", meaning all interfaces, if option present with no address mention]',
    'port': 'TCP port of the web interface [8000 by default]',
    'hip': 'IP address of the DLNA controller/client [auto-selected by default - "0.0.0.0", meaning all interfaces, if option present with no address mention]',
    'rendereruuid': 'uuid of the renderer [first renderer without selection on the uuid by default]',
    'renderername': 'name of the renderer [first renderer without selection on the name by default]',
    'servertype': 'type of server (a:auto, s:sequential, r:random, g:gapless/random, n:none) [a by default]',
    'buffersize': 'size of the buffer in blocks of 1 MB [75 by default]',
    'bufferahead': 'size of the sub-buffer of loading in advance in blocks of 1 MB [25 by default]',
    'muxcontainer': 'type of remuxing container preceded by ! so that it is systematic [MP4 by default]',
    'onreadyplay': 'direct playback as soon as the media content and the renderer are ready [disabled by default]',
    'displayrenderers': 'Displays the renderers present on the network',
    'start': 'Starts the interface from the launch page',
    'control': 'Starts the interface from the control page',
    'mediasrc1': 'adress of the multimedia content [none by default]',
    'mediasrc2': 'adress of the multimedia content',
    'mediasubsrc': 'adress of the subtitles content [none by default]',
    'mediasublang': 'language of the subtitles, . for no selection [en,eng,en.* by default]',
    'mediasublangcode': 'en,eng,en.*',
    'mediastartfrom': 'start time position or display duration in format H:MM:SS [start/indefinite by default]',
    'slideshowduration': 'display duration of the pictures, if mediastrartfrom not defined, in the format H:MM:SS [none by default]',
    'endless': 'loop playback [disabled by default, always enabled in list random playback mode]',
    'verbosity': 'verbosity level from 0 to 2 [0 by default]',
    'stopkey': 'Press "S" to stop',
    'auto': 'auto',
    'sequential': 'sequential',
    'random': 'random',
    'remuxkey': 'Press "!" and "M" to switch between the remuxing modes (MP4, MPEGTS, !MP4, !MPEGTS) for the next playback session - current mode: %s',
    'servertypekey': 'Press "T" to switch between the types of server (auto, sequential, random) for the next playback session - current mode: %s',
    'endlesskey': 'Press "E" to enable/disable the loop playback - current mode: %s',
    'enabled': 'enabled',
    'disabled': 'disabled',
    'remuxnext': 'Remuxing mode for the next playback session: %s',
    'servertypenext': 'Type of server for the next playback session: %s',
    'endlessstatus': 'Loop playback: %s'
  }
}
LSTRINGS = EN_STRINGS
try:
  if locale.getlocale()[0][:2].lower() == 'fr':
    LSTRINGS = FR_STRINGS
except:
  pass


class log_event:

  def __init__(self, kmod, verbosity):
    self.kmod = kmod
    self.verbosity = verbosity

  def log(self, level, kmsg, *var):
    if level <= self.verbosity:
      now = time.localtime()
      s_now = '%02d/%02d/%04d %02d:%02d:%02d' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec)
      try:
        print(s_now, ':', LSTRINGS[self.kmod][kmsg] % var)
      except:
        try:
          print(s_now, ':', kmsg % var)
        except:
          print(s_now, ':', kmsg)


class ThreadedDualStackServer(socketserver.ThreadingMixIn, server.HTTPServer):

  block_on_close = False

  def __init__(self, *args, kmod, verbosity, auth_ip=None, **kwargs):
    self.logger = log_event(kmod, verbosity)
    if auth_ip:
      if isinstance(auth_ip, tuple):
        self.auth_ip = (*auth_ip, '127.0.0.1')
      else:
        self.auth_ip = (auth_ip, '127.0.0.1')
    else:
      self.auth_ip = None
    server.HTTPServer.__init__(self, *args, **kwargs)
    self.__dict__['_BaseServer__is_shut_down'].set()
  
  def server_bind(self):
    self.conn_sockets = []
    try:
      self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except:
      pass
    socketserver.TCPServer.server_bind(self)
    self.server_name = '%s:%s' % self.server_address
    self.server_port = self.server_address[1]
    
  def process_request_thread(self, request, client_address):
    self.conn_sockets.append(request)
    self.logger.log(2, 'connection', *client_address)
    super().process_request_thread(request, client_address)

  def shutdown(self):
    self.socket.close()
    super().shutdown()

  def server_close(self):
    pass


class MediaBuffer:

  def __init__(self, BufferSize, BufferBlocSize):
    self.content = [None] * BufferSize
    self.bloc_size = BufferBlocSize
    self.w_index = 0
    self.r_indexes = []
    self.create_lock = threading.Lock()
    self.r_event = threading.Event()
    self.w_condition = threading.Condition()
    self.len = 0
    self.t_index = None


class MediaProvider(threading.Thread):

  STATUS_INITIALIZING = 0
  STATUS_ABORTED = 1
  STATUS_RUNNING = 2
  STATUS_COMPLETED = 3
  SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
  
  SERVER_MODE_AUTO = 0
  SERVER_MODE_SEQUENTIAL = 1
  SERVER_MODE_RANDOM = 2
  SERVER_MODES = ("auto", "séquentiel", "aléatoire")

  TITLE_MAX_LENGTH = 200

  @classmethod
  def open_url(cls, url, method=None):
    header = {'User-Agent': 'Lavf'}
    if method:
      if method.upper() == 'HEAD':
        header['Range'] = 'bytes=0-'
    req = urllib.request.Request(url, headers=header, method=method)
    rep = None
    try:
      rep = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
      if e.code == HTTPStatus.NOT_ACCEPTABLE and method.upper() == 'HEAD':
        del header['Range']
        req = urllib.request.Request(url, headers=header, method=method)
        rep = None
        try:
          rep = urllib.request.urlopen(req)
        except:
          pass
    except:
      pass
    return rep

  def __init__(self, ServerMode, MediaSrc, MediaSrcType=None, MediaStartFrom=None, MediaBuffer=None, MediaBufferAhead=None, MediaMuxContainer=None, MediaSubSrc=None, MediaSubSrcType=None, MediaSubLang=None, MediaSubBuffer=None, MediaProcessProfile=None, FFmpegPort=None, BuildFinishedEvent=None, verbosity=0):
    threading.Thread.__init__(self)
    self.logger = log_event('mediaprovider', verbosity)
    self.ServerMode = ServerMode if ServerMode in (MediaProvider.SERVER_MODE_SEQUENTIAL, MediaProvider.SERVER_MODE_RANDOM) else MediaProvider.SERVER_MODE_AUTO
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaStartFrom = MediaStartFrom if not MediaStartFrom in (None, '0', '0:00', '00:00', '0:00:00', '00:00:00') else ''
    self.MediaBuffer = MediaBuffer
    if MediaBuffer:
      self.MediaBufferSize = len(MediaBuffer.content)
      self.MediaBufferAhead = MediaBufferAhead
    else:
      self.MediaBufferSize = 0
      self.MediaBufferAhead = 0
    if FFmpegPort:
      if MediaMuxContainer:
        self.MediaMuxAlways = MediaMuxContainer[0:1] == '!'
      else:
        self.MediaMuxAlways = None
        self.MediaMuxContainer = None
      if self.MediaMuxAlways:
        self.MediaMuxContainer = MediaMuxContainer[1:]
      else:
        self.MediaMuxContainer = MediaMuxContainer
      if self.MediaMuxContainer:
        self.ffmpeg_server_url = 'http://127.0.0.1:%s' % FFmpegPort
        if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          self.MediaMuxAlways = None
          self.MediaMuxContainer = None
      else:
        self.ffmpeg_server_url = ''
        self.MediaMuxAlways = None
        self.MediaMuxContainer = None
    else:
      self.ffmpeg_server_url = ''
      self.MediaMuxAlways = None
      self.MediaMuxContainer = None
    if self.ServerMode == MediaProvider.SERVER_MODE_AUTO:
      if self.MediaMuxAlways:
        self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
      if not self.MediaMuxContainer:
        self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
    self.FFmpeg_process = None
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
      if (not MediaSubBuffer[1] if len(MediaSubBuffer) >= 2 else True):
        if MediaSubSrc:
          self.MediaSubSrc = MediaSubSrc
          self.MediaSubSrcType = MediaSubSrcType
          self.MediaSubLang = MediaSubLang
          self.MediaSubBuffer.clear()
          self.MediaSubBuffer.append(b'')
          self.MediaSubBuffer.append('')
        else:
          self.MediaSubSrc = None
          self.MediaSubSrcType = None
          self.MediaSubLang = None
      else:
        self.MediaSubSrc = ''
    else:
      self.MediaSubSrc = None
      self.MediaSubSrcType = None
      self.MediaSubLang = None
    self.FFmpeg_sub_process = None
    self.MediaProcessProfile = MediaProcessProfile if MediaProcessProfile else ''
    self.Connection = None
    self.Persistent = None
    self.AcceptRanges = None
    self.MediaFeed = None
    self.MediaFeedExt = None
    self.MediaSize = None
    self.MediaTitle = ''
    self.Status = None
    self.shutdown_requested = False
    if isinstance(BuildFinishedEvent, threading.Event):
      self.BuildFinishedEvent = BuildFinishedEvent
    else:
      self.BuildFinishedEvent = threading.Event()

  def _open_FFmpeg(self, vid=None, aud=None, sub=None, in_sub_buffer=None, out_sub_buffer=None):
    if not vid and not (sub and out_sub_buffer):
      return None
    ffmpeg_env = {'mediabuilder_address': '-' if sub else self.ffmpeg_server_url, 'mediabuilder_start': self.MediaStartFrom, 'mediabuilder_mux': self.MediaMuxContainer if vid else 'SRT', 'mediabuilder_profile': self.MediaProcessProfile}
    ffmpeg_env['mediabuilder_vid'] = '"%s"' % (vid) if vid else ''
    ffmpeg_env['mediabuilder_aud'] = '"%s"' % (aud) if aud else ''
    ffmpeg_env['mediabuilder_sub'] = '-' if in_sub_buffer else ('"%s"' % (sub) if sub else '')
    ffmpeg_env['mediabuilder_lang'] = '%s' % (self.MediaSubLang) if sub and self.MediaSubLang else ''
    media_feed = None
    while True:
      if not sub:
        self.FFmpeg_process = subprocess.Popen(r'"%s\%s"' % (MediaProvider.SCRIPT_PATH, 'ffmpeg.bat'), env={**os.environ,**ffmpeg_env}, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=6))
        media_feed = None
        while not media_feed and self.FFmpeg_process.poll() == None and not self.shutdown_requested:
          try:
            media_feed = urllib.request.urlopen(self.ffmpeg_server_url, timeout=1)
          except:
            pass
        if not self.shutdown_requested:
          time.sleep(0.5)
          if self.FFmpeg_process.poll() in (None, 0):
            media_feed.fp.raw._sock.settimeout(None)
            break
        if media_feed:
          try:
            media_feed.close()
          except:
            pass
        media_feed = None
      else:
        if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          ffmpeg_env['mediabuilder_start'] = ''
        sub_charenc = False
        if in_sub_buffer:
          try:
            in_sub_buffer.decode('utf-8')
          except:
            sub_charenc = True
        ffmpeg_env['mediabuilder_subcharenc'] = 'sub_charenc' if sub_charenc else ''
        self.FFmpeg_sub_process = subprocess.Popen(r'"%s\%s"' % (MediaProvider.SCRIPT_PATH, 'ffmpeg.bat'), env={**os.environ,**ffmpeg_env}, stdin=None if not in_sub_buffer else subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=6))
        out_sub_buffer[0] = self.FFmpeg_sub_process.communicate(input=None if not in_sub_buffer else in_sub_buffer, timeout=30)[0]
        if out_sub_buffer[0]:
          out_sub_buffer[1] = '.srt'
          break
      if self.shutdown_requested:
        break
      if ffmpeg_env['mediabuilder_mux'][-2] != '-' :
        ffmpeg_env['mediabuilder_mux'] = ffmpeg_env['mediabuilder_mux'] + '-'
      else:
        break
    return media_feed

  @classmethod
  def parse_playlist(cls, src, check=True, stop=None):
    if not mimetypes.inited:
      mimetypes.init()
    is_stop = lambda : False if stop == None else stop.is_set()
    get_p_t = lambda j: (j['url'], j.get('title', j['url']))
    sh_str = lambda s: s if len(s) <= cls.TITLE_MAX_LENGTH else s[:cls.TITLE_MAX_LENGTH] + '…'
    playlist = False
    titles = []
    if r'://' in src:
      playlist = '?'
      if '.' in src[-5:]:
        if ''.join(src.rpartition('.')[1:3]).lower() in ('.m3u', '.m3u8'):
          playlist = False
        else:
          media_mime = mimetypes.guess_type(src)[0]
          if (media_mime or '')[0:5] in ('video', 'audio', 'image'):
            playlist = False
      if playlist:
        playlist = '/playlist' in src.lower() or '/channels' in src.lower()
      if playlist:
        try:
          process_result = subprocess.run(r'"%s\%s" %s' % (cls.SCRIPT_PATH, 'youtube-dl.bat', 'playlist'), env={**os.environ, 'mediabuilder_url': '"%s"' % src, 'mediabuilder_profile': ''}, capture_output=True)
          if process_result.returncode == 0:
            try:
              p_t = list(get_p_t(json.loads(e)) for e in process_result.stdout.splitlines() if not is_stop())
            except:
              return (False, []) if check else ([src], [sh_str(src)])
            if not is_stop():
              playlist = (e[0] for e in p_t)
              titles = (sh_str(e[1]) for e in p_t)
              if '//www.youtube' in src.lower():
                playlist = (('https://www.youtube.com/watch?v=' if not 'http' in e.lower() else '') + e for e in playlist)
              elif '//vimeo' in src.lower():
                playlist = (('https://vimeo.com/' + ''.join(e.split('channels/')[1].split('/')[1:]) if 'channels/' in e else e) for e in playlist)
                titles = (html.unescape(t) for t in titles)
            if not is_stop():
              playlist = list(playlist)
              titles = list(titles)
            else:
              playlist = []
              titles = []
        except:
          playlist = []
          titles = []
        return playlist, titles
      else:
        return (False, []) if check else ([src], [sh_str(src)])
    elif os.path.isdir(src):
      numb_exp = lambda t: '.'.join([(t[0].rstrip('0123456789') + t[0][len(t[0].rstrip('0123456789')):].rjust(5,'0')) if ('0' <= t[0][-1:] and t[0][-1:] <= '9') else t[0]] + t[1:2])
      try:
        dirs = list(f.path for f in os.scandir(src) if not is_stop() and f.is_dir())
        dirs.sort(key=str.lower)
        dirs.sort(key=lambda f: numb_exp(f.lower().rsplit('.', 1)))
        if not is_stop():
          playlist = list(f.path for f in os.scandir(src) if not is_stop() and f.is_file() and not ''.join(f.path.rpartition('.')[1:3]).lower() in ('.m3u', '.m3u8', '.wpl'))
          playlist = list(e for e in playlist if not is_stop() and (mimetypes.guess_type(e)[0] or '')[0:5] in ('video', 'audio', 'image'))
          if playlist and not is_stop():
            playlist.sort(key=str.lower)
            playlist.sort(key=lambda f: numb_exp(f.lower().rsplit('.', 1)))
          if not is_stop():
            playlist = playlist + list(e for p in (MediaProvider.parse_playlist(d, False, stop)[0] for d in dirs) if not is_stop() for e in p)
        if is_stop():
          playlist = []
      except:
        playlist = []
      return playlist, list(map(sh_str, playlist))
    elif '.' in src[-4:] and src.rsplit('.',1)[-1].lower() == 'wpl':
      try:
        wpl = minidom.parse(src)
        playlist = list((os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(src)), e.getAttribute('src'))) if not '://' in e.getAttribute('src') else e.getAttribute('src')) for e in wpl.getElementsByTagName('media') if not is_stop())
      except:
        playlist = []
      if is_stop():
        playlist = []
      return playlist, list(map(sh_str, playlist))
    elif '.' in src[-5:] and src.rsplit('.',1)[-1].lower() in ('m3u8', 'm3u'):
      try:
        f = open(src, 'rt', encoding='utf-8' if src.rsplit('.',1)[-1].lower() == 'm3u8' else None)
        p_t = list(zip(*(MediaProvider.parse_playlist(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(src)), e.rstrip('\r\n'))) if not '://' in e else e.rstrip('\r\n'), False, stop) for e in f.readlines() if not is_stop() and e[:1] != '#' and e.rstrip('\r\n'))))
        if not is_stop():
          playlist = list(e for p in p_t[0] for e in p)
          titles = list(e for p in p_t[1] for e in p)
        f.close()
      except:
        playlist = []
      if is_stop():
        playlist = []
      return playlist, titles
    else:
      return (False, False) if check else ([src], [sh_str(src)])

  @classmethod
  def convert_to_smi(cls, MediaSubBuffer):
    if not MediaSubBuffer:
      return None
    if not MediaSubBuffer[0]:
      return None
    if len(MediaSubBuffer) >= 4:
      if MediaSubBuffer[3] == '.smi':
        if MediaSubBuffer[2]:
          return True
        else:
          return None
      else:
        MediaSubBuffer[2] = None
        MediaSubBuffer[3] = '.smi'
    else:
      MediaSubBuffer.extend([None] * (4 - len(MediaSubBuffer)))
      MediaSubBuffer[3] = '.smi'
    ffmpeg_env = {'mediabuilder_address': '-', 'mediabuilder_start': '', 'mediabuilder_mux': 'SRT', 'mediabuilder_profile': ''}
    ffmpeg_env['mediabuilder_sub'] = '-'
    ffmpeg_env['mediabuilder_lang'] = ''
    sub_charenc = False
    try:
      MediaSubBuffer[0].decode('utf-8')
    except:
      sub_charenc = True
    try:
      ffmpeg_env['mediabuilder_subcharenc'] = 'sub_charenc' if sub_charenc else ''
      FFmpeg_sub_process = subprocess.Popen(r'"%s\%s"' % (MediaProvider.SCRIPT_PATH, 'ffmpeg.bat'), env={**os.environ,**ffmpeg_env}, stdin=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=6))
      srt_sub_buffer = FFmpeg_sub_process.communicate(input=MediaSubBuffer[0], timeout=30)[0].decode('utf-8')
      if not srt_sub_buffer:
        return None
    except:
      return None
    smi_sub_buffer = \
    '<SAMI>\r\n' \
    '<HEAD>\r\n' \
    '  <STYLE TYPE="text/css">\r\n' \
    '    <!--\r\n' \
    '    P {\r\n' \
    '      background-color: black;\r\n' \
    '      color: white;\r\n' \
    '      margin-left: 1pt;\r\n' \
    '      margin-right: 1pt;\r\n' \
    '      margin-bottom: 2pt;\r\n' \
    '      margin-top: 2pt;\r\n' \
    '      text-align: center;\r\n' \
    '      font-size: 16pt;\r\n' \
    '      font-family: arial;\r\n' \
    '      font-weight: bold;\r\n' \
    '    }\r\n' \
    '    .CC {Name:default; lang: default;}\r\n' \
    '    -->\r\n' \
    '  </STYLE>\r\n' \
    '</HEAD>\r\n' \
    '<BODY>\r\n'
    bloc_ln = 0
    was_bl = True
    d_ms = 0
    f_ms = 0
    try:
      for ln in srt_sub_buffer.splitlines():
        l = ln.rstrip('\r\n')
        if l == '':
          was_bl = True
          if bloc_ln >= 2:
            smi_sub_buffer = smi_sub_buffer + '<br>'
          continue
        if bloc_ln == 0:
          if not l.strip().isdecimal():
            return None
          bloc_ln += 1
          was_bl = False
        elif was_bl and l.strip().isdecimal() and bloc_ln >= 2:
          bloc_ln = 1
          was_bl = False
          while smi_sub_buffer[-4:] == '<br>':
            smi_sub_buffer = smi_sub_buffer[:-4]
          smi_sub_buffer = smi_sub_buffer + '</SYNC>\r\n'
          smi_sub_buffer = smi_sub_buffer + '<SYNC start="%d"><P Class="CC"> </SYNC>\r\n' % f_ms
        elif bloc_ln == 1:
          d, f = l.split('-->')
          d = d.strip()
          f = f.strip()
          if ',' in d:
            d, d_ms = d.rsplit(',')
            d_ms = int(d_ms)
          else:
            d_ms = 0
          if ',' in f:
            f, f_ms = f.rsplit(',')
            f_ms = int(f_ms)
          else:
            f_ms = 0
          d_ms += sum(int(t[0])*t[1] for t in zip(reversed(d.split(':')), [1,60,3600])) * 1000
          f_ms += sum(int(t[0])*t[1] for t in zip(reversed(f.split(':')), [1,60,3600])) * 1000
          if d_ms > 0 and smi_sub_buffer[-8:-2] == '<BODY>':
            smi_sub_buffer = smi_sub_buffer + '<SYNC start="0"><P Class="CC"> </SYNC>\r\n'
          smi_sub_buffer = smi_sub_buffer + '<SYNC start="%d"><P Class="CC">' % d_ms
          bloc_ln += 1
          was_bl = False
        elif bloc_ln >= 2:
          smi_sub_buffer = smi_sub_buffer + l + '<br>'
          bloc_ln += 1
          was_bl = False
      while smi_sub_buffer[-4:] == '<br>':
        smi_sub_buffer = smi_sub_buffer[:-4]
      if '<SYNC' in smi_sub_buffer:
        smi_sub_buffer = smi_sub_buffer + '</SYNC>\r\n'
        smi_sub_buffer = smi_sub_buffer + '<SYNC start="%d"><P Class="CC"> </SYNC>\r\n' % f_ms
      smi_sub_buffer = smi_sub_buffer + '</BODY>\r\n</SAMI>'
    except:
      return None
    MediaSubBuffer[2] = smi_sub_buffer.encode('ansi')
    return True

  def MediaBuilder(self):
    if not self.MediaBuffer and self.ServerMode in (MediaProvider.SERVER_MODE_AUTO, MediaProvider.SERVER_MODE_SEQUENTIAL):
      return False
    if not mimetypes.inited:
      mimetypes.init()
    if not self.MediaSrcType:
      if r'://' in self.MediaSrc:
        self.MediaSrcType = 'WebPageURL'
        if '.' in self.MediaSrc[-5:]:
          media_mime = mimetypes.guess_type(self.MediaSrc)[0]
          if media_mime:
            if media_mime[0:5] in ('video', 'audio', 'image'):
              self.MediaSrcType = 'ContentURL'
      else:
        self.MediaSrcType = 'ContentPath'
    if self.MediaSubSrc and not self.MediaSubSrcType:
      sub_ext = (''.join(self.MediaSubSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubSrc else ''
      if r'://' in self.MediaSubSrc:
        if '?' in sub_ext:
          sub_ext = sub_ext.rpartition('?')[0]
        if sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt', '.m3u8'):
          self.MediaSubSrcType = 'ContentURL'
        else:
          self.MediaSubSrcType = 'WebPageURL'
      else:
        if os.path.isdir(self.MediaSubSrc):
          for sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt'):
            if os.path.exists(os.path.join(self.MediaSubSrc, os.path.splitext(os.path.basename(self.MediaSrc))[0]) + sub_ext):
              self.MediaSubSrc = os.path.join(self.MediaSubSrc, os.path.splitext(os.path.basename(self.MediaSrc))[0]) + sub_ext
              break
          if os.path.isdir(self.MediaSubSrc) and os.path.exists(os.path.join(self.MediaSubSrc, os.path.basename(self.MediaSrc))):
            self.MediaSubSrc = os.path.join(self.MediaSubSrc, os.path.basename(self.MediaSrc))    
        self.MediaSubSrcType = 'ContentPath'
    if self.MediaSrcType.lower() == 'ContentPath'.lower() and not self.MediaMuxAlways and self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL and self.MediaSubSrc == None and self.MediaSubBuffer:
      for sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt'):
        if os.path.exists(os.path.splitext(self.MediaSrc)[0] + sub_ext):
          self.MediaSubSrc = os.path.splitext(self.MediaSrc)[0] + sub_ext
          self.MediaSubSrcType = 'ContentPath'
          break
    if self.MediaSubSrc:
      MediaSubFeed = None
      sub_ext = None
      MediaSubBuffer = None
      if self.MediaSubSrcType.lower() == 'ContentPath'.lower():
        try:
          sub_ext = (''.join(self.MediaSubSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubSrc else ''
        except:
          pass
      elif self.MediaSubSrcType.lower() == 'ContentURL'.lower():
        try:
          MediaSubFeed = MediaProvider.open_url(self.MediaSubSrc)
          sub_ext = (''.join(MediaSubFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in MediaSubFeed.url else ''
          if '?' in sub_ext:
            sub_ext = sub_ext.rpartition('?')[0]
        except:
          pass
      elif self.MediaSubSrcType.lower() == 'WebPageURL'.lower():
        sub_url = None
        try:
          process_result = subprocess.run(r'"%s\%s" %s' % (MediaProvider.SCRIPT_PATH, 'youtube-dl.bat', 'sub'), env={**os.environ, 'mediabuilder_url': '"%s"' % (self.MediaSubSrc), 'mediabuilder_lang': '%s' % (self.MediaSubLang), 'mediabuilder_profile': self.MediaProcessProfile}, capture_output=True)
          if process_result.returncode == 0 and not self.shutdown_requested:
            process_output = json.loads(process_result.stdout)
            sub_url = list(process_output['requested_subtitles'].values())[0]['url']
        except:
          pass
        if not sub_url and not self.shutdown_requested:
          sub_lang = self.MediaSubLang.partition(',')[0].encode('utf-8') if self.MediaSubLang else b''
          try:
            rep = MediaProvider.open_url(self.MediaSubSrc)
            page = rep.read(1000000)
            rep.close()
            sub_url = None
            tracks = None
            try:
              tracks = (s.split(b'>')[0].split() for s in page.split(b'<track')[1:])
            except:
              pass
            if tracks:
              sub_url_lang = None
              sub_url_label = None
              for track in tracks:
                try:    
                  dic_track = {kv[0]:kv[1] for kv in (p.split(b'=') for p in track) if len(kv)==2}
                  if not sub_url:
                    sub_url = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                    if not sub_lang:
                      break
                  if sub_lang in dic_track.get(b'srclang','').lower():
                    sub_url_lang = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                    break
                  if sub_lang in dic_track.get(b'label','').lower():
                    if not sub_url_label:
                      sub_url_label = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                except:
                  pass
              if sub_url_lang:
                sub_url = sub_url_lang
              elif sub_url_label:
                sub_url = sub_url_label
              if sub_url:
                if not 'http' in sub_url[0:4].lower():
                  if sub_url[0] == '/':
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[0:3]) + sub_url
                  elif sub_url[0] == '../':
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[:-2]) + sub_url[2:]
                  else:
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[:-1] + [sub_url])
            if not sub_url and not self.shutdown_requested:
              tracks = None
              try:
                tracks_srt = (b'http' + s.split(b'http')[-1] + b'.srt' for s in page.split(b'.srt')[:-1] if b'http' in s)
                tracks_vtt = (b'http' + s.split(b'http')[-1] + b'.vtt' for s in page.split(b'.vtt')[:-1] if b'http' in s)
                tracks = list(track for track in tracks_srt if not b'\n' in track) + list(track for track in tracks_vtt if not b'\n' in track)
              except:
                pass
              if tracks:
                if sub_lang:
                  len_pos = list((len(track),track.lower().rfind(sub_lang)) for track in tracks)
                  ind = min(range(len(len_pos)), key=lambda i: len_pos[i][0]-len_pos[i][1] if len_pos[i][1] >=0 else 1000000)
                else:
                  ind = 0
                sub_url = html.unescape(tracks[ind].decode('utf-8'))
          except:
            pass
        if sub_url and not self.shutdown_requested:
          try:
            MediaSubFeed = MediaProvider.open_url(sub_url)
            sub_ext = (''.join(MediaSubFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in MediaSubFeed.url else ''
            if '?' in sub_ext:
              sub_ext = sub_ext.rpartition('?')[0]
          except:
            pass
      if MediaSubFeed:
        if not self.shutdown_requested:
          try:
            MediaSubBuffer = MediaSubFeed.read(1000000)
            if len(MediaSubBuffer) == 1000000:
              MediaSubBuffer = b''
          except:
            pass
        try:
          MediaSubFeed.close()
        except:
          pass
        MediaSubFeed = None
    if self.shutdown_requested:
      return None
    if self.MediaSrcType.lower() == 'ContentPath'.lower():
      if os.path.exists(self.MediaSrc):
        try:
          if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
            if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom):
              self.MediaFeed = self._open_FFmpeg(vid=self.MediaSrc)
              self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
            else:
              self.MediaFeed = open(self.MediaSrc, "rb")
              self.MediaFeedExt = (''.join(self.MediaSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSrc else ''
              self.MediaStartFrom = ''
          else:
            self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
            self.MediaFeed = self.MediaSrc
            self.MediaFeedExt = (''.join(self.MediaSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSrc else ''
            self.MediaSize = os.path.getsize(self.MediaSrc)
            self.AcceptRanges = True
          self.MediaTitle = self.MediaSrc.rsplit('\\', 1)[-1][:501]
        except:
          pass
    elif self.MediaSrcType.lower() == 'ContentURL'.lower():
      try:
        if self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL:
          rep = MediaProvider.open_url(self.MediaSrc, 'HEAD')
          self.MediaSize = int(rep.getheader('Content-Length', 0))
          if not self.MediaSize:
            try:
              self.MediaSize = int(rep.getheader('Content-Range', '').rpartition('/')[2])
            except:
              pass
          if rep.getheader('Accept-Ranges'):
            if rep.getheader('Accept-Ranges').lower() != 'none':
              self.AcceptRanges = True
            else:
              self.AcceptRanges = False
          elif rep.status == HTTPStatus.PARTIAL_CONTENT:
            self.AcceptRanges = True
          else:
            self.AcceptRanges = False
          if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
            if self.MediaSize:
              self.MediaFeed = rep.url
              self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
            if not self.AcceptRanges:
              self.MediaStartFrom = ''
          elif self.MediaSize and self.AcceptRanges:
            self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
            self.MediaFeed = rep.url
            self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
          else:
            self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
          rep.close()
        if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
          if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom):
            self.MediaFeed = self._open_FFmpeg(vid=self.MediaSrc)
            self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
          else:
            self.MediaFeed = MediaProvider.open_url(self.MediaSrc)
            self.MediaFeedExt = (''.join(self.MediaFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaFeed.url else ''
            self.MediaStartFrom = ''
        if self.MediaFeedExt:
          if '?' in self.MediaFeedExt:
            self.MediaFeedExt = self.MediaFeedExt.rpartition('?')[0]
        self.MediaTitle = self.MediaSrc.rsplit('/', 1)[-1][:501]
      except:
        pass
    elif self.MediaSrcType.lower() == 'WebPageURL'.lower():
      try:
        process_result = subprocess.run(r'"%s\%s" %s' % (MediaProvider.SCRIPT_PATH, 'youtube-dl.bat', 'mux' if self.MediaMuxAlways or self.ServerMode == MediaProvider.SERVER_MODE_AUTO else 'nomux'), env={**os.environ, 'mediabuilder_url': '"%s"' % (self.MediaSrc), 'mediabuilder_profile': self.MediaProcessProfile}, capture_output=True)
        if process_result.returncode == 0 and not self.shutdown_requested:
          process_output = process_result.stdout.splitlines()
          process_output.reverse()
          del process_output[0]
          if b'###PlayOn_Separator###' in process_output:
            del process_output[process_output.index(b'###PlayOn_Separator###'):]
          self.MediaTitle = process_output.pop(-1).decode('utf-8')[:501].replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
          if (self.MediaMuxAlways or self.ServerMode == MediaProvider.SERVER_MODE_AUTO) and len(process_output) == 2:
            self.MediaFeed = self._open_FFmpeg(vid=process_output[1].decode('utf-8'), aud=process_output[0].decode('utf-8'))
            self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
            self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
          elif len(process_output) == 1:
            if self.ServerMode == MediaProvider.SERVER_MODE_AUTO and self.MediaMuxContainer and (b'.m3u8' in process_output[0] or b'.mpd' in process_output[0]):
              self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
            if self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL:
              rep = MediaProvider.open_url(process_output[0].decode('utf-8'), 'HEAD')
              self.MediaSize = int(rep.getheader('Content-Length', 0))
              if not self.MediaSize:
                try:
                  self.MediaSize = int(rep.getheader('Content-Range', '').rpartition('/')[2])
                except:
                  pass
              if rep.getheader('Accept-Ranges'):
                if rep.getheader('Accept-Ranges').lower() != 'none':
                  self.AcceptRanges = True
                else:
                  self.AcceptRanges = False
              elif rep.status == HTTPStatus.PARTIAL_CONTENT:
                self.AcceptRanges = True
              else:
                self.AcceptRanges = False
              if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
                if self.MediaSize:
                  self.MediaFeed = rep.url
                  self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
                  if not self.AcceptRanges:
                    self.MediaStartFrom = ''
              elif self.MediaSize and self.AcceptRanges:
                self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
                self.MediaFeed = rep.url
                self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
              else:
                self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
              if not self.AcceptRanges:
                self.MediaStartFrom = ''
              rep.close()
            if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
              if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom or b'.m3u8' in process_output[0] or b'.mpd' in process_output[0]):
                self.MediaFeed = self._open_FFmpeg(vid=process_output[0].decode('utf-8'))
                self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
              else:
                self.MediaFeed = MediaProvider.open_url(process_output[0].decode('utf-8'))
                self.MediaFeedExt = (''.join(self.MediaFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubFeed.url else ''
                self.MediaStartFrom = ''
          if self.MediaFeedExt:
            if '?' in self.MediaFeedExt:
              self.MediaFeedExt = self.MediaFeedExt.rpartition('?')[0]
      except:
        pass
    if not self.shutdown_requested:
      if self.MediaFeed:
        self.logger.log(1, 'opening', self.MediaSrc, LSTRINGS['mediaprovider'].get(self.MediaSrcType.lower(), self.MediaSrcType), MediaProvider.SERVER_MODES[self.ServerMode], self.MediaTitle)
        if self.MediaFeedExt:
          media_mime = mimetypes.guess_type('f' + self.MediaFeedExt)[0]
          if media_mime:
            if not media_mime[0:5] in ('video', 'audio', 'image'):
              self.MediaFeedExt = ''
          else:
            self.MediaFeedExt = ''
        else:
          self.MediaFeedExt = ''
        if not self.MediaFeedExt and self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          if 'mp4' in self.MediaFeed.lower():
            self.MediaFeedExt = '.mp4'
        self.logger.log(2, 'extension', self.MediaSrc, self.MediaFeedExt)
        if self.MediaSubSrc:
          if self.MediaSubSrcType.lower() == 'ContentPath'.lower():
            try:
              if not os.path.isfile(self.MediaSubSrc):
                pass
              elif not sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass') or (self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and (self.MediaStartFrom or self.MediaMuxAlways)):
                if sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt'):
                  MediaSubFeed = open(self.MediaSubSrc, "rb")
                  MediaSubBuffer = MediaSubFeed.read(1000000)
                  MediaSubFeed.close()
                  if len(MediaSubBuffer) == 1000000:
                    MediaSubBuffer = b'' 
                  if MediaSubBuffer:
                    if sub_ext == '.vtt':
                      MediaSubBuffer = re.sub(b'((?<=\r) *\r\n?|(?<=\n) *(\r?\n|r)) *STYLE.*?(\r *(?=\r)|\n *(?=\r|\n))', b'', MediaSubBuffer, flags=re.DOTALL+re.IGNORECASE)
                    self._open_FFmpeg(sub='-', in_sub_buffer=MediaSubBuffer, out_sub_buffer=self.MediaSubBuffer)
                else:
                  self._open_FFmpeg(sub=self.MediaSubSrc, in_sub_buffer=None, out_sub_buffer=self.MediaSubBuffer)
              else:
                MediaSubFeed = open(self.MediaSubSrc, "rb")
                try:
                  self.MediaSubBuffer[0] = MediaSubFeed.read(1000000)
                  if len(self.MediaSubBuffer[0]) == 1000000:
                    self.MediaSubBuffer[0] = b''
                  else:
                    self.MediaSubBuffer[1] = sub_ext
                except:
                  pass
                try:
                  MediaSubFeed.close()
                except:
                  pass
              MediaSubFeed = None
            except:
              pass
          elif MediaSubBuffer:
            try:
              if not sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass') or (self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and (self.MediaStartFrom or self.MediaMuxAlways)):
                if sub_ext == '.vtt':
                  MediaSubBuffer = re.sub(b'((?<=\r) *\r\n?|(?<=\n) *(\r?\n|r)) *STYLE.*?(\r *(?=\r)|\n *(?=\r|\n))', b'', MediaSubBuffer, flags=re.DOTALL+re.IGNORECASE)
                self._open_FFmpeg(sub='-', in_sub_buffer=MediaSubBuffer, out_sub_buffer=self.MediaSubBuffer)
              else:
                self.MediaSubBuffer[0] = MediaSubBuffer
                self.MediaSubBuffer[1] = sub_ext
            except:
              pass
          if self.MediaSubBuffer[0]:
            self.logger.log(1, 'subopening', self.MediaSubSrc, LSTRINGS['mediaprovider'].get(self.MediaSubSrcType.lower(), self.MediaSubSrcType))
            self.logger.log(2, 'subextension', self.MediaSubBuffer[1])
          else:
            self.logger.log(0, 'subfailure', self.MediaSubSrc, LSTRINGS['mediaprovider'].get(self.MediaSubSrcType.lower(), self.MediaSubSrcType))
        return True
      else:
        self.logger.log(0, 'failure', self.MediaSrc, LSTRINGS['mediaprovider'].get(self.MediaSrcType.lower(), self.MediaSrcType))
        return False
    else:
      return None

  def MediaFeederS(self):
    if not self.MediaBuffer:
      return
    self.logger.log(1, 'loadstart')
    self.MediaBuffer.w_index = 1
    while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index > 0:
      while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index <= max(max(self.MediaBuffer.r_indexes, default=0), 1) + self.MediaBufferAhead:
        bloc = None
        try:
          bloc = self.MediaFeed.read(self.MediaBuffer.bloc_size)
        except:
          self.Status = MediaProvider.STATUS_ABORTED
          self.logger.log(1, 'segmentfailure', self.MediaBuffer.w_index)
        if not bloc:
          self.MediaBuffer.w_index = - abs(self.MediaBuffer.w_index)
          break
        else:
          self.MediaBuffer.content[(self.MediaBuffer.w_index - 1) % self.MediaBufferSize] = bloc
          self.logger.log(2, 'segmentbuffering', self.MediaBuffer.w_index, (self.MediaBuffer.w_index - 1) % self.MediaBufferSize)
          self.MediaBuffer.w_index += 1
          self.MediaBuffer.w_condition.acquire()
          self.MediaBuffer.w_condition.notify_all()
          self.MediaBuffer.w_condition.release()
      if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index > 0:
        self.MediaBuffer.r_event.wait()
        self.MediaBuffer.r_event.clear()
    if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.Status = MediaProvider.STATUS_COMPLETED
      self.logger.log(1, 'loadstop')
    else:
      self.logger.log(1, 'loadinterrupt')
    self.MediaBuffer.w_condition.acquire()
    self.MediaBuffer.w_condition.notify_all()
    self.MediaBuffer.w_condition.release()
    try:
      self.MediaFeed.close()
    except:
      pass

  def MediaFeederR(self):
    if not self.MediaSize:
      return
    self.logger.log(1, 'loadstart')
    header = {'User-Agent': 'Lavf'}
    header['Range'] = 'bytes=0-'
    header['Connection'] = 'keep-alive'
    rep = None
    try:
      url = urllib.parse.urlparse(self.MediaFeed)
      self.MediaSrcURL = self.MediaFeed[len(url.scheme) + 3 + len(url.netloc):]
      if url.scheme.lower() == 'http':
        self.Connection = client.HTTPConnection(url.netloc)
      elif url.scheme.lower() == 'https':
        self.Connection = client.HTTPSConnection(url.netloc)
      self.Connection.request('HEAD', self.MediaSrcURL, headers=header)
      rep = self.Connection.getresponse()
      self.Persistent = not rep.will_close
      self.logger.log(2, 'connection', self.MediaFeed, LSTRINGS['mediaprovider'].get('yes' if self.Persistent else 'no', self.Persistent), LSTRINGS['mediaprovider'].get('yes' if self.AcceptRanges else 'no', self.AcceptRanges))
    except:
      self.Status = MediaProvider.STATUS_ABORTED
    if rep:
      try:
        rep.read()
        rep.close()
      except:
        pass
    rep = None
    while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.MediaBuffer.create_lock.acquire()
      t_index = None
      r_index = None
      for ind in range(len(self.MediaBuffer.r_indexes) - 1, -1, -1):
        if self.MediaBuffer.r_indexes[ind] != 0:
          t_index = ind
          break
      self.MediaBuffer.create_lock.release()
      if t_index != None:
        if self.MediaBuffer.t_index != t_index:
          self.MediaBuffer.t_index = t_index
          self.logger.log(2, 'indexation', self.MediaBuffer.t_index + 1)
          self.MediaBuffer.w_condition.acquire()
          self.MediaBuffer.w_condition.notify_all()
          self.MediaBuffer.w_condition.release()
        r_index = self.MediaBuffer.r_indexes[t_index]
      elif self.MediaBuffer.t_index != None:
        self.MediaBuffer.t_index = None
        self.logger.log(2, 'deindexation')
      if r_index and (r_index -1) * self.MediaBuffer.bloc_size < self.MediaSize:
        if r_index < self.MediaBuffer.w_index or ((r_index if self.AcceptRanges else 1) > self.MediaBuffer.w_index + self.MediaBuffer.len):
          self.MediaBuffer.w_condition.acquire()
          if r_index < self.MediaBuffer.w_index:
            self.MediaBuffer.content = [None] * min(self.MediaBuffer.w_index - (r_index if self.AcceptRanges else 1), self.MediaBufferSize) + self.MediaBuffer.content[:(r_index if self.AcceptRanges else 1) - self.MediaBuffer.w_index]
          else:
            self.MediaBuffer.content = self.MediaBuffer.content[r_index - self.MediaBuffer.w_index:] + [None] * min(r_index - self.MediaBuffer.w_index, self.MediaBufferSize)
          self.MediaBuffer.w_index = r_index if self.AcceptRanges else 1
          self.MediaBuffer.len = 0
          self.MediaBuffer.w_condition.release()
          self.logger.log(2, 'translation', self.MediaBuffer.w_index)
          if rep:
            try:
              rep.close()
            except:
              pass
          rep = None
        if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index + self.MediaBuffer.len <= self.MediaBuffer.r_indexes[t_index] + self.MediaBufferAhead and (self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size < self.MediaSize:
          if self.MediaBuffer.len < self.MediaBufferSize:
            if self.MediaBuffer.content[self.MediaBuffer.len] and self.AcceptRanges and not rep:
              self.MediaBuffer.len += 1
              self.logger.log(2, 'present', self.MediaBuffer.w_index + self.MediaBuffer.len - 1, self.MediaBuffer.len)
              self.MediaBuffer.w_condition.acquire()
              self.MediaBuffer.w_condition.notify_all()
              self.MediaBuffer.w_condition.release()
              continue
          bloc = None
          try:
            header = {'User-Agent': 'Lavf'}
            if self.Persistent and self.AcceptRanges:
              header['Range'] = 'bytes=%d-%d' % ((self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size, min(self.MediaSize, (self.MediaBuffer.w_index + self.MediaBuffer.len) * self.MediaBuffer.bloc_size) - 1)
              header['Connection'] = 'keep-alive'
              self.Connection.request('GET', self.MediaSrcURL, headers=header)
              rep = self.Connection.getresponse()
              bloc = rep.read(self.MediaBuffer.bloc_size)
              rep.close()
              rep = None
            else:
              if rep == None:
                try:
                  self.Connection.close()
                except:
                  pass
                header = {'User-Agent': 'Lavf'}
                if self.AcceptRanges:
                  header['Range'] = 'bytes=%d-' % ((self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size)
                self.Connection.request('GET', self.MediaSrcURL, headers=header)
                rep = self.Connection.getresponse()
              bloc = rep.read(self.MediaBuffer.bloc_size)
          except:
            if self.Persistent and self.AcceptRanges:
              try:
                self.Connection.close()
                self.Connection.request('GET', self.MediaSrcURL, headers=header)
                rep = self.Connection.getresponse()
                bloc = rep.read(self.MediaBuffer.bloc_size)
                rep.close()
                rep = None
              except:
                pass
            elif self.AcceptRanges:
              try:
                self.Connection.close()
                header = {'User-Agent': 'Lavf'}
                header['Range'] = 'bytes=%d-' % ((self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size)
                self.Connection.request('GET', self.MediaSrcURL, headers=header)
                rep = self.Connection.getresponse()
                bloc = rep.read(self.MediaBuffer.bloc_size)
              except:
                pass
          if bloc:
            if len(bloc) != min(self.MediaSize, (self.MediaBuffer.w_index + self.MediaBuffer.len) * self.MediaBuffer.bloc_size) - (self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size:
              bloc = None
          if not bloc:
            self.Status = MediaProvider.STATUS_ABORTED
            self.logger.log(1, 'segmentfailure', self.MediaBuffer.w_index + self.MediaBuffer.len)
            try:
              self.Connection.close()
            except:
              pass
            if rep:
              try:
                rep.close()
              except:
                pass
            rep = None
            self.Connection = None
            break
          else:
            self.MediaBuffer.w_condition.acquire()
            if self.MediaBuffer.len < self.MediaBufferSize:
              self.MediaBuffer.content[self.MediaBuffer.len] = bloc
              self.MediaBuffer.len +=1
            else:
              self.MediaBuffer.w_index += 1
              del self.MediaBuffer.content[0]
              self.logger.log(2, 'translation', self.MediaBuffer.w_index)
              self.MediaBuffer.content += [bloc]
            self.logger.log(2, 'segmentbuffering', self.MediaBuffer.w_index + self.MediaBuffer.len - 1, self.MediaBuffer.len)
            self.MediaBuffer.w_condition.notify_all()
            self.MediaBuffer.w_condition.release()
        elif self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
          self.MediaBuffer.r_event.wait()
          self.MediaBuffer.r_event.clear()
      elif self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
        self.MediaBuffer.r_event.wait()
        self.MediaBuffer.r_event.clear()
    try:
      self.Connection.close()
    except:
      pass
    if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.Status = MediaProvider.STATUS_COMPLETED
      self.logger.log(1, 'loadstop')
    else:
      self.logger.log(1, 'loadinterrupt')
    self.MediaBuffer.t_index = -1
    self.MediaBuffer.w_condition.acquire()
    self.MediaBuffer.w_condition.notify_all()
    self.MediaBuffer.w_condition.release()

  def run(self):
    self.Status = MediaProvider.STATUS_INITIALIZING
    build_success = False
    if not self.shutdown_requested:
      build_success = self.MediaBuilder()
    if build_success and not self.shutdown_requested:
      if self.BuildFinishedEvent.is_set():
        self.Status = MediaProvider.STATUS_ABORTED
        return
      self.Status = MediaProvider.STATUS_RUNNING
      self.BuildFinishedEvent.set()
      if self.shutdown_requested:
        self.Status = MediaProvider.STATUS_ABORTED
        return
      if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
        self.MediaFeederS()
      elif self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
        if self.MediaSrcType.lower() in ('ContentURL'.lower(), 'WebPageURL'.lower()):
          self.MediaFeederR()
      else:
        self.Status = MediaProvider.STATUS_ABORTED
        self.BuildFinishedEvent.set()
    else:
      self.Status = MediaProvider.STATUS_ABORTED
      self.BuildFinishedEvent.set()

  def shutdown(self):
    self.shutdown_requested = True
    if self.FFmpeg_process:
      if self.FFmpeg_process.poll() == None:
        try:
          os.system('taskkill /t /f /pid %s >nul 2>&1' % (self.FFmpeg_process.pid))
        except:
          pass
    if self.FFmpeg_sub_process:
      if self.FFmpeg_sub_process.poll() == None:
        try:
          os.system('taskkill /t /f /pid %s >nul 2>&1' % (self.FFmpeg_process.pid))
        except:
          pass
    if self.Status == MediaProvider.STATUS_INITIALIZING:
      self.Status = MediaProvider.STATUS_ABORTED
    if self.Status == MediaProvider.STATUS_RUNNING:
      self.Status = MediaProvider.STATUS_ABORTED
      self.MediaBuffer.r_event.set()


class MediaRequestHandlerS(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"

  def __init__(self, *args, MediaBuffer, MediaSubBuffer, MediaExt, **kwargs):
    self.MediaBuffer = MediaBuffer
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
    else:
      self.MediaSubBuffer = None
    self.MediaExt = MediaExt
    super().__init__(*args, **kwargs)

  def log_message(self, *args, **kwargs):
    if self.server.logger.verbosity < 2:
      pass
    else:
      super().log_message(*args, **kwargs)

  def send_head(self):
    if self.server.auth_ip:
      if not self.client_address[0] in self.server.auth_ip:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized client")
        except:
          pass
        return False
    alt_sub = '/mediasub'
    if self.MediaSubBuffer:
      if self.MediaSubBuffer[1]:
        alt_sub = '/media' + self.MediaSubBuffer[1]
    if self.path.lower() in ('/media', '/media' + self.MediaExt):
      self.MediaBufferSize = len(self.MediaBuffer.content)
      self.MediaBuffer.create_lock.acquire()
      self.MediaBufferId = len(self.MediaBuffer.r_indexes)
      self.MediaBuffer.r_indexes.append(0)
      self.MediaBuffer.create_lock.release()
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
      self.send_header("Pragma", "no-cache")
      self.send_header("Accept-Ranges", "none")
      self.send_header("Transfer-Encoding", "chunked")
      if self.MediaSubBuffer:
        if self.MediaSubBuffer[0]:
          self.send_header("CaptionInfo.sec", r"http://%s:%s/mediasub%s" % (*self.server.server_address[:2], self.MediaSubBuffer[1]))
      try:
        self.end_headers()
      except:
        self.close_connection = True
        return False
      return 'media'
    elif (self.path.lower().rsplit(".", 1)[0] == '/mediasub' or self.path.lower() == alt_sub) and self.MediaSubBuffer:
      if not self.MediaSubBuffer[0]:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return False
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Cache-Control", "no-cache, must-revalidate")
      self.send_header("Pragma", "no-cache")
      self.send_header("Transfer-Encoding", "chunked")
      try:
        self.end_headers()
      except:
        self.close_connection = True
        return False
      return 'mediasub'
    elif self.path.lower() == '/media.smi' and self.MediaSubBuffer:
      sub_size = len(self.MediaSubBuffer[0])
      if sub_size > 0:
        try:
          if MediaProvider.convert_to_smi(self.MediaSubBuffer):
            sub_size = len(self.MediaSubBuffer[2])
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Transfer-Encoding", "chunked")
            try:
              self.end_headers()
            except:
              self.close_connection = True
              return False
            return 'mediasubsmi'
          else:
            sub_size = 0
        except:
          sub_size = 0
      if sub_size == 0:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return False
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      except:
        pass
      return False

  def do_GET(self):
    f = self.send_head()
    if f in ('media', 'mediasub', 'mediasubsmi'):
      try:
        self.copyfile(f, self.wfile)
      except:
        pass

  def do_HEAD(self):
    f = self.send_head()

  def copyfile(self, source, outputfile):
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set() or not source in ('media', 'mediasub', 'mediasubsmi'):
      self.close_connection = True
      try:
        outputfile.write(b"0\r\n\r\n")
      except:
        pass
      return
    if source in ('mediasub', 'mediasubsmi'):
      try:
        outputfile.write(hex(len(self.MediaSubBuffer[0] if source == 'mediasub' else self.MediaSubBuffer[2])).encode("ISO-8859-1")[2:] + b"\r\n" + (self.MediaSubBuffer[0] if source == 'mediasub' else self.MediaSubBuffer[2]) + b"\r\n")
        self.server.logger.log(2, 'subdelivery', *self.client_address)
      except:
        self.server.logger.log(1, 'subfailure', *self.client_address)
    else:
      self.server.logger.log(1, 'deliverystart', self.MediaBufferId + 1, *self.client_address)
      self.MediaBuffer.r_indexes[self.MediaBufferId] = 1
      while not self.MediaBuffer.r_indexes[self.MediaBufferId] == - self.MediaBuffer.w_index:
        self.MediaBuffer.w_condition.acquire()
        while self.MediaBuffer.r_indexes[self.MediaBufferId] == self.MediaBuffer.w_index:
          if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            break
          self.MediaBuffer.w_condition.wait()
        self.MediaBuffer.w_condition.release()
        if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if self.MediaBuffer.r_indexes[self.MediaBufferId] != - self.MediaBuffer.w_index:
          bloc = self.MediaBuffer.content[(self.MediaBuffer.r_indexes[self.MediaBufferId] -1) % self.MediaBufferSize]
          if self.MediaBuffer.r_indexes[self.MediaBufferId] <= abs(self.MediaBuffer.w_index) - self.MediaBufferSize:
            self.server.logger.log(2, 'exceeded', self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId], (self.MediaBuffer.r_indexes[self.MediaBufferId] - 1) % self.MediaBufferSize)
            self.server.logger.log(1, 'failure', self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId])
            break
          else:
            try:
              outputfile.write(hex(len(bloc)).encode("ISO-8859-1")[2:] + b"\r\n" + bloc + b"\r\n")
              self.server.logger.log(2, 'delivery1', self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId], (self.MediaBuffer.r_indexes[self.MediaBufferId] - 1) % self.MediaBufferSize)
              self.MediaBuffer.r_indexes[self.MediaBufferId] += 1
              self.MediaBuffer.r_event.set()
            except:
               self.server.logger.log(1, 'failure', self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId])
               break
      self.MediaBuffer.r_indexes[self.MediaBufferId] = - self.MediaBuffer.r_indexes[self.MediaBufferId]
      self.server.logger.log(1, 'deliverystop', self.MediaBufferId + 1)
    try:
      outputfile.write(b"0\r\n\r\n")
    except:
      pass
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      self.close_connection = True

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


class MediaRequestHandlerR(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"
  
  def __init__(self, *args, MediaBuffer, MediaSubBuffer, MediaSrc, MediaSrcType, MediaExt, MediaSize, AcceptRanges, **kwargs):
    self.MediaBuffer = MediaBuffer
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
    else:
      self.MediaSubBuffer = None
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaExt = MediaExt
    self.MediaSize = MediaSize
    self.AcceptRanges = AcceptRanges
    super().__init__(*args, **kwargs)

  def log_message(self, *args, **kwargs):
    if self.server.logger.verbosity < 2:
      pass
    else:
      super().log_message(*args, **kwargs)

  def send_head(self):
    if self.server.auth_ip:
      if not self.client_address[0] in self.server.auth_ip:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized client")
        except:
          pass
        return None, None, None
    alt_sub = '/mediasub'
    if self.MediaSubBuffer:
      if self.MediaSubBuffer[1]:
        alt_sub = '/media' + self.MediaSubBuffer[1]
    if self.path.lower() in ('/media', '/media' + self.MediaExt):
      bad_range = False
      req_range = self.headers.get('Range', "") if self.AcceptRanges else ""
      if req_range:
        try:
          req_start, req_end = map(str.strip, req_range.split(",")[0].split("=")[-1].split("-"))
          if not req_start:
            req_start = self.MediaSize - int(req_end)
            req_end = self.MediaSize
          else:
            req_start = int(req_start)
            if req_end:
              req_end = min(int(req_end) + 1, self.MediaSize)
            else:
              req_end = self.MediaSize
          if req_start >= req_end:
            raise
        except:
          req_start = None
          req_end = None
          bad_range = True
      else:
        req_start = None
        req_end = None
      if bad_range:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "Bad range request")
        except:
          pass
        return None, None, None
      if req_start == None:
        self.send_response(HTTPStatus.OK)
      else:
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Content-Length", str(self.MediaSize if req_start == None else req_end - req_start))
      self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
      self.send_header("Pragma", "no-cache")
      if self.AcceptRanges:
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("contentFeatures.dlna.org", "DLNA.ORG_PN=;DLNA.ORG_OP=01;DLNA.ORG_FLAGS=21700000000000000000000000000000")
      else:
        self.send_header("Accept-Ranges", "none")
        self.send_header("contentFeatures.dlna.org", "DLNA.ORG_PN=;DLNA.ORG_OP=00;DLNA.ORG_FLAGS=01700000000000000000000000000000")
      if req_start != None:
        self.send_header("Content-Range", "bytes %d-%d/%d" % (req_start, req_end - 1, self.MediaSize))
      if self.MediaSubBuffer:
        if self.MediaSubBuffer[0]:
          self.send_header("CaptionInfo.sec", r"http://%s:%s/mediasub%s" % (*self.server.server_address[:2], self.MediaSubBuffer[1]))
      return 'media', req_start or 0, req_end or self.MediaSize
    elif (self.path.lower().rsplit(".", 1)[0] == '/mediasub' or self.path.lower() == alt_sub) and self.MediaSubBuffer:
      sub_size = len(self.MediaSubBuffer[0])
      if sub_size == 0:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return None, None, None
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Content-Length", str(sub_size))
      self.send_header("Cache-Control", "no-cache, must-revalidate")
      self.send_header("Pragma", "no-cache")
      return 'mediasub', None, None
    elif self.path.lower() == '/media.smi' and self.MediaSubBuffer:
      sub_size = len(self.MediaSubBuffer[0])
      if sub_size > 0:
        try:
          if MediaProvider.convert_to_smi(self.MediaSubBuffer):
            sub_size = len(self.MediaSubBuffer[2])
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Length", str(sub_size))
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            return 'mediasubsmi', None, None
          else:
            sub_size = 0
        except:
          sub_size = 0
      if sub_size == 0:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return None, None, None
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
      except:
        pass
      return None, None, None

  def do_GET(self):
    source, req_start, req_end = self.send_head()
    if source in ('media', 'mediasub', 'mediasubsmi'):
      try:
        self.copyfile(source, req_start, req_end, self.wfile)
      except:
        pass

  def do_HEAD(self):
    source, req_start, req_end = self.send_head()
    try:
      self.end_headers()
    except:
      self.close_connection = True

  def copyfile(self, source, req_start, req_end, outputfile):
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set() or not source in ('media', 'mediasub', 'mediasubsmi'):
      self.close_connection = True
      return
    f = None
    if source == 'media':
      if self.MediaSrcType == 'ContentPath':
        self.MediaBuffer.create_lock.acquire()
        self.MediaBufferId = len(self.MediaBuffer.r_indexes)
        self.MediaBuffer.r_indexes.append(0)
        self.MediaBuffer.create_lock.release()
        self.server.logger.log(1, 'deliverystart', self.MediaBufferId + 1, *self.client_address)
        try:
          f = open(self.MediaSrc, 'rb')
          if req_start:
            f.seek(req_start)
          self.end_headers()
        except:
          self.close_connection = True
          self.server.logger.log(1, 'deliveryfailure', self.MediaBufferId + 1)
          try:
            f.close()
          except:
            pass
          return
        try:
          index = req_start
          while not self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            if index < req_end:
              bloc = None
              bloc = f.read(min(self.MediaBuffer.bloc_size, req_end - index))
              outputfile.write(bloc)
              self.server.logger.log(2, 'delivery2', self.MediaBufferId + 1, index)
              index = index + min(self.MediaBuffer.bloc_size, req_end - index)
            else:
              break
        except:
          index = -1
          self.close_connection = True
        try:
          f.close()
        except:
          pass
        if index < 0:
          self.server.logger.log(1, 'deliveryfailure', self.MediaBufferId + 1)
        else:
          self.server.logger.log(1, 'deliverystop', self.MediaBufferId + 1)
      elif self.MediaSrcType in ('ContentURL', 'WebPageURL'):
        self.MediaBuffer.create_lock.acquire()
        self.MediaBufferId = len(self.MediaBuffer.r_indexes)
        r_index = req_start // self.MediaBuffer.bloc_size + 1
        self.MediaBuffer.r_indexes.append(r_index)
        self.MediaBuffer.create_lock.release()
        self.MediaBuffer.r_event.set()
        bloc = None
        first_loop = True
        self.server.logger.log(1, 'deliverystart', self.MediaBufferId + 1, *self.client_address)
        while not self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          self.MediaBuffer.w_condition.acquire()
          while r_index < self.MediaBuffer.w_index or r_index >= self.MediaBuffer.w_index + self.MediaBuffer.len - (1 if first_loop and r_index * self.MediaBuffer.bloc_size < req_end else 0):
            if self.MediaBufferId < (self.MediaBuffer.t_index if self.MediaBuffer.t_index !=None else 0) and r_index != self.MediaBuffer.w_index + self.MediaBuffer.len:
              self.server.logger.log(2, 'expulsion', self.MediaBufferId + 1, r_index)  
              r_index = 0
              break
            if self.MediaBuffer.t_index == -1:
              r_index = 0
              break
            if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
              break
            self.MediaBuffer.w_condition.wait()
          if r_index == 0 or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            self.MediaBuffer.w_condition.release()
            break
          if r_index >= self.MediaBuffer.w_index and r_index < self.MediaBuffer.w_index + self.MediaBuffer.len:
            bloc = self.MediaBuffer.content[(r_index - self.MediaBuffer.w_index)][(0 if not first_loop else req_start % self.MediaBuffer.bloc_size):]
          self.MediaBuffer.w_condition.release()
          if not bloc:
            r_index = 0
            break
          try:
            if first_loop:
              self.end_headers()
              first_loop = False
            if r_index * self.MediaBuffer.bloc_size >= req_end:
              outputfile.write(bloc[:(req_end - 1) % self.MediaBuffer.bloc_size + 1])
            else:
              self.MediaBuffer.r_indexes[self.MediaBufferId] += 1
              self.MediaBuffer.r_event.set()
              outputfile.write(bloc)
            self.server.logger.log(2, 'delivery3', self.MediaBufferId + 1, r_index)
            r_index += 1
          except:
            r_index = 0
            break
          if (r_index - 1) * self.MediaBuffer.bloc_size >= req_end:
            break
        if r_index == 0:
          self.server.logger.log(1, 'failure', self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId])
          self.close_connection = True
          if first_loop and not self.server.__dict__['_BaseServer__is_shut_down']:
            try:
              self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
            except:
              pass
        else:
          r_index = 0
          self.server.logger.log(1, 'deliverystop', self.MediaBufferId + 1)
        self.MediaBuffer.r_indexes[self.MediaBufferId] = 0
        self.MediaBuffer.r_event.set()
    elif source in ('mediasub', 'mediasubsmi'):
      try:
        self.end_headers()
      except:
        self.close_connection = True
        self.server.logger.log(1, 'subfailure', *self.client_address)
        return
      self.server.logger.log(2, 'subdelivery', *self.client_address)
      try:
        outputfile.write(self.MediaSubBuffer[0] if source == 'mediasub' else self.MediaSubBuffer[2])
      except:
        self.close_connection = True
        self.server.logger.log(1, 'subfailure', *self.client_address)
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
      except:
        pass
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      self.close_connection = True

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


class MediaServer(threading.Thread):

  MediaBufferBlocSize = 1024 * 1024

  def __init__(self, MediaServerMode, MediaServerAddress, MediaSrc, MediaSrcType=None, MediaStartFrom=0, MediaBufferSize=75, MediaBufferAhead=25, MediaMuxContainer=None, MediaSubSrc=None, MediaSubSrcType=None, MediaSubLang=None, MediaSubBuffer=None, MediaProcessProfile=None, verbosity=0, auth_ip=None):
    threading.Thread.__init__(self)
    self.verbosity = verbosity
    self.auth_ip = auth_ip
    self.logger = log_event('mediaserver', verbosity)
    self.MediaServerMode = MediaServerMode
    self.MediaServerAddress = MediaServerAddress
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaStartFrom = MediaStartFrom
    self.MediaBufferAhead = MediaBufferAhead
    self.MediaBufferSize = max(MediaBufferSize, self.MediaBufferAhead + 2)
    self.MediaMuxContainer = MediaMuxContainer
    self.MediaBufferInstance = MediaBuffer(self.MediaBufferSize, MediaServer.MediaBufferBlocSize)
    self.MediaSubSrc = MediaSubSrc
    self.MediaSubSrcType = MediaSubSrcType
    self.MediaSubLang = MediaSubLang
    if MediaSubBuffer:
      if len(MediaSubBuffer) >= 2:
        self.MediaSubBufferInstance = MediaSubBuffer
      else:
        self.MediaSubBufferInstance = [b'', '']
    else:
      self.MediaSubBufferInstance = [b'', '']
    self.MediaProcessProfile = MediaProcessProfile
    self.is_running = None
    self.BuildFinishedEvent = threading.Event()
    self.MediaServerFinishedEvent = threading.Event()
    self.shut_lock = threading.Lock()

  def run(self):
    self.shut_lock.acquire()
    if self.is_running is not None:
      self.shut_lock.release()
      return
    self.is_running = True
    slr = False
    self.MediaProviderInstance = MediaProvider(self.MediaServerMode, self.MediaSrc, self.MediaSrcType, self.MediaStartFrom, self.MediaBufferInstance, self.MediaBufferAhead, self.MediaMuxContainer, self.MediaSubSrc, self.MediaSubSrcType, self.MediaSubLang, self.MediaSubBufferInstance, self.MediaProcessProfile, self.MediaServerAddress[1]+1, self.BuildFinishedEvent, self.verbosity)
    self.MediaProviderInstance.start()
    self.BuildFinishedEvent.wait()
    if self.is_running and self.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED):
      if self.MediaProviderInstance.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
        self.MediaRequestBoundHandler = partial(MediaRequestHandlerS, MediaBuffer=self.MediaBufferInstance, MediaSubBuffer=self.MediaSubBufferInstance, MediaExt=self.MediaProviderInstance.MediaFeedExt)
      elif self.MediaProviderInstance.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
        self.MediaRequestBoundHandler = partial(MediaRequestHandlerR, MediaBuffer=self.MediaBufferInstance, MediaSubBuffer=self.MediaSubBufferInstance, MediaSrc=self.MediaProviderInstance.MediaSrc, MediaSrcType=self.MediaProviderInstance.MediaSrcType, MediaExt=self.MediaProviderInstance.MediaFeedExt, MediaSize=self.MediaProviderInstance.MediaSize, AcceptRanges=self.MediaProviderInstance.AcceptRanges)
      else:
        self.is_running = False
    else:
      self.is_running = False
    if self.is_running:
      try:
        with ThreadedDualStackServer(self.MediaServerAddress, self.MediaRequestBoundHandler, kmod='mediaserver', verbosity=self.verbosity, auth_ip=self.auth_ip) as self.MediaServerInstance:
          if self.is_running:
            self.logger.log(1, 'start', self.MediaServerAddress[0], LSTRINGS['mediaserver'].get({MediaProvider.SERVER_MODE_SEQUENTIAL: 'sequential', MediaProvider.SERVER_MODE_RANDOM: 'random'}.get(self.MediaProviderInstance.ServerMode, ''), ''), '' if self.MediaProviderInstance.ServerMode==MediaProvider.SERVER_MODE_SEQUENTIAL else ('' if self.MediaProviderInstance.AcceptRanges else LSTRINGS['mediaserver'].get('unsupported', 'unsupported')))
            self.MediaServerFinishedEvent.set()
            self.shut_lock.release()
            slr = True
            self.MediaServerInstance.serve_forever()
      except:
        pass
    if not slr:
      try:
        self.MediaProviderInstance.shutdown()
      except:
        pass
      self.shut_lock.release()
    self.MediaServerFinishedEvent.set()
    self.is_running = False

  def ready(self):
    if self.MediaServerFinishedEvent.is_set():
      try:
        return self.is_running == True and self.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED) and hasattr(self, 'MediaServerInstance')
      except:
        return False
    else:
      return False

  def wait(self, InterruptSetter=None):
    if InterruptSetter is not None:
      InterruptSetter(self.BuildFinishedEvent)
    self.BuildFinishedEvent.wait()
    if self.is_running and self.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED):
      if InterruptSetter is not None:
        InterruptSetter(self.MediaServerFinishedEvent)
      self.MediaServerFinishedEvent.wait()
      return self.ready()
    else:
      return False

  def shutdown(self):
    self.BuildFinishedEvent.set()
    with self.shut_lock:
      if not self.is_running:
        self.is_running = False
        return
      self.is_running = False
    try:
      self.MediaProviderInstance.shutdown()
    except:
      pass
    try:
      self.MediaServerInstance.shutdown()
      self.logger.log(1, 'shutdown')
      for sock in self.MediaServerInstance.conn_sockets:
        try:
          sock.shutdown(socket.SHUT_RDWR)
        except:
          pass
    except:
      pass
    self.MediaBufferInstance.r_event.set()
    self.MediaBufferInstance.w_condition.acquire()
    self.MediaBufferInstance.w_condition.notify_all()
    self.MediaBufferInstance.w_condition.release()


def _XMLGetNodeText(node):
  text = []
  for childNode in node.childNodes:
    if childNode.nodeType == node.TEXT_NODE:
      text.append(childNode.data)
  return(''.join(text))

def _XMLGetRTagElements(node, tag):
  return node.getElementsByTagNameNS('urn:schemas-upnp-org:device-1-0', tag) or node.getElementsByTagNameNS('*', tag)

def _XMLGetSTagElements(node, tag):
  return node.getElementsByTagNameNS('urn:schemas-upnp-org:service-1-0', tag) or node.getElementsByTagNameNS('*', tag)

def _XMLGetRTagText(node, tag):
  return _XMLGetNodeText(_XMLGetRTagElements(node, tag)[0])

def _XMLGetSTagText(node, tag):
  return _XMLGetNodeText(_XMLGetSTagElements(node, tag)[0])


class HTTPExplodedMessage:

  __slots__ = ('method', 'path', 'version', 'code', 'message', 'headers', 'body', 'expect_close')

  def __init__(self):
    self.method = self.path = self.version = self.code = self.message = self.body = self.expect_close = None
    self.headers = {}

  def __bool__(self):
    return self.method is not None or self.code is not None

  def clear(self):
    self.__init__()
    return self

  def header(self, name, default=None):
    return self.headers.get(name.title(), default)

  def in_header(self, name, value):
    h = self.header(name)
    return False if h is None else (value.lower() in map(str.strip, h.lower().split(',')))

  def __repr__(self):
    if self:
      try:
        return '\r\n'.join(('<HTTPExplodedMessage at %#x>\r\n----------' % id(self), (' '.join(filter(None, (self.method, self.path, self.version, self.code, self.message)))), *map(': '.join, self.headers.items()), '----------\r\nLength of body: %s byte(s)' % len(self.body or ''), '----------\r\nClose expected: %s' % self.expect_close))
      except:
        return '<HTTPExplodedMessage at %#x>\r\n<corrupted object>' % id(self)
    else:
      return '<HTTPExplodedMessage at %#x>\r\n<no message>' % id(self)


class HTTPMessage:

  @staticmethod
  def _read_headers(msg, http_message):
    if not msg:
      return False
    a = None
    for msg_line in msg.replace('\r\n', '\n').split('\n')[:-2]:
      if a is None:
        try:
          a, b, c = msg_line.strip().split(None, 2)
        except:
          try:
            a, b, c = *msg_line.strip().split(None, 2), ''
          except:
            return False
      else:
        try:
          header_name, header_value = msg_line.split(':', 1)
        except:
          return False
        header_name = header_name.strip().title()
        if header_name:
          header_value = header_value.strip()
          if not header_name in ('Content-Length', 'Location', 'Host') and http_message.headers.get(header_name):
            if header_value:
              http_message.headers[header_name] += ', ' + header_value
          else:
            http_message.headers[header_name] = header_value
        else:
          return False
    if a is None:
      return False
    if a[:4].upper() == 'HTTP':
      http_message.version = a.upper()
      http_message.code = b
      http_message.message = c
    else:
      http_message.method = a.upper()
      http_message.path = b
      http_message.version = c.upper()
    http_message.expect_close = http_message.in_header('Connection', 'close') or (http_message.version.upper() != 'HTTP/1.1' and not http_message.in_header('Connection', 'keep-alive'))
    return True

  @staticmethod
  def _read(message, max_data, start_time, max_time, stop):
    is_stop = lambda : False if stop == None else stop.is_set()
    start_read_time = time.time()
    with selectors.DefaultSelector() as selector:
      selector.register(message, selectors.EVENT_READ)
      ready = False
      rem_time = 0.5
      while not ready and not is_stop():
        t = time.time()
        if message.timeout:
          rem_time = min(rem_time, message.timeout - t + start_read_time)
        if max_time:
          rem_time = min(rem_time, max_time - t + start_time)
        if rem_time <= 0:
          return None
        if hasattr(message, 'pending'):
          if message.pending():
            ready = True
          else:
            ready = selector.select(rem_time)
        else:
          ready = selector.select(rem_time)
        if ready:
          try:
            return message.recv(min(max_data, 1048576))
          except:
            return None
    return None

  def __new__(cls, message=None, body=True, decode='utf-8', timeout=5, max_length=1048576, max_hlength=1048576, max_time=None, stop=None):
    http_message = HTTPExplodedMessage()
    if message is None:
      return http_message
    start_time = time.time()
    max_hlength = min(max_length, max_hlength)
    rem_length = max_hlength
    iss = isinstance(message, socket.socket)
    if not iss:
      msg = message[0]
    else:
      message.settimeout(None if max_time else timeout)
      msg = b''
    while True:
      msg = msg.lstrip(b'\r\n')
      body_pos = msg.find(b'\r\n\r\n')
      if body_pos >= 0:
        body_pos += 4
        break
      body_pos = msg.find(b'\n\n')
      if body_pos >= 0:
        body_pos += 2
        break
      if not iss or rem_length <= 0:
        return http_message
      try:
        bloc = cls._read(message, rem_length, start_time, max_time, stop)
        if not bloc:
          return http_message
      except:
        return http_message
      rem_length -= len(bloc)
      msg = msg + bloc
    if not cls._read_headers(msg[:body_pos].decode('ISO-8859-1'), http_message):
      return http_message.clear()
    if not iss:
      http_message.expect_close = True
    if http_message.code in ('100', '101', '204', '304'):
      http_message.body = b''
      return http_message
    if not body:
      http_message.body = msg[body_pos:]
      return http_message
    rem_length += max_length - max_hlength
    chunked = http_message.in_header('Transfer-Encoding', 'chunked')
    if chunked:
      body_len = -1
    else:
      body_len = http_message.header('Content-Length')
      if body_len is None:
        if not iss or (http_message.code in ('200', '206') and http_message.expect_close):
          body_len = -1
        else:
          body_len = 0
      else:
        try:
          body_len = max(0, int(body_len))
        except:
          return http_message.clear()
    if http_message.in_header('Expect', '100-continue') and iss:
      if max_time:
        message.settimeout(timeout)
      try:
        if body_pos + body_len - len(msg) <= rem_length:
          message.sendall('HTTP/1.1 100 Continue\r\n\r\n'.encode('ISO-8859-1'))
        else:
          message.sendall(('HTTP/1.1 413 Payload too large\r\nContent-Length: 0\r\nDate: %s\r\nCache-Control: no-cache, no-store, must-revalidate\r\n\r\n' % email.utils.formatdate(time.time(), usegmt=True)).encode('ISO-8859-1'))
          return http_message.clear()
      except:
        return http_message.clear()
      finally:
        if max_time:
          message.settimeout(None)
    if not chunked:
      if body_len < 0:
        if not iss:
          http_message.body = msg[body_pos:]
        else:
          bbuf = BytesIO()
          rem_length -= bbuf.write(msg[body_pos:])
          while rem_length > 0:
            try:
              bw = bbuf.write(cls._read(message, rem_length, start_time, max_time, stop))
              if not bw:
                break
              rem_length -= bw
            except:
              return http_message.clear()
          if rem_length <= 0:
            return http_message.clear()
          http_message.body = bbuf.getvalue()
      elif len(msg) < body_pos + body_len:
        if not iss or body_pos + body_len - len(msg) > rem_length:
          return http_message.clear()
        bbuf = BytesIO()
        body_len -= bbuf.write(msg[body_pos:])
        while body_len:
          try:
            bw = bbuf.write(cls._read(message, body_len, start_time, max_time, stop))
            if not bw:
              return http_message.clear()
            body_len -= bw
          except:
            return http_message.clear()
        http_message.body = bbuf.getvalue()
      else:
        http_message.body = msg[body_pos:body_pos+body_len]
    else:
      bbuf = BytesIO()
      buff = msg[body_pos:]
      while True:
        chunk_pos = -1
        rem_slength = max_hlength - len(buff)
        while chunk_pos < 0:
          buff = buff.lstrip(b'\r\n')
          chunk_pos = buff.find(b'\r\n')
          if chunk_pos >= 0:
            chunk_pos += 2
            break
          chunk_pos = buff.find(b'\n')
          if chunk_pos >= 0:
            chunk_pos += 1
            break
          if not iss or rem_slength <= 0 or rem_length <= 0:
            return http_message.clear()
          try:
            bloc = cls._read(message, min(rem_length, rem_slength), start_time, max_time, stop)
            if not bloc:
              return http_message.clear()
          except:
            return http_message.clear()
          rem_length -= len(bloc)
          rem_slength -= len(bloc)
          buff = buff + bloc
        try:
          chunk_len = int(buff[:chunk_pos].split(b';', 1)[0].rstrip(b'\r\n'), 16)
          if not chunk_len:
            break
        except:
          return http_message.clear()
        if chunk_pos + chunk_len - len(buff) > rem_length:
          return http_message.clear()
        if len(buff) < chunk_pos + chunk_len:
          if not iss:
            return http_message.clear()
          chunk_len -= bbuf.write(buff[chunk_pos:])
          while chunk_len:
            try:
              bw = bbuf.write(cls._read(message, chunk_len, start_time, max_time, stop))
              if not bw:
                return http_message.clear()
              chunk_len -= bw
            except:
              return http_message.clear()
            rem_length -= bw
          buff = b''
        else:
          bbuf.write(buff[chunk_pos:chunk_pos+chunk_len])
          buff = buff[chunk_pos+chunk_len:]
      http_message.body = bbuf.getvalue()
      rem_length = min(rem_length, max_hlength - body_pos - len(buff) + chunk_pos)
      while not (b'\r\n\r\n' in buff or b'\n\n' in buff):
        if not iss or rem_length <= 0:
          return http_message.clear()
        try:
          bloc = cls._read(message, rem_length, start_time, max_time, stop)
          if not bloc:
            return http_message.clear()
        except:
          return http_message.clear()
        rem_length -= len(bloc)
        buff = buff + bloc
    if http_message.body:
      try:
        if decode:
          http_message.body = http_message.body.decode(decode)
      except:
        return http_message.clear()
    return http_message


class HTTPRequest:

  SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
  SSLContext.check_hostname = False
  SSLContext.verify_mode = ssl.CERT_NONE
  RequestPattern = \
    '%s %s HTTP/1.1\r\n' \
    'Host: %s\r\n%s' \
    '\r\n'

  def __new__(cls, url, method=None, headers=None, data=None, timeout=3, max_length=1048576, max_hlength=1048576, max_time=None, stop=None, pconnection=None, ip=''):
    if url is None:
      return HTTPMessage()
    is_stop = lambda : False if stop == None else stop.is_set()
    if method is None:
      method = 'GET' if data is None else 'POST'
    redir = 0
    try:
      url_p = urllib.parse.urlsplit(url, allow_fragments=False)
      if headers is None:
        headers = {}
      hitems = headers.items()
      if pconnection is None:
        pconnection = [None]
        hccl = True
      else:
        hccl = 'close' in (e.strip() for k, v in hitems if k.lower() == 'connection' for e in v.lower().split(','))
      headers = {k: v for k, v in hitems if not k.lower() in ('host', 'content-length', 'connection', 'expect')}
      if not 'accept-encoding' in (k.lower() for k, v in hitems):
        headers['Accept-Encoding'] = 'identity'
      if data is not None:
        if not 'chunked' in (e.strip() for k, v in hitems if k.lower() == 'transfer-encoding' for e in v.lower().split(',')):
          headers['Content-Length'] = str(len(data))
      headers['Connection'] = 'close' if hccl else 'keep-alive'
    except:
      return HTTPMessage()
    if max_time:
      start_time = time.time()
    while True:
      try:
        if max_time:
          if time.time() - start_time > max_time:
            raise
        if is_stop():
          raise
        if pconnection[0] is None:
          if url_p.scheme.lower() == 'http':
            pconnection[0] = socket.create_connection((url_p.netloc + ':80').split(':', 2)[:2], timeout=timeout, source_address=(ip, 0))
          elif url_p.scheme.lower() == 'https':
            pconnection[0] = cls.SSLContext.wrap_socket(socket.create_connection((url_p.netloc + ':443').split(':', 2)[:2], timeout=timeout, source_address=(ip, 0)), server_side=False, server_hostname=url_p.netloc.split(':')[0])
          else:
            raise
        else:
          try:
            pconnection[0].settimeout(timeout)
          except:
            pass
        if max_time:
          if time.time() - start_time > max_time:
            raise
        if is_stop():
          raise
        msg = cls.RequestPattern % (method, (url_p.path + ('?' + url_p.query if url_p.query else '')).replace(' ', '%20') or '/', url_p.netloc, ''.join(k + ': ' + v + '\r\n' for k, v in headers.items()))
        pconnection[0].sendall(msg.encode('iso-8859-1') + (data or b''))
        code = '100'
        while code == '100':
          if max_time:
            rem_time = max_time - time.time() + start_time
            if rem_time <= 0:
              raise
          if is_stop():
            raise
          resp = HTTPMessage(pconnection[0], body=(method.upper() != 'HEAD'), decode=None, timeout=timeout, max_length=max_length, max_time=(rem_time if max_time else None), stop=stop)
          code = resp.code
          if code == '100':
            redir += 1
            if redir > 5:
              raise
        if code is None:
          raise
        if code[:2] == '30' and code != '304':
          if resp.header('location'):
            url = urllib.parse.urljoin(url, resp.header('location'))
            urlo_p = url_p
            url_p = urllib.parse.urlsplit(url, allow_fragments=False)
            if headers['Connection'] == 'close' or resp.expect_close or (urlo_p.scheme != url_p.scheme or urlo_p.netloc != url_p.netloc):
              try:
                pconnection[0].close()
              except:
                pass
              pconnection[0] = None
              headers['Connection'] = 'close'
            redir += 1
            if redir > 5:
              raise
            if code == '303':
              if method.upper() != 'HEAD':
                method = 'GET'
              data = None
              for k in list(headers.keys()):
                if k.lower() in ('transfer-encoding', 'content-length', 'content-type'):
                  del headers[k]
          else:
            raise
        else:
          break
      except:
        try:
          pconnection[0].close()
        except:
          pass
        pconnection[0] = None
        return HTTPMessage()
    if headers['Connection'] == 'close' or resp.expect_close:
      try:
        pconnection[0].close()
      except:
        pass
      pconnection[0] = None
    return resp


class DLNAArgument:

  def __init__(self):
    self.Name = None
    self.Direction = None
    self.Event = None
    self.Type = None
    self.AllowedValueList = None
    self.AllowedValueRange = None
    self.DefaultValue = None


class DLNAAction:

  def __init__(self):
    self.Name = None
    self.Arguments = []


class DLNAService:

  def __init__(self):
    self.Type = None
    self.Id = None
    self.ControlURL = None
    self.SubscrEventURL = None
    self.DescURL = None
    self.Actions = []
    self.EventThroughLastChange = None


class DLNADevice:

  DEVICE_TYPE = 'Device'

  def __init__(self):
    self.DescURL = None
    self.BaseURL = None
    self.Ip = None
    self.Manufacturer = None
    self.ModelName = None
    self.FriendlyName = None
    self.ModelDesc = None
    self.ModelNumber = None
    self.SerialNumber = None
    self.UDN = None
    self.IconURL = None
    self.Services = []
    self.StatusAlive = None
    self.StatusTime = None
    self.StatusAliveLastTime = None


class DLNARenderer(DLNADevice):

  DEVICE_TYPE = 'Renderer'


class DLNAServer(DLNADevice):

  DEVICE_TYPE = 'Server'


class DLNAEvent:

  def __init__(self):
    self.ReceiptTime = None
    self.Changes = []


class DLNAEventWarning:

  def __init__(self, event_listener, prop_name, *warn_values, WarningEvent=None):
    self.EventListener = event_listener
    self.WatchedProperty = prop_name
    self.WarningEvent = WarningEvent
    self.WatchedValues = warn_values or None
    self.Triggered = None
    self.TriggerSEQ = None
    self.TriggerLastValue = None
    self.lock = threading.RLock()

  def clear(self):
    with self.lock:
      self.TriggerLastValue = None
      self.TriggerSEQ = self.EventListener.CurrentSEQ
      self.Triggered = None

  def submit(self, seq, prop_name, prop_nvalue):
    if prop_name == self.WatchedProperty:
      with self.lock:
        warn_update = True if (self.TriggerSEQ is None) else (self.TriggerSEQ < seq)
        if warn_update and self.WatchedValues:
          warn_update = prop_nvalue in self.WatchedValues
        if warn_update:
          self.TriggerLastValue = prop_nvalue
          self.TriggerSEQ = seq
          self.Triggered = True
          if self.WarningEvent is not None:
            self.WarningEvent.set()
          return True
    return False

  def fresh(self):
    with self.lock:
      if self.Triggered:
        self.Triggered = False
        return self.TriggerLastValue
    return None

  def last(self):
    return self.TriggerLastValue


class DLNAEventListener:

  def __init__(self, log):
    self.event_notification_listener = None
    self.SID = None
    self.Device = None
    self.Service = None
    self.hip = None
    self.callback_number = None
    self.log = log
    self.EventsLog = []
    self.CurrentSEQ = None
    self.Warnings = []
    self.is_running = None


class DLNAEventNotificationServer(socketserver.TCPServer):

  request_queue_size = 100

  def __init__(self, *args, verbosity, **kwargs):
    self.logger = log_event('dlnanotification', verbosity)
    super().__init__(*args, **kwargs)
    self.__dict__['_BaseServer__is_shut_down'].set()
  
  def server_bind(self):
    try:
      self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except:
      pass
    super().server_bind()

  def shutdown(self):
    self.socket.close()
    super().shutdown()

  def server_close(self):
    pass


class DLNAEventNotificationHandler(socketserver.BaseRequestHandler):

  def __init__(self, *args, EventListeners, process_lastchange, **kwargs):
    self.EventListeners = EventListeners
    self.process_lastchange = process_lastchange
    try:
      super().__init__(*args, **kwargs)
    except:
      pass
  
  def handle(self):
    try:
      req = HTTPMessage(self.request)
      event_listeners = list(self.EventListeners)
      if req.method != 'NOTIFY':
        raise
      callback_number = int(req.path.strip(' /'))
      EventListener = next(e for e in event_listeners if e.callback_number == callback_number)
      if req.header('SID', '') != EventListener.SID:
        raise
      dlna_event = DLNAEvent()
      seq = req.header('SEQ', '')
      self.server.logger.log(1, 'receipt', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], seq)
      seq = int(seq)
      if EventListener.CurrentSEQ is None:
        EventListener.CurrentSEQ = seq
      elif seq > EventListener.CurrentSEQ:
        EventListener.CurrentSEQ = seq
      if EventListener.log:
        dlna_event.ReceiptTime = time.localtime()
        if len(EventListener.EventsLog) < seq:
          EventListener.EventsLog = EventListener.EventsLog + [None]*(seq - len(EventListener.EventsLog))
      root_xml = minidom.parseString(req.body)
      try:
        self.request.sendall("HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n".encode("ISO-8859-1"))
      except:
        pass
    except:
      self.request.sendall("HTTP/1.0 400 Bad Request\r\nContent-Length: 0\r\n\r\n".encode("ISO-8859-1"))
      return
    try:
      for node in root_xml.documentElement.childNodes:
        if node.nodeType != node.ELEMENT_NODE:
          continue
        if node.localName.lower() != 'property':
          continue
        for child_node in node.childNodes:
          try:
            prop_name = child_node.localName
          except:
            continue
          try:
            prop_nvalue = _XMLGetNodeText(child_node)
          except:
            continue
          self.server.logger.log(2, 'notification', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], seq, prop_name, prop_nvalue)
          if prop_name.upper() == 'LastChange'.upper():
            try:
              dlna_event.Changes.extend(self.process_lastchange(prop_nvalue))
            except:
              dlna_event.Changes.append((prop_name, prop_nvalue))
          else:
            dlna_event.Changes.append((prop_name, prop_nvalue))
      if EventListener.log:
        EventListener.EventsLog.append(dlna_event)
      for (prop_name, prop_nvalue) in dlna_event.Changes:
        for warning in EventListener.Warnings:
          if warning.submit(seq, prop_name, prop_nvalue):
            self.server.logger.log(2, 'alert', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], seq, prop_name, prop_nvalue)
    except:
      return


class DLNAEventNotificationListener:

  def __init__(self, handler, port, private=False):
    self.logger = log_event('dlnanotification', handler.verbosity)
    self.Handler = handler
    self.port = port
    self.private = private
    self.EventListeners = []
    self.seq = 0
    self.receiver_thread = None
    self.is_running = None

  def register(self, eventlistener):
    if not self.private or not self.seq:
      self.EventListeners.append(eventlistener)
      self.seq += 1
      return self.seq
    else:
      return None

  def unregister(self, eventlistener):
    try:
      self.EventListeners.remove(eventlistener)
      return True
    except:
      return False

  def _start_event_notification_receiver(self, server_ready):
    DLNAEventNotificationBoundHandler = partial(DLNAEventNotificationHandler, process_lastchange=self.Handler._process_lastchange, EventListeners=self.EventListeners)
    try:
      with DLNAEventNotificationServer((self.Handler.ip, self.port), DLNAEventNotificationBoundHandler, verbosity=self.Handler.verbosity) as self.DLNAEventNotificationReceiver:
        server_ready.set()
        self.DLNAEventNotificationReceiver.serve_forever()
    except:
      server_ready.set()
    self.is_running = None

  def _shutdown_event_notification_receiver(self):
    if self.is_running:
      self.is_running = False
      try:
        self.DLNAEventNotificationReceiver.shutdown()
        self.receiver_thread.join()
      except:
        pass

  def start(self):
    if self.is_running:
      self.logger.log(1, 'alreadyactivated', self.Handler.DEVICE_TYPE, self.Handler.ip, self.port)
      return None
    self.is_running = True
    self.logger.log(1, 'start', self.Handler.DEVICE_TYPE, self.Handler.ip, self.port)
    server_ready = threading.Event()
    self.receiver_thread = threading.Thread(target=self._start_event_notification_receiver, args=(server_ready,))
    self.receiver_thread.start()
    server_ready.wait()

  def stop(self):
    if self.is_running:
      self._shutdown_event_notification_receiver()
      self.logger.log(1, 'stop', self.Handler.DEVICE_TYPE, self.Handler.ip, self.port)


class DLNAAdvertisementServer:

  def __init__(self, handlers, verbosity):
    self.logger = log_event('dlnaadvertisement', verbosity)
    self.Handlers = handlers
    self.__shutdown_request = False
    self.__is_shut_down = threading.Event()
    self.__is_shut_down.set()
    self.Sockets = ()
    self.Ips = ()

  def _handle(self, i, msg, addr):
    sock = self.Sockets[i]
    ip = self.Ips[i]
    try:
      req = HTTPMessage((msg, sock))
      if req.method != 'NOTIFY':
        return
      nt = req.header('NT', '')
      only_media = True
      for handler in self.Handlers:
        if not handler.DEVICE_TYPE.lower() in ('renderer', 'server'):
          only_media = False
          break
      if only_media and not 'media' in nt.lower():
        return
      time_req = time.localtime()
      nts = req.header('NTS', '')
      usn = req.header('USN', '')
      udn = usn[0:6] + usn[6:].split(':', 1)[0]
      desc_url = req.header('Location','')
      self.logger.log(2, 'receipt', ip, usn, *addr, nts)
      dip = urllib.parse.urlparse(desc_url).netloc.split(':', 1)[0]
      for handler in self.Handlers:
        if not ip in handler.ips:
          continue
        if handler.DEVICE_TYPE.lower() != 'device':
          if not ('Media' + handler.DEVICE_TYPE).lower() in nt.lower():
            continue
        if 'alive' in nts.lower():
          for dev in handler.Devices:
            if dev.DescURL == desc_url and dev.UDN == udn:
              if dev.StatusAlive:
                if dev.StatusTime < time_req:
                  dev.StatusTime = time_req
                  dev.StatusAliveLastTime = time_req
              else:
                handler._update_devices(desc_url, time_req, ip, handler.advert_status_change)
              break
          else:
            if dip == addr[0]:
              handler._update_devices(desc_url, time_req, ip, handler.advert_status_change)
            else:
              self.logger.log(2, 'ignored', usn, *addr)
        elif 'byebye' in nts.lower():
          for dev in handler.Devices:
            if dev.DescURL == desc_url and dev.UDN == udn:
              if dev.StatusAlive:
                dev.StatusAlive = False
                handler.advert_status_change.set()
              dev.StatusTime = time_req
              break
    except:
      return

  def handle(self, i, msg, addr):
    t = threading.Thread(target=self._handle, args=(i, msg, addr), daemon=True)
    t.start()

  def serve_forever(self):
    self.__is_shut_down.clear()
    self.__shutdown_request = False
    can_run = False
    self.Ips = tuple(set(ip for handler in self.Handlers for ip in handler.ips))
    self.Sockets = tuple(socket.socket(type=socket.SOCK_DGRAM) for ip in self.Ips)
    with selectors.DefaultSelector() as selector:
      for i in range(len(self.Ips)):
        sock = self.Sockets[i]
        ip = self.Ips[i]
        try:
          sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          sock.bind((ip, 1900))
          sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4s4s', socket.inet_aton('239.255.255.250'), socket.inet_aton(ip)))
          selector.register(sock, selectors.EVENT_READ, i)
          self.logger.log(2, 'set', ip)
          can_run = True
        except:
          self.logger.log(1, 'fail', ip)
      if not can_run:
        self.__shutdown_request = True
      while not self.__shutdown_request:
        try:
          ready = selector.select(0.5)
          if self.__shutdown_request:
            break
          for r in ready:
            try:
              self.handle(r[0].data, *self.Sockets[r[0].data].recvfrom(8192))
            except:
              pass
        except:
          pass
    self.__shutdown_request = False
    self.__is_shut_down.set()

  def shutdown(self):
    self.__shutdown_request = True
    for sock in self.Sockets:
      try:
        sock.close()
      except:
        pass
    self.__is_shut_down.wait()

  def __enter__(self):
    return self

  def __exit__(self, *args):
    pass


class DLNAAdvertisementListener:

  def __init__(self, handlers=[], verbosity=0):
    self.DLNAHandlers = handlers
    for handler in handlers:
      handler.advertisement_listener = self
    self.is_advert_receiver_running = None
    self.verbosity = verbosity
    self.logger = log_event('dlnaadvertisement', verbosity)

  def _start_advertisement_receiver(self):
    with DLNAAdvertisementServer(self.DLNAHandlers, self.verbosity) as self.DLNAAdvertisementReceiver:
      self.DLNAAdvertisementReceiver.serve_forever()
    self.is_advert_receiver_running = None
    for handler in self.DLNAHandlers:
      handler.is_advert_receiver_running = None

  def _shutdown_advertisement_receiver(self):
    if self.is_advert_receiver_running:
      try:
        self.DLNAAdvertisementReceiver.shutdown()
      except:
        pass
    self.is_advert_receiver_running = False
    for handler in self.DLNAHandlers:
      handler.is_advert_receiver_running = False

  def start(self):
    if self.is_advert_receiver_running:
      self.logger.log(1, 'alreadyactivated')
      return False
    else:
      self.is_advert_receiver_running = True
      for handler in self.DLNAHandlers:
        handler.is_advert_receiver_running = True
      self.logger.log(1, 'start')
      for handler in self.DLNAHandlers:
        if not isinstance(handler.advert_status_change, threading.Event):
          handler.advert_status_change = threading.Event()
      receiver_thread = threading.Thread(target=self._start_advertisement_receiver)
      receiver_thread.start()
      return True
  
  def stop(self):
    if self.is_advert_receiver_running:
      self.logger.log(1, 'stop')
      self._shutdown_advertisement_receiver()

  def wait(self, handler, timeout=None):
    adv_event = None
    try:
      adv_event = handler.advert_status_change.wait(timeout)
    except:
      pass
    if adv_event:
      handler.advert_status_change.clear()
    return adv_event


class DLNAHandler:

  DEVICE_TYPE = 'Device'

  @staticmethod
  def retrieve_ips():
    DWORD = ctypes.wintypes.DWORD
    USHORT = ctypes.wintypes.USHORT
    ULONG = ctypes.wintypes.ULONG
    iphlpapi = ctypes.WinDLL('iphlpapi', use_last_error=True)
    class MIB_IPADDRROW(ctypes.Structure):
      _fields_=[('dwAddr', DWORD), ('dwIndex', DWORD), ('dwMask', DWORD), ('dwBCastAddr', DWORD), ('dwReasmSize', DWORD), ('unused', USHORT), ('wType', USHORT)]
    class MIB_IPADDRTABLE(ctypes.Structure):
      _fields_ = [('dwNumEntries', DWORD), ('table', MIB_IPADDRROW*0)]
    P_MIB_IPADDRTABLE = ctypes.POINTER(MIB_IPADDRTABLE)
    s = ULONG(0)
    b = ctypes.create_string_buffer(s.value)
    while iphlpapi.GetIpAddrTable(b, ctypes.byref(s), False) == 122:
      b = ctypes.create_string_buffer(s.value)
    r = ctypes.cast(b, P_MIB_IPADDRTABLE).contents
    n = r.dwNumEntries
    t = ctypes.cast(ctypes.byref(r.table), ctypes.POINTER(MIB_IPADDRROW * n)).contents
    return tuple(socket.inet_ntoa(e.dwAddr.to_bytes(4, 'little')) for e in t if e.wType & 1)

  def __init__(self, ip='', verbosity=0):
    self.Devices = []
    self.Hips = []
    self.verbosity = verbosity
    self.logger = log_event('dlnahandler', verbosity)
    self.advertisement_listener = None
    self.is_advert_receiver_running = None
    self.advert_status_change = None
    self.is_discovery_polling_running = None
    self.discovery_status_change = None
    self.discovery_polling_shutdown = None
    if ip:
      self.ip = ip
    else:
      try:
        s = socket.socket(type=socket.SOCK_DGRAM)
        s.connect(('239.255.255.250', 1900))
        self.ip = s.getsockname()[0]
        s.close()
      except:
        try:
          self.ip = socket.gethostbyname(socket.gethostname())
        except:
          try:
            self.ip = socket.gethostbyname(socket.getfqdn())
          except:
            self.ip = '0.0.0.0'
            self.logger.log(LSTRINGS['ip_failure'], 0)
    if socket.inet_aton(self.ip) != b'\x00\x00\x00\x00':
      self.ips = (self.ip,)
    else:
      self.ips = self.retrieve_ips()
    self.update_devices = threading.Lock()

  def _update_devices(self, desc_url, time_msg, hip, status_change=None, cond_numb=None):
    try:
      resp = HTTPRequest(desc_url, timeout=5, ip=hip)
      if resp.code != '200':
        raise
      root_xml = minidom.parseString(resp.body)
      if not ('Media' + self.DEVICE_TYPE).lower() in _XMLGetRTagText(root_xml, 'deviceType').lower():
        raise
      udn = _XMLGetRTagText(root_xml, 'UDN')
      self.update_devices.acquire()
      dind = None
      try:
        for d, dev in enumerate(self.Devices):
          if dev.DescURL == desc_url and dev.UDN == udn:
            if dev.StatusAlive:
              if dev.StatusTime < time_msg:
                dev.StatusTime = time_msg
                dev.StatusAliveLastTime = time_msg
              raise
            dind = d
            break
        try:
          device = eval('DLNA' + self.DEVICE_TYPE + '()')
        except:
          device = DLNADevice()
        device.Ip = urllib.parse.urlparse(desc_url).netloc.split(':', 1)[0]
        baseurl_elem = _XMLGetRTagElements(root_xml, 'URLBase')
        if baseurl_elem:
          baseurl = _XMLGetNodeText(baseurl_elem[0])
          if urllib.parse.urlparse(baseurl).netloc.split(':', 1)[0] != device.Ip:
            raise
        else:
          baseurl = desc_url
      except:
        self.update_devices.release()
        raise
    except:
      if cond_numb:
        with cond_numb[0]:
          cond_numb[1] += 1
          cond_numb[0].notify()
      return False
    try:
      device.IconURL = None
      nodes_ic = _XMLGetRTagElements(root_xml, 'icon')
      for node_ic in reversed(nodes_ic):
        try:
          if 'png' in _XMLGetRTagText(node_ic, 'mimetype').lower():
            device.IconURL = urllib.parse.urljoin(baseurl, _XMLGetRTagText(node_ic, 'url'))
        except:
          pass
      if not device.IconURL:
        try:
          device.IconURL = urllib.parse.urljoin(baseurl, _XMLGetRTagText(_XMLGetRTagElements(root_xml, 'icon')[-1], 'url'))
        except:
          device.IconURL = ''
      if device.IconURL:
        if urllib.parse.urlparse(device.IconURL).netloc.split(':', 1)[0] != device.Ip:
          iconurl = ''
    except:
      pass
    try:
      device.FriendlyName = _XMLGetRTagText(root_xml, 'friendlyName')
    except:
      device.FriendlyName = ''
    device.DescURL = desc_url
    device.UDN = udn
    device.StatusAlive = True
    device.StatusTime = time_msg
    device.StatusAliveLastTime = time_msg
    if dind is None:
      self.Hips.append(hip)
      self.Devices.append(device)
    else:
      self.Hips[d] = hip
      self.Devices[d] = device
    self.update_devices.release()
    if cond_numb:
      with cond_numb[0]:
        cond_numb[1] += 1
        cond_numb[0].notify()
    try:
      device.Manufacturer = _XMLGetRTagText(root_xml, 'manufacturer')
    except:
      pass
    try:
      device.ModelName = _XMLGetRTagText(root_xml, 'modelName')
    except:
      pass
    if dind is None:
      self.logger.log(1, 'registering', self.DEVICE_TYPE.lower(), device.FriendlyName, hip)
    try:
      device.ModelDesc = _XMLGetRTagText(root_xml, 'modelDescription')
    except:
      pass
    try:
      device.ModelNumber = _XMLGetRTagText(root_xml, 'modelNumber')
    except:
      pass
    try:
      device.SerialNumber = _XMLGetRTagText(root_xml, 'serialNumber')
    except:
      pass
    for node in _XMLGetRTagElements(root_xml, 'service'):
      service = DLNAService()
      try:
        service.Type = _XMLGetRTagText(node, 'serviceType')
        service.Id = _XMLGetRTagText(node, 'serviceId')
        service.ControlURL = urllib.parse.urljoin(baseurl, _XMLGetRTagText(node, 'controlURL'))
        if urllib.parse.urlparse(service.ControlURL).netloc.split(':', 1)[0] != device.Ip:
          continue
        service.SubscrEventURL = urllib.parse.urljoin(baseurl, _XMLGetRTagText(node, 'eventSubURL'))
        if urllib.parse.urlparse(service.SubscrEventURL).netloc.split(':', 1)[0] != device.Ip:
          continue
        service.DescURL = urllib.parse.urljoin(baseurl, _XMLGetRTagText(node, 'SCPDURL'))
        if urllib.parse.urlparse(service.DescURL).netloc.split(':', 1)[0] != device.Ip:
          continue
      except:
        continue
      try:
        resp = HTTPRequest(service.DescURL, timeout=5, ip=hip)
        if resp.code != '200':
          raise
      except:
        continue
      root_s_xml = minidom.parseString(resp.body)
      for node_s in _XMLGetSTagElements(root_s_xml, 'action'):
        action = DLNAAction()
        try:
          action.Name = _XMLGetSTagText(node_s, 'name')
        except:
          continue
        for node_a in _XMLGetSTagElements(node_s, 'argument'):
          argument = DLNAArgument()
          try:
            argument.Name = _XMLGetSTagText(node_a, 'name')
            argument.Direction = _XMLGetSTagText(node_a, 'direction')
            statevar = _XMLGetSTagText(node_a, 'relatedStateVariable')
            node_sv = next(sv for sv in _XMLGetSTagElements(root_s_xml, 'stateVariable') if _XMLGetSTagElements(sv, 'name')[0].childNodes[0].data == statevar)
            if node_sv.getAttribute('sendEvents') == 'yes':
              argument.Event = True
            elif node_sv.getAttribute('sendEvents') == 'no':
              argument.Event = False
            argument.Type = _XMLGetSTagText(node_sv, 'dataType')
            try:
              node_sv_av = _XMLGetSTagElements(node_sv, 'allowedValueList')[0]
              argument.AllowedValueList = *(_XMLGetNodeText(av) for av in _XMLGetSTagElements(node_sv_av,'allowedValue')),
            except:
              pass
            try:
              node_sv_ar = _XMLGetSTagElements(node_sv, 'allowedValueRange')[0]
              argument.AllowedValueRange = (_XMLGetSTagText(node_sv_ar, 'minimum'), _XMLGetSTagText(node_sv_ar, 'maximum'))
            except:
              pass
            try:
              argument.DefaultValue = _XMLGetSTagText(node_sv, 'defaultValue')
            except:
              pass
          except:
            argument = None
            continue
          if argument:
            action.Arguments.append(argument)
          else:
            action = None
            break
        if action:
          service.Actions.append(action)
      service.EventThroughLastChange = False
      try:
        node_sv = next(sv for sv in _XMLGetSTagElements(root_s_xml, 'stateVariable') if _XMLGetSTagElements(sv, 'name')[0].childNodes[0].data.upper() == 'LastChange'.upper())
        if node_sv.getAttribute('sendEvents') == 'yes':
          service.EventThroughLastChange = True
      except:
        pass
      device.Services.append(service)
    device.BaseURL = baseurl
    if status_change:
      try:
        status_change.set()
      except:
        pass
    return True

  def _discover(self, uuid=None, timeout=2, alive_persistence=0, from_polling=False):
    if uuid:
      self.logger.log(2, 'msearch1', uuid)
      msg = \
      'M-SEARCH * HTTP/1.1\r\n' \
      'HOST: 239.255.255.250:1900\r\n' \
      'ST: uuid:' + uuid + '\r\n' \
      'MX: 2\r\n' \
      'MAN: "ssdp:discover"\r\n' \
      '\r\n'
    elif self.DEVICE_TYPE == 'Device':
      self.logger.log(2, 'msearch2')
      msg = \
      'M-SEARCH * HTTP/1.1\r\n' \
      'HOST: 239.255.255.250:1900\r\n' \
      'ST: upnp:rootdevice\r\n' \
      'MX: 2\r\n' \
      'MAN: "ssdp:discover"\r\n' \
      '\r\n'
    else:
      self.logger.log(2, 'msearch3', self.DEVICE_TYPE.lower())
      msg = \
      'M-SEARCH * HTTP/1.1\r\n' \
      'HOST: 239.255.255.250:1900\r\n' \
      'ST: urn:schemas-upnp-org:device:Media%s:1\r\n' \
      'MX: 2\r\n' \
      'MAN: "ssdp:discover"\r\n' \
      '\r\n' % self.DEVICE_TYPE
    socks = []
    for ip in self.ips:
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
      sock.settimeout(timeout)
      socks.append(sock)
      try:
        sock.bind((ip, 0))
        try:
          sock.sendto(msg.encode("ISO-8859-1"), (ip, 1900))
        except:
          pass
        try:
          sock.sendto(msg.encode("ISO-8859-1"), ('239.255.255.250', 1900))
          self.logger.log(2, 'sent', ip)
        except:
          self.logger.log(1, 'fail', ip)
      except:
        self.logger.log(1, 'fail', ip)
    loca_time_hip = []
    stopped = False
    time_req = time.localtime()
    with selectors.DefaultSelector() as selector:
      for i in range(len(self.ips)):
        try:
          selector.register(socks[i], selectors.EVENT_READ, i)
        except:
          pass
      start_time = time.monotonic()
      tupds = []
      if from_polling:
        cond_numb = [threading.Condition(), 0]
      else:
        cond_numb = None
      while time.monotonic() - start_time <= timeout and (not from_polling or self.is_discovery_polling_running):
        ready = selector.select(0.5)
        for r in ready:
          try:
            sock = socks[r[0].data]
            ip = self.ips[r[0].data]
            resp, addr = sock.recvfrom(65507)
            self.logger.log(2, 'receipt', ip, *addr)
            time_resp = time.localtime()
            try:
              resp = HTTPMessage((resp, addr), body=False)
              if resp.code != '200' or not (uuid or ('' if self.DEVICE_TYPE == 'Device' else ('Media' + self.DEVICE_TYPE))).lower() in resp.header('ST', '').lower():
                continue
              loca = resp.header('Location')
              if (urllib.parse.urlparse(loca)).netloc.split(':',1)[0] == addr[0]:
                t = threading.Thread(target=self._update_devices, args=(loca, time_resp, ip, self.discovery_status_change if from_polling else None, cond_numb), daemon=True)
                tupds.append(t)
                t.start()
              else:
                self.logger.log(2, 'ignored', *addr)
            except:
              pass
          except:
            pass
    time_resp = time.localtime()
    for sock in socks:
      try:
        sock.close()
      except:
        pass
    tot_numb = len(tupds)
    if cond_numb and tot_numb:
      with cond_numb[0]:
        while cond_numb[1] < tot_numb:
          cond_numb[0].wait()
    trimmed = False
    for dev in self.Devices:
      if dev.StatusAlive:
        if (True if not uuid else dev.UDN == 'uuid:' + uuid):
          with self.update_devices:
            if time.mktime(time_req) - time.mktime(dev.StatusAliveLastTime) > alive_persistence:
              dev.StatusAlive = False
              dev.StatusTime = time_resp
              trimmed = True
    if trimmed and from_polling:
      try:
        self.discovery_status_change.set()
      except:
        pass
    if not from_polling:
      for t in tupds:
        t.join()

  def discover(self, uuid=None, timeout=2, alive_persistence=0, from_polling=False):
    if from_polling:
      t = threading.Thread(target=self._discover, args=(uuid, timeout, alive_persistence, from_polling), daemon=True)
      t.start()
      return t
    else:
      self._discover(uuid, timeout, alive_persistence, from_polling)

  def search(self, uuid=None, name=None, complete=False):
    device = None
    for dev in self.Devices:
      if uuid:
        if name:
          if dev.UDN == 'uuid:' + uuid and dev.FriendlyName.lower() == name.lower():
            device = dev
            if dev.StatusAlive and (not complete or dev.BaseURL):
              break
        else:
          if dev.UDN == 'uuid:' + uuid:
            device = dev
            if dev.StatusAlive and (not complete or dev.BaseURL):
              break
      else:
        if name:
          if dev.FriendlyName.lower() == name.lower():
            device = dev
            if dev.StatusAlive and (not complete or dev.BaseURL):
              break
        else:
          if dev.StatusAlive and (not complete or dev.BaseURL):
            device = dev
            break
    return device

  def _discovery_polling(self, timeout=2, alive_persistence=0, polling_period=30):
    self.is_discovery_polling_running = True
    if self.discovery_status_change == None:
      self.discovery_status_change = threading.Event()
    first_time = True
    while self.is_discovery_polling_running and not self.discovery_polling_shutdown.is_set():
      if first_time:
        self.discover(uuid=None, timeout=timeout, alive_persistence=86400, from_polling=True)
      else:
        self.discover(uuid=None, timeout=timeout, alive_persistence=alive_persistence, from_polling=True)
      if not self.is_discovery_polling_running:
        break
      if first_time:
        first_time = False
      self.discovery_polling_shutdown.wait(polling_period)
    self.discovery_polling_shutdown = None
    self.is_discovery_polling_running = None

  def start_discovery_polling(self, timeout=2, alive_persistence=0, polling_period=30, DiscoveryEvent=None):
    if self.is_discovery_polling_running:
      self.logger.log(1, 'alreadyactivated', self.DEVICE_TYPE.lower())
    else:
      self.logger.log(1, 'start', self.DEVICE_TYPE.lower())
      if isinstance(DiscoveryEvent, threading.Event):
        self.discovery_status_change = DiscoveryEvent
      else:
        self.discovery_status_change = threading.Event()
      self.discovery_polling_shutdown = threading.Event()
      discovery_thread = threading.Thread(target=self._discovery_polling, args=(timeout, alive_persistence, polling_period))
      discovery_thread.start()
      return self.discovery_status_change

  def stop_discovery_polling(self):
    try:
      self.discovery_polling_shutdown.set()
    except:
      pass
    if self.is_discovery_polling_running:
      self.logger.log(1, 'stop', self.DEVICE_TYPE.lower())
      self.is_discovery_polling_running = False
      self.discovery_status_change.set()

  def wait_for_discovery(self, timeout=None):
    disc_event = None
    try:
      disc_event = self.discovery_status_change.wait(timeout)
    except:
      pass
    if disc_event:
      self.discovery_status_change.clear()
    if self.is_discovery_polling_running:
      return disc_event
    else:
      return None

  def _build_soap_msg(self, device, service, action, **arguments):
    if not device:
      return None
    serv = next((serv for serv in device.Services if serv.Id == ('urn:upnp-org:serviceId:' + service)), None)
    if not serv:
      return None
    act = next((act for act in serv.Actions if act.Name == action), None)
    if not act :
      return None
    msg_body = \
      '<?xml version="1.0"?>\n' \
      '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' \
      '<s:Body>\n' \
      '<u:##action## xmlns:u="urn:schemas-upnp-org:service:##service##:1">\n' \
      '##arguments##' \
      '</u:##action##>\n' \
      '</s:Body>\n' \
      '</s:Envelope>'
    msg_body = msg_body.replace('##service##', service)
    msg_body = msg_body.replace('##action##', action)
    msg_arguments = ''
    cnt_arg = 0
    out_args = {}
    for arg in act.Arguments:
      if arg.Direction == 'in':
        if not arguments:
          return None
        cnt_arg += 1
        if not arg.Name in arguments:
          if arg.DefaultValue:
            arguments[arg.Name] = arg.DefaultValue
          else:
            return None
        msg_arguments = msg_arguments + '<%s>%s</%s>' % (arg.Name, html.escape(str(arguments[arg.Name])) , arg.Name) + '\n'
      if arg.Direction == 'out':
        out_args[arg.Name] = None
    if arguments:
      if len(arguments) > cnt_arg:
        return None
    msg_body = msg_body.replace('##arguments##', msg_arguments)
    msg_body_b = msg_body.encode("utf-8")
    soap_action = 'urn:schemas-upnp-org:service:%s:1#%s' % (service, action)
    msg_headers = {
      'User-Agent': 'PlayOn DLNA Controller',
      'Content-Type': 'text/xml; charset="utf-8"',
      'SOAPAction': '"%s"' % soap_action
    }
    return serv.ControlURL, msg_headers, msg_body_b, out_args

  def send_soap_msg(self, device, service, action, soap_timeout=5, soap_stop=None, **arguments):
    if not device:
      return None
    try:
      ip = self.Hips[self.Devices.index(device)]
    except:
      return None
    cturl_headers_body_oargs = self._build_soap_msg(device, service, action, **arguments)
    if not cturl_headers_body_oargs:
      self.logger.log(1, 'commandabandonment', self.DEVICE_TYPE, device.FriendlyName, service, action)
      return None
    self.logger.log(2, 'commandsending', self.DEVICE_TYPE, device.FriendlyName, service, action)
    resp = HTTPRequest(cturl_headers_body_oargs[0], method='POST', headers=cturl_headers_body_oargs[1], data=cturl_headers_body_oargs[2], timeout=3, max_length=104857600, max_time=soap_timeout+1, stop=soap_stop, ip=ip)
    if resp.code != '200':
      self.logger.log(1, 'commandfailure', self.DEVICE_TYPE, device.FriendlyName, service, action)
      return None
    self.logger.log(1, 'commandsuccess', self.DEVICE_TYPE, device.FriendlyName, service, action)
    try:
      root_xml = minidom.parseString(resp.body)
    except:
      self.logger.log(2, 'responsefailure', self.DEVICE_TYPE, device.FriendlyName, service, action)
      return None
    out_args = cturl_headers_body_oargs[3]
    try:
      for arg in out_args:
        out_args[arg] = _XMLGetNodeText(root_xml.getElementsByTagName(arg)[0])
    except:
      self.logger.log(2, 'responsefailure', self.DEVICE_TYPE, device.FriendlyName, service, action)
      return None
    self.logger.log(2, 'responsesuccess', self.DEVICE_TYPE, device.FriendlyName, service, action)
    if out_args:
      return out_args
    else:
      return True

  def start_advertisement_listening(self, AdvertisementEvent=None):
    if self.is_advert_receiver_running:
      self.logger.log(1, 'advertalreadyactivated', self.DEVICE_TYPE.lower())
    else:
      self.is_advert_receiver_running = True
      self.logger.log(1, 'advertstart', self.DEVICE_TYPE.lower())
      if isinstance(AdvertisementEvent, threading.Event):
        self.advert_status_change = AdvertisementEvent
      else:
        self.advert_status_change = threading.Event()
      self.advertisement_listener = DLNAAdvertisementListener([self], self.verbosity)
      self.advertisement_listener.start()
      return self.advert_status_change
  
  def stop_advertisement_listening(self):
    if self.is_advert_receiver_running:
      self.logger.log(1, 'advertstop', self.DEVICE_TYPE.lower())
      self.advertisement_listener.stop()

  def wait_for_advertisement(self, timeout=None):
    return self.advertisement_listener.wait(self, timeout)

  @staticmethod
  def _process_lastchange(value):
    return [('LastChange', value)]

  def new_event_subscription(self, device, service, port_or_listener, log=False):
    if not device:
      return None
    try:
      hip = self.Hips[self.Devices.index(device)]
    except:
      return None
    serv = next((serv for serv in device.Services if serv.Id == ('urn:upnp-org:serviceId:' + service)), None)
    if not serv:
      return None
    EventListener = DLNAEventListener(log)
    if isinstance(port_or_listener, DLNAEventNotificationListener):
      EventListener.event_notification_listener = port_or_listener
    else:
      try:
        port = int(port_or_listener)
      except:
        return None
      EventListener.event_notification_listener = DLNAEventNotificationListener(self, port, private=True)
    EventListener.callback_number = EventListener.event_notification_listener.register(EventListener)
    if EventListener.callback_number is None:
      return None
    EventListener.Device = device
    EventListener.Service = serv
    EventListener.hip = hip
    return EventListener

  def send_event_subscription(self, EventListener, timeout):
    if not EventListener:
      return None
    msg_headers = {
    'Callback': '<http://%s:%s/%s>' % (EventListener.hip, EventListener.event_notification_listener.port, EventListener.callback_number),
    'NT': 'upnp:event',
    'Timeout': 'Second-%s' % timeout
    }
    if EventListener.is_running:
      self.logger.log(1, 'subscralreadyactivated', EventListener.Device.FriendlyName, EventListener.Service.Id[23:])
      return None
    EventListener.is_running = True
    if EventListener.event_notification_listener.private:
      EventListener.event_notification_listener.start()
    resp = HTTPRequest(EventListener.Service.SubscrEventURL, method='SUBSCRIBE', headers=msg_headers, ip=EventListener.hip, timeout=5)
    if resp.code != '200':
      EventListener.is_running = None
    else:
      EventListener.SID = resp.header('SID', '')
      if not EventListener.SID:
        EventListener.is_running = None
    if EventListener.is_running:
      self.logger.log(1, 'subscrsuccess', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], EventListener.SID, resp.header('TIMEOUT', ''))
      return True
    else:
      EventListener.event_notification_listener.unregister(EventListener)
      self.logger.log(1, 'subscrfailure', EventListener.Device.FriendlyName, EventListener.Service.Id[23:])
      return None
    
  def renew_event_subscription(self, EventListener, timeout):
    if not EventListener:
      return None
    msg_headers = {
    'SID': '%s' % EventListener.SID,
    'Timeout': 'Second-%s' % timeout
    }
    resp = HTTPRequest(EventListener.Service.SubscrEventURL, method='SUBSCRIBE', headers=msg_headers, ip=EventListener.hip, timeout=5)
    if resp.code != '200':
      self.logger.log(1, 'subscrrenewfailure', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], EventListener.SID)
      return None
    self.logger.log(1, 'subscrrenewsuccess', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], EventListener.SID, resp.header('TIMEOUT', ''))
    return True
    
  def send_event_unsubscription(self, EventListener):
    if not EventListener:
      return None
    msg_headers = {
    'SID': '%s' % EventListener.SID
    }
    EventListener.event_notification_listener.unregister(EventListener)
    resp = HTTPRequest(EventListener.Service.SubscrEventURL, method='UNSUBSCRIBE', headers=msg_headers, ip=EventListener.hip, timeout=5)
    if EventListener.event_notification_listener.private:
      EventListener.event_notification_listener.stop()
    if resp.code != '200':
      self.logger.log(1, 'subscrunsubscrfailure', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], EventListener.SID)
      return None 
    self.logger.log(1, 'subscrunsubscrsuccess', EventListener.Device.FriendlyName, EventListener.Service.Id[23:], EventListener.SID)
    return True

  def add_event_warning(self, EventListener, property, *values, WarningEvent=None):
    warning = DLNAEventWarning(EventListener, property, *values, WarningEvent=WarningEvent)
    EventListener.Warnings.append(warning)
    return warning
    
  def wait_for_warning(self, warning, timeout=None, clear=None):
    if clear:
      with warning.lock:
        warning.clear()
        if warning.WarningEvent is not None:
          warning.WarningEvent.clear()
    with warning.lock:
      v = warning.fresh()
      if v is not None:
        if warning.WarningEvent is not None:
          warning.WarningEvent.clear()
        return v
    if warning.WarningEvent is not None:
      if warning.WarningEvent.wait(timeout):
        warning.WarningEvent.clear()
    with warning.lock:
      v = warning.fresh()
      if v is not None:
        if warning.WarningEvent is not None:
          warning.WarningEvent.clear()
        return v
    return None


class DLNAController(DLNAHandler):

  DEVICE_TYPE = 'Renderer'

  def __init__(self, ip='', verbosity=0):
    super().__init__(ip, verbosity)
    self.Renderers = self.Devices

  def _build_didl(self, uri, title, kind=None, size=None, duration=None, suburi=None):
    if size:
      size_arg = ' size="%s"' % (size)
    else:
      size_arg = ''
    if duration:
      duration_arg = ' duration="%s"' % (duration)
    else:
      duration_arg = ''
    media_class = 'object.item.videoItem'
    try:
      if kind.lower() == 'audio':
        media_class = 'object.item.audioItem'
      if kind.lower() == 'image':
        media_class = 'object.item.imageItem'
    except:
      pass
    subtype = None
    try:
      subtype = suburi.rsplit('.', 1)[1]
    except:
      pass
    if not subtype:
      suburi = None
    else:
      if len(subtype) > 4:
        suburi = None
    didl_lite = \
      '<DIDL-Lite '\
      'xmlns:dc="http://purl.org/dc/elements/1.1/" ' \
      'xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" ' \
      'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" ' \
      'xmlns:sec="http://www.sec.co.kr/" ' \
      'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">' \
      '<item restricted="1" id="PlayOn-content" parentID="">' \
      '<upnp:class>%s</upnp:class>' \
      '<dc:title>%s</dc:title>' \
      '<res protocolInfo="http-get:*:application/octet-stream:DLNA.ORG_PN=;DLNA.ORG_OP=00;DLNA.ORG_FLAGS=01700000000000000000000000000000" sec:URIType="public"%s%s>%s</res>' \
      '%s' \
      '</item>' \
      '</DIDL-Lite>' % (media_class, html.escape(title), size_arg, duration_arg, html.escape(uri), '<sec:CaptionInfoEx sec:type="%s">%s</sec:CaptionInfoEx>' %(html.escape(subtype), html.escape(suburi)) if suburi else '')
    return didl_lite
    
  def send_URI(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None, stop=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetAVTransportURI', soap_timeout=20,  soap_stop=stop, InstanceID=0, CurrentURI=uri, CurrentURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True
      
  def send_Local_URI(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None, stop=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    didl_lite = didl_lite.replace(' sec:URIType="public"', '').replace('DLNA.ORG_OP=00', 'DLNA.ORG_OP=01').replace('DLNA.ORG_FLAGS=017', 'DLNA.ORG_FLAGS=217')
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetAVTransportURI', soap_timeout=20, soap_stop=stop, InstanceID=0, CurrentURI=uri, CurrentURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True

  def send_URI_Next(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None, stop=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetNextAVTransportURI', soap_timeout=20,  soap_stop=stop, InstanceID=0, NextURI=uri, NextURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True
      
  def send_Local_URI_Next(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None, stop=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    didl_lite = didl_lite.replace(' sec:URIType="public"', '').replace('DLNA.ORG_OP=00', 'DLNA.ORG_OP=01').replace('DLNA.ORG_FLAGS=017', 'DLNA.ORG_FLAGS=217')
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetNextAVTransportURI', soap_timeout=20, soap_stop=stop, InstanceID=0, NextURI=uri, NextURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True

  def send_Play(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Play', InstanceID=0, Speed=1)
    if not out_args:
      return None
    else:
      return True

  def send_Stop(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Stop', InstanceID=0)
    if not out_args:
      return None
    else:
      return True
      
  def send_Pause(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Pause', InstanceID=0)
    if not out_args:
      return None
    else:
      return True

  def send_Seek(self, renderer, target="0:00:00"):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Seek', InstanceID=0, Unit="REL_TIME", Target=target)
    if not out_args:
      return None
    else:
      return True

  def get_Position(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetPositionInfo', soap_timeout=3, InstanceID=0)
    if not out_args:
      return None
    return out_args['RelTime']

  def get_Duration(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetMediaInfo', soap_timeout=3, InstanceID=0)
    if not out_args:
      return None
    return out_args['MediaDuration']

  def get_Duration_Fallback(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetPositionInfo', soap_timeout=3, InstanceID=0)
    if not out_args:
      return None
    return out_args['TrackDuration']

  def get_TransportInfo(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetTransportInfo', InstanceID=0)
    if not out_args:
      return None
    return out_args['CurrentTransportState'], out_args['CurrentTransportStatus']

  def get_Mute(self, renderer):
    out_args = self.send_soap_msg(renderer, 'RenderingControl', 'GetMute', InstanceID=0, Channel='Master')
    if not out_args:
      return None
    return out_args['CurrentMute']

  def set_Mute(self, renderer, mute=False):
    out_args = self.send_soap_msg(renderer, 'RenderingControl', 'SetMute', InstanceID=0, Channel='Master', DesiredMute=(1 if mute else 0))
    if not out_args:
      return None
    return True

  def get_Volume(self, renderer):
    out_args = self.send_soap_msg(renderer, 'RenderingControl', 'GetVolume', InstanceID=0, Channel='Master')
    if not out_args:
      return None
    return out_args['CurrentVolume']

  def set_Volume(self, renderer, volume=0):
    out_args = self.send_soap_msg(renderer, 'RenderingControl', 'SetVolume', InstanceID=0, Channel='Master', DesiredVolume=volume)
    if not out_args:
      return None
    return True

  def get_StoppedReason(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'X_GetStoppedReason', InstanceID=0)
    if not out_args:
      return None
    return out_args['StoppedReason'], out_args['StoppedReasonData']

  @staticmethod
  def _process_lastchange(value):
    try:
      lc_xml = minidom.parseString(value)
      changes = []
      for node in lc_xml.documentElement.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
          break
      if node.nodeType == node.ELEMENT_NODE:
        for p_node in node.childNodes:
          if p_node.nodeType == p_node.ELEMENT_NODE:
            lc_prop_name = p_node.localName
            lc_prop_value = None
            for att in p_node.attributes.items():
              if att[0].lower() == 'val':
                lc_prop_value = att[1]
                break
            if lc_prop_value != None:
              changes.append((lc_prop_name, lc_prop_value))
      return changes
    except:
      return DLNAHandler._process_lastchange(value)

  def new_event_subscription(self, *args, **kwargs):
    EventListener = super().new_event_subscription(*args, **kwargs)
    EventListener.Renderer = EventListener.Device
    return EventListener


class DLNAClient(DLNAHandler):

  DEVICE_TYPE = 'Server'

  def __init__(self, ip='', verbosity=0):
    super().__init__(ip, verbosity)
    self.Servers = self.Devices

  def _extract_metadata(self, node):
    try:
      obj_id = ''
      for att in node.attributes.items():
        if att[0].lower() == 'id':
          obj_id = att[1]
          break
      if not obj_id:
        return None
      obj_type = node.localName
      obj_class = ''
      obj_title = ''
      obj_album = ''
      obj_artist = ''
      obj_track = ''
      obj_uri = ''
      for ch_node in node.childNodes:
        if ch_node.nodeType == ch_node.ELEMENT_NODE:
          chn_ln = ch_node.localName.lower()
          if chn_ln == 'class':
            obj_class = '.'.join(_XMLGetNodeText(ch_node).split('.')[:3])
          elif chn_ln == 'title':
            obj_title = _XMLGetNodeText(ch_node)
          elif chn_ln == 'album':
            obj_album = _XMLGetNodeText(ch_node)
          elif chn_ln == 'creator':
            obj_artist = _XMLGetNodeText(ch_node)
          elif chn_ln == 'originaltracknumber':
            obj_track = _XMLGetNodeText(ch_node)
          elif chn_ln == 'res':
            if not obj_uri:
              obj_uri = _XMLGetNodeText(ch_node)
            for att in node.attributes.items():
              if att[0].lower() == 'protocolinfo':
                if not 'DLNA.ORG_CI=1' in att[1].upper().replace(' ',''):
                  obj_uri = _XMLGetNodeText(ch_node)
                  break
      return {'id': obj_id, 'type': obj_type, 'class': obj_class, 'uri': obj_uri, 'title': obj_title, 'album': obj_album, 'track': obj_track, 'artist': obj_artist}
    except:
     return None

  def get_Metadata(self, server, id='0', stop=None):
    out_args = self.send_soap_msg(server, 'ContentDirectory', 'Browse', soap_timeout=10, soap_stop=stop, ObjectID=id, BrowseFlag='BrowseMetadata', Filter='*', StartingIndex=0, RequestedCount=0, SortCriteria='')
    if not out_args:
      return None
    else:
      try:
        root_xml = minidom.parseString(out_args['Result'])
        for node in root_xml.documentElement.childNodes:
          if node.nodeType == node.ELEMENT_NODE:
            break
        d = self._extract_metadata(node)
      except:
        return None
      return d

  def get_Children(self, server, id='0', stop=None):
    out_args = self.send_soap_msg(server, 'ContentDirectory', 'Browse', soap_timeout=60, soap_stop=stop,ObjectID=id, BrowseFlag='BrowseDirectChildren', Filter='*', StartingIndex=0, RequestedCount=0, SortCriteria='')
    if not out_args:
      return None
    else:
      children = []
      try:
        root_xml = minidom.parseString(out_args['Result'])
        for node in root_xml.documentElement.childNodes:
          if node.nodeType != node.ELEMENT_NODE:
            continue
          d = self._extract_metadata(node)
          if d:
            children.append(d)
      except:
        return None
      return children

  def get_Content(self, server, id='0', stop=None):
    try:
      obj = None
      obj = self.get_Metadata(server, id, stop)
      if not obj:
        return None
      kind = obj['type']
      if not kind in ('container', 'item'):
        return None
      if id == '0':
        obj['title'] = server.FriendlyName
      if kind == 'item':
        containers = []
        items = [obj]
      else:
        children = self.get_Children(server, id, stop)
        containers = list(e for e in children if e['type'].lower() == 'container')
        numb_exp = lambda t: '.'.join([(t[0].rstrip('0123456789') + t[0][len(t[0].rstrip('0123456789')):].rjust(5,'0')) if ('0' <= t[0][-1:] and t[0][-1:] <= '9') else t[0]] + t[1:2])
        if id !='0':
          containers.sort(key=lambda e: e['title'].lower())
          containers.sort(key=lambda e: numb_exp(e['title'].lower().rsplit('.', 1)))
          containers.sort(key=lambda e: e['class'].lower())
        items = list(e for e in children if e['type'].lower() == 'item')
        items.sort(key=lambda e: e['title'].lower())
        items.sort(key=lambda e: numb_exp(e['title'].lower().rsplit('.', 1)))
        items.sort(key=lambda e: e['artist'].lower() if e['class'].lower() == 'object.item.audioitem' else '')
        items.sort(key=lambda e: '%10s' % e['track'].lower() if e['class'].lower() == 'object.item.audioitem' else '')
        items.sort(key=lambda e: e['album'].lower() if e['class'].lower() == 'object.item.audioitem' else '')
    except:
      return None
    return [obj, containers, items]


class WebSocketDataStore:

  def __init__(self, IncomingEvent=None):
    self.outgoing = []
    self.outgoing_seq = []
    self.outgoing_lock = threading.Lock()
    self.incoming = []
    self.incoming_text_only = False
    self.before_shutdown = None
    self.o_condition = threading.Condition()
    if isinstance(IncomingEvent, threading.Event):
      self.IncomingEvent = IncomingEvent
    else:
      self.IncomingEvent = threading.Event()

  def notify_outgoing(self):
    with self.o_condition:
      self.o_condition.notify_all()

  def set_outgoing(self, ind, value, if_different = False):
    with self.outgoing_lock:
      if ind >= len(self.outgoing):
        self.outgoing = self.outgoing + [None]*(ind - len(self.outgoing) + 1)
        self.outgoing_seq = self.outgoing_seq + [None]*(ind - len(self.outgoing_seq) + 1)
      cvt_value = None if value == None else str(value)
      if not if_different or cvt_value != self.outgoing[ind]:
        self.outgoing[ind] = cvt_value
        if self.outgoing_seq[ind] == None:
          self.outgoing_seq[ind] = 0
        else:
          self.outgoing_seq[ind] += 1
    self.notify_outgoing()

  def add_outgoing(self, value):
    with self.outgoing_lock:
      self.outgoing.append(None if value == None else str(value))
      self.outgoing_seq.append(0)
    self.notify_outgoing()

  def nest_outgoing(self, value):
    with self.outgoing_lock:
      if len(self.outgoing) == 0:
        self.outgoing.append(None if value == None else str(value))
        self.outgoing_seq.append(0)
      else:
        old_value = self.outgoing[-1]
        self.outgoing[-1] = None if value == None else str(value)
        self.outgoing_seq[-1] += 1
        self.outgoing.append(old_value)
        self.outgoing_seq.append(0)
    self.notify_outgoing()

  def set_before_shutdown(self, value):
    self.before_shutdown = value

  def add_incoming(self, value):
    self.incoming.append(value)
    self.IncomingEvent.set()

  def get_incoming(self):
    if self.incoming:
      return self.incoming.pop(0)
    else:
      return None

  def wait_for_incoming_event(self, timeout=None, clear=None):
    if clear:
      self.IncomingEvent.clear()
    incoming_event = self.IncomingEvent.wait(timeout)
    if incoming_event:
      self.IncomingEvent.clear()
      return True
    else:
      return None


class WebSocketRequestHandler(socketserver.BaseRequestHandler):

  PING_PONG_STRICT = False
  MAX_INACTIVE_TIME = 120
  PONG_TIMEOUT = 20
  timeout = 5

  def __init__(self, *args, **kwargs):
    self.Channel = None
    self.ClientClosing = False
    self.Error = 0
    self.ShutdownMessageTime = None
    self.CloseMessageTime = None
    self.Closed = False
    self.Buffer = bytearray()
    self.MessageData = None
    self.MessageType = None
    self.MessageReady = False
    self.FrameType = None
    self.FrameLength = None
    self.DataLength = None
    self.SendEvent = threading.Event()
    self.PingData = None
    self.PingLock = threading.Lock()
    self.PongData = None
    self.CloseData = None
    self.LastReceptionTime = None
    self.PendingPings = 0
    self.PingTime = None
    self.OutgoingSeq = []
    super().__init__(*args, **kwargs)

  @staticmethod
  def XOR32_decode(mask_data):
    o = len(mask_data) % 4
    data = mask_data[o:].cast('L')
    mask = struct.unpack('L', mask_data[o:4].tobytes() + mask_data[0:o].tobytes())[0]
    return memoryview(array.array('L', map(mask.__xor__, data))).cast('B')[4-o:]

  @classmethod
  def build_frame(cls, type, data):
    opcodes = {'text_data': 0x01, 'binary_data': 0x02, 'close': 0x08, 'ping': 0x09, 'pong': 0x0a}
    if type == 'data':
      if isinstance(data, str):
        type = 'text_data'
        data_b = data.encode('utf-8')
      elif isinstance(data, bytes):
        type = 'binary_data'
        data_b = data
      else:
        return None
    else:
      data_b = data
    if not type.lower() in opcodes:
      return None
    if len(data_b) <= 0x7d:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B',len(data_b)) + data_b
    elif len(data_b) <= 0xffff:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B', 0x7e) + struct.pack('!H',len(data_b)) + data_b
    elif len(data_b) <= 0x7fffffffffffffff:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B', 0x7f) + struct.pack('!Q',len(data_b)) + data_b
    else:
      return None
    return frame

  def send_ping(self):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('ping', b'ping'))
    except:
      return False
    return True
      
  def send_pong(self):
    if self.PingData == None:
      return False
    self.PingLock.acquire()
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('pong', self.PingData))
    except:
      return False
    finally:
      self.PingData = None
      self.PingLock.release()
    return True

  def send_close(self, data=b''):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('close', data))
    except:
      return False
    return True

  def send_data(self, data=''):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('data', data))
    except:
      return False
    return True

  def get_type(self):
    opcodes = {0x00: 'data', 0x01: 'data', 0x02: 'data', 0x08: 'close', 0x09: 'ping', 0x0a: 'pong'}
    if len(self.Buffer) == 0:
      return False
    self.FrameType = opcodes.get(self.Buffer[0] & 0x0f, 'bad')
    return True

  def get_length(self):
    if len(self.Buffer) < 2:
      return False
    if self.Buffer[1] & 0x7f <= 0x7d:
      self.DataLength = self.Buffer[1] & 0x7f
      self.FrameLength = 6 + self.DataLength
    elif self.Buffer[1] & 0x7f == 0x7e:
      if len(self.Buffer) < 4:
        return False
      self.DataLength = struct.unpack('!H', self.Buffer[2:4])[0]
      self.FrameLength = 8 + self.DataLength
    elif self.Buffer[1] & 0x7f == 0x7f:
      if len(self.Buffer) < 10:
        return False
      self.DataLength = struct.unpack('!Q', self.Buffer[2:10])[0]
      self.FrameLength = 14 + self.DataLength
    return True

  def check_mask(self):
    if len(self.Buffer) < 2:
      return False
    if self.Buffer[1] >> 7 != 1:
      return False
    return True

  def get_data(self):
    if not self.FrameType or not self.FrameLength or self.DataLength == None:
      return False
    if len(self.Buffer) < self.FrameLength:
      return False
    if self.FrameType == 'data':
      if self.MessageType == None:
        if self.Buffer[0] & 0x0f == 0:
          return False
        else:
          self.MessageType = {0x01: 'text', 0x02: 'binary'}[self.Buffer[0] & 0x0f]
          self.MessageData = []
      else:
        if self.Buffer[0] & 0x0f != 0:
          self.MessageType = {0x01: 'text', 0x02: 'binary'}[self.Buffer[0] & 0x0f]
          self.MessageData = []
    if self.FrameType != 'data' and self.Buffer[0] >> 7 != 1:
      return False
    with memoryview(self.Buffer) as buff:
      if self.FrameType == 'data':
        self.MessageData.append(WebSocketRequestHandler.XOR32_decode(buff[self.FrameLength-self.DataLength-4:self.FrameLength]))
      elif self.FrameType == 'close':
        if self.DataLength <= 0x7d:
          self.CloseData = bytes(WebSocketRequestHandler.XOR32_decode(buff[2:self.FrameLength]))
        else:
          return False
      elif self.FrameType == 'ping':
        if self.DataLength <= 0x7d:
          self.PingLock.acquire()
          self.PingData = bytes(WebSocketRequestHandler.XOR32_decode(buff[2:self.FrameLength]))
          self.PingLock.release()
        else:
          return False
      elif self.FrameType == 'pong':
        if self.DataLength <= 0x7d:
          self.PongData = bytes(WebSocketRequestHandler.XOR32_decode(buff[2:self.FrameLength]))
        else:
          return False
      else:
        return False
    if self.FrameType == 'data' and self.Buffer[0] >> 7 == 1:
      self.MessageData = b''.join(self.MessageData)
      if self.MessageType == 'text':
        try:
          self.MessageData = self.MessageData.decode('utf-8')
        except:
          return False
      self.MessageReady = True
    return True

  def purge_frame(self):
    self.FrameType = None
    del self.Buffer[0:self.FrameLength]
    self.FrameLength = None
    self.DataLength = None

  def handle_out(self):
    self.SendEvent.set()
    while not self.Closed:
      se = self.SendEvent.is_set()
      if se:
        self.SendEvent.clear()
      if self.ClientClosing:
        if not self.CloseMessageTime:
          if self.CloseData == None:
            self.CloseData = b''
          if self.send_close(self.CloseData[0:2]):
            self.server.logger.log(2, 'endacksuccess', *self.server.Address, self.Channel.Path, *self.client_address)
          else:
            self.server.logger.log(2, 'endackfailure', *self.server.Address, self.Channel.Path, *self.client_address)
        self.CloseData = None
        self.Closed = True
        break
      if self.Error:
        self.server.logger.log(2, 'errorendnotification', *self.server.Address, self.Channel.Path, *self.client_address, self.Error)
        if self.send_close(struct.pack('!H', self.Error)):
          self.server.logger.log(2, 'errorendnotificationsuccess', *self.server.Address, self.Channel.Path, *self.client_address)
        else:
          self.server.logger.log(2, 'errorendnotificationfailure', *self.server.Address, self.Channel.Path, *self.client_address)
        self.Closed = True
        break
      if self.PingData != None:
        self.send_pong()
      if self.Channel.Closed:
        shutdown_value = True
        if self.ShutdownMessageTime and not self.CloseMessageTime:
          if time.time() - self.ShutdownMessageTime > 3:
            shutdown_value = False
        if not self.CloseMessageTime and not self.ShutdownMessageTime:
          shutdown_value = self.Channel.DataStore.before_shutdown
          if shutdown_value:
            if self.send_data(shutdown_value):
              self.ShutdownMessageTime = time.time()
              self.server.logger.log(2, 'terminationdatasuccess', *self.server.Address, self.Channel.Path, *self.client_address, shutdown_value)
            else:
              shutdown_value = False
              self.server.logger.log(2, 'terminationdatafailure', *self.server.Address, self.Channel.Path, *self.client_address, shutdown_value)
        if not shutdown_value:
          if self.send_close():
            self.server.logger.log(2, 'endnotificationsuccess', *self.server.Address, self.Channel.Path, *self.client_address)
          else:
            self.server.logger.log(2, 'endnotificationfailure', *self.server.Address, self.Channel.Path, *self.client_address)
          self.CloseMessageTime = time.time()
          break
      if not self.Channel.Closed and se:
        nb_values = len(self.Channel.DataStore.outgoing_seq)
        for i in range(nb_values):
          if self.ClientClosing or self.Channel.Closed:
            break
          if i == len(self.OutgoingSeq):
            self.OutgoingSeq.append(None)
          try:
            seq_value = self.Channel.DataStore.outgoing_seq[i]
            data_value = self.Channel.DataStore.outgoing[i]
          except:
            break
          if seq_value != self.OutgoingSeq[i]:
            if data_value != None:
              if self.send_data(data_value):
                self.server.logger.log(2, 'datasuccess', *self.server.Address, self.Channel.Path, *self.client_address, data_value)
              else:
                self.server.logger.log(2, 'datafailure', *self.server.Address, self.Channel.Path, *self.client_address, data_value)
                self.Error = 1002
                continue
            self.OutgoingSeq[i] = seq_value
      if not self.Channel.Closed:
        cur_time = time.time()
        if (cur_time - self.LastReceptionTime > WebSocketRequestHandler.MAX_INACTIVE_TIME / 3 and self.PendingPings == 0) or (cur_time - self.LastReceptionTime > 2 * WebSocketRequestHandler.MAX_INACTIVE_TIME / 3 and self.PendingPings <= 1):
          if not self.PingTime:
            self.PingTime = cur_time
          self.send_ping()
          self.PendingPings += 1
        if WebSocketRequestHandler.PING_PONG_STRICT and self.PingTime:
          if cur_time - self.PingTime > WebSocketRequestHandler.PONG_TIMEOUT / 2 and self.PendingPings <=1:
            self.send_ping()
            self.PendingPings += 1
        if cur_time - self.LastReceptionTime < WebSocketRequestHandler.MAX_INACTIVE_TIME and not WebSocketRequestHandler.PING_PONG_STRICT:
          self.PingTime = None
          self.PendingPings = 0
      self.SendEvent.wait(0.5)
   
  def handle(self):
    if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      return
    self.server.logger.log(2, 'connectionrequest', *self.server.Address, *self.client_address)
    resp_err_br = \
      'HTTP/1.1 400 Bad Request\r\n' \
      'Content-Length: 0\r\n' \
      'Connection: close\r\n' \
      '\r\n'
    resp_err_nf = \
      'HTTP/1.1 404 File not found\r\n' \
      'Content-Length: 0\r\n' \
      'Connection: close\r\n' \
      '\r\n'
    req = HTTPMessage(self.request)
    if req.method != 'GET' or not req.in_header('Upgrade', 'websocket') or not req.header('Sec-WebSocket-Key', ''):
      try:
        self.request.sendall(resp_err_br.encode('ISO-8859-1'))
        self.server.logger.log(2, 'connectionrequestinvalid', *self.server.Address, *self.client_address)
      except:
        pass
      return
    self.Channel = self.server.Channels.get(req.path.lstrip('/').strip(), None)
    if self.Channel is None:
      try:
        self.request.sendall(resp_err_nf.encode('ISO-8859-1'))
        self.server.logger.log(2, 'connectionrequestnotfound', *self.server.Address, *self.client_address, req.path.lstrip('/').strip())
      except:
        pass
      return
    guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    sha1 = hashlib.sha1((req.header('Sec-WebSocket-Key') + guid).encode('utf-8')).digest()
    ws_acc = base64.b64encode(sha1).decode('utf-8')
    resp= \
      'HTTP/1.1 101 Switching Protocols\r\n' \
      'Upgrade: websocket\r\n' \
      'Connection: Upgrade\r\n' \
      'Sec-WebSocket-Accept: %s\r\n' \
      '\r\n' % (ws_acc)
    try:
      self.request.sendall(resp.encode('ISO-8859-1'))
    except:
      self.server.logger.log(2, 'connectionresponsefailure', *self.server.Address, self.Channel.Path, *self.client_address)
      return
    self.server.logger.log(2, 'connection', *self.server.Address, self.Channel.Path, *self.client_address)
    with self.Channel.DataStore.o_condition:
      self.Channel.SendEvents.append(self.SendEvent)
    self.LastReceptionTime = time.time()
    out_handler_thread = threading.Thread(target=self.handle_out)
    out_handler_thread.start()
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      while not self.Closed:
        if self.CloseMessageTime:
          if time.time() - self.CloseMessageTime > 2:
            self.Closed = True
            break
        if not self.FrameType and len(self.Buffer) > 0:
          ready = True
        else:
          ready = selector.select(0.5)
          if ready:
            chunk = None
            try:
              chunk = self.request.recv(65535)
            except:
              ready = False
              self.Error = 1002
              self.SendEvent.set()
              break
            if not chunk:
              ready = False
              self.Error = 1002
              self.SendEvent.set()
              break
            else:
              self.LastReceptionTime = time.time()
              if not WebSocketRequestHandler.PING_PONG_STRICT:
                self.PingTime = None
                self.PendingPings = 0
              self.Buffer += chunk
        if self.Channel.Closed:
          self.SendEvent.set()
        if WebSocketRequestHandler.PING_PONG_STRICT and self.PingTime:
          if time.time() - self.PingTime > WebSocketRequestHandler.PONG_TIMEOUT:
            self.Error = 1002
            self.SendEvent.set()
            break
        if not ready:
          if time.time() - self.LastReceptionTime > WebSocketRequestHandler.MAX_INACTIVE_TIME:
            self.Error = 1002
            self.SendEvent.set()
            break
          continue
        self.get_type()
        if self.FrameType == 'bad':
          self.Error = 1002
          self.SendEvent.set()
          break
        if not self.get_length():
          continue
        if not self.check_mask():
          self.Error = 1002
          self.SendEvent.set()
          break
        if len(self.Buffer) < self.FrameLength:
          continue
        if not self.get_data():
          self.Error = 1002
          self.SendEvent.set()
          break
        if self.FrameType == 'close':
          if self.CloseMessageTime:
            self.Closed = True
            self.server.logger.log(2, 'endack', *self.server.Address, self.Channel.Path, *self.client_address)
            break
          else:
            self.server.logger.log(2, 'endnotification', *self.server.Address, self.Channel.Path, *self.client_address)
            self.ClientClosing = True
            self.SendEvent.set()
            break
        elif self.FrameType == 'ping':
          self.SendEvent.set()
          self.purge_frame()
        elif self.FrameType == 'pong':
          if self.PongData == b'ping':
            self.PingTime = None
            self.PendingPings = 0
          self.purge_frame()
        elif self.FrameType == 'data':
          if self.MessageReady:
            if self.Channel.DataStore.incoming_text_only and self.MessageType != 'text':
              self.Error = 1003
              self.SendEvent.set()
              break
            if not self.Channel.Closed:
              self.server.logger.log(2, 'datareceipt', *self.server.Address, self.Channel.Path, *self.client_address, self.MessageData)
              self.Channel.DataStore.add_incoming(self.MessageData)
            self.MessageData = None
            self.MessageReady = False
            self.MessageType = None
          self.purge_frame()
    if out_handler_thread.is_alive():
      try:
        out_handler_thread.join()
      except:
        pass
    with self.Channel.DataStore.o_condition:
      self.Channel.SendEvents.remove(self.SendEvent)
    self.server.logger.log(2, 'connectionend', *self.server.Address, self.Channel.Path, *self.client_address)


class WebSocketServerChannel:

  def __init__(self, path, datastore):
    self.Path = path
    self.DataStore = datastore
    self.SendEvents = []
    self.Closed = False


class ThreadedWebSocketServer(socketserver.ThreadingTCPServer):

  request_queue_size = 100
  block_on_close = False

  def server_bind(self):
    self.__dict__['_BaseServer__is_shut_down'].set()
    try:
      self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except:
      pass
    super().server_bind()

  def shutdown(self):
    self.__dict__['_BaseServer__shutdown_request'] = True
    self.socket.close()
    super().shutdown()

  def server_close(self):
    pass


class WebSocketServer:

  def __init__(self, WebSocketServerAddress, verbosity=0):
    self.verbosity = verbosity
    self.Channels = {}
    self.Address = WebSocketServerAddress
    self.is_running = None
    self.shutdown_lock = threading.Lock()

  def _sendevents_dispatcher(self, channel):
    with channel.DataStore.o_condition:
      for se in channel.SendEvents:
        se.set()
      while not channel.Closed:
        channel.DataStore.o_condition.wait()
        for se in channel.SendEvents:
          se.set()

  def open(self, Path, WebSocketDataStore):
    path = Path.lstrip('/').strip()
    channel = WebSocketServerChannel(path, WebSocketDataStore)
    with self.shutdown_lock:
      if not self.is_running:
        return False
      if self.Channels.setdefault(path, channel) is not channel:
        return False
      t = threading.Thread(target=self._sendevents_dispatcher, args=(channel,))
      t.start()
    self.WebSocketServerInstance.logger.log(2, 'open', *self.Address, channel.Path)
    return True

  def close(self, Path, no_lock=False):
    path = Path.lstrip('/').strip()
    if not no_lock:
      self.shutdown_lock.acquire()
    if not self.is_running:
      if not no_lock:
        self.shutdown_lock.release()
      return False
    channel = self.Channels.pop(path, None)
    if channel is None:
      if not no_lock:
        self.shutdown_lock.release()
      return False
    channel.Closed = True
    try:
      channel.DataStore.notify_outgoing()
    except:
      pass
    if not no_lock:
      self.shutdown_lock.release()
    self.WebSocketServerInstance.logger.log(2, 'close', *self.Address, channel.Path)
    return True

  def _run(self):
    slr = False
    try:
      with ThreadedWebSocketServer(self.Address, WebSocketRequestHandler) as self.WebSocketServerInstance:
        self.WebSocketServerInstance.logger = log_event('websocket', self.verbosity)
        self.WebSocketServerInstance.logger.log(2, 'start', *self.Address)
        self.WebSocketServerInstance.Address = self.Address
        self.WebSocketServerInstance.Channels = self.Channels
        self.shutdown_lock.release()
        slr = True
        self.WebSocketServerInstance.serve_forever()
    except:
      if self.is_running:
        self.is_running = False
        log_event('websocket', self.verbosity).log(1, 'fail', *self.Address)
      if not slr:
        self.shutdown_lock.release()
    self.is_running = None

  def start(self):
    self.shutdown_lock.acquire()
    if self.is_running is not None:
      self.shutdown_lock.release()
      return
    self.is_running = True
    t = threading.Thread(target=self._run)
    t.start()
    self.shutdown_lock.acquire()
    self.shutdown_lock.release()
      
  def shutdown(self):
    with self.shutdown_lock:
      if self.is_running:
        pathes = list(self.Channels.keys())
        for path in pathes:
          self.close(path, no_lock=True)
        self.is_running = False
        try:
          self.WebSocketServerInstance.logger.log(2, 'shutdown', *self.Address)
          self.WebSocketServerInstance.shutdown()
        except:
          pass
      self.is_running = False
  

class DLNAWebInterfaceControlDataStore(WebSocketDataStore):

  def __init__(self, IncomingEvent=None):
    super().__init__(IncomingEvent)
    self.outgoing = [None, None, None, None, None, None, None, None, None, None]
    self.outgoing_seq = [None, None, None, None, None, None, None, None, None, None]
    self.incoming_text_only = True
    self.set_before_shutdown('close')

  @property
  def Status(self):
    return self.outgoing[0]

  @Status.setter
  def Status(self, value):
    self.set_outgoing(0, value, True)

  @property
  def Position(self):
    return self.outgoing[1]

  @Position.setter
  def Position(self, value):
    self.set_outgoing(1, value, True)

  @property
  def Duration(self):
    if self.outgoing[2]:
      return self.outgoing[2][9:]
    else:
      return self.outgoing[2]

  @Duration.setter
  def Duration(self, value):
    if value != None:
      self.set_outgoing(2, 'Duration:' + value, True)
    else:
      self.set_outgoing(2, None)

  @property
  def URL(self):
    if self.outgoing[3]:
      return html.unescape(self.outgoing[3][4:])
    else:
      return self.outgoing[3]

  @URL.setter
  def URL(self, value):
    if value != None:
      self.set_outgoing(3, 'URL:' + html.escape(value), True)
    else:
      self.set_outgoing(3, None)

  @property
  def Playlist(self):
    if self.outgoing[4]:
      return self.outgoing[4][9:].splitlines()[1:]
    else:
      return self.outgoing[4]

  @Playlist.setter
  def Playlist(self, value):
    if value != None:
      self.set_outgoing(4, 'Playlist:\r\n' + '\r\n'.join(value), True)
    else:
      self.set_outgoing(4, None)

  @property
  def Current(self):
    if self.outgoing[5]:
      if self.outgoing[5][8:].lstrip().isdecimal():
        return int(self.outgoing[5][8:]) - 1
      else:
        return -1
    else:
      return self.outgoing[5]

  @Current.setter
  def Current(self, value):
    if value != None:
      self.set_outgoing(5, 'Current:' + str(value + 1), False)
    else:
      self.set_outgoing(5, None)

  @property
  def ShowStartFrom(self):
    if self.outgoing[6] != None:
      return self.outgoing[6][14:] == 'true'
    else:
      return self.outgoing[6]

  @ShowStartFrom.setter
  def ShowStartFrom(self, value):
    if value != None:
      self.set_outgoing(6, 'Showstartfrom:' + ('true' if value else 'false'), True)
    else:
      self.set_outgoing(6, None)

  @property
  def Shuffle(self):
    if self.outgoing[7] != None:
      return self.outgoing[7][8:] == 'true'
    else:
      return self.outgoing[7]

  @Shuffle.setter
  def Shuffle(self, value):
    if value != None:
      self.set_outgoing(7, 'Shuffle:' + ('true' if value else 'false'), True)
    else:
      self.set_outgoing(7, None)      

  @property
  def Mute(self):
    if self.outgoing[8] != None:
      return (True if self.outgoing[8][5:] == 'true' else (False if self.outgoing[8][5:] == 'false' else ''))
    else:
      return self.outgoing[8]

  @Mute.setter
  def Mute(self, value):
    if value != None:
      self.set_outgoing(8, 'Mute:' + ('true' if value == True else ('false' if value == False else 'none')), True)
    else:
      self.set_outgoing(8, None)

  @property
  def Volume(self):
    if self.outgoing[9] != None:
      if self.outgoing[9][7:].lstrip().isdecimal():
        return int(self.outgoing[9][7:])
      else:
        return 0
    else:
      return self.outgoing[9]

  @Volume.setter
  def Volume(self, value):
    if value != None:
      self.set_outgoing(9, 'Volume:' + str(value), True)
    else:
      self.set_outgoing(9, None)

  @property
  def Command(self):
    return self.get_incoming()

  @Command.setter
  def Command(self, value):
    self.add_incoming(value)

  @property
  def Redirect(self):
    if self.before_shutdown == 'redirect':
      return True
    else:
      return False

  @Redirect.setter
  def Redirect(self, value):
    if value:
      self.set_before_shutdown('redirect')
    else:
      self.set_before_shutdown('close')


class DLNAWebInterfaceRenderersDataStore(WebSocketDataStore):

  def __init__(self, IncomingEvent=None):
    super().__init__(IncomingEvent)
    self.incoming_text_only = True
    self.add_outgoing('end')
    self.set_before_shutdown('close')

  @property
  def Message(self):
    if len(self.outgoing) > 1:
      return self.outgoing[-2]
    else:
      return None

  @Message.setter
  def Message(self, value):
    self.nest_outgoing(value)

  @property
  def Redirect(self):
    if self.before_shutdown == 'redirect':
      return True
    else:
      return False

  @Redirect.setter
  def Redirect(self, value):
    if value:
      self.set_before_shutdown('redirect')
    else:
      self.set_before_shutdown('close')


class DLNAWebInterfaceRequestHandler(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"
  
  HTML_WAIT_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page d\'attente</title>\r\n' \
  '  <head>\r\n' \
  '    <meta http-equiv="refresh" content="5;URL=/">\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;Interface occupée<br></h1>\r\n' \
  '    <p">Quelques secondes de patience...</p>\r\n' \
  '</body>\r\n' \
  '</html>'

  def log_message(self, *args, **kwargs):
    if self.server.logger.verbosity < 2:
      pass
    else:
      super().log_message(*args, **kwargs)

  def send_head(self):
    if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING :
      self.close_connection = True
      self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      return None
    self.server.logger.log(1, 'response', *self.client_address, self.raw_requestline)
    if not self.server.Interface.html_ready:
      nb_wait = 0
      while self.server.Interface.Status != DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING and not self.server.Interface.html_ready and nb_wait < 8:
        time.sleep(0.5)
        nb_wait +=1
      if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING :
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        except:
          pass
        return None
      if not self.server.Interface.html_ready:
        html_wait = DLNAWebInterfaceRequestHandler.HTML_WAIT_TEMPLATE.encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(html_wait))
        f = BytesIO(html_wait)
        self.end_headers()
        return f
    if self.path == '/':
      self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
      if self.server.Interface.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        self.send_header("Location", "/start.html")
      elif self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.send_header("Location", "/control.html")
      else:
        self.close_connection = True
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return
      self.send_header("Content-Length", 0)
      self.end_headers()
      return None
    if self.path.lower() == '/control.html':
      if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", len(self.server.Interface.html_control))
        f = BytesIO(self.server.Interface.html_control)
        self.end_headers()
        return f
      else:
        self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
        self.send_header("Location", "/start.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
        return None
    elif self.path.lower() == '/start.html':
      if self.server.Interface.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", len(self.server.Interface.html_start))
        f = BytesIO(self.server.Interface.html_start)
        self.end_headers()
        return f
      else:
        self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
        self.send_header("Location", "/control.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
        return None
    elif self.path.lower()[:5] == '/icon':
      if self.server.Interface.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        renderer_icon = b""
        renderer_icon_ct = ""
        try:
          renderer = self.server.Interface.DLNAControllerInstance.Renderers[int(self.path[5:])]
          renderer_hip = self.server.Interface.DLNAControllerInstance.Hips[int(self.path[5:])]
          if renderer.IconURL:
            icon_resp = HTTPRequest(renderer.IconURL, timeout=5, ip=renderer_hip)
            if icon_resp.code == '200':
              if icon_resp.body:
                renderer_icon = icon_resp.body
                renderer_icon_ct = icon_resp.header('content-type', "image")
        except:
          pass
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", renderer_icon_ct)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", len(renderer_icon))
        f = BytesIO(renderer_icon)
        self.end_headers()
        return f
      else:
        self.close_connection = True
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return
    elif self.path.lower()[:10] == '/upnp.html':
      if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_START and self.server.Interface.DLNAClientInstance.search(complete=True):
        try:
          url = urllib.parse.urlparse(self.path)
          path = self.path.replace('/upnp.html;refresh', '/upnp.html')
          if len(path) == 10:
            if url.params == 'refresh':
              self.server.Interface._discover_servers()
              raise
            html_upnp = self.server.Interface.HTML_UPNP_TEMPLATE.replace('##UPNP-VAL##','0').replace('##UPNP-TITLE##','').replace('##UPNP-OBJ##', self.server.Interface.build_server_html()).encode('utf-8')
          else:
            req = urllib.parse.parse_qs(url.query, keep_blank_values=True)
            server = self.server.Interface.DLNAClientInstance.search(uuid=req['uuid'][0])
            if not server:
              raise
            html_upnp = None
            if url.params != 'refresh':
              for c in self.server.Interface.DLNAClientCache:
                if c[0] == path:
                  html_upnp = c[1]
                  break
            if not html_upnp or url.params == 'refresh':
              content = self.server.Interface.DLNAClientInstance.get_Content(server, req['id'][0], self.server.Interface.DLNAClientStop)
              if not content and url.params == 'refresh':
                for c in self.server.Interface.DLNAClientCache:
                  if c[0] == path:
                    c[0] = '/upnp.html?uuid=0&id=0'
                    c[1] = self.server.Interface.HTML_UPNP_TEMPLATE.replace('##UPNP-VAL##','e').replace('##UPNP-TITLE##','').replace('##UPNP-OBJ##', '').encode('utf-8')
                    c[2] = []
                    c[3] = []
                    break
              html_upnp = self.server.Interface.HTML_UPNP_TEMPLATE.replace('##UPNP-VAL##','1'if len(content[2]) >= 1 else '0').replace('##UPNP-TITLE##', html.escape(content[0]['title'])).replace('##UPNP-OBJ##', self.server.Interface.build_server_html(req['uuid'][0], content)).encode('utf-8')
              for c in self.server.Interface.DLNAClientCache:
                if c[0] == path:
                  c[1] = html_upnp
                  c[2] = list(e['uri'] for e in content[2])
                  c[3] = list({'object.item.videoitem': 'video', 'object.item.audioitem': 'audio', 'object.item.imageitem': 'image'}.get(e['class'].lower(), 'video') for e in content[2])
                  break
              else:
                self.server.Interface.DLNAClientCache.append([path, html_upnp, list(e['uri'] for e in content[2]), list({'object.item.videoitem': 'video', 'object.item.audioitem': 'audio', 'object.item.imageitem': 'image'}.get(e['class'].lower(), 'video') for e in content[2])])
              if url.params == 'refresh':
                raise
        except:
          html_upnp = self.server.Interface.HTML_UPNP_TEMPLATE.replace('##UPNP-VAL##','e').replace('##UPNP-TITLE##','').replace('##UPNP-OBJ##', '').encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", len(html_upnp))
        f = BytesIO(html_upnp)
        self.end_headers()
        return f
      elif self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_START:
        html_upnp = self.server.Interface.HTML_UPNP_TEMPLATE.replace('##UPNP-VAL##','e').replace('##UPNP-TITLE##','').replace('##UPNP-OBJ##', '').encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", len(html_upnp))
        f = BytesIO(html_upnp)
        self.end_headers()
        return f
      else:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        except:
          pass
        return None
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      except:
        pass
      return None

  def do_POST(self):
    if self.path == '/control.html':
      qs = self.rfile.read(int(self.headers.get("Content-Length")))
      self.do_GET()
    elif self.path == '/start.html':
      qs = self.rfile.read(int(self.headers.get("Content-Length")))
      self.server.logger.log(2, 'formdatareceipt', qs, *self.client_address)
      media_src = ''
      media_startfrom = '0:00:00'
      media_subsrc = ''
      renderer_ind = ''
      renderer = None
      try:
        data = urllib.parse.parse_qs(qs.decode('utf-8'))
        if 'MediaSrc' in data:
          media_src = data['MediaSrc'][0]
        if 'MediaStartFrom' in data:
          media_startfrom = (data['MediaStartFrom'][0])[1:]
        if 'MediaSubSrc' in data:
          media_subsrc = data['MediaSubSrc'][0]
        if 'RendererInd' in data:
          renderer = self.server.Interface.DLNAControllerInstance.Renderers[int(data['RendererInd'][0])]
      except:
        pass
      if media_src and renderer:
        self.server.post_lock.acquire()
        if self.server.Interface.TargetStatus == DLNAWebInterfaceServer.INTERFACE_START:
          self.server.logger.log(1, 'playbackaccept', media_src, LSTRINGS['webinterface'].get('playbacksub', 'playbacksub %s') % media_subsrc if media_subsrc else '', media_startfrom, renderer.FriendlyName, *self.client_address)
          self.server.Interface.Renderer = renderer
          self.server.Interface.Renderer_uuid = renderer.UDN[5:]
          self.server.Interface.Renderer_name = renderer.FriendlyName
          self.server.Interface.MediaSrc = media_src
          self.server.Interface.MediaPosition = media_startfrom
          self.server.Interface.MediaSubSrc = media_subsrc
          self.server.Interface.TargetStatus = DLNAWebInterfaceServer.INTERFACE_CONTROL
          self.server.Interface.html_ready = False
          self.server.Interface.RenderersEvent.set()
        else:
          self.server.logger.log(1, 'playbackreject', media_src, LSTRINGS['webinterface'].get('playbacksub', 'playbacksub %s') % media_subsrc if media_subsrc else '', media_startfrom, renderer.FriendlyName, *self.client_address)
        self.server.post_lock.release()
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/control.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
      else:
        self.server.logger.log(2, 'formdatareject', qs, *self.client_address)
        self.do_GET()
    else:
      self.close_connection = True
      self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      return None

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


def _position_to_seconds(position):
  try:
    sec = sum(int(t[0])*t[1] for t in zip(reversed(position.rsplit('.', 1)[0].split(':')), [1,60,3600]))
  except:
    return None
  return sec

def _seconds_to_position(seconds):
  try:
    pos = '%d:%02d:%02d' % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)
  except:
    return None
  return pos


class DLNAWebInterfaceServer:

  INTERFACE_NOT_RUNNING = 0
  INTERFACE_DISPLAY_RENDERERS = 1
  INTERFACE_START = 2
  INTERFACE_CONTROL = 3
  
  SERVER_MODE_GAPLESS = 3
  SERVER_MODE_NONE = 4
  
  HTML_UPNP_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '  <head>\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Navigation UPnP</title>\r\n' \
  '    <script>\r\n' \
  '      page_loading = false;\r\n' \
  '      function open_link_abs(uri) {\r\n' \
  '        if (page_loading) {return;}\r\n' \
  '        page_loading = true;\r\n' \
  '        if (window.parent.window.getSelection) {window.parent.window.getSelection().removeAllRanges();}\r\n' \
  '        window.parent.document.getElementById("upnp_loading").style.color = "rgb(225,225,225)";\r\n' \
  '        window.parent.document.getElementById("upnp_loading").style.animationName = "rotating";\r\n' \
  '        document.styleSheets[0].cssRules[1].style.color="rgb(225,225,225)";\r\n' \
  '        document.styleSheets[0].cssRules[1].style.cursor="default";\r\n' \
  '        let bc = "";\r\n' \
  '        for (let i=0; i<window.parent.upnp_hist.length; i++) {\r\n' \
  '          if (i==0) {\r\n' \
  '            bc = "<span style=\\"font-size:200%;line-height:100%;\\">&capand;</span>&nbsp;&sc;&nbsp;";\r\n' \
  '          } else {\r\n' \
  '            bc = bc + "<span>" + window.parent.upnp_hist[i][1] + "</span>&nbsp;&sc;&nbsp;";\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        if (document.links.length == 0) {bc = bc.slice(0, -10);}\r\n' \
  '        window.parent.document.getElementById("upnp_bc").innerHTML = bc;\r\n' \
  '        window.location = uri;\r\n'\
  '      }\r\n' \
  '      function open_link(uri) {\r\n' \
  '        let abs_uri = "";\r\n' \
  '        if (uri.indexOf("uuid=") != -1) {\r\n' \
  '          abs_uri = window.location.toString() + "?" + uri;\r\n'\
  '        } else if (uri.indexOf("id=") == -1) {\r\n' \
  '          abs_uri = uri;\r\n'\
  '        } else {\r\n' \
  '          abs_uri = window.location.toString().substring(0,window.location.toString().indexOf("&id=")) + "&" + uri;\r\n'\
  '        }\r\n' \
  '        open_link_abs(abs_uri);\r\n' \
  '      }\r\n' \
  '    </script>\r\n' \
  '    <style type="text/css">\r\n' \
  '      a {\r\n' \
  '        color: rgb(225,225,225);\r\n' \
  '        text-decoration: none;\r\n' \
  '      }\r\n' \
  '      a:hover {\r\n' \
  '        color: rgb(200,250,240);\r\n' \
  '        cursor: pointer;\r\n' \
  '      }\r\n' \
  '    </style>\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50,0);color:rgb(225,225,225);font-size:20px;line-height:10px;">\r\n' \
  '    <p id="upnp_val" style="display:none;">##UPNP-VAL##</p>\r\n' \
  '    <p id="upnp_title" style="display:none;">##UPNP-TITLE##</p>\r\n' \
  '##UPNP-OBJ##' \
  '  </body>\r\n' \
  '</html>'
  HTML_START_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '  <head>\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page de démarrage</title>\r\n' \
  '    <script>\r\n' \
  '      selected = "";\r\n' \
  '      selected_set = "";\r\n' \
  '      upnp_hist = [];\r\n' \
  '      displayed = false;\r\n' \
  '      function new_socket() {\r\n' \
  '        try {\r\n' \
  '          socket = new WebSocket("ws://" + location.hostname + ":" + String(parseInt(location.port,10)+1) + "/start");\r\n' \
  '        } catch(exception) {\r\n' \
  '          window.alert("{#jmwebsocketfailure#}");\r\n' \
  '        }\r\n' \
  '        socket.onerror = function(event) {\r\n' \
  '          window.location.reload(true);\r\n' \
  '        }\r\n' \
  '        socket.onmessage = function(event) {\r\n' \
  '           if (event.data == "close") {\r\n' \
  '            socket.onclose = function(event) {};\r\n' \
  '            socket.close();\r\n' \
  '            document.getElementById("table").innerHTML = "{#jmrenderersclosed#}";\r\n' \
  '            document.getElementById("play").style.display = "none";\r\n' \
  '            document.getElementById("reset").style.display = "none";\r\n' \
  '            upnp_cancel();\r\n' \
  '            document.getElementById("upnp_but").style.display = "none";\r\n' \
  '          } else if (event.data == "redirect") {\r\n' \
  '            window.location.replace("##CONTROL-URL##");\r\n' \
  '          } else if (event.data == "upnp") {\r\n' \
  '            document.getElementById("upnp_but").style.display = "block";\r\n' \
  '          } else if (event.data == "end" && !displayed) {\r\n' \
  '            displayed = true;\r\n' \
  '            document.getElementById("Renderers").style.display = "table";\r\n' \
  '          } else {\r\n' \
  '            let data_list = event.data.split("&");\r\n' \
  '            if (data_list.length >= 2) {\r\n' \
  '              if (data_list[0] == "command=add") {\r\n' \
  '                let data = [];\r\n' \
  '                for (let i=1; i<data_list.length; i++) {\r\n' \
  '                  let data_name_value = data_list[i].split("=");\r\n' \
  '                  if (data_name_value.length == 2) {\r\n' \
  '                    data.push([data_name_value[0], decodeURIComponent(data_name_value[1])]);\r\n' \
  '                  }\r\n' \
  '                }\r\n' \
  '                if (data.length > 0) {add_renderer(data);}\r\n' \
  '              } else if (data_list[0] == "command=sel") {\r\n' \
  '                let data_name_value = data_list[1].split("=");\r\n' \
  '                if (data_name_value.length == 2) {\r\n' \
  '                  let data = [data_name_value[0], data_name_value[1]];\r\n' \
  '                  sel_renderer(data);\r\n' \
  '                }\r\n' \
  '              } else if (data_list[0] == "command=show") {\r\n' \
  '                let data = [];\r\n' \
  '                for (let i=1; i<data_list.length; i++) {\r\n' \
  '                  let data_name_value = data_list[i].split("=");\r\n' \
  '                  if (data_name_value.length == 2) {\r\n' \
  '                    data.push([data_name_value[0], decodeURIComponent(data_name_value[1])]);\r\n' \
  '                  }\r\n' \
  '                }\r\n' \
  '                if (data.length > 0) {show_renderer(data);}\r\n' \
  '              } else if (data_list[0] == "command=hide") {\r\n' \
  '                let data_name_value = data_list[1].split("=");\r\n' \
  '                if (data_name_value.length == 2) {\r\n' \
  '                  let data = [data_name_value[0], data_name_value[1]];\r\n' \
  '                  hide_renderer(data);\r\n' \
  '                }\r\n' \
  '              }\r\n' \
  '            }\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        socket.onclose = socket.onerror;\r\n' \
  '        window.onbeforeunload = function () {\r\n' \
  '          upnp_cancel();\r\n' \
  '          socket.onclose = function(event) {};\r\n' \
  '          socket.close();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function select_renderer(renderer) {\r\n' \
  '        if (selected != "") {document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";}\r\n' \
  '        renderer.style.color = "rgb(200,250,240)";\r\n' \
  '        selected = renderer.id.substring(9);\r\n' \
  '        document.getElementById("Renderer").value = selected;\r\n' \
  '      }\r\n' \
  '      function add_renderer(data) {\r\n' \
  '        let renderers = document.getElementById("Renderers");\r\n' \
  '        let renderer_index = "";\r\n' \
  '        let renderer_name = "";\r\n' \
  '        let renderer_ip = "";\r\n' \
  '        let renderer_icon = "";\r\n' \
  '        let renderer_status = "False";\r\n' \
  '        for (let data_item of data) {\r\n' \
  '          if (data_item[0] == "index") {\r\n' \
  '            renderer_index = data_item[1];\r\n' \
  '          } else if (data_item[0] == "name") {\r\n' \
  '            renderer_name = data_item[1];\r\n' \
  '          } else if (data_item[0] == "ip") {\r\n' \
  '            renderer_ip = data_item[1];\r\n' \
  '          } else if (data_item[0] == "icon") {\r\n' \
  '            renderer_icon = data_item[1];\r\n' \
  '          } else if (data_item[0] == "status") {\r\n' \
  '            renderer_status = data_item[1];\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        if (renderer_index != "") {\r\n' \
  '          let n_row = renderers.tBodies[0].insertRow();\r\n' \
  '          n_row.id = "renderer_" + renderer_index;\r\n' \
  '          let n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_icon";\r\n' \
  '          n_cell.innerHTML = "<img style=\'height:36px;width:auto;vertical-align:middle;\' src=\'" + renderer_icon + "\' alt=\' \'/>";\r\n' \
  '          n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_name";\r\n' \
  '          n_cell.innerHTML = renderer_name;\r\n' \
  '          n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_ip";\r\n' \
  '          n_cell.innerHTML = renderer_ip;\r\n' \
  '          n_cell.style.fontSize="70%";\r\n' \
  '          if (renderer_status == "True") {\r\n' \
  '            n_row.style.display = "table-row";\r\n' \
  '          } else {\r\n' \
  '            n_row.style.display = "none";\r\n' \
  '          }\r\n' \
  '          n_row.onclick = function() {select_renderer(this);};\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function sel_renderer(data) {\r\n' \
  '        if (data[0] == "index") {\r\n' \
  '          selected_set = data[1];\r\n' \
  '          if (selected == "" && document.getElementById("renderer_" + selected_set).style.display != "none") {\r\n' \
  '            selected = selected_set;\r\n' \
  '            document.getElementById("renderer_" + selected).style.color = "rgb(200,250,240)";\r\n' \
  '            document.getElementById("Renderer").value = selected;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function show_renderer(data) {\r\n' \
  '        let renderer_index = "";\r\n' \
  '        let renderer_icon = "";\r\n' \
  '        for (let data_item of data) {\r\n' \
  '          if (data_item[0] == "index") {\r\n' \
  '            renderer_index = data_item[1];\r\n' \
  '          } else if (data_item[0] == "icon") {\r\n' \
  '            renderer_icon = data_item[1];\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        if (renderer_index != "") {\r\n' \
  '          document.getElementById("renderer_" + renderer_index).style.display = "table-row";\r\n' \
  '          if (renderer_icon != "") {document.getElementById("renderer_" + renderer_index).cells[0].getElementsByTagName("img").item(0).setAttribute("src", renderer_icon);}\r\n' \
  '          if (selected == "" && selected_set == renderer_index) {\r\n' \
  '            selected = selected_set;\r\n' \
  '            document.getElementById("renderer_" + selected).style.color = "rgb(200,250,240)";\r\n' \
  '            document.getElementById("Renderer").value = selected;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function hide_renderer(data) {\r\n' \
  '        if (data[0] == "index") {\r\n' \
  '          document.getElementById("renderer_" + data[1]).style.display = "none";\r\n' \
  '          if (selected == data[1]) {\r\n' \
  '            document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";\r\n' \
  '            selected="";\r\n' \
  '            document.getElementById("Renderer").value = selected;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function reset_button() {\r\n' \
  '        if (selected != "") {document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";}\r\n' \
  '        selected = "";\r\n' \
  '        if (selected_set != "") {\r\n' \
  '          if (document.getElementById("renderer_" + selected_set).style.display != "none") {\r\n' \
  '            document.getElementById("renderer_" + selected_set).style.color="rgb(200,250,240)";\r\n' \
  '            selected = selected_set;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        document.getElementById("Renderer").value = selected;\r\n' \
  '        document.getElementById("URL-").value = URL_set;\r\n' \
  '        document.getElementById("StartFrom").value = StartFrom_set;\r\n' \
  '      }\r\n' \
  '      function play_button() {\r\n' \
  '        let url_ok = true;\r\n' \
  '        let url_lines = document.getElementById("URL-").value.split(/\\r?\\n/g);\r\n' \
  '        document.getElementById("URL").value=url_lines[0];\r\n' \
  '        if (!document.getElementById("URL").checkValidity()) {\r\n' \
  '          url_ok = false;\r\n' \
  '          window.alert("{#jmentervalidurl#}");\r\n' \
  '        } else {\r\n' \
  '          if (url_lines.length >= 2) {\r\n' \
  '            document.getElementById("SUBURL").value=url_lines[1];\r\n' \
  '            if (!document.getElementById("SUBURL").checkValidity()) {\r\n' \
  '              url_ok = false;\r\n' \
  '              window.alert("{#jmentervalidsuburl#}");\r\n' \
  '            }\r\n' \
  '         }\r\n' \
  '        }\r\n' \
  '        if (url_ok) {\r\n' \
  '          if (selected == "") {\r\n' \
  '            window.alert("{#jmselectrenderer#}");\r\n' \
  '          } else {\r\n' \
  '          document.getElementById("form").submit();\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function get_elt (uri, elt) {\r\n' \
  '        let data_list = uri.split("?");\r\n' \
  '        if (data_list.length <= 1) {return "";}\r\n' \
  '        data_list = data_list[1].split("&");\r\n' \
  '        for (let i=0; i<data_list.length; i++) {\r\n' \
  '          let data_name_value = data_list[i].split("=");\r\n' \
  '          if (data_name_value.length == 2 && data_name_value[0].toLowerCase() == elt) {return decodeURIComponent(data_name_value[1]);}\r\n' \
  '        }\r\n' \
  '        return "";\r\n' \
  '      }\r\n' \
  '      function get_uuid (uri) {\r\n' \
  '        return get_elt (uri, "uuid");\r\n' \
  '      }\r\n' \
  '      function get_id (uri) {\r\n' \
  '        return get_elt (uri, "id");\r\n' \
  '      }\r\n' \
  '      function upnp_button() {\r\n' \
  '        if (document.getElementById("upnp_content").contentWindow.location.toString().indexOf("upnp") == -1 || document.getElementById("upnp_content").contentWindow.location.toString().slice(-9) == "upnp.html") {document.getElementById("upnp_content").contentWindow.location = "##UPNP-URL##";}\r\n' \
  '        document.getElementById("upnp_nav").style.display = "block";\r\n' \
  '      }\r\n' \
  '      function upnp_cancel() {\r\n' \
  '        document.getElementById("upnp_nav").style.display = "none";\r\n' \
  '      }\r\n' \
  '      function upnp_back() {\r\n' \
  '        if (window.getSelection) {window.getSelection().removeAllRanges();}\r\n' \
  '        if (upnp_hist.length >= 2) {\r\n' \
  '          document.getElementById("upnp_content").contentWindow.location = upnp_hist[upnp_hist.length - 2][0];\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function upnp_validate() {\r\n' \
  '        if (document.getElementById("upnp_content").contentWindow.document.getElementById("upnp_val").innerHTML == 1) {\r\n' \
  '          let obj_uuid = get_uuid(document.getElementById("upnp_content").contentWindow.location.toString());\r\n' \
  '          let obj_id = get_id(document.getElementById("upnp_content").contentWindow.location.toString());\r\n' \
  '          if (obj_uuid != "" && obj_id !="") {\r\n' \
  '            document.getElementById("URL-").value = "upnp://" + obj_uuid + "?" + obj_id;\r\n' \
  '            upnp_cancel();\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function open_link(uri) {\r\n' \
  '        if (window.getSelection) {window.getSelection().removeAllRanges();}\r\n' \
  '        document.getElementById("upnp_content").contentWindow.open_link_abs(uri);\r\n' \
  '      }\r\n' \
  '      function upnp_load() {\r\n' \
  '        let page_ad = document.getElementById("upnp_content").contentWindow.location.toString();\r\n' \
  '        if (page_ad == "about:blank") {return;}\r\n' \
  '        for (let i=0; i<upnp_hist.length; i++) {\r\n' \
  '          if (upnp_hist[i][0] == page_ad) {\r\n' \
  '             upnp_hist = upnp_hist.splice(0, i);\r\n' \
  '             break;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        document.getElementById("upnp_loading").style.animationName = "";\r\n' \
  '        document.getElementById("upnp_loading").style.color = "rgb(40,45,50)";\r\n' \
  '        let upnp_content = document.getElementById("upnp_content").contentWindow.document\r\n' \
  '        if (upnp_content.getElementById("upnp_val").innerHTML == "e") {\r\n' \
  '          if (upnp_hist.length == 0) {\r\n' \
  '            upnp_cancel();\r\n' \
  '          } else {\r\n' \
  '            document.getElementById("upnp_content").contentWindow.location = upnp_hist[upnp_hist.length - 1][0];\r\n' \
  '          }\r\n' \
  '          return;\r\n' \
  '        }\r\n' \
  '        upnp_hist.push([page_ad, upnp_content.getElementById("upnp_title").innerHTML]);\r\n' \
  '        let bc = "";\r\n' \
  '        for (let i=0; i<upnp_hist.length; i++) {\r\n' \
  '          if (i == 0 && upnp_hist.length==1) {\r\n' \
  '            bc = "<a class=\\"refresh\\" style=\\"font-size:200%;line-height:100%;\\" href=\\"javascript:open_link(\'" + encodeURIComponent(upnp_hist[0][0]+ ";refresh") + "\')\\">&capand;</a>&nbsp;&sc;&nbsp;";\r\n' \
  '          } else if (i == 0) {\r\n' \
  '            bc = "<a style=\\"font-size:200%;line-height:100%;\\" href=\\"javascript:open_link(\'" + encodeURIComponent(upnp_hist[0][0]) + "\')\\">&capand;</a>&nbsp;&sc;&nbsp;";\r\n' \
  '          } else if (i < upnp_hist.length -1) {\r\n' \
  '            bc = bc + "<a href=\\"javascript:open_link(\'" + encodeURIComponent(upnp_hist[i][0]) + "\')\\">" + upnp_hist[i][1] + "</a>&nbsp;&sc;&nbsp;";\r\n' \
  '          } else {\r\n' \
  '            bc = bc + "<a class=\\"refresh\\" href=\\"javascript:open_link(\'" + encodeURIComponent(upnp_hist[i][0].replace("?", ";refresh?")) + "\')\\">" + upnp_hist[i][1] + "</a>&nbsp;&sc;&nbsp;";\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        if (upnp_content.links.length == 0) {bc = bc.slice(0, -10);}\r\n' \
  '        document.getElementById("upnp_bc").innerHTML = bc;\r\n' \
  '        let but_val = document.getElementById("upnp_validate");\r\n' \
  '        if (upnp_content.getElementById("upnp_val").innerHTML == "1") {\r\n' \
  '          but_val.onclick = upnp_validate;\r\n'\
  '          but_val.style.cursor = "pointer";\r\n' \
  '          but_val.style.color = "rgb(200,250,240)";\r\n' \
  '        } else {\r\n' \
  '          but_val.onclick = function() {};\r\n'\
  '          but_val.style.cursor = "default";\r\n' \
  '          but_val.style.color = "rgb(5,60,50)";\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '    </script>\r\n' \
  '    <style type="text/css">\r\n' \
  '      table {\r\n' \
  '        border: 1px solid rgb(0,0,0);\r\n' \
  '        border-collapse:collapse;\r\n' \
  '        margin-left: 10px;\r\n' \
  '        width: 85%;\r\n' \
  '        table-layout:fixed;\r\n' \
  '      }\r\n' \
  '      td {\r\n' \
  '        border-top: 1px solid rgb(20,20,20);\r\n' \
  '        padding: 5px;\r\n' \
  '        vertical-align:middle;\r\n' \
  '        word-wrap:break-word;\r\n' \
  '        height:20px;\r\n' \
  '      }\r\n' \
  '      td:hover {\r\n' \
  '        cursor:pointer\r\n' \
  '      }\r\n' \
  '      input, textarea {\r\n' \
  '        border: none;\r\n' \
  '        background-color:rgb(30,30,35);\r\n' \
  '        color:rgb(200,250,240);\r\n' \
  '        margin-left:30px;\r\n' \
  '        margin-top:10px;\r\n' \
  '        vertical-align:middle;\r\n' \
  '        word-wrap:break-word;\r\n' \
  '        overflow-y:auto;\r\n' \
  '      }\r\n' \
  '      label {\r\n' \
  '        vertical-align:middle;\r\n' \
  '      }\r\n' \
  '      button {\r\n' \
  '        vertical-align:middle;\r\n' \
  '        border:none;\r\n' \
  '        padding-top:20px;\r\n' \
  '        padding-bottom:20px;\r\n' \
  '        margin-left:10%;\r\n' \
  '        margin-right:10%;\r\n' \
  '        width:250px;\r\n' \
  '        font-size:100%;\r\n' \
  '        font-weight:bold;\r\n' \
  '        cursor:pointer;\r\n' \
  '        display:##DISPLAY##;\r\n' \
  '      }\r\n' \
  '      .modal {\r\n' \
  '        display: none;\r\n' \
  '        position: fixed;\r\n' \
  '        z-index: 1;\r\n' \
  '        left: 0;\r\n' \
  '        top: 80px;\r\n' \
  '        width: 100%;\r\n' \
  '        height: 100%;\r\n' \
  '        overflow: auto;\r\n' \
  '        background-color: rgb(40,45,50);\r\n' \
  '        background-color: rgba(40,45,50,0.97);\r\n' \
  '      }\r\n' \
  '      a {\r\n' \
  '        color: rgb(225,225,225);\r\n' \
  '        text-decoration: none;\r\n' \
  '      }\r\n' \
  '      a:hover {\r\n' \
  '        color: rgb(200,250,240);\r\n' \
  '        cursor: pointer;\r\n' \
  '      }\r\n' \
  '      .refresh {\r\n' \
  '        cursor: url(\'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" style="font-size:30px;font-weight:bold;"><text x="2" y="-4" fill="white" rotate="90">↻</text></svg>\') 10 10, progress !important;\r\n' \
  '      }\r\n' \
  '      @keyframes rotating {\r\n' \
  '        0% {transform:rotate(0deg);vertical-align:0px;margin-bottom:0px;}\r\n' \
  '        25% {transform:rotate(90deg);vertical-align:-3px;margin-bottom:-3px;margin-left:2px;margin-right:-2px;}\r\n' \
  '        50% {transform:rotate(180deg);vertical-align:-8px;margin-bottom:-8px;margin-left:2px;margin-right:-2px;}\r\n' \
  '        75% {transform:rotate(270deg);vertical-align:-5px;margin-bottom:-5px;margin-left:-6px;margin-right:6px;}\r\n' \
  '        100% {transform:rotate(360deg);vertical-align:0px;margin-bottom:0px;}\r\n' \
  '      }\r\n' \
  '    </style>\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;{#jstart#}<br></h1>\r\n' \
  '    <div id="upnp_nav" class="modal">\r\n' \
  '      <span id="upnp_back" style="cursor:pointer;margin-left:10px;" onclick="upnp_back()">&larr;</span>&nbsp;&nbsp;<span id="upnp_validate" style="color:rgb(5,60,50);">&check;</span>&nbsp;&nbsp;<span id="upnp_cancel" style="cursor:pointer;color:rgb(250,220,200);" onclick="upnp_cancel()">&cross;</span>&nbsp;&nbsp;<div id="upnp_loading" style="color:rgb(40,45,50);animation-duration:1s;animation-iteration-count:infinite;animation-timing-function:linear;display:inline-block">&orarr;</div>&nbsp;&nbsp;<div id="upnp_bc" style="font-size:20px;display:inline-block"></div>\r\n' \
  '      <iframe id="upnp_content" src="about:blank" title="navigation UPnP" style="border:none;width:100%;height:80%;" onload="upnp_load()"> </iframe>\r\n' \
  '    </div>\r\n' \
  '    <label for="URL-" style="display:##DISPLAY##;">URL :<span id="upnp_but" style="display:none;"><button style="margin-left:5px;margin-right:0px;width:60px;height:30px;padding-left:2px;padding-right:2px;padding-top:0px;padding-bottom:0px;font-size:40%;" onclick="upnp_button()">UPnP &gt;</button></span></label>\r\n' \
  '    <textarea id="URL-" name="MediaSrc-" required style="height:110px;resize:none;display:##DISPLAY##; font-size:50%;width:80%">##URL##</textarea>\r\n' \
  '    <br>\r\n' \
  '    <form method="post" id="form" style="display:##DISPLAY##;">\r\n' \
  '      <input type="URL" id="URL" name="MediaSrc" value="" style="display:none;" required>\r\n' \
  '      <input type="URL" id="SUBURL" name="MediaSubSrc" value="" style="display:none;">\r\n' \
  '      <br>\r\n' \
  '      <label for="StartFrom">{#jplaybackposition#} :</label>\r\n' \
  '      <input type="time" id="StartFrom" name="MediaStartFrom" step="1" value="0##STARTFROM##" style="height:50px;font-size:70%;">\r\n' \
  '      <input type="hidden" id="Renderer" name="RendererInd" value="" required>\r\n' \
  '    </form>\r\n' \
  '    <button id="play" style="background-color:rgb(200,250,240);" onclick="play_button()">{#jgoplay#}</button>\r\n' \
  '    <button id="reset" style="background-color:rgb(250,220,200);" onclick="reset_button()">{#jreset#}</button>\r\n' \
  '    <br><br>\r\n' \
  '    <table id="Renderers" style="display:none;">\r\n' \
  '      <colgroup>\r\n' \
  '      <col style="width:10%;">\r\n' \
  '      <col style="width:65%;">\r\n' \
  '      <col style="width:25%;">\r\n' \
  '      </colgroup>\r\n' \
  '      <thead>\r\n' \
  '          <tr>\r\n' \
  '              <th colspan="3" id="table">{#jrenderers#}</th>\r\n' \
  '          </tr>\r\n' \
  '      </thead>\r\n' \
  '      <tbody>\r\n' \
  '      </tbody>\r\n' \
  '    </table>\r\n' \
  '    <br>\r\n' \
  '    <script>\r\n' \
  '      new_socket();\r\n' \
  '      URL_set = document.getElementById("URL-").value;\r\n' \
  '      StartFrom_set = document.getElementById("StartFrom").value;\r\n' \
  '    </script>\r\n' \
  '  </body>\r\n' \
  '</html>'
  HTML_START_TEMPLATE = HTML_START_TEMPLATE.replace('{', '{{').replace('}', '}}').replace('{{#', '{').replace('#}}', '}').format_map(LSTRINGS['webinterface']).replace('{{', '{').replace('}}', '}')
  HTML_CONTROL_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '  <head>\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page de contrôle</title>\r\n' \
  '    <script>\r\n' \
  '      function new_socket() {\r\n' \
  '        try {\r\n' \
  '          socket = new WebSocket("ws://" + location.hostname + ":" + String(parseInt(location.port,10)+1) + "/control");\r\n' \
  '        } catch(exception) {\r\n' \
  '          window.alert("{#jmwebsocketfailure#}");\r\n' \
  '        }\r\n' \
  '        socket.onerror = function(event) {\r\n' \
  '          window.location.reload(true);\r\n' \
  '        }\r\n' \
  '        socket.onmessage = function(event) {\r\n' \
  '          if (event.data == "close") {\r\n' \
  '            socket.onclose = function(event) {};\r\n' \
  '            socket.close();\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinterfaceclosed#}";\r\n' \
  '            document.getElementById("play-pause").style.display = "none";\r\n' \
  '            document.getElementById("stop").style.display = "none";\r\n' \
  '            document.getElementById("mute").style.display = "none";\r\n' \
  '            document.getElementById("volume").style.display = "none";\r\n' \
  '            seekbar.style.display = "none";\r\n' \
  '            seektarget.style.display = "none";\r\n' \
  '            document.getElementById("seektarget").style.display = "none";\r\n' \
  '          } else if (event.data == "redirect") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jback#}";\r\n' \
  '            window.location.replace("##START-URL##");\r\n' \
  '          } else if (event.data == "initialisation") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinitialization#}";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "{#jplay#}";\r\n' \
  '          } else if (event.data == "prêt") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jready#}";\r\n' \
  '          } else if (event.data == "prêt (lecture à partir du début)") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jreadyfromstart#}";\r\n' \
  '          } else if (event.data == "en cours...") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinprogress#}...";\r\n' \
  '          } else if (event.data == "Lecture") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinplayback#}";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "{#jpause#}";\r\n' \
  '          } else if (event.data == "Pause") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinpause#}";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "{#jplay#}";\r\n' \
  '          } else if (event.data.substring(0,13) == "Showstartfrom") {\r\n' \
  '            if (event.data.substring(14) == "true") {\r\n' \
  '              startfrom.value = "0" + document.getElementById("position").innerHTML;\r\n' \
  '              document.getElementById("lStartFrom").style.display = "inline-block";\r\n' \
  '              startfrom.style.display = "inline-block";\r\n' \
  '            } else {\r\n' \
  '              startfrom.value = "0:00:00";\r\n' \
  '              document.getElementById("lStartFrom").style.display = "none";\r\n' \
  '              startfrom.style.display = "none";\r\n' \
  '            }\r\n' \
  '          } else if (event.data == "Arrêt") {\r\n' \
  '            document.getElementById("status").innerHTML = "{#jinstop#}";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "{#jplay#}";\r\n' \
  '          } else if (event.data.substring(0,8) == "Duration") {\r\n' \
  '            duration = parseInt(event.data.substring(9),10);\r\n' \
  '            let seekduration_d = new Date(duration*1000);\r\n' \
  '            document.getElementById("seekduration").innerHTML = seekduration_d.toISOString().substr(12, 7);\r\n' \
  '            if (duration != 0) {\r\n' \
  '              if (document.getElementById("position").innerHTML !="-") {\r\n' \
  '                let cur_pos = document.getElementById("position").innerHTML.split(":");\r\n' \
  '                seekbar.value = Math.floor((parseInt(cur_pos[0],10)*3600 + parseInt(cur_pos[1],10)*60 + parseInt(cur_pos[2],10)) / duration * 10000);\r\n' \
  '                seekposition.innerHTML = document.getElementById("position").innerHTML;\r\n' \
  '              }\r\n' \
  '              seekbar.style.display = "inline-block";\r\n' \
  '              seektarget.style.display = "block";\r\n' \
  '            } else {\r\n' \
  '              seekbar.style.display = "none";\r\n' \
  '              seektarget.style.display = "none";\r\n' \
  '            }\r\n' \
  '          } else if (event.data.substring(0,3) == "URL") {\r\n' \
  '            document.getElementById("media_src").innerHTML = event.data.substring(4);\r\n' \
  '          } else if (event.data.substring(0,8) == "Playlist") {\r\n' \
  '            let pl = event.data.substring(9).split("\\r\\n");\r\n' \
  '            if (pl[1] != "") {\r\n' \
  '              if (playlist.options.length == 1) {\r\n' \
  '                for (let i=1;i<pl.length;i++) {\r\n' \
  '                  playlist.options.add(new Option(pl[i].replace(/ /g,"\xa0"), i.toString()));\r\n' \
  '                }\r\n' \
  '                playlist.style.display="inline-block";\r\n' \
  '                document.getElementById("shuffle").style.display = "inline-block";\r\n' \
  '              } else {\r\n' \
  '                let ml = Math.min(pl.length, playlist.options.length)\r\n' \
  '                for (let i=1;i<ml;i++) {\r\n' \
  '                  if (playlist.options[i].label != pl[i].replace(/ /g,"\xa0")) {\r\n' \
  '                    playlist.options[i].label = pl[i].replace(/ /g,"\xa0");\r\n' \
  '                  }\r\n' \
  '                }\r\n' \
  '              }\r\n' \
  '            }\r\n' \
  '          } else if (event.data.substring(0,7) == "Current") {\r\n' \
  '            playlist.selectedIndex = parseInt(event.data.substring(8),10);\r\n' \
  '          } else if (event.data.substring(0,7) == "Shuffle") {\r\n' \
  '              if (event.data.substring(8) == "true") {\r\n' \
  '                document.getElementById("shuffle").style.backgroundColor = "rgb(200,250,240)";\r\n' \
  '              } else {\r\n' \
  '                document.getElementById("shuffle").style.backgroundColor = "";\r\n' \
  '              }\r\n' \
  '          } else if (event.data.substring(0,4) == "Mute") {\r\n' \
  '              if (event.data.substring(5) == "none") {\r\n'\
  '                document.getElementById("mute").style.display = "none";\r\n' \
  '                document.getElementById("volume").style.display = "none";\r\n' \
  '              } else if (document.getElementById("mute").style.display == "none") {\r\n' \
  '                document.getElementById("mute").style.display = "inline-block";\r\n' \
  '                document.getElementById("volume").style.display = "inline-block";\r\n' \
  '              }\r\n' \
  '              if (event.data.substring(5) == "true") {\r\n'\
  '                document.getElementById("mute").innerHTML = "🔈 <strong style=\'visibility:visible;\'>&setmn;</strong>";\r\n' \
  '              } else {\r\n' \
  '               document.getElementById("mute").innerHTML = "🔈 <strong style=\'visibility:hidden;\'>&setmn;</strong>";\r\n' \
  '              }\r\n' \
  '          } else if (event.data.substring(0,6) == "Volume") {\r\n' \
  '              document.getElementById("volume").value = parseInt(event.data.substring(7),10);\r\n' \
  '          } else if (event.data != "close") {\r\n' \
  '            document.getElementById("position").innerHTML = event.data;\r\n' \
  '            if (duration != 0 && !seekongoing ) {\r\n' \
  '              let cur_pos = event.data.split(":");\r\n' \
  '              seekbar.value = Math.floor((parseInt(cur_pos[0],10)*3600 + parseInt(cur_pos[1],10)*60 + parseInt(cur_pos[2],10)) / duration * 10000);\r\n' \
  '              seekposition.innerHTML = event.data;\r\n' \
  '            }\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        socket.onclose = function(event) {\r\n' \
  '          new_socket();\r\n' \
  '        }\r\n' \
  '        window.onbeforeunload = function () {\r\n' \
  '          socket.onclose = function(event) {};\r\n' \
  '          socket.close();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      duration = 0;\r\n' \
  '      seekongoing = false;\r\n' \
  '      function play_pause_button() {\r\n' \
  '        if (document.getElementById("status").innerHTML != "{#jinitialization#}") {\r\n' \
  '          if (document.getElementById("status").innerHTML == "{#jinstop#}" && duration != 0) {socket.send("Seek:" + seekposition.innerHTML);}\r\n' \
  '          socket.send(document.getElementById("play-pause").innerHTML=="{#jplay#}"?"Lecture":"Pause");\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function stop_button() {\r\n' \
  '        conf = window.confirm("{#jmstop#}");\r\n' \
  '        if (conf) {socket.send(\'Arrêt\');}\r\n' \
  '      }\r\n' \
  '      function jump() {\r\n' \
  '        socket.send("Jump:" + playlist.selectedIndex.toString());\r\n' \
  '      }\r\n ' \
  '      function shuffle_button() {\r\n' \
  '        socket.send("Shuffle");\r\n' \
  '      }\r\n ' \
  '      function mute_button() {\r\n' \
  '        if (document.getElementById("mute").innerHTML.indexOf("hidden") > 0) {\r\n' \
  '          socket.send("Mute:true");\r\n' \
  '        } else {\r\n' \
  '          socket.send("Mute:false");\r\n' \
  '        }\r\n' \
  '      }\r\n ' \
  '      function volume_range() {\r\n' \
  '        socket.send("Volume:" + document.getElementById("volume").value.toString());\r\n' \
  '      }\r\n ' \
  '    </script>\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;{#jcontrol#}<br></h1>\r\n' \
  '    <img id="renderer_icon" src="data:;base64,##RENDERERICON##" alt=" " style="height:36px;width:auto;vertical-align:middle;">\r\n' \
  '    <span id="renderer_name" style="font-size:130%;">&nbsp;&nbsp;##RENDERERNAME##</span>\r\n' \
  '    <br style="line-height:100px;">\r\n' \
  '    <select id="playlist" onchange="jump()" style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:50%;width:91%;display:none;">\r\n' \
  '    <option value="0" disabled hidden>{#jplaylist#}</option>\r\n' \
  '    </select>&nbsp;<button id="shuffle" style="border:none;vertical-align:middle;display:none;" onclick="shuffle_button()"><svg xmlns="http://www.w3.org/2000/svg" width="15px" height="23px" style="font-size:30px;font-weight:bold;"><text x="-5" y="21" >&nesear;</text></svg></button>\r\n' \
  '    <p style="margin-bottom:0px;">{#jurl#} : </p>\r\n' \
  '    <p id="media_src" style="margin-left:30px;margin-top:10px;font-size:50%;word-wrap:break-word;height:110px;width:90%;overflow-y:auto;white-space:pre-wrap;">##URL##</p>\r\n' \
  '    <p style="line-height:60px;">{#jstatus#} :&nbsp;&nbsp;&nbsp;<span id="status" style="color:rgb(200,250,240);">{#jinitialization#}</span></p>\r\n' \
  '    <p style="line-height:60px;">{#jplaybackposition#} :&nbsp;&nbsp;&nbsp;<span id="position" style="color:rgb(200,250,240);">-</span></p>\r\n' \
  '    <br>\r\n' \
  '    <button id="play-pause" style="background-color:rgb(200,250,240);border:none;padding-top:20px;padding-bottom:20px;margin-left:50px;margin-right:75px;width:200px;font-size:100%;font-weight:bold;cursor:pointer;" onclick="play_pause_button()">{#jplay#}</button>\r\n' \
  '    <button id="stop" style="background-color:rgb(250,220,200);border:none;padding-top:20px;padding-bottom:20px;margin-left:75px;margin-right:150px;width:200px;font-size:100%;font-weight:bold;cursor:pointer;" onclick="stop_button()">{#jstop#}</button>\r\n' \
  '    <span id="mute" style="color:red;word-spacing:-30px;cursor:pointer;display:none;" onclick="mute_button()">🔈 <strong style="visibility:hidden;">&setmn;</strong></span>&nbsp;<input type="range" min="0" max="100" value="100" id="volume" style="width:100px;cursor:pointer;display:none;" onchange="volume_range()">\r\n' \
  '    <br>\r\n' \
  '    <br>\r\n' \
  '    <input type="range" min="0" max="10000" value="0" id="seekbar" style="margin-left:50px;margin-right:50px;width:80%;cursor:pointer;display:none;">\r\n' \
  '    <p id="seektarget" style="margin-left:50px;font-size:75%;display:none;"> {#jtargetposition#} : <span id="seekposition">0:00:00</span> / <span id="seekduration">0:00:00</span></p>\r\n' \
  '    <label for="StartFrom" id="lStartFrom" style="margin-left:50px;font-size:75%;display:none;">{#jtargetposition#} :</label>\r\n' \
  '    <input type="time" id="StartFrom" step="1" value="00:00:00" style="height:40px;font-size:70%;border: none;background-color:rgb(30,30,35);color:rgb(200,250,240);display:none;">\r\n' \
  '    <script>\r\n' \
  '      new_socket();\r\n' \
  '      seekbar = document.getElementById("seekbar");\r\n' \
  '      seekposition = document.getElementById("seekposition");\r\n' \
  '      seekbar.onmousedown = function() {seekongoing = true;};\r\n' \
  '      seekbar.onmouseup = function() {seekongoing = false;};\r\n' \
  '      seekbar.ontouchstart = function() {seekongoing = true;};\r\n' \
  '      seekbar.ontouchend = function() {seekongoing = false;};\r\n' \
  '      seekbar.oninput = function() {\r\n' \
  '        let seekposition_d = new Date(seekbar.value*duration/10);\r\n' \
  '        seekposition.innerHTML = seekposition_d.toISOString().substr(12, 7);\r\n' \
  '      }\r\n' \
  '      seekbar.onchange = function() {\r\n' \
  '        if (document.getElementById("status").innerHTML != "initialisation") {socket.send("Seek:" + seekposition.innerHTML);}\r\n' \
  '        seekbar.blur();\r\n' \
  '      }\r\n' \
  '      playlist = document.getElementById("playlist");\r\n' \
  '      playlist.selectedIndex = 0;\r\n' \
  '      startfrom = document.getElementById("StartFrom");\r\n' \
  '      startfrom.onchange = function() {\r\n' \
  '        startfrom.onblur = function() {};\r\n' \
  '        startfrom.blur();\r\n' \
  '        if (startfrom.value.substring(1) != document.getElementById("position").innerHTML) {\r\n' \
  '          socket.send("Seek:" + startfrom.value.substring(1));\r\n' \
  '          jump();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      startfrom.onblur = function() {\r\n' \
  '        if (startfrom.value.substring(1) != document.getElementById("position").innerHTML) {\r\n' \
  '          socket.send("Seek:" + startfrom.value.substring(1));\r\n' \
  '          jump();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      startfrom.onkeydown = function(k) {\r\n' \
  '        startfrom.onchange = function() {};\r\n' \
  '        if (k.keyCode == 13) {startfrom.blur();}\r\n' \
  '      }\r\n' \
  '    </script>\r\n' \
  '  </body>\r\n' \
  '</html>'
  HTML_CONTROL_TEMPLATE = HTML_CONTROL_TEMPLATE.replace('{', '{{').replace('}', '}}').replace('{{#', '{').replace('#}}', '}').format_map(LSTRINGS['webinterface']).replace('{{', '{').replace('}}', '}')

  def __init__(self, DLNAWebInterfaceServerAddress=None, DLNAJoinIp=None, Launch=INTERFACE_NOT_RUNNING, Renderer_uuid=None, Renderer_name=None, MediaServerMode=None, MediaSrc='', MediaStartFrom='0:00:00', MediaBufferSize=75, MediaBufferAhead=25, MediaMuxContainer=None, OnReadyPlay=False, MediaSubSrc='', MediaSubLang=None, SlideshowDuration=None, EndLess=False, verbosity=0):
    self.verbosity = verbosity
    self.logger = log_event('webinterface', verbosity)
    if not DLNAWebInterfaceServerAddress:
      ip = None
    elif DLNAWebInterfaceServerAddress[0]:
      ip = DLNAWebInterfaceServerAddress[0]
    else:
      ip = None
    if not ip:
      try:
        ip = socket.gethostbyname(socket.gethostname())
      except:
        try:
          ip = socket.gethostbyname(socket.getfqdn())
        except:
          ip = '0.0.0.0'
          self.logger.log(LSTRINGS['ip_failure'], 1)
    self.DLNAWebInterfaceServerAddress =  (ip, DLNAWebInterfaceServerAddress[1] or 8000)
    self.DLNAControllerInstance = DLNAController(DLNAJoinIp, verbosity)
    self.RenderersEvent = None
    self.ControlDataStore = None
    self.RenderersDataStore = None
    self.WebSocketServerInstance = None
    self.html_control = b''
    self.html_start = b''
    self.html_ready = False
    self.Renderer_uuid = Renderer_uuid
    self.Renderer_name = Renderer_name
    self.Renderer = None
    self.RendererNotFound = False
    self.MediaServerInstance = None
    self.MediaSrc = MediaSrc
    if MediaStartFrom:
      try:
        self.MediaPosition = _seconds_to_position(_position_to_seconds(MediaStartFrom))
      except:
        self.MediaPosition = '0:00:00'
    else:
      self.MediaPosition = '0:00:00'
    self.MediaBufferSize = MediaBufferSize
    self.MediaBufferAhead = MediaBufferAhead
    self.MediaMuxContainer = MediaMuxContainer
    self.OnReadyPlay = OnReadyPlay
    self.MediaSubSrc = MediaSubSrc
    self.MediaSubLang = MediaSubLang
    self.TargetStatus = Launch
    self.MediaServerMode = MediaServerMode if MediaServerMode is not None else MediaProvider.SERVER_MODE_AUTO
    if self.MediaServerMode == DLNAWebInterfaceServer.SERVER_MODE_GAPLESS:
      self.Gapless = True
      self.MediaServerMode = MediaProvider.SERVER_MODE_RANDOM
    else:
      self.Gapless = False
    self.NextMediaServerInstance = None
    if self.MediaServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and not MediaMuxContainer:
      self.MediaPosition = '0:00:00'
    self.SlideshowDuration = SlideshowDuration if self.MediaPosition == '0:00:00' else None
    self.EndLess = EndLess
    self.Status = None
    self.shutdown_requested = False
    if not mimetypes.inited:
      mimetypes.init()
    self.DLNAClientInstance = DLNAClient(DLNAJoinIp, verbosity)
    self.DLNAClientCache = []
    self.DLNAClientStop = threading.Event()
    if Launch == DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
      self.DLNAAdvertisementListenerInstance = DLNAAdvertisementListener((self.DLNAControllerInstance,), verbosity)
    else:
      self.DLNAAdvertisementListenerInstance = DLNAAdvertisementListener((self.DLNAControllerInstance,self.DLNAClientInstance), verbosity)
    self.WebServerReady = threading.Event()

  def _discover_servers(self):
    self.DLNAClientInstance.discover(timeout=3, alive_persistence=86400, from_polling=True).join()
    if self.DLNAClientInstance.is_discovery_polling_running:
      self.DLNAClientInstance.discover(timeout=5, alive_persistence=15, from_polling=True)

  def discover_servers(self):
    self.DLNAClientInstance.is_discovery_polling_running = True
    self.DLNAClientInstance.discovery_status_change = self.RenderersEvent
    discovery_thread = threading.Thread(target=self._discover_servers, daemon=True)
    discovery_thread.start()

  def build_server_html(self, uuid=None, content=[None, [],[]]):
    html_bloc = ''
    if not uuid:
      for i in range(len(self.DLNAClientInstance.Servers)):
        skip_server = False
        if not self.DLNAClientInstance.Servers[i].StatusAlive:
          skip_server = True
        else:
          for j in range(i):
            if self.DLNAClientInstance.Servers[i].UDN == self.DLNAClientInstance.Servers[j].UDN and self.DLNAClientInstance.Servers[j].StatusAlive:
              skip_server = True
              break
        if not skip_server:
          html_bloc = html_bloc + ('    <p><span style="display:inline-block;width:40px;height:22px;margin-top:-10px;"><img style="height:22px;width:30px;object-fit:contain;" src="%s" alt=" "/></span><span style="vertical-align:4px;"><a href="javascript:open_link(\'' % html.escape(self.DLNAClientInstance.Servers[i].IconURL)) + urllib.parse.quote(urllib.parse.urlencode({'uuid': self.DLNAClientInstance.Servers[i].UDN[5:], 'id': 0}, quote_via=urllib.parse.quote)) + ('\')">%s</a></span></p>\r\n' % html.escape(self.DLNAClientInstance.Servers[i].FriendlyName))
      return html_bloc
    for e in content[1]:
      html_bloc = html_bloc + '    <p><a href="javascript:open_link(\'' +  urllib.parse.quote(urllib.parse.urlencode({'id': e['id']}, quote_via=urllib.parse.quote)) + ('\')">&rect;&nbsp;%s%s</a></p>\r\n' % (html.escape(e['title']), html.escape(' (' + e['artist'] + ')') if e['artist'] and e['class'].lower() == 'object.container.album' else '',))
    for e in content[2]:
      html_bloc = html_bloc + '    <p>' + (('<a href="javascript:open_link(\'' +  urllib.parse.quote(urllib.parse.urlencode({'id': e['id']}, quote_via=urllib.parse.quote)) + '\')">') if content[0]['type'] == 'container' else '') + ('%s%s%s%s</a></p>\r\n' % (html.escape(e['album'] + ' - ') if e['album'] and e['class'].lower() == 'object.item.audioitem' else '', html.escape(e['track'] + ' - ') if e['track'] and e['track'] != '0' and e['class'].lower() == 'object.item.audioitem' else '', html.escape(e['artist'] + ' - ') if e['artist'] and e['class'].lower() == 'object.item.audioitem' else '', html.escape(e['title'])))
    return html_bloc

  def manage_start(self):
    if self.shutdown_requested:
      return
    self.RenderersDataStore = DLNAWebInterfaceRenderersDataStore()
    self.SlideshowDuration = None
    if self.Status == DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
      self.logger.log(2, 'rendererstart')
      self.html_start = DLNAWebInterfaceServer.HTML_START_TEMPLATE.replace('##CONTROL-URL##', '/control.html').replace('##DISPLAY##', 'none').replace('##STARTFROM##', '0:00:00').encode('utf-8')
    elif self.Status == DLNAWebInterfaceServer.INTERFACE_START:
      self.logger.log(2, 'launchrendererstart')
      self.html_start = DLNAWebInterfaceServer.HTML_START_TEMPLATE.replace('##CONTROL-URL##', '/control.html').replace('##UPNP-URL##', '/upnp.html').replace('##DISPLAY##', 'inline-block').replace('##URL##', html.escape(self.MediaSrc) + ('\r\n' + html.escape(self.MediaSubSrc) if self.MediaSubSrc else '')).replace('##STARTFROM##', self.MediaPosition).encode('utf-8')
    else:
      return
    self.DLNAControllerInstance.start_discovery_polling(timeout=5, alive_persistence=45, polling_period=30, DiscoveryEvent=self.RenderersEvent)
    self.WebSocketServerInstance.open('start', self.RenderersDataStore)
    self.DLNAClientStop.clear()
    self.html_ready = True
    rend_stat = []
    first_loop = True
    upnp_button = False
    if self.Status == DLNAWebInterfaceServer.INTERFACE_START:
      self.discover_servers()
    while self.TargetStatus in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START) and not self.shutdown_requested:
      if (first_loop or self.DLNAControllerInstance.wait_for_advertisement(1)) and not self.shutdown_requested:
        first_loop = False
        for ind in range(len(self.DLNAControllerInstance.Renderers)):
          renderer = self.DLNAControllerInstance.Renderers[ind]
          status = renderer.StatusAlive and bool(renderer.BaseURL)
          if ind == len(rend_stat):
            rend_stat.append(status)
            self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'add', 'index': str(ind), 'name': html.escape(renderer.FriendlyName), 'ip': renderer.Ip, 'icon': '/icon%d' % ind, 'status': status}, quote_via=urllib.parse.quote)
            if self.Renderer:
              if renderer == self.Renderer:
                self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'sel', 'index': str(ind)}, quote_via=urllib.parse.quote)
            elif self.Renderer_uuid or self.Renderer_name:
              if renderer == self.DLNAControllerInstance.search(self.Renderer_uuid, self.Renderer_name):
                self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'sel', 'index': str(ind)}, quote_via=urllib.parse.quote)
                if self.RendererNotFound and self.OnReadyPlay:
                  self.Renderer = renderer
                  self.Renderer_uuid = renderer.UDN[5:]
                  self.Renderer_name = renderer.FriendlyName
                  self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_CONTROL
          elif status != rend_stat[ind]:
            rend_stat[ind] = status
            if status:
              self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'show', 'index': str(ind), 'icon': '/icon%d' % ind}, quote_via=urllib.parse.quote)
            else:
              self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'hide', 'index': str(ind)}, quote_via=urllib.parse.quote)
      if self.Status == DLNAWebInterfaceServer.INTERFACE_START:
        if not upnp_button and self.DLNAClientInstance.search(complete=True):
          self.RenderersDataStore.Message = 'upnp'
          upnp_button = True
    self.DLNAClientStop.set()
    self.html_ready = False
    self.DLNAControllerInstance.stop_discovery_polling()
    if self.Status != DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
      self.DLNAClientInstance.is_discovery_polling_running = False
    self.logger.log(2, 'rendererstop')
    if self.Status == DLNAWebInterfaceServer.INTERFACE_START and not self.shutdown_requested:
      self.RenderersDataStore.Redirect = True
    self.WebSocketServerInstance.close('start')
    self.RenderersDataStore = None

  def manage_control(self):
    if self.shutdown_requested or self.Status != DLNAWebInterfaceServer.INTERFACE_CONTROL:
      return
    self.ControlDataStore = DLNAWebInterfaceControlDataStore()
    self.ControlDataStore.Status = 'initialisation'
    self.ControlDataStore.Position = '0:00:00'
    self.logger.log(2, 'controlstart')
    renderer = self.Renderer or self.DLNAControllerInstance.search(uuid=self.Renderer_uuid, name=self.Renderer_name, complete=True)
    if not renderer:
      self.DLNAControllerInstance.is_discovery_polling_running = True
      nb_search = 0
      start_time = time.monotonic()
      elapsed_time = 0
      while self.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL and not renderer and elapsed_time < 12:
        if nb_search * 6 <= elapsed_time:
          self.DLNAControllerInstance.discover(timeout=5, alive_persistence=86400, from_polling=True)
          nb_search += 1
        self.RenderersEvent.wait(6 * (nb_search + 1) - elapsed_time)
        self.RenderersEvent.clear()
        renderer = self.DLNAControllerInstance.search(uuid=self.Renderer_uuid, name=self.Renderer_name, complete=True)
        elapsed_time = time.monotonic() - start_time
      self.DLNAControllerInstance.is_discovery_polling_running = False
    if renderer:
      self.Renderer = renderer
      self.Renderer_uuid = renderer.UDN[5:]
      self.Renderer_name = renderer.FriendlyName
      self.RendererNotFound = False
    else:
      self.RendererNotFound = True
    if self.shutdown_requested or not renderer:
      self.logger.log(2, 'controlinterrupt')
      return
    try:
      renderer_hip = self.DLNAControllerInstance.Hips[self.DLNAControllerInstance.Renderers.index(renderer)]
    except:
      self.RendererNotFound = False
      self.logger.log(2, 'controlinterrupt')
      return
    self.logger.log(1, 'controlrenderer', renderer.FriendlyName, renderer_hip)
    renderer_icon = b''
    if renderer.IconURL:
      try:
        icon_resp = HTTPRequest(renderer.IconURL, timeout=5, ip=renderer_hip)
        if icon_resp.code == '200':
          if icon_resp.body:
            renderer_icon = base64.b64encode(icon_resp.body)
      except:
        pass
    gapless = self.Gapless
    if gapless:
      serv = next((serv for serv in self.Renderer.Services if serv.Id == 'urn:upnp-org:serviceId:AVTransport'), None)
      if serv:
        gapless = next((act for act in serv.Actions if act.Name == 'SetNextAVTransportURI'), None) is not None
      else:
        gapless = None
      if not gapless:
        self.logger.log(0, 'nonegapless', self.Renderer.FriendlyName)
    self.html_control = DLNAWebInterfaceServer.HTML_CONTROL_TEMPLATE.replace('##START-URL##', '/start.html').replace('##URL##', html.escape(self.MediaSrc) + ('<br>' + html.escape(self.MediaSubSrc) if self.MediaSubSrc else '')).replace('##RENDERERNAME##', html.escape(renderer.FriendlyName)).encode('utf-8').replace(b'##RENDERERICON##', renderer_icon)
    self.WebSocketServerInstance.open('control', self.ControlDataStore)
    self.html_ready = True
    try:
      self.DLNAControllerInstance.send_Stop(renderer)
    except:
      pass
    event_notification_listener = DLNAEventNotificationListener(self.DLNAControllerInstance, self.DLNAWebInterfaceServerAddress[1]+2)
    event_notification_listener.start()
    event_listener = self.DLNAControllerInstance.new_event_subscription(renderer, 'AVTransport', event_notification_listener)
    prep_success = True
    if not event_listener:
      prep_success = False
    if prep_success:
      warning = self.DLNAControllerInstance.add_event_warning(event_listener, 'TransportState', 'PLAYING', 'STOPPED', 'PAUSED_PLAYBACK', WarningEvent=self.ControlDataStore.IncomingEvent)
      for nb_try in range(3):
        prep_success = self.DLNAControllerInstance.send_event_subscription(event_listener, 36000)
        if prep_success:
          break
    spare_event = threading.Event()
    incoming_event = self.ControlDataStore.IncomingEvent
    self.ControlDataStore.IncomingEvent = spare_event
    if not prep_success or self.shutdown_requested or self.ControlDataStore.Command == 'Arrêt':
      self.logger.log(2, 'controlinterrupt')
      self.html_ready = False
      if not self.shutdown_requested:
        self.ControlDataStore.Redirect = True
      self.WebSocketServerInstance.close('control')
      self.ControlDataStore = None
      if event_listener:
        self.DLNAControllerInstance.send_event_unsubscription(event_listener)
      event_notification_listener.stop()
      return
    event_listener_rc = self.DLNAControllerInstance.new_event_subscription(renderer, 'RenderingControl', event_notification_listener)
    if event_listener_rc:
      warning_m = self.DLNAControllerInstance.add_event_warning(event_listener_rc, 'Mute', WarningEvent=incoming_event)
      warning_v = self.DLNAControllerInstance.add_event_warning(event_listener_rc, 'Volume', WarningEvent=incoming_event)
      if not self.DLNAControllerInstance.send_event_subscription(event_listener_rc, 36000):
        self.DLNAControllerInstance.send_event_unsubscription(event_listener_rc)
        event_listener_rc = None
      if event_listener_rc:
        if (self.DLNAControllerInstance.get_Volume(renderer) is None or self.DLNAControllerInstance.get_Mute(renderer) is None):
          self.DLNAControllerInstance.send_event_unsubscription(event_listener_rc)
          event_listener_rc = None
      if event_listener_rc:
        try:
          vol_max = int(next((arg for arg in next((act for act in next((serv for serv in renderer.Services if serv.Id == 'urn:upnp-org:serviceId:RenderingControl')).Actions if act.Name == 'SetVolume'), None).Arguments if arg.Name == 'DesiredVolume'), None).AllowedValueRange[1])
        except:
          vol_max = 100
        if vol_max <=0:
          vol_max = 100
    playlist = None
    titles = []
    mediakinds = []
    order = [0]
    if self.MediaSrc[:7].lower() == 'upnp://':
      try:
        obj_uuid = self.MediaSrc[7:].partition('?')[0]
        obj_id = self.MediaSrc[7:].partition('?')[2]
        for c in self.DLNAClientCache:
          req = urllib.parse.parse_qs(urllib.parse.urlparse(c[0]).query.lower())
          if req.get('uuid')[0] == obj_uuid.lower() and req.get('id')[0] == obj_id.lower():
            playlist = c[2]
            titles = list(html.unescape(l.split('</')[0].rsplit('>', 1)[1]) for l in c[1].decode('utf-8').splitlines() if l.lstrip()[:3] == '<p>')
            del titles[0:len(titles) - len(playlist)]
            mediakinds = c[3]
            break
        if playlist is None:
          server = self.DLNAClientInstance.search(uuid=obj_uuid)
          if not server:
            if self.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
              self.DLNAClientInstance.discover(timeout=3, alive_persistence=86400)
              server = self.DLNAClientInstance.search(uuid=obj_uuid)
            if not server:
              raise
          if not server.StatusAlive:
            raise
          content = self.DLNAClientInstance.get_Content(server, obj_id, self.ControlDataStore.IncomingEvent)
          playlist = list(e['uri'] for e in content[2])
          titles = list(((e['album'] + ' - ') if e['album'] and e['class'].lower() == 'object.item.audioitem' else '') + ((e['track'] + ' - ') if e['track'] and e['track'] != '0' and e['class'].lower() == 'object.item.audioitem' else '') + ((e['artist'] + ' - ') if e['artist'] and e['class'].lower() == 'object.item.audioitem' else '') + e['title'] for e in content[2])
          mediakinds = list({'object.item.videoitem': 'video', 'object.item.audioitem': 'audio', 'object.item.imageitem': 'image'}.get(e['class'].lower(), 'video') for e in content[2])
      except:
        playlist = []
        titles = []
        mediakinds = []
    if playlist is None:
      playlist, titles = MediaProvider.parse_playlist(self.MediaSrc, True, self.ControlDataStore.IncomingEvent)
    self.ControlDataStore.IncomingEvent = incoming_event
    if playlist != False:
      if playlist:
        self.logger.log(1, 'playlist', self.MediaSrc, len(playlist))
        self.ControlDataStore.Playlist = titles
        random.seed()
        order = list(range(len(playlist)))
      else:
        self.logger.log(0, 'nocontent', self.MediaSrc)
      if self.SlideshowDuration:
        self.MediaPosition = self.SlideshowDuration
    if gapless:
      if self.MediaSrc[:7].lower() != 'upnp://':
        ind = 0
        mediakinds = []
        while (ind < (len(playlist) if playlist != False else 1)):
          media_src = playlist[ind] if playlist != False else self.MediaSrc
          media_mime = mimetypes.guess_type(media_src)[0] or ''
          media_kind = media_mime[0:5]
          if r'://' in media_src:
            if not media_kind in ('video', 'audio'):
              gapless = False
              break
          else:
            if media_kind == 'image':
              gapless = False
              break
            if not media_kind in ('video', 'audio'):
              media_kind = 'video'
          mediakinds.append(media_kind)
          ind += 1
        if playlist == False and self.MediaSubSrc:
          sub_ext = (''.join(self.MediaSubSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubSrc else ''
          if r'://' in self.MediaSubSrc:
            if '?' in sub_ext:
              sub_ext = sub_ext.rpartition('?')[0]
            if not sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt', '.m3u8'):
              gapless = False
      if 'image' in mediakinds:
        gapless = False
      if gapless:
        self.logger.log(1, 'gapless', self.MediaSrc)
      else:
        self.logger.log(0, 'nogapless', self.MediaSrc)
    cmd_stop = not self.OnReadyPlay
    playlist_stop = False
    media_kind = None
    ind = -1
    jump_ind = None
    restart_from = None
    warning_e = self.DLNAControllerInstance.add_event_warning(event_listener, 'TransportStatus', 'ERROR_OCCURRED')
    warning_d = self.DLNAControllerInstance.add_event_warning(event_listener, 'CurrentMediaDuration')
    server_mode = None
    if gapless:
      gapless_status = 0
      warning_n = self.DLNAControllerInstance.add_event_warning(event_listener, 'AVTransportURI', WarningEvent=incoming_event)
    else:
      gapless_status = -1
    self.NextMediaServerInstance = None
    incoming_event_setter = partial(self.ControlDataStore.__setattr__, 'IncomingEvent')
    while (ind < (len(playlist) - 1 if playlist != False else 0)) or jump_ind is not None or self.ControlDataStore.Shuffle or self.EndLess:
      if self.shutdown_requested or playlist_stop:
        break
      if jump_ind is None:
        ind += 1
        if playlist:
          if ind == len(playlist):
            ind = 0
        elif self.EndLess:
          ind = 0
      else:
        ind = order.index(jump_ind) if playlist else 0
        jump_ind = None
      media_src = playlist[order[ind]] if playlist != False else self.MediaSrc
      self.ControlDataStore.ShowStartFrom = False
      self.ControlDataStore.incoming = []
      if playlist:
        if self.MediaSubSrc and os.path.isdir(self.MediaSrc):
          if os.path.isdir(self.MediaSubSrc):
            media_sub_src = os.path.dirname(os.path.join(self.MediaSubSrc, os.path.normpath(media_src)[len(os.path.normpath(self.MediaSrc)) + 1:]))
          else:
            media_sub_src = ''
        else:
          media_sub_src = media_src if self.MediaSubSrc == self.MediaSrc else ''
        if gapless_status < 3:
          self.ControlDataStore.Status = 'initialisation'
          self.ControlDataStore.Position = '0:00:00'
        self.ControlDataStore.URL = media_src + ('\r\n' + media_sub_src if media_sub_src else '')
        self.ControlDataStore.Current = order[ind]
        media_start_from = '0:00:00' if not restart_from else restart_from
        restart_from = None
      else:
        media_sub_src = self.MediaSubSrc
        if gapless_status < 3:
          self.ControlDataStore.Status = 'initialisation'
          if self.EndLess and self.ControlDataStore.Position is not None:
            self.ControlDataStore.Position = '0:00:00'
          else:
            cmd_stop = not self.OnReadyPlay and (restart_from is None or restart_from == '')
      self.ControlDataStore.Duration = '0'
      prev_media_kind = media_kind
      if self.MediaSrc[:7].lower() == 'upnp://' or gapless:
        media_kind = mediakinds[order[ind]]
      else:
        media_kind = 'video'
        media_mime = mimetypes.guess_type(media_src.rsplit('?',1)[0])[0]
        if media_mime:
          if media_mime[0:5] in ('audio', 'image'):
            media_kind = media_mime[0:5]
      if media_kind == 'image':
        media_start_from = '0:00:00'
        image_duration = _position_to_seconds(self.MediaPosition or '0:00:00')
        image_start = None
      elif not playlist:
        media_start_from = self.MediaPosition if not restart_from else restart_from
        restart_from = None
      if prev_media_kind == 'image' and media_kind != 'image':
        try:
          self.DLNAControllerInstance.send_Stop(renderer)
        except:
          pass
      self.MediaServerInstance = None
      check_renderer = False
      if self.MediaServerMode != DLNAWebInterfaceServer.SERVER_MODE_NONE:
        if gapless:
          if self.NextMediaServerInstance:
            self.MediaServerInstance = self.NextMediaServerInstance
            self.NextMediaServerInstance = None
          nind = ind + 1
          if self.EndLess or self.ControlDataStore.Shuffle:
            if playlist:
              if nind == len(playlist):
                nind = 0
            else:
              nind = 0
          elif playlist:
            if nind == len(playlist):
              nind = None
          else:
            nind = None
        if not self.MediaServerInstance:
          self.MediaServerInstance = MediaServer(self.MediaServerMode, (renderer_hip, self.DLNAWebInterfaceServerAddress[1]+3), media_src, MediaSrcType=('ContentURL' if self.MediaSrc[:7].lower()=='upnp://' else None), MediaStartFrom=media_start_from, MediaBufferSize=self.MediaBufferSize, MediaBufferAhead=self.MediaBufferAhead, MediaMuxContainer=self.MediaMuxContainer, MediaSubSrc=media_sub_src, MediaSubSrcType='ContentURL' if self.MediaSrc[:7].lower()=='upnp://' else None, MediaSubLang=self.MediaSubLang, MediaProcessProfile=renderer.FriendlyName, verbosity=self.verbosity, auth_ip=(renderer.Ip, *self.DLNAControllerInstance.ips))
          self.MediaServerInstance.start()
        if not self.shutdown_requested:
          prep_success = self.MediaServerInstance.wait(InterruptSetter=incoming_event_setter)
        else:
          prep_success = False
        self.ControlDataStore.IncomingEvent = incoming_event
        if prep_success and not self.shutdown_requested:
          suburi = None
          if self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer:
            if self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer[0]:
              suburi = 'http://%s:%s/mediasub%s' % (*self.MediaServerInstance.MediaServerAddress, self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer[1])
          server_mode = self.MediaServerInstance.MediaProviderInstance.ServerMode
          if playlist and self.MediaServerInstance.MediaProviderInstance.MediaSrcType == 'WebPageURL' and playlist[order[ind]][:MediaProvider.TITLE_MAX_LENGTH] == titles[order[ind]][:MediaProvider.TITLE_MAX_LENGTH]:
            titles[order[ind]] = self.MediaServerInstance.MediaProviderInstance.MediaTitle if len(self.MediaServerInstance.MediaProviderInstance.MediaTitle) <= MediaProvider.TITLE_MAX_LENGTH else self.MediaServerInstance.MediaProviderInstance.MediaTitle[:MediaProvider.TITLE_MAX_LENGTH] + '…'
            self.ControlDataStore.Playlist = titles
          if self.MediaSrc[:7].lower() == 'upnp://':
            media_title = titles[order[ind]]
          else:
            media_title = self.MediaServerInstance.MediaProviderInstance.MediaTitle
          if gapless_status < 3:
            self.DLNAControllerInstance.wait_for_warning(warning, 0, True)
            spare_event.clear()
            self.ControlDataStore.IncomingEvent = spare_event
            if server_mode == MediaProvider.SERVER_MODE_RANDOM and not self.shutdown_requested:
              accept_ranges = self.MediaServerInstance.MediaProviderInstance.AcceptRanges
              try:
                if accept_ranges:
                  prep_success = self.DLNAControllerInstance.send_Local_URI(self.Renderer, 'http://%s:%s/media%s' % (*self.MediaServerInstance.MediaServerAddress, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), media_title, kind=media_kind, suburi=suburi, stop=self.ControlDataStore.IncomingEvent)
                else:
                  prep_success = self.DLNAControllerInstance.send_URI(self.Renderer, 'http://%s:%s/media%s' % (*self.MediaServerInstance.MediaServerAddress, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), media_title, kind=media_kind, suburi=suburi)
              except:
                prep_success = False
            elif server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL and not self.shutdown_requested:
              accept_ranges = False
              try:
                prep_success = self.DLNAControllerInstance.send_URI(self.Renderer, 'http://%s:%s/media%s' % (*self.MediaServerInstance.MediaServerAddress, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), media_title, kind=media_kind, suburi=suburi)
              except:
                prep_success = False
            else:
              prep_success = False
            self.ControlDataStore.IncomingEvent = incoming_event
            if not prep_success:
              check_renderer = True
          if gapless:
            if nind is not None:
              nmedia_src = playlist[order[nind]] if playlist != False else self.MediaSrc
              if playlist:
                if self.MediaSubSrc and os.path.isdir(self.MediaSrc):
                  if os.path.isdir(self.MediaSubSrc):
                    nmedia_sub_src = os.path.dirname(os.path.join(self.MediaSubSrc, os.path.normpath(nmedia_src)[len(os.path.normpath(self.MediaSrc)) + 1:]))
                  else:
                    nmedia_sub_src = ''
                else:
                  nmedia_sub_src = nmedia_src if self.MediaSubSrc == self.MediaSrc else ''
              else:
                nmedia_sub_src = self.MediaSubSrc
              self.NextMediaServerInstance = MediaServer(self.MediaServerMode, (renderer_hip, self.DLNAWebInterfaceServerAddress[1]+(self.MediaServerInstance.MediaServerAddress[1]-self.DLNAWebInterfaceServerAddress[1])%4+2), nmedia_src, MediaSrcType=('ContentURL' if self.MediaSrc[:7].lower()=='upnp://' else None), MediaStartFrom='0:00:00', MediaBufferSize=self.MediaBufferSize, MediaBufferAhead=self.MediaBufferAhead, MediaMuxContainer=self.MediaMuxContainer, MediaSubSrc=nmedia_sub_src, MediaSubSrcType='ContentURL' if self.MediaSrc[:7].lower()=='upnp://' else None, MediaSubLang=self.MediaSubLang, MediaProcessProfile=renderer.FriendlyName, verbosity=self.verbosity, auth_ip=(renderer.Ip, *self.DLNAControllerInstance.ips))
              self.NextMediaServerInstance.start()
      else:
        suburi = media_sub_src
        server_mode = DLNAWebInterfaceServer.SERVER_MODE_NONE
        accept_ranges = True
        media_ip = None
        if r'://' in media_src:
          try:
            media_ip = urllib.parse.urlparse(media_src).netloc.split(':',1)[0]
          except:
            pass
        else:
          media_ip = ''
        self.DLNAControllerInstance.wait_for_warning(warning, 0, True)
        if self.MediaSrc[:7].lower() == 'upnp://':
          media_title = titles[order[ind]]
        else:
          media_title = media_src
        spare_event.clear()
        self.ControlDataStore.IncomingEvent = spare_event
        try:
          if (media_ip == '' or renderer_hip == media_ip) and not self.shutdown_requested:
            prep_success = self.DLNAControllerInstance.send_Local_URI(self.Renderer, media_src, media_title, kind=media_kind, suburi=suburi)
          elif not self.shutdown_requested:
            prep_success = self.DLNAControllerInstance.send_URI(self.Renderer, media_src, media_title, kind=media_kind, suburi=suburi)
          else:
            prep_success = False
        except:
          prep_success = False
        self.ControlDataStore.IncomingEvent = incoming_event
        if not prep_success:
          check_renderer = True
      if self.shutdown_requested:
        prep_success = False
      if gapless_status < 3:
        wi_cmd = self.ControlDataStore.Command
        if wi_cmd == 'Arrêt':
          prep_success = False
          playlist_stop = True
        elif (wi_cmd or '')[:4] == 'Jump' and playlist:
          if wi_cmd[5:].isdecimal():
            jump_ind = int(wi_cmd[5:]) - 1
          prep_success = False
      if playlist:
        self.ControlDataStore.Current = order[ind]
      if not prep_success:
        if self.MediaServerInstance:
          try:
            self.MediaServerInstance.shutdown()
          except:
            pass
          self.MediaServerInstance = None
        if self.NextMediaServerInstance:
          try:
            self.NextMediaServerInstance.shutdown()
          except:
            pass
          self.NextMediaServerInstance = None
        if not playlist or self.shutdown_requested:
          self.logger.log(2, 'controlinterrupt')
          self.html_ready = False
          if not self.shutdown_requested:
            self.ControlDataStore.Redirect = True
          self.WebSocketServerInstance.close('control')
          self.ControlDataStore = None
          self.DLNAControllerInstance.send_event_unsubscription(event_listener)
          try:
            self.DLNAControllerInstance.send_Stop(renderer)
          except:
            pass
          if event_listener_rc:
            self.DLNAControllerInstance.send_event_unsubscription(event_listener_rc)
          event_notification_listener.stop()
          return
        else:
          if check_renderer:
            if HTTPRequest(renderer.DescURL, 'HEAD', timeout=5, ip=renderer_hip).code != '200':
              self.logger.log(1, 'norendereranswer', renderer.FriendlyName)
              break
          continue
      self.logger.log(0, 'ready', media_title, LSTRINGS['webinterface'].get('subtitled', 'subtitled') if suburi else '', LSTRINGS['webinterface'].get('direct', 'direct') if server_mode == DLNAWebInterfaceServer.SERVER_MODE_NONE else {MediaProvider.SERVER_MODE_RANDOM: LSTRINGS['webinterface'].get('random', 'random'), MediaProvider.SERVER_MODE_SEQUENTIAL: LSTRINGS['webinterface'].get('sequential', 'sequential%s') % ((LSTRINGS['webinterface'].get('remuxed', 'remuxed %s') % self.MediaServerInstance.MediaMuxContainer.lstrip('!')) if self.MediaServerInstance.MediaProviderInstance.FFmpeg_process else '')}.get(server_mode,''), self.Renderer.FriendlyName)
      status_dict = {'PLAYING': 'Lecture', 'PAUSED_PLAYBACK': 'Pause', 'STOPPED': 'Arrêt'}
      new_duration = None
      transport_status = ''
      stop_reason = ''
      max_renderer_position = '0:00:00'
      if server_mode != DLNAWebInterfaceServer.SERVER_MODE_NONE:
        renderer_stopped_position = self.MediaServerInstance.MediaProviderInstance.MediaStartFrom
      else:
        renderer_stopped_position = media_start_from
      if not renderer_stopped_position or renderer_stopped_position == '0:00:00':
        renderer_stopped_position = None
      wi_cmd = None
      if gapless_status < 3:
        old_value = None
        is_paused = True
        renderer_position = '0:00:00'
        self.ControlDataStore.Position = media_start_from
        if server_mode == MediaProvider.SERVER_MODE_RANDOM:
          if accept_ranges or media_kind == 'image':
            self.ControlDataStore.Status = 'prêt'
          else:
            self.ControlDataStore.Status = 'prêt (lecture à partir du début)'
        elif server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
          if self.MediaServerInstance.MediaProviderInstance.MediaMuxContainer or media_kind == 'image':
            self.ControlDataStore.Status = 'prêt'
          else:
            self.ControlDataStore.Status = 'prêt (lecture à partir du début)'
        else:
          self.ControlDataStore.Status = 'prêt'
        if not cmd_stop:
          wi_cmd = 'Lecture'
          self.ControlDataStore.IncomingEvent.set()
        warning_d.clear()
        warning_e.clear()
        gapless_status = 0 if self.NextMediaServerInstance else -1
      else:
        old_value = new_value
        try:
          renderer_position = self.DLNAControllerInstance.get_Position(renderer).rsplit('.')[0]
        except:
          renderer_position = '0:00:00'
        self.ControlDataStore.Position = renderer_position
        self.ControlDataStore.IncomingEvent.set()
        gapless_status = 1 if self.NextMediaServerInstance else -1
      new_value = None
      cmd_stop = False
      if event_listener_rc:
        tv = warning_v.last()
        warning_v.clear()
        if tv is not None:
          try:
            tv = int(int(tv) * 100 / vol_max)
          except:
            tv = None
        if tv is None:
          try:
            tv = int(int(self.DLNAControllerInstance.get_Volume(renderer)) * 100 / vol_max)
          except:
            pass
        if tv is not None:
          self.ControlDataStore.Volume = tv
        tv = warning_m.last()
        warning_m.clear()
        if tv is not None:
          tv = tv == "1"
        else:
          try:
            tv = self.DLNAControllerInstance.get_Mute(renderer) == "1"
          except:
            pass
        if tv is not None:
          self.ControlDataStore.Mute = tv
      redo_seek = None
      check_renderer = False
      while not self.shutdown_requested and new_value != 'STOPPED':
        new_value = self.DLNAControllerInstance.wait_for_warning(warning, 10 if is_paused else 1)
        if self.shutdown_requested:
          break
        if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and accept_ranges:
          if old_value and media_kind != 'image':
            new_duration = warning_d.fresh()
            if new_duration:
              if _position_to_seconds(new_duration):
                self.ControlDataStore.Duration = str(_position_to_seconds(new_duration))
        try:
          renderer_new_position = self.DLNAControllerInstance.get_Position(renderer).rsplit('.')[0]
        except:
          renderer_new_position = ''
        if media_kind != 'image' and renderer_new_position:
          if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and _position_to_seconds(renderer_new_position) == 0 and _position_to_seconds(renderer_position) != 0:
            if not renderer_stopped_position:
              try:
                transport_status = self.DLNAControllerInstance.get_TransportInfo(renderer)[0]
              except:
                transport_status = ''
              if transport_status in ('PAUSED_PLAYBACK', 'PLAYING'):
                renderer_position = renderer_new_position
          else:
            renderer_position = renderer_new_position
          if _position_to_seconds(renderer_position) > _position_to_seconds(max_renderer_position):
            max_renderer_position = renderer_position
        if media_kind != 'image' and accept_ranges and self.ControlDataStore.Duration == '0' and ((new_value and not old_value) or gapless_status in (0, 1)) and renderer_new_position:
          try:
            new_duration = self.DLNAControllerInstance.get_Duration(self.Renderer)
            if new_duration:
              if _position_to_seconds(new_duration):
                self.ControlDataStore.Duration = str(_position_to_seconds(new_duration))
            if self.ControlDataStore.Duration == '0':
              new_duration = self.DLNAControllerInstance.get_Duration_Fallback(self.Renderer)
              if new_duration:
                if _position_to_seconds(new_duration):
                  self.ControlDataStore.Duration = str(_position_to_seconds(new_duration))
          except:
            pass
        if media_kind == 'image' and image_duration and self.ControlDataStore.Status != 'Arrêt':
          renderer_position = _seconds_to_position(int(max(0, image_duration - ((time.time() - image_start) if image_start else 0))))
        if not old_value and new_value == 'STOPPED':
          if warning_e.fresh() is None:
            new_value = None
        if new_value and new_value != old_value:
          if restart_from is not None:
            restart_from = None
            self.ControlDataStore.ShowStartFrom = False
          if new_value != 'STOPPED' and server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
            if renderer_stopped_position:
              if accept_ranges:
                try:
                  self.DLNAControllerInstance.send_Seek(renderer, renderer_stopped_position)
                except:
                  pass
              renderer_stopped_position = None
              redo_seek = None
            elif redo_seek:
              try:
                self.DLNAControllerInstance.send_Seek(renderer, redo_seek)
              except:
                pass
              redo_seek = None
            if not old_value:
              if media_kind != 'image':
                media_start_from = '0:00:00'
          if new_value != 'STOPPED' and not old_value and server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
            if not self.MediaServerInstance.MediaProviderInstance.MediaMuxContainer and media_kind != 'image':
              media_start_from = '0:00:00'
          if new_value == 'PLAYING':
            is_paused = False
            if media_kind == 'image' and image_duration:
              image_start = time.time()
            if gapless_status == 0:
              gapless_status = 1
          elif new_value == 'PAUSED_PLAYBACK':
            is_paused = True
            if media_kind == 'image' and image_duration and image_start:
              image_duration = max(0, image_duration - (time.time() - image_start))
              image_start = None
          self.ControlDataStore.Status = status_dict[new_value]
          if new_value == 'PAUSED_PLAYBACK' and (server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL or (server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and (not self.ControlDataStore.Duration or self.ControlDataStore.Duration == '0') and accept_ranges) or media_kind == 'image'):
            restart_from = ''
            self.ControlDataStore.ShowStartFrom = True
          old_value = new_value
        if new_value != 'STOPPED' or server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
          if server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL or not renderer_stopped_position:
            if media_kind != 'image':
              self.ControlDataStore.Position = _seconds_to_position(_position_to_seconds(media_start_from) + _position_to_seconds(renderer_position))
            else:
              self.ControlDataStore.Position = renderer_position
          if new_value == 'STOPPED' and server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
            self.ControlDataStore.Status = status_dict[new_value]
            if (accept_ranges or media_kind == 'image') and not playlist and not self.EndLess:
              new_value = None
              if not renderer_stopped_position:
                is_paused = True
                renderer_stopped_position = renderer_position
                if media_kind != 'image':
                  try:
                    self.DLNAControllerInstance.send_Seek(renderer, '0:00:00')
                  except:
                    pass
            if media_kind == 'image':
              image_duration = _position_to_seconds(self.MediaPosition or '0:00:00')
              image_start = None
              self.ControlDataStore.Position = self.MediaPosition
          if event_listener_rc:
            tv = warning_m.fresh()
            if tv is not None:
              self.ControlDataStore.Mute = tv == "1"
            tv = warning_v.fresh()
            if tv is not None:
              try:
                self.ControlDataStore.Volume = int(int(tv) * 100 / vol_max)
              except:
                pass
          if not wi_cmd:
            wi_cmd = self.ControlDataStore.Command
          if wi_cmd == 'Lecture':
            try:
              if server_mode == MediaProvider.SERVER_MODE_RANDOM:
                if self.MediaServerInstance.MediaProviderInstance.Status == MediaProvider.STATUS_ABORTED:
                  try:
                    self.MediaServerInstance.shutdown()
                  except:
                    pass
                  try:
                    media_feed = self.MediaServerInstance.MediaProviderInstance.MediaFeed
                    media_type = self.MediaServerInstance.MediaProviderInstance.MediaSrcType.replace('WebPageURL', 'ContentURL')
                    media_sub = self.MediaServerInstance.MediaSubBufferInstance
                    server_address = self.MediaServerInstance.MediaServerAddress
                    self.MediaServerInstance = MediaServer(MediaProvider.SERVER_MODE_RANDOM, server_address, media_feed, MediaSrcType=media_type, MediaStartFrom='', MediaBufferSize=self.MediaBufferSize, MediaBufferAhead=self.MediaBufferAhead, MediaSubBuffer=media_sub, verbosity=self.verbosity, auth_ip=(renderer.Ip, *self.DLNAControllerInstance.ips))
                    self.MediaServerInstance.start()
                    incoming_event = self.ControlDataStore.IncomingEvent
                    if not self.shutdown_requested:
                      self.ControlDataStore.IncomingEvent = self.MediaServerInstance.BuildFinishedEvent
                      self.MediaServerInstance.BuildFinishedEvent.wait()
                      self.ControlDataStore.IncomingEvent = incoming_event
                      if (self.MediaServerInstance.is_running == True) and self.MediaServerInstance.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED):
                        self.ControlDataStore.IncomingEvent = self.MediaServerInstance.MediaServerFinishedEvent
                        self.MediaServerInstance.MediaServerFinishedEvent.wait()
                        self.ControlDataStore.IncomingEvent = incoming_event
                  except:
                    pass
              if restart_from is not None:
                restart_from = None
                self.ControlDataStore.ShowStartFrom = False
              if self.ControlDataStore.Status in ('prêt', 'prêt (lecture à partir du début)', 'Arrêt'):
                self.ControlDataStore.Status = 'en cours...'
              self.DLNAControllerInstance.send_Play(renderer)
            except:
              pass
          elif wi_cmd == 'Pause':
            try:
              self.DLNAControllerInstance.send_Pause(renderer)
            except:
              pass
          elif wi_cmd == 'Arrêt':
            cmd_stop = True
            if self.ControlDataStore.Status in ('prêt', 'prêt (lecture à partir du début)'):
              playlist_stop = True
            self.ControlDataStore.Status = 'en cours...'
            if restart_from is not None:
              restart_from = None
              self.ControlDataStore.ShowStartFrom = False
            try:
              transport_status = self.DLNAControllerInstance.get_TransportInfo(renderer)[0] or ''
            except:
              transport_status = ''
            if transport_status in ('PAUSED_PLAYBACK', 'PLAYING', 'TRANSITIONING'):
              old_value = 'STOPPED'
              try:
                if not self.DLNAControllerInstance.send_Stop(renderer):
                  raise
              except:
                new_value = 'STOPPED'
                playlist_stop = True
              self.ControlDataStore.Status = 'Arrêt'
            else:
              new_value = 'STOPPED'
              if transport_status == '':
                playlist_stop = True
                check_renderer = True
          elif wi_cmd == 'Fin':
            try:
              self.DLNAControllerInstance.send_Stop(renderer)
            except:
              pass
          elif (wi_cmd or '')[:4] == 'Jump':
            if wi_cmd[5:].isdecimal():
              jump_ind = max(0, int(wi_cmd[5:]) - 1)
              if server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL or jump_ind != order[ind]:
                if media_kind != 'image':
                  try:
                    self.DLNAControllerInstance.send_Stop(renderer)
                  except:
                    pass
                new_value = 'STOPPED'
                if self.NextMediaServerInstance:
                  if gapless_status == 2:
                    try:
                      if self.NextMediaServerInstance.MediaProviderInstance.AcceptRanges:
                        self.DLNAControllerInstance.send_Local_URI_Next(self.Renderer, '', '')
                      else:
                        self.DLNAControllerInstance.send_URI_Next(self.Renderer, '', '')
                    except:
                      pass
                  gapless_status = -1
                  try:
                    self.NextMediaServerInstance.shutdown()
                  except:
                    pass
                  self.NextMediaServerInstance = None
            if restart_from is not None:
              self.ControlDataStore.ShowStartFrom = False
              if media_kind == 'image' and jump_ind == order[ind]:
                restart_from = None
                jump_ind = None
                try:
                  self.DLNAControllerInstance.send_Play(renderer)
                except:
                  pass
          elif playlist and wi_cmd == 'Shuffle':
            if self.ControlDataStore.Shuffle:
              ind = order[ind]
              order = list(range(len(playlist)))
              self.ControlDataStore.Shuffle = False
            else:
              random.shuffle(order)
              self.ControlDataStore.Shuffle = True
              if old_value:
                ind = order.index(ind)
              else:
                ind = -1
                try:
                  self.DLNAControllerInstance.send_Stop(renderer)
                except:
                  pass
                new_value = 'STOPPED'
            if self.NextMediaServerInstance:
              if gapless_status == 2:
                try:
                  if self.NextMediaServerInstance.MediaProviderInstance.AcceptRanges:
                    self.DLNAControllerInstance.send_Local_URI_Next(self.Renderer, '', '')
                  else:
                    self.DLNAControllerInstance.send_URI_Next(self.Renderer, '', '')
                except:
                  pass
              gapless_status = -1
              try:
                self.NextMediaServerInstance.shutdown()
              except:
                pass
              self.NextMediaServerInstance = None
          elif (wi_cmd or '')[:4] == 'Seek':
            if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and accept_ranges and media_kind != 'image':
              if not renderer_stopped_position:
                try:
                  if not self.ControlDataStore.Duration or self.ControlDataStore.Duration == '0':
                    self.DLNAControllerInstance.send_Play(renderer)
                  if not self.DLNAControllerInstance.send_Seek(renderer, wi_cmd[5:]):
                    if is_paused:
                      redo_seek = wi_cmd[5:]
                except:
                  pass
              else:
                renderer_stopped_position = wi_cmd[5:]
            elif server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL and media_kind != 'image':
              restart_from = wi_cmd[5:]
            elif media_kind == 'image':
              try:
                image_duration = _position_to_seconds(wi_cmd[5:])
                self.MediaPosition = wi_cmd[5:]
                self.ControlDataStore.Position = self.MediaPosition
                renderer_position = self.MediaPosition
              except:
                pass
          elif (wi_cmd or '')[:4] == 'Mute':
            try:
              self.DLNAControllerInstance.set_Mute(renderer, wi_cmd[5:] == "true")
            except:
              pass
          elif (wi_cmd or '')[:6] == 'Volume':
            try:
              self.DLNAControllerInstance.set_Volume(renderer, int(int(wi_cmd[7:]) * vol_max / 100))
            except:
              pass
          wi_cmd = self.ControlDataStore.Command
          if media_kind == 'image' and image_start:
            if renderer_position == '0:00:00':
              wi_cmd = 'Fin'
              if playlist:
                new_value = 'STOPPED'
          if wi_cmd:
            self.ControlDataStore.IncomingEvent.set()
        if gapless_status == 1 and not self.shutdown_requested and new_value != 'STOPPED':
          prep_success = not self.shutdown_requested and self.NextMediaServerInstance.ready
          if prep_success:
            nsuburi = None
            if self.NextMediaServerInstance.MediaProviderInstance.MediaSubBuffer:
              if self.NextMediaServerInstance.MediaProviderInstance.MediaSubBuffer[0]:
                nsuburi = 'http://%s:%s/mediasub%s' % (*self.NextMediaServerInstance.MediaServerAddress, self.NextMediaServerInstance.MediaProviderInstance.MediaSubBuffer[1])
            if self.MediaSrc[:7].lower() == 'upnp://':
              nmedia_title = titles[order[nind]]
            else:
              nmedia_title = self.NextMediaServerInstance.MediaProviderInstance.MediaTitle
            warning_n.clear()
            try:
              if self.NextMediaServerInstance.MediaProviderInstance.AcceptRanges:
                prep_success = self.DLNAControllerInstance.send_Local_URI_Next(self.Renderer, 'http://%s:%s/media%s' % (*self.NextMediaServerInstance.MediaServerAddress, self.NextMediaServerInstance.MediaProviderInstance.MediaFeedExt), nmedia_title, kind=mediakinds[order[nind]], suburi=nsuburi)
              else:
                prep_success = self.DLNAControllerInstance.send_URI_Next(self.Renderer, 'http://%s:%s/media%s' % (*self.NextMediaServerInstance.MediaServerAddress, self.NextMediaServerInstance.MediaProviderInstance.MediaFeedExt), nmedia_title, kind=mediakinds[order[nind]], suburi=nsuburi)
            except:
              prep_success = False
            if prep_success:
              gapless_status = 2
              self.NextMediaServerInstance.MediaBufferInstance.create_lock.acquire()
              self.NextMediaServerInstance.MediaBufferInstance.r_indexes.append(1)
              self.NextMediaServerInstance.MediaBufferInstance.create_lock.release()
              self.NextMediaServerInstance.MediaBufferInstance.r_event.set()
            else:
              gapless_status = -1
        if gapless_status == 2 and not self.shutdown_requested:
          if warning_n.fresh() is not None:
            if warning.last() == 'PLAYING':
              transport_status = 'PLAYING'
            else:
              try:
                transport_status = self.DLNAControllerInstance.get_TransportInfo(renderer)[0]
              except:
                transport_status = ''
            if transport_status == 'PAUSED_PLAYBACK':
              try:
                if not self.DLNAControllerInstance.send_Play(renderer):
                  raise
              except:
                transport_status = ''
                try:
                  self.DLNAControllerInstance.send_Stop(renderer)
                except:
                  pass
            if transport_status in ('PLAYING', 'TRANSITIONING', 'PAUSED_PLAYBACK'):
              if (warning_n.last() or '').split('/', 3)[2:3].count('%s:%s' % self.NextMediaServerInstance.MediaServerAddress):
                gapless_status = 3
                accept_ranges = self.NextMediaServerInstance.MediaProviderInstance.AcceptRanges
              else: 
                try:
                  self.DLNAControllerInstance.send_Stop(renderer)
                except:
                  pass
            new_value = 'STOPPED'
      if self.MediaServerInstance:
        try:
          self.MediaServerInstance.shutdown()
        except:
          pass
        self.MediaServerInstance = None
      if event_listener_rc:
        self.ControlDataStore.Mute = ''
      if gapless_status == 2:
        try:
          if self.NextMediaServerInstance.MediaProviderInstance.AcceptRanges:
            self.DLNAControllerInstance.send_Local_URI_Next(self.Renderer, '', '')
          else:
            self.DLNAControllerInstance.send_URI_Next(self.Renderer, '', '')
        except:
          pass
    transport_status = ''
    stop_reason = ''
    if check_renderer or not renderer.StatusAlive:
      if HTTPRequest(renderer.DescURL, 'HEAD', timeout=5, ip=renderer_hip).code != '200':
        self.logger.log(1, 'norendereranswer', renderer.FriendlyName)
        check_renderer = True
      else:
        check_renderer = False
    if not check_renderer:
      if not self.shutdown_requested and self.verbosity == 2:
        try:
          transport_status = self.DLNAControllerInstance.get_TransportInfo(renderer)[1]
          stop_reason = self.DLNAControllerInstance.get_StoppedReason(renderer)[0]
        except:
          pass
      try:
        if self.DLNAControllerInstance.send_Stop(renderer) is None:
          raise
      except:
        if self.shutdown_requested:
          check_renderer = True
    if playlist == False and server_mode is not None:
      if server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
        renderer_position = max_renderer_position
      if media_kind != 'image':
        self.MediaPosition = _seconds_to_position(max(0, _position_to_seconds(media_start_from) + _position_to_seconds(renderer_position) - 5))
      self.ControlDataStore.Position = self.MediaPosition
    if self.MediaServerInstance:
      try:
        self.MediaServerInstance.shutdown()
      except:
        pass
      self.MediaServerInstance = None
    if self.NextMediaServerInstance:
      try:
        self.NextMediaServerInstance.shutdown()
      except:
        pass
      self.NextMediaServerInstance = None
    self.html_ready = False
    if not check_renderer:
      self.DLNAControllerInstance.send_event_unsubscription(event_listener)
      if event_listener_rc:
        self.DLNAControllerInstance.send_event_unsubscription(event_listener_rc)
    event_notification_listener.stop()
    self.logger.log(2, 'controlstop', LSTRINGS['webinterface'].get('status', 'status') if transport_status or stop_reason else '', transport_status, ':' if transport_status and stop_reason else '', stop_reason)
    if not self.shutdown_requested:
      self.ControlDataStore.Redirect = True
    self.WebSocketServerInstance.close('control')
    self.ControlDataStore = None

  def _start_webserver(self):
    try:
      with ThreadedDualStackServer(self.DLNAWebInterfaceServerAddress, DLNAWebInterfaceRequestHandler, kmod='webinterface', verbosity=self.verbosity) as self.DLNAWebInterfaceServerInstance:
        self.DLNAWebInterfaceServerInstance.Interface = self
        self.DLNAWebInterfaceServerInstance.post_lock = threading.Lock()
        self.WebServerReady.set()
        try:
          self.DLNAWebInterfaceServerInstance.serve_forever()
        except:
          if self.shutdown_requested:
            pass
          else:
            raise
    except:
      self.logger.log(0, 'fail', '%s:%s' % self.DLNAWebInterfaceServerAddress)
      self.WebServerReady.set()

  def run(self):
    if self.Status is not None:
      self.logger.log(1, 'alreadyrunning')
      return
    self.logger.log(0, 'start', '%s:%s' % self.DLNAWebInterfaceServerAddress)
    webserver_thread = threading.Thread(target=self._start_webserver)
    webserver_thread.start()
    self.WebSocketServerInstance = WebSocketServer((self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+1), self.verbosity)
    self.WebSocketServerInstance.start()
    if self.TargetStatus in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL):
      self.DLNAAdvertisementListenerInstance.start()
      self.RenderersEvent = self.DLNAControllerInstance.advert_status_change
      self.DLNAControllerInstance.discovery_status_change = self.RenderersEvent
    while (self.Status is None or self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_START) and not self.shutdown_requested:
      if self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
        self.Status = DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS
        self.manage_start()
      elif self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_START:
        self.Status = DLNAWebInterfaceServer.INTERFACE_START
        self.manage_start()
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_CONTROL
      if self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_CONTROL and not self.shutdown_requested:
        self.Status = DLNAWebInterfaceServer.INTERFACE_CONTROL
        self.manage_control()
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_START
      if self.shutdown_requested:
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
        self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
    if self.RenderersEvent:
      self.DLNAAdvertisementListenerInstance.stop()
      self.RenderersEvent = None
    self.WebSocketServerInstance.shutdown()
    self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
    self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING

  def start(self):
    t = threading.Thread(target=self.run)
    t.start()
    self.WebServerReady.wait()
    self.WebServerReady.clear()
    if not hasattr(self, 'DLNAWebInterfaceServerInstance'):
      return False
    return True

  def shutdown(self):
    if not self.shutdown_requested:
      self.logger.log(0, 'shutdown')
      self.shutdown_requested = True
      if self.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.RenderersEvent.set()
        if self.ControlDataStore is not None:
          try:
            self.ControlDataStore.IncomingEvent.set()
          except:
            pass
        if self.MediaServerInstance:
          try:
            self.MediaServerInstance.shutdown()
          except:
            pass
      elif self.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        self.RenderersEvent.set()
      self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
      self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
      try:
        self.DLNAWebInterfaceServerInstance.shutdown()
        for sock in self.DLNAWebInterfaceServerInstance.conn_sockets:
          try:
            sock.shutdown(socket.SHUT_RDWR)
          except:
            pass
      except:
        pass


if __name__ == '__main__':

  print('DLNAPlayOn v1.8.1 (https://github.com/PCigales/DLNAPlayOn)    Copyright © 2022 PCigales')
  print(LSTRINGS['parser']['license'])
  print('');

  formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=65, width=119)
  CustomArgumentParser = partial(argparse.ArgumentParser, formatter_class=formatter, add_help=False)
  parser = CustomArgumentParser()
  parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help=LSTRINGS['parser']['help'])
  subparsers = parser.add_subparsers(dest='command', parser_class=CustomArgumentParser)
  
  common_parser = CustomArgumentParser()
  common_parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help=LSTRINGS['parser']['help'])
  common_parser.add_argument('--ip', '-i', metavar='INTERFACE_IP', help=LSTRINGS['parser']['ip'], nargs='?', const='0.0.0.0', default='')
  common_parser.add_argument('--port', '-p', metavar='INTERFACE_PORT', help=LSTRINGS['parser']['port'], default=8000, type=int)
  common_parser.add_argument('--join', '-j', metavar='HANDLER_IP', help=LSTRINGS['parser']['hip'], nargs='?', const='0.0.0.0', default='')
  common_parser.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help=LSTRINGS['parser']['rendereruuid'], default=None)
  common_parser.add_argument('--name', '-n', metavar='RENDERER_NAME', help=LSTRINGS['parser']['renderername'], default=None)
  
  server_parser = CustomArgumentParser()
  server_parser.add_argument('--typeserver', '-t', metavar='TYPE_SERVER', help=LSTRINGS['parser']['servertype'], choices=['a', 's', 'r', 'g', 'n'], default='a')
  server_parser.add_argument('--buffersize', '-b', metavar='BUFFER_SIZE', help=LSTRINGS['parser']['buffersize'], default=75, type=int)
  server_parser.add_argument('--bufferahead', '-a', metavar='BUFFER_AHEAD', help=LSTRINGS['parser']['bufferahead'], default=25, type=int)
  server_parser.add_argument('--muxcontainer', '-m', metavar='MUX_CONTAINER', help=LSTRINGS['parser']['muxcontainer'], choices=['MP4', 'MPEGTS', '!MP4', '!MPEGTS'], default='MP4', type=str.upper)
  server_parser.add_argument('--onreadyplay', '-o', help=LSTRINGS['parser']['onreadyplay'], action='store_true')
  
  subparser_display_renderers = subparsers.add_parser('display_renderers', aliases=['r'], parents=[common_parser], help=LSTRINGS['parser']['displayrenderers'])
  subparser_display_renderers.add_argument('--verbosity', '-v', metavar='VERBOSE', help=LSTRINGS['parser']['verbosity'], type=int, choices=[0, 1, 2], default=0)

  subparser_start = subparsers.add_parser('start', aliases=['s'], parents=[common_parser, server_parser], help=LSTRINGS['parser']['start'])
  subparser_start.add_argument('--mediasrc', '-c', metavar='MEDIA_ADDRESS', help=LSTRINGS['parser']['mediasrc1'], default='')
  subparser_start.add_argument('--mediasubsrc', '-s', metavar='MEDIA_SUBADDRESS', help=LSTRINGS['parser']['mediasubsrc'], default='')
  subparser_start.add_argument('--mediasublang', '-l', metavar='MEDIA_SUBLANG', help=LSTRINGS['parser']['mediasublang'], default='')
  subparser_start.add_argument('--mediastartfrom', '-f', metavar='MEDIA_START_FROM', help=LSTRINGS['parser']['mediastartfrom'], default=None)
  subparser_start.add_argument('--verbosity', '-v', metavar='VERBOSE', help=LSTRINGS['parser']['verbosity'], type=int, choices=[0, 1, 2], default=0)

  subparser_control = subparsers.add_parser('control', aliases=['c'], parents=[common_parser, server_parser], help=LSTRINGS['parser']['control'])
  subparser_control.add_argument('mediasrc', metavar='MEDIA_ADDRESS', help=LSTRINGS['parser']['mediasrc2'])
  subparser_control.add_argument('--mediasubsrc', '-s', metavar='MEDIA_SUBADDRESS', help=LSTRINGS['parser']['mediasubsrc'], default='')
  subparser_control.add_argument('--mediasublang', '-l', metavar='MEDIA_SUBLANG', help=LSTRINGS['parser']['mediasublang'], default='')
  subparser_control.add_argument('--mediastartfrom', '-f', metavar='MEDIA_START_FROM', help=LSTRINGS['parser']['mediastartfrom'], default=None)
  subparser_control.add_argument('--slideshowduration', '-d', metavar='SLIDESHOW_DURATION', help=LSTRINGS['parser']['slideshowduration'], default=None)
  subparser_control.add_argument('--endless', '-e', help=LSTRINGS['parser']['endless'], action='store_true')
  subparser_control.add_argument('--verbosity', '-v', metavar='VERBOSE', help=LSTRINGS['parser']['verbosity'], type=int, choices=[0, 1, 2], default=0)


  args = parser.parse_args()
  if not args.command:
    parser.print_help()
    exit()

  if args.command in ('display_renderers', 'r'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), DLNAJoinIp=args.join, Launch=DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, Renderer_uuid=args.uuid, Renderer_name=args.name, verbosity=args.verbosity)
  elif args.command in ('start', 's'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), DLNAJoinIp=args.join, Launch=DLNAWebInterfaceServer.INTERFACE_START, Renderer_uuid=args.uuid, Renderer_name=args.name, MediaServerMode={'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM, 'g':DLNAWebInterfaceServer.SERVER_MODE_GAPLESS, 'n':DLNAWebInterfaceServer.SERVER_MODE_NONE}.get(args.typeserver,None) , MediaSrc=os.path.abspath(args.mediasrc) if args.mediasrc and not '://' in args.mediasrc else args.mediasrc, MediaStartFrom=args.mediastartfrom, MediaBufferSize=args.buffersize, MediaBufferAhead=args.bufferahead, MediaMuxContainer=args.muxcontainer, OnReadyPlay=args.onreadyplay, MediaSubSrc=os.path.abspath(args.mediasubsrc) if args.mediasubsrc and not '://' in args.mediasubsrc else args.mediasubsrc, MediaSubLang=args.mediasublang if (args.mediasublang and args.mediasublang != '.') else ('' if args.mediasublang == '.' else LSTRINGS['parser'].get('mediasublangcode', '')), verbosity=args.verbosity)
  elif args.command in ('control', 'c'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), DLNAJoinIp=args.join, Launch=DLNAWebInterfaceServer.INTERFACE_CONTROL, Renderer_uuid=args.uuid, Renderer_name=args.name, MediaServerMode={'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM, 'g':DLNAWebInterfaceServer.SERVER_MODE_GAPLESS, 'n':DLNAWebInterfaceServer.SERVER_MODE_NONE}.get(args.typeserver,None), MediaSrc=os.path.abspath(args.mediasrc) if not '://' in args.mediasrc else args.mediasrc, MediaStartFrom=args.mediastartfrom, MediaBufferSize=args.buffersize, MediaBufferAhead=args.bufferahead, MediaMuxContainer=args.muxcontainer, OnReadyPlay=args.onreadyplay, MediaSubSrc=os.path.abspath(args.mediasubsrc) if args.mediasubsrc and not '://' in args.mediasubsrc else args.mediasubsrc, MediaSubLang=args.mediasublang if (args.mediasublang and args.mediasublang != '.') else ('' if args.mediasublang == '.' else LSTRINGS['parser'].get('mediasublangcode', '')), SlideshowDuration=args.slideshowduration, EndLess=args.endless, verbosity=args.verbosity)

  if DLNAWebInterfaceServerInstance.start():
    if socket.inet_aton(DLNAWebInterfaceServerInstance.DLNAWebInterfaceServerAddress[0]) == b'\x00\x00\x00\x00':
      webbrowser.open('http://127.0.0.1:%s/' % DLNAWebInterfaceServerInstance.DLNAWebInterfaceServerAddress[1])
    else: 
      webbrowser.open('http://%s:%s/' % DLNAWebInterfaceServerInstance.DLNAWebInterfaceServerAddress)
  else:
    DLNAWebInterfaceServerInstance.shutdown()
    exit()
  print(LSTRINGS['parser']['stopkey'])
  remux_list = ('MP4', 'MPEGTS', '!MP4', '!MPEGTS')
  server_modes = {MediaProvider.SERVER_MODE_AUTO: LSTRINGS['parser']['auto'], MediaProvider.SERVER_MODE_SEQUENTIAL: LSTRINGS['parser']['sequential'], MediaProvider.SERVER_MODE_RANDOM: LSTRINGS['parser']['random']}
  if DLNAWebInterfaceServerInstance.Status in (DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL):
    if not args.typeserver in ('g', 'n'):
      print(LSTRINGS['parser']['remuxkey'] % args.muxcontainer)
      print(LSTRINGS['parser']['servertypekey'] % server_modes.get({'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM}.get(args.typeserver,''),''))
    print(LSTRINGS['parser']['endlesskey'] % LSTRINGS['parser']['enabled' if DLNAWebInterfaceServerInstance.EndLess else 'disabled'])
  while DLNAWebInterfaceServerInstance.Status != DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING:
    k = msvcrt.getch()
    if k == b'\xe0':
      k = msvcrt.getch()
      k = b''
    if k.upper() == b'S':
        break
    if DLNAWebInterfaceServerInstance.Status in (DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL) and not args.typeserver in ('g', 'n'):
      if k.upper() == b'M':
        DLNAWebInterfaceServerInstance.MediaMuxContainer = remux_list[(remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)+1)%2+remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)//2*2]
        print(LSTRINGS['parser']['remuxnext'] % DLNAWebInterfaceServerInstance.MediaMuxContainer)
      elif k.upper() == b'!' :
        DLNAWebInterfaceServerInstance.MediaMuxContainer = remux_list[(remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)+2)%4]
        print(LSTRINGS['parser']['remuxnext'] % DLNAWebInterfaceServerInstance.MediaMuxContainer)
      elif k.upper() == b'T':
        DLNAWebInterfaceServerInstance.MediaServerMode = (DLNAWebInterfaceServerInstance.MediaServerMode + 1) % 3
        print(LSTRINGS['parser']['servertypenext'] % server_modes.get(DLNAWebInterfaceServerInstance.MediaServerMode,None))
    if DLNAWebInterfaceServerInstance.Status in (DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL) and k.upper() == b'E':
      DLNAWebInterfaceServerInstance.EndLess = not DLNAWebInterfaceServerInstance.EndLess
      print(LSTRINGS['parser']['endlessstatus'] % LSTRINGS['parser']['enabled' if DLNAWebInterfaceServerInstance.EndLess else 'disabled'])
  DLNAWebInterfaceServerInstance.shutdown()