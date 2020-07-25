import argparse
import time
import os
from functools import partial
import msvcrt
import PlayOn

formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=60, width=119)
CustomArgumentParser = partial(argparse.ArgumentParser, formatter_class=formatter)
parser = CustomArgumentParser()
parser.add_argument('mediasrc', metavar='MEDIA_ADDRESS', help='Adresse du contenu multimédia')
parser.add_argument('--ip', '-i', metavar='SERVER_IP_ADDRESS', help='Adresse IP du serveur [localhost par défaut]', default='localhost')
parser.add_argument('--port', '-p', metavar='SERVER_TCP_PORT', help='Port TCP du serveur [8000 par défaut]', default=8000, type=int)
parser.add_argument('--typeserver', '-t', metavar='TYPE_SERVER', help='type de serveur (a:auto, s:séquentiel, r:aléatoire) [a par défaut]', choices=['a', 's', 'r'], default='a')
parser.add_argument('--buffersize', '-b', metavar='BUFFER_SIZE', help='Taille du tampon en blocs de 1 Mo [75 par défaut]', default=75, type=int)
parser.add_argument('--bufferahead', '-a', metavar='BUFFER_AHEAD', help='Taille du sous-tampon de chargement par anticipation en blocs de 1 Mo [25 par défaut]', default=25, type=int)
parser.add_argument('--mediamuxcontainer', '-m', metavar='MUX_CONTAINER', help='Type de conteneur de remuxage précédé de ! pour qu\'il soit systématique [pas de remuxage par défaut]', choices=['MP4', 'MPEGTS', '!MP4', '!MPEGTS'], default=None, type=str.upper)
parser.add_argument('--mediasrctype', '-k', metavar='MEDIA_ADDRESS_KIND', help='Type d\'addresse du contenu média (ContentPath, ContentURL ou WebPageURL) [à deviner par défaut]', choices=['ContentPath', 'ContentURL', 'WebPageURL'], default=None)
parser.add_argument('--mediastartfrom', '-f', metavar='MEDIA_START_FROM', help='Position temporelle de démarrage au format H:MM:SS [Début par défaut]', default=None)
parser.add_argument('--mediasubsrc', '-s', metavar='MEDIA_SUBADDRESS', help='adresse du contenu de sous-titres [aucun par défaut]', default='')
parser.add_argument('--mediasubsrctype', '-j', metavar='MEDIA_SUBADDRESS_KIND', help='Type d\'addresse du contenu de sous-titres (ContentPath, ContentURL ou WebPageURL) [à deviner par défaut]', choices=['ContentPath', 'ContentURL', 'WebPageURL'], default=None)
parser.add_argument('--mediasublang', '-l', metavar='MEDIA_SUBLANG', help='langue de sous-titres, . pour pas de sélection [fr,fre,fra par défaut]', default='fr,fre,fra')
parser.add_argument('--verbosity', '-v', metavar='VERBOSE', help='Niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)
args = parser.parse_args()

MediaServerInstance = PlayOn.MediaServer({'a':PlayOn.MediaProvider.SERVER_MODE_AUTO, 's':PlayOn.MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':PlayOn.MediaProvider.SERVER_MODE_RANDOM}.get(args.typeserver,None), (args.ip, args.port), args.mediasrc, args.mediasrctype, args.mediastartfrom, args.buffersize, args.bufferahead, args.mediamuxcontainer, args.mediasubsrc, args.mediasubsrctype, args.mediasublang, None, "[TV]Samsung LED40", verbosity=args.verbosity)
MediaServerInstance.start()
print('Appuyez sur "S" pour stopper')
while True:
  k = msvcrt.getch()
  if k == b'\xe0':
    k = msvcrt.getch()
    k = b''
  if k.upper() == b'S':
    break
MediaServerInstance.shutdown()
