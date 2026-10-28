#!/usr/bin/env bash
###############################################################################
#  restore-live.sh — restaure une base Odoo dans une stack DÉJÀ EN SERVICE,
#  qu'elle soit pilotée par Dokploy, Coolify ou docker compose.
#
#  POURQUOI CE SCRIPT :
#  `make restore` lance `docker compose` depuis clients/<slug>/, donc dans un
#  projet Docker nommé d'après le DOSSIER. Quand la stack appartient à Dokploy
#  ou Coolify, elle vit dans un projet nommé « <slug>-xxxx-<uuid> » : aucun
#  conteneur, aucun volume, aucun réseau en commun. D'où le
#      service "backup" is not running
#  et, si on insistait, une restauration dans une base vide sans rapport.
#  Ce script ne passe pas par compose : il trouve les conteneurs qui TOURNENT
#  et travaille dedans.
#
#  USAGE
#      ./restore-live.sh -s <slug> -d <base> <fichier> [--filestore <dir|zip>] [--keep]
#
#      -s   motif identifiant la stack (ex. jed) — défaut : nom du dossier courant
#      -d   nom de la base cible       (ex. jed) — défaut : DB_NAME du .env local
#      --keep       ne pas désactiver les crons et les serveurs SMTP
#      --no-filestore  ignorer le filestore présent dans l'archive
#      -n           simulation : montre ce qui serait fait, n'écrit rien
#
#  FORMATS acceptés, détectés sur le contenu :
#      .zip (sauvegarde Odoo)  ·  .sql  ·  .sql.gz  ·  .tar.gz (backup.sh)
#      ·  dump binaire pg_dump -Fc
#
#  ATTENTION : la base cible est SUPPRIMÉE puis recréée. Irréversible.
###############################################################################
set -euo pipefail

c_ok=$'\033[32m'; c_w=$'\033[33m'; c_e=$'\033[31m'; c_off=$'\033[0m'
log()  { printf '[restore] %s\n' "$*"; }
ok()   { printf '%s✓%s %s\n' "${c_ok}" "${c_off}" "$*"; }
warn() { printf '%s⚠%s %s\n' "${c_w}"  "${c_off}" "$*"; }
die()  { printf '%s✗%s %s\n' "${c_e}"  "${c_off}" "$*" >&2; exit 1; }

SLUG=""; TARGET_DB=""; SRC=""; FS_OVERRIDE=""; KEEP=0; NO_FS=0; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    -s) SLUG="${2:?}"; shift 2 ;;
    -d) TARGET_DB="${2:?}"; shift 2 ;;
    --filestore) FS_OVERRIDE="${2:?}"; shift 2 ;;
    --keep) KEEP=1; shift ;;
    --no-filestore) NO_FS=1; shift ;;
    -n|--dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,32p' "$0"; exit 0 ;;
    -*) die "option inconnue : $1" ;;
    *)  SRC="$1"; shift ;;
  esac
done

[ -n "${SRC}" ] || die "usage : $0 -s <slug> -d <base> <fichier>  (-h pour l'aide)"
[ -f "${SRC}" ] || die "fichier introuvable : ${SRC}"

[ -n "${SLUG}" ] || SLUG="$(basename "$PWD")"
if [ -z "${TARGET_DB}" ] && [ -f ./.env ]; then
  TARGET_DB="$(sed -n 's/^DB_NAME=\([^ #]*\).*/\1/p' ./.env | head -1)"
fi
[ -n "${TARGET_DB}" ] || die "base cible inconnue : précisez -d <base>"

command -v docker >/dev/null || die "docker introuvable"

# ------------------------------------------------- 1. trouver les conteneurs
pick() {   # pick <motif-service> : un seul conteneur EN MARCHE, sinon on s'arrête
  local svc="$1" hits
  hits="$(docker ps --format '{{.ID}} {{.Names}}' | awk -v s="${SLUG}" -v v="${svc}" \
          '$0 ~ s && $0 ~ v {print $1}')"
  local n; n="$(printf '%s' "${hits}" | grep -c . || true)"
  [ "${n}" -eq 1 ] || { printf '%s\n' "${hits}" >&2; return 1; }
  printf '%s' "${hits}"
}

DB="$(pick db)"   || die "conteneur « db » de la stack « ${SLUG} » : 0 ou plusieurs trouvés.
         Vérifiez :  docker ps --format '{{.Names}}' | grep ${SLUG}
         La stack est-elle démarrée ?"
OD="$(pick odoo)" || die "conteneur « odoo » de la stack « ${SLUG} » : 0 ou plusieurs trouvés."

ok "db   : $(docker inspect -f '{{.Name}}' "${DB}" | cut -c2-)"
ok "odoo : $(docker inspect -f '{{.Name}}' "${OD}" | cut -c2-)"

PGUSER_IN="$(docker exec "${DB}" printenv POSTGRES_USER 2>/dev/null || true)"
[ -n "${PGUSER_IN}" ] || PGUSER_IN=odoo
ok "rôle PostgreSQL : ${PGUSER_IN}"

docker exec "${DB}" pg_isready -U "${PGUSER_IN}" -d postgres >/dev/null \
  || die "PostgreSQL ne répond pas dans ${DB}"

# ------------------------------------------------- 2. préparer la source
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

magic="$(dd if="${SRC}" bs=5 count=1 2>/dev/null | od -An -tx1 | tr -d ' \n')"
DUMP=""; FS_IN=""; SRC_DB=""; MODE="sql"

case "${magic}" in
  504b03*)                                   # PK.. -> zip Odoo
    log "format : sauvegarde Odoo (.zip)"
    if command -v unzip >/dev/null; then unzip -q "${SRC}" -d "${WORK}/z"
    else python3 -I -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
           "${SRC}" "${WORK}/z"; fi
    DUMP="$(find "${WORK}/z" -maxdepth 2 -name 'dump.sql' | head -1)"
    [ -n "${DUMP}" ] || die "pas de dump.sql dans l'archive"
    FS_IN="$(find "${WORK}/z" -maxdepth 2 -type d -name 'filestore' | head -1)"
    ;;
  1f8b*)                                     # gzip : tar.gz ou sql.gz
    inner="$(gunzip -c "${SRC}" 2>/dev/null | dd bs=1 skip=257 count=5 2>/dev/null || true)"
    if [ "${inner}" = "ustar" ]; then
      log "format : archive tar.gz (backup.sh)"
      tar -xzf "${SRC}" -C "${WORK}"
      SRC_DB="$(sed -n 's/^database=//p' "${WORK}/manifest.txt" 2>/dev/null || true)"
      DUMP="$(find "${WORK}" -maxdepth 2 -name 'dump.sql' | head -1)"
      FS_IN="$(find "${WORK}" -maxdepth 2 -type d -name 'filestore' | head -1)"
    else
      log "format : dump SQL compressé (.sql.gz)"
      gunzip -c "${SRC}" > "${WORK}/dump.sql"; DUMP="${WORK}/dump.sql"
    fi
    ;;
  5047444d*)                                 # PGDMP
    log "format : dump binaire pg_dump -Fc"
    DUMP="${SRC}"; MODE="pgcustom"
    ;;
  *)  log "format : dump SQL en clair"; DUMP="${SRC}" ;;
esac

[ "${NO_FS}" -eq 1 ] && FS_IN=""
[ -n "${FS_OVERRIDE}" ] && FS_IN="${FS_OVERRIDE}"

# ------------------------------------------------- 3. pré-vol
if [ "${MODE}" = "sql" ] && grep -qim1 'CREATE EXTENSION.*vector' "${DUMP}"; then
  if ! docker exec "${DB}" psql -U "${PGUSER_IN}" -d postgres -tAc \
        "SELECT 1 FROM pg_available_extensions WHERE name='vector'" | grep -q 1; then
    die "ce dump exige l'extension « vector » (pgvector), absente de l'image PostgreSQL.
         Passez le service db sur  pgvector/pgvector:pg16  puis redéployez."
  fi
  ok "extension vector disponible"
fi

printf '\n'
log "source      : ${SRC}"
log "base cible  : ${TARGET_DB}   (sera SUPPRIMÉE puis recréée)"
log "filestore   : ${FS_IN:-aucun}"
[ "${DRY}" -eq 1 ] && { warn "simulation : rien n'a été écrit"; exit 0; }
printf '\n'

# ------------------------------------------------- 4. figer Odoo
POLICY="$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "${OD}")"
docker update --restart=no "${OD}" >/dev/null
docker stop "${OD}" >/dev/null
ok "odoo arrêté (politique de redémarrage neutralisée : ${POLICY})"

relance() {
  docker update --restart="${POLICY:-unless-stopped}" "${OD}" >/dev/null 2>&1 || true
  docker start "${OD}" >/dev/null 2>&1 || true
}
trap 'rm -rf "${WORK}"; relance' EXIT

# ------------------------------------------------- 5. recréer et charger
docker cp "${DUMP}" "${DB}:/tmp/restore-dump" >/dev/null
ok "dump copié dans le conteneur db ($(du -h "${DUMP}" | cut -f1))"

docker exec -i "${DB}" psql -v ON_ERROR_STOP=1 -q -U "${PGUSER_IN}" -d postgres <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
 WHERE datname = '${TARGET_DB}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "${TARGET_DB}";
CREATE DATABASE "${TARGET_DB}" TEMPLATE template0 ENCODING 'UTF8';
SQL
#  Vérification explicite : un « docker exec » sans -i n'attache pas stdin,
#  psql ne reçoit alors jamais le script SQL et sort sans rien faire. Le DROP /
#  CREATE passait inaperçu et l'échec ne surgissait qu'au chargement, avec un
#  « database does not exist » incompréhensible. On contrôle donc le résultat.
EXISTS_SQL="SELECT 1 FROM pg_database WHERE datname = '${TARGET_DB}'"
docker exec "${DB}" psql -tAq -U "${PGUSER_IN}" -d postgres -c "${EXISTS_SQL}" \
  | grep -q 1 \
  || die "la base ${TARGET_DB} est absente apres le CREATE DATABASE : le script
         SQL n a pas ete execute. Verifiez que la commande comporte bien
         « docker exec -i », sans quoi psql ne lit pas son entree standard."
ok "base ${TARGET_DB} recréée (présence vérifiée)"

log "chargement — plusieurs minutes sur un gros dump"
if [ "${MODE}" = "pgcustom" ]; then
  docker exec "${DB}" pg_restore --no-owner --no-privileges --exit-on-error \
       -U "${PGUSER_IN}" -d "${TARGET_DB}" /tmp/restore-dump
else
  docker exec "${DB}" psql -v ON_ERROR_STOP=1 -q -U "${PGUSER_IN}" \
       -d "${TARGET_DB}" -f /tmp/restore-dump
fi
docker exec "${DB}" rm -f /tmp/restore-dump
ok "dump chargé"

# ------------------------------------------------- 6. filestore
if [ -n "${FS_IN}" ] && [ -d "${FS_IN}" ]; then
  SUB="${FS_IN}"
  if [ -n "${SRC_DB}" ] && [ -d "${FS_IN}/${SRC_DB}" ]; then
    SUB="${FS_IN}/${SRC_DB}"
  else
    first="$(find "${FS_IN}" -mindepth 1 -maxdepth 1 -type d | head -1)"
    [ -n "${first}" ] && SUB="${first}"      # filestore/<base>/ab/...
  fi
  docker exec "${OD}" sh -c "rm -rf /var/lib/odoo/filestore/${TARGET_DB}; \
                             mkdir -p /var/lib/odoo/filestore" >/dev/null
  docker cp "${SUB}/." "${OD}:/var/lib/odoo/filestore/${TARGET_DB}" >/dev/null
  docker exec -u 0 "${OD}" chown -R odoo:odoo "/var/lib/odoo/filestore/${TARGET_DB}" || true
  ok "filestore restauré ($(du -sh "${SUB}" | cut -f1))"
else
  warn "aucun filestore : pièces jointes, images et PDF seront absents"
fi

# ------------------------------------------------- 7. neutralisation
if [ "${KEEP}" -eq 0 ]; then
  docker exec -i "${DB}" psql -q -U "${PGUSER_IN}" -d "${TARGET_DB}" >/dev/null 2>&1 <<'SQL' || true
UPDATE ir_cron SET active = false;
UPDATE ir_mail_server SET active = false;
DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code','database.uuid');
SQL
  ok "crons et serveurs SMTP désactivés (--keep pour les conserver)"
fi

# ------------------------------------------------- 8. contrôles
q() { docker exec "${DB}" psql -tAq -U "${PGUSER_IN}" -d "${TARGET_DB}" -c "$1" 2>/dev/null; }
NB="$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" || echo 0)"
VER="$(q "SELECT latest_version FROM ir_module_module WHERE name='base'" || echo '?')"
ATT="$(q "SELECT count(*) FROM ir_attachment WHERE store_fname IS NOT NULL" || echo '?')"

printf '\n'
ok "tables        : ${NB}"
ok "version Odoo  : ${VER}"
ok "attachments   : ${ATT}"
[ "${NB}" -gt 50 ] || warn "très peu de tables — le dump était-il complet ?"

trap 'rm -rf "${WORK}"' EXIT
relance
ok "odoo redémarré"
printf '\n'
log "suivez le démarrage :  docker logs -f ${OD}"
log "la version ci-dessus doit correspondre à l'image de base, sinon Odoo refusera de démarrer"
