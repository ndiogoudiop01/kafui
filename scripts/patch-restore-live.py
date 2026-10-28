import sys, re, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text()

old = '''pick() {   # pick <motif-service> : un seul conteneur EN MARCHE, sinon on s'arrête
  local svc="$1" hits
  hits="$(docker ps --format '{{.ID}} {{.Names}}' | awk -v s="${SLUG}" -v v="${svc}" \\
          '$0 ~ s && $0 ~ v {print $1}')"
  local n; n="$(printf '%s' "${hits}" | grep -c . || true)"
  [ "${n}" -eq 1 ] || { printf '%s\\n' "${hits}" >&2; return 1; }
  printf '%s' "${hits}"
}'''

new = '''pick() {   # pick <service> : un seul conteneur EN MARCHE pour ce service
  local svc="$1" hits n
  #  Filtrer sur le LABEL, pas sur le nom : le nom de projet peut lui-meme
  #  contenir le mot « odoo » (ex. kafui-odoo19-entreprise19-xxxx-proxy-1),
  #  auquel cas un filtre textuel fait correspondre les quatre services.
  #  Le label com.docker.compose.service est pose par compose, donc par
  #  Dokploy comme par Coolify.
  hits="$(docker ps -q --filter "label=com.docker.compose.service=${svc}" \\
                       --filter "name=${SLUG}")"
  if [ -z "${hits}" ]; then
    #  Repli pour un conteneur sans label : on exige le suffixe -<service>-<n>
    hits="$(docker ps --format '{{.ID}} {{.Names}}' \\
            | awk -v s="${SLUG}" -v v="${svc}" \\
                  '$2 ~ s && $2 ~ ("-" v "-[0-9]+$") {print $1}')"
  fi
  n="$(printf '%s' "${hits}" | grep -c . || true)"
  [ "${n}" -eq 1 ] || { printf '%s\\n' "${hits}" >&2; return 1; }
  printf '%s' "${hits}"
}'''

if old not in s:
    sys.exit("bloc pick() introuvable — le fichier a-t-il deja ete modifie ?")
p.write_text(s.replace(old, new))
print("pick() corrige")
