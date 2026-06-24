# TODO — VLK Launcher fixes

## Avatar / PDP unification

## Admin login / stats 401
- [ ] Vérifier la route `/admin/stats` (server) et la méthode `_api`/header côté client.
- [ ] Ajuster la manière d’envoyer le master password (et gérer message d’erreur réseau vs 401).

## FastAPI upload avatar
- [x] Ajouter `python-multipart` dans `src/server/requirements.txt`.

## Script serveur
- [ ] Confirmer/ajuster `scripts/copy_server_to_remote.sh` (rsync + restart), et s’assurer qu’il copie bien ce qui est nécessaire.

## Session chiffrée au relaunch
- [ ] Corriger la logique de déverrouillage UI pour ne pas redemander un master password à chaque relance quand la décryption a déjà été faite / peut être auto-décryptée.

## i18n FR/EN via OS + modifiable dans profile
- [ ] Détecter la locale OS au démarrage et initialiser `i18n`.
- [ ] Ajouter dans `ProfilePanel` un choix langue (FR/EN) et sauvegarder via `/auth/profile`.
- [ ] Côté serveur: stocker `language` sur l’utilisateur.

## Test
- [ ] Relancer client (sans crash) et valider: tchat/voice avatars, admin stats, décryption, langue.

