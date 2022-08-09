import argparse
import time
import os
from functools import partial
import msvcrt
import urllib.parse
import webbrowser
import PlayOn

formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=52, width=119)
CustomArgumentParser = partial(argparse.ArgumentParser, formatter_class=formatter)
parser = CustomArgumentParser()
subparsers = parser.add_subparsers(dest='command', parser_class=CustomArgumentParser)

common_parser = CustomArgumentParser(add_help=False)
common_parser.add_argument('--join', '-j', metavar='HANDLER_IP', help='adresse IP du contrôleur DLNA [auto-sélectionnée par défaut - "0.0.0.0", soit toutes les interfaces, si option présente sans mention d\'adresse]', nargs='?', const='0.0.0.0', default='')

subparser_show_renderers = subparsers.add_parser('discover_renderers', aliases=['d'], parents=[common_parser], help='Affiche les renderers découverts sur le réseau')
subparser_show_renderers.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

subparser_show_services = subparsers.add_parser('show_services', aliases=['s'], parents=[common_parser], help='Affiche les services disponibles')
subparser_show_services.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help='uid du renderer [pas de sélection sur l\'uuid par défaut]', default=None)
subparser_show_services.add_argument('--name', '-n', metavar='RENDERER_NAME', help='nom du renderer [pas de sélection sur le nom par défaut]', default=None)
subparser_show_services.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

subparser_show_actions = subparsers.add_parser('show_actions', aliases=['a'], parents=[common_parser], help='Affiche les actions disponibles')
subparser_show_actions.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help='uuid du renderer [pas de sélection sur l\'uuid par défaut]', default=None)
subparser_show_actions.add_argument('--name', '-n', metavar='RENDERER_NAME', help='nom du renderer [pas de sélection sur le nom par défaut]', default=None)
subparser_show_actions.add_argument('--service', '-s', metavar='SERVICE_NAME', help='nom du service [pas de sélection de service par défaut]', default=None)
subparser_show_actions.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

subparser_show_arguments = subparsers.add_parser('show_arguments', aliases=['g'], parents=[common_parser], help='Affiche les arguments des actions')
subparser_show_arguments.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help='uuid du renderer [pas de sélection sur l\'uuid par défaut]', default=None)
subparser_show_arguments.add_argument('--name', '-n', metavar='RENDERER_NAME', help='nom du renderer [pas de sélection sur le nom par défaut]', default=None)
subparser_show_arguments.add_argument('--service', '-s', metavar='SERVICE_NAME', help='nom du service [pas de sélection de service par défaut]', default=None)
subparser_show_arguments.add_argument('--action', '-a', metavar='ACTION_NAME', help='nom de l\'action [pas de sélection de l\'action par défaut]', default=None)
subparser_show_arguments.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

subparser_listen_renderers = subparsers.add_parser('listen_renderers', aliases=['l'], parents=[common_parser], help='Affiche les publicités émises par les renderers')
subparser_listen_renderers.add_argument('--webinterface', '-w', help='suivi via l\'interface web', action='store_true')
subparser_listen_renderers.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

subparser_play_on = subparsers.add_parser('play_on', aliases=['p'], parents=[common_parser], help='Lit un contenu média sur le renderer')
subparser_play_on.add_argument('mediasrc', metavar='MEDIA_ADDRESS', help='adresse du contenu multimédia')
subparser_play_on.add_argument('--type', '-t', metavar='MEDIA_TYPE', help='type de contenu multimédia (vidéo, audio, image) [vidéo par défaut]', choices=['vidéo', 'audio', 'image'], default=None)
subparser_play_on.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help='uuid du renderer [premier renderer sans sélection sur l\'uuid par défaut]', default=None)
subparser_play_on.add_argument('--name', '-n', metavar='RENDERER_NAME', help='nom du renderer [premier renderer sans sélection sur le nom par défaut]', default=None)
subparser_play_on.add_argument('--interactive', '-i', help='lecture avec commande interactive', action='store_true')
subparser_play_on.add_argument('--webinterface', '-w', help='lecture avec contrôle via l\'interface web', action='store_true')
subparser_play_on.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)
args = parser.parse_args()

if not args.command:
  parser.print_help()
  exit()

DLNARendererControllerInstance = PlayOn.DLNAController(ip=args.join, verbosity=args.verbosity)
if args.command in ('discover_renderers', 'd'):
  DLNARendererControllerInstance.discover(timeout=5)
  for hip, renderer in zip(DLNARendererControllerInstance.Hips, DLNARendererControllerInstance.Renderers):
    print('\r\n' + renderer.FriendlyName)
    print('UUID: %s' % (renderer.UDN[5:]))
    print('Modèle: %s' % (renderer.ModelName))
    print('Description: %s' % (renderer.ModelDesc))
    print('Fabriquant: %s' % (renderer.Manufacturer))
    print('N° de série: %s' % (renderer.SerialNumber))
    print('URL du XML de description: %s' % (renderer.DescURL))
    print('Interface de connexion: %s' % (hip))
elif args.command in ('show_services', 's'):
  DLNARendererControllerInstance.discover(timeout=5)
  for hip, renderer in zip(DLNARendererControllerInstance.Hips, DLNARendererControllerInstance.Renderers):
    rend_match = True
    if args.uuid:
      if renderer.UDN != 'uuid:' + args.uuid:
        rend_match = False
    if args.name:
      if renderer.FriendlyName != args.name:
        rend_match = False
    if rend_match:
      print('\r\n' + renderer.FriendlyName, '[%s]' % hip)
      print('UUID: %s' % (renderer.UDN[5:]))
      print('URL du XML de description: %s' % (renderer.DescURL))
      for service in renderer.Services:
        print('\r\nService %s:' % (service.Id[23:]))
        print('  URL de contrôle: %s' % (service.ControlURL))
        print('  URL de souscription au serveur d\'événements: %s' % (service.SubscrEventURL))
        print('  URL de XML de description: %s' % (service.DescURL))
elif args.command in ('show_actions', 'a'):
  DLNARendererControllerInstance.discover(timeout=5)
  for hip, renderer in zip(DLNARendererControllerInstance.Hips, DLNARendererControllerInstance.Renderers):
    rend_match = True
    if args.uuid:
      if renderer.UDN != 'uuid:' + args.uuid:
        rend_match = False
    if args.name:
      if renderer.FriendlyName != args.name:
        rend_match = False
    if rend_match:
      print('\r\n' + renderer.FriendlyName, '[%s]' % hip)
      print('UUID: %s' % (renderer.UDN[5:]))
      print('URL du XML de description: %s' % (renderer.DescURL))
      for service in renderer.Services:
        servmatch = True
        if args.service:
          if service.Id != 'urn:upnp-org:serviceId:' + args.service:
            servmatch = False
        if servmatch:
          print('\r\nService %s:' % (service.Id[23:]))
          print('  URL de contrôle: %s' % (service.ControlURL))
          print('  Actions:')
          for action in service.Actions:
            print('    %s' % (action.Name))
elif args.command in ('show_arguments', 'g'):
  DLNARendererControllerInstance.discover(timeout=5)
  for hip, renderer in zip(DLNARendererControllerInstance.Hips, DLNARendererControllerInstance.Renderers):
    rend_match = True
    if args.uuid:
      if renderer.UDN != 'uuid:' + args.uuid:
        rend_match = False
    if args.name:
      if renderer.FriendlyName != args.name:
        rend_match = False
    if rend_match:
      print('\r\n' + renderer.FriendlyName, '[%s]' % hip)
      print('UUID: %s' % (renderer.UDN[5:]))
      print('URL du XML de description: %s' % (renderer.DescURL))
      for service in renderer.Services:
        serv_match = True
        if args.service:
          if service.Id != 'urn:upnp-org:serviceId:' + args.service:
            serv_match = False
        if serv_match:
          print('\r\nService %s:' % (service.Id[23:]))
          print('  URL de contrôle: %s' % (service.ControlURL))
          if service.EventThroughLastChange:
            print('  Notification d\'événement via LastChange: oui')
          elif service.EventThroughLastChange == False :
            print('  Notification d\'événement via LastChange: non')
          print('  Actions:')
          for action in service.Actions:
            act_match = True
            if args.action:
              if action.Name != args.action:
                act_match = False
            if act_match:
              print('\r\n    Action %s:' % (action.Name))
              for argument in action.Arguments:
                print('      Argument %s:' % (argument.Name))
                print('        Direction: %s' % (argument.Direction))
                if argument.Event:
                  print('        Événement associé: oui')
                elif argument.Event == False:
                  print('        Événement associé: non')
                print('        Type: %s' % (argument.Type))
                if argument.AllowedValueList:
                  if len(argument.AllowedValueList) == 1:
                    print('        Valeurs autorisées: (\'%s\')' % argument.AllowedValueList)
                  else:
                    print('        Valeurs autorisées:', argument.AllowedValueList)
                if argument.AllowedValueRange:
                  print('        Intervalle de valeurs autorisé:', argument.AllowedValueRange)
                if argument.DefaultValue:
                  print('        Valeur par défaut: %s' % (argument.DefaultValue))
elif args.command in ('listen_renderers', 'l'):
  if args.webinterface:
    DLNAWebInterfaceServerInstance = PlayOn.DLNAWebInterfaceServer(('127.0.0.1', 9000), DLNAJoinIp=args.join, Launch=PlayOn.DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, verbosity=args.verbosity)
    DLNARendererControllerInstance = DLNAWebInterfaceServerInstance.DLNAControllerInstance
    DLNAWebInterfaceServerInstance.start()
    webbrowser.open('http://127.0.0.1:9000/start.html')
  else:
    renderer_event = DLNARendererControllerInstance.start_advertisement_listening()
    DLNARendererControllerInstance.start_discovery_polling(timeout=3, alive_persistence=86400, polling_period=30, DiscoveryEvent=renderer_event)
  print("Appuyez sur une touche pour stopper")
  rend_stat = []
  while True:
    try:
      DLNARendererControllerInstance.wait_for_advertisement(1)
      for ind in range(len(DLNARendererControllerInstance.Renderers)):
        renderer = DLNARendererControllerInstance.Renderers[ind]
        hip = DLNARendererControllerInstance.Hips[ind]
        if ind == len(rend_stat):
          rend_stat.append(None)
        if renderer.StatusAlive != rend_stat[ind]:
          rend_stat[ind] = renderer.StatusAlive
          print('\r\n' + renderer.FriendlyName, '[%s]' % hip)
          print('UUID: %s' % (renderer.UDN[5:]))
          if renderer.StatusAlive:
            print('Statut: présent')
          else:
            print('Statut: absent')
      if msvcrt.kbhit():
        break
    except:
      break
  if args.webinterface:
    DLNAWebInterfaceServerInstance.shutdown()
  else:
    DLNARendererControllerInstance.stop_discovery_polling()
    DLNARendererControllerInstance.stop_advertisement_listening()
elif args.command in ('play_on', 'p'):
  DLNARendererControllerInstance.discover(timeout=3)
  renderer = DLNARendererControllerInstance.search(uuid=args.uuid, name=args.name)
  if renderer:
    if args.webinterface:
      DLNAWebInterfaceServerInstance = PlayOn.DLNAWebInterfaceServer(('127.0.0.1', 9000), DLNAJoinIp=args.join, Launch=PlayOn.DLNAWebInterfaceServer.INTERFACE_CONTROL, Renderer_uuid=renderer.UDN[5:], MediaSrc=args.mediasrc, MediaServerMode=PlayOn.DLNAWebInterfaceServer.SERVER_MODE_NONE, verbosity=args.verbosity)
      DLNAWebInterfaceServerInstance.start()
      webbrowser.open('http://127.0.0.1:9000/control.html')
    print('\r\nLecture de "%s" sur "%s"\r\n' % (args.mediasrc, renderer.FriendlyName))
    event_listener = DLNARendererControllerInstance.new_event_subscription(renderer, 'AVTransport', 9004)
    warning = DLNARendererControllerInstance.add_event_warning(event_listener, 'TransportState', 'PLAYING', 'STOPPED', 'PAUSED_PLAYBACK', WarningEvent=PlayOn.threading.Event())
    if not args.interactive:
        warning2 = DLNARendererControllerInstance.add_event_warning(event_listener, 'TransportState', 'STOPPED', 'PLAYING', WarningEvent=PlayOn.threading.Event())
    if DLNARendererControllerInstance.send_event_subscription(event_listener, 10000):
      if DLNARendererControllerInstance.send_URI(renderer, args.mediasrc, 'Média', args.type):
        if DLNARendererControllerInstance.send_Play(renderer):
          status_dict = {'PLAYING': 'Lecture', 'PAUSED_PLAYBACK': 'Pause', 'STOPPED': 'Arrêt'}
          if args.interactive:
            print('L: Lecture - P: Pause - A: Arrêt\r\n')
            old_value = None
            new_value = None
            is_paused = False
            renderer_position = '0:00:00'
            max_renderer_position = '00:00:00'
            while new_value != 'STOPPED':
              new_value = DLNARendererControllerInstance.wait_for_warning(warning, 1)
              renderer_new_position = DLNARendererControllerInstance.get_Position(renderer)
              if renderer_new_position:
                renderer_position = renderer_new_position
                if renderer_position > max_renderer_position:
                  max_renderer_position = renderer_position
              if not old_value and new_value == 'STOPPED':
                new_value = None
              if new_value and new_value != old_value:
                if args.verbosity >= 1:
                  print('TransportState:', new_value)
                if new_value == 'PLAYING':
                  is_paused = False
                elif new_value == 'PAUSED_PLAYBACK':
                  is_paused = True
                old_value = new_value
              if args.verbosity >= 1:
                if not is_paused:
                  print('Position:', renderer_position)
                else:
                  print('En pause')
              else:
                if not is_paused:
                  print('Position:', renderer_position, end ='\b'*18, flush=True)
                else:
                  print('En pause:', renderer_position, end ='\b'*18, flush=True)
              k = b''
              while msvcrt.kbhit():
                k = msvcrt.getch()
                if not k:
                  k = b''
                if k == b'\xe0':
                  k = msvcrt.getch()
                  k = b''
                  continue
                if k.upper() in (b'L', b'P', b'A'):
                  break
                else:
                  k = b''
              if k.upper() == b'L':
                DLNARendererControllerInstance.send_Play(renderer)
              elif k.upper() == b'P':
                DLNARendererControllerInstance.send_Pause(renderer)
              elif k.upper() == b'A':
                DLNARendererControllerInstance.send_Stop(renderer)
                break
            stop_reason = ""
            try:
              stop_reason = DLNARendererControllerInstance.get_StoppedReason(renderer)[0]
            except:
              pass
            if not stop_reason:
              stop_reason = '\b '
            print('\r\nFin de lecture à %s - statut: %s:%s' % (max_renderer_position, DLNARendererControllerInstance.get_TransportInfo(renderer)[1], stop_reason))
          else:
            old_value = None
            new_value = None
            while new_value != 'STOPPED':
              new_value = DLNARendererControllerInstance.wait_for_warning(warning, 2)
              if not old_value and new_value == 'STOPPED':
                new_value = None
              if new_value and new_value != old_value:
                old_value = new_value
              if args.verbosity >= 1:
                if new_value:
                  print('TransportState:', new_value)
                print('Position:', DLNARendererControllerInstance.get_Position(renderer))
              else:
                print('Position:', DLNARendererControllerInstance.get_Position(renderer), end ='\b'*18, flush=True)
              if new_value == 'PAUSED_PLAYBACK':
                if args.verbosity >= 1:
                  print('En pause')
                else:
                  print('En pause:', DLNARendererControllerInstance.get_Position(renderer), end ='\b'*18, flush=True)
                new_value2 = DLNARendererControllerInstance.wait_for_warning(warning2, clear=True)
            print('\r\nFin de lecture')
        else:
          print('Échec de la lecture du contenu média')
      else:
        print('Échec de la lecture du contenu média')
      DLNARendererControllerInstance.send_event_unsubscription(event_listener)
    else:
      print('Échec de la souscription au serveur d\'événements')
    if args.webinterface:
      DLNAWebInterfaceServerInstance.shutdown()
  else:
    print('Renderer introuvable')